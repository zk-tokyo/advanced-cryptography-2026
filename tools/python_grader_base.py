#!/usr/bin/env python3
"""Helpers for deterministic Python execution graders."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Any


Grade = dict[str, Any]
DEFAULT_TIMEOUT_SECONDS = 3


@dataclass(frozen=True)
class PythonTestCase:
    name: str
    max_points: float
    code: str


@dataclass(frozen=True)
class PythonTestResult:
    passed: bool
    comment: str


def run_python_grader(
    *,
    test_cases: list[PythonTestCase],
    required_file: str = "solution.py",
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> int:
    """Run Python tests with the standard CLI and JSON output contract."""
    args = parse_args()
    submission_dir = Path(args.submission_dir)
    output_path = Path(args.output)
    submission_file = (submission_dir / required_file).resolve()

    if not submission_file.exists():
        write_grade(
            output_path,
            {
                "score": 0,
                "summary": f"必須ファイル `{required_file}` が見つかりません。",
                "items": [
                    {
                        "name": "提出形式",
                        "points": 0,
                        "max_points": 100,
                        "comment": f"`{required_file}` を提出してください。",
                    }
                ],
                "needs_human_review": False,
            },
        )
        return 0

    items: list[dict[str, Any]] = []
    score = 0.0
    for test_case in test_cases:
        result = run_test_case(
            submission_file=submission_file,
            test_case=test_case,
            timeout_seconds=timeout_seconds,
        )
        points = test_case.max_points if result.passed else 0.0
        score += points
        items.append(
            {
                "name": test_case.name,
                "points": points,
                "max_points": test_case.max_points,
                "comment": result.comment,
            }
        )

    passed_count = sum(1 for item in items if item["points"] == item["max_points"])
    write_grade(
        output_path,
        {
            "score": score,
            "summary": f"Pythonテスト {passed_count}/{len(test_cases)} 件に合格しました。",
            "items": items,
            "needs_human_review": False,
        },
    )
    return 0


def run_test_case(
    *,
    submission_file: Path,
    test_case: PythonTestCase,
    timeout_seconds: int,
) -> PythonTestResult:
    runner = build_runner_source(submission_file, test_case.code)
    with tempfile.TemporaryDirectory(prefix="python-grader-") as temp_dir_name:
        runner_path = Path(temp_dir_name) / "run_case.py"
        runner_path.write_text(runner, encoding="utf-8")
        try:
            completed = subprocess.run(
                [sys.executable, "-I", str(runner_path)],
                cwd=temp_dir_name,
                env=minimal_env(),
                text=True,
                capture_output=True,
                timeout=timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return PythonTestResult(
                False,
                f"テストが {timeout_seconds} 秒以内に終了しませんでした。",
            )

    if completed.returncode == 0:
        return PythonTestResult(True, "合格しました。")

    detail = completed.stderr.strip() or completed.stdout.strip() or "テストが失敗しました。"
    return PythonTestResult(False, clip_detail(detail))


def build_runner_source(submission_file: Path, test_code: str) -> str:
    test_block = textwrap.dedent(test_code).strip()
    preamble = textwrap.dedent(
        f"""
        from __future__ import annotations

        import importlib.util
        from pathlib import Path

        submission_path = Path({str(submission_file)!r})
        spec = importlib.util.spec_from_file_location("student_solution", submission_path)
        if spec is None or spec.loader is None:
            raise RuntimeError("solution.py を読み込めません。")
        student = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(student)
        """
    )
    return f"{preamble}\n{test_block}\n"


def minimal_env() -> dict[str, str]:
    env: dict[str, str] = {}
    for key in ("PATH", "SYSTEMROOT", "WINDIR"):
        value = os.environ.get(key)
        if value:
            env[key] = value
    env["PYTHONUTF8"] = "1"
    return env


def clip_detail(detail: str, max_length: int = 800) -> str:
    if len(detail) <= max_length:
        return detail
    return detail[: max_length - 3] + "..."


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("python",), default="python")
    parser.add_argument("--submission-dir", required=True)
    parser.add_argument("--config")
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def write_grade(path: Path, grade: Grade) -> None:
    path.write_text(json.dumps(grade, ensure_ascii=False, indent=2), encoding="utf-8")
