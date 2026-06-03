#!/usr/bin/env python3
"""Run deterministic Python graders for pull requests.

This script is intended to run from a pull_request workflow without secrets.
It executes untrusted student Python only after checking out the PR head in a
separate directory and always runs trusted grader code from the base checkout.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.autograde_pr import (
    AutogradeError,
    build_context,
    evaluate_grade,
    list_pull_request_files,
    load_simple_yaml,
)


PYTHON_SUBMISSION_NAME = "solution.py"
PYTHON_SUBMISSION_RE = re.compile(
    r"^week(?P<week>0|[1-9][0-9]*)/exercises/submissions/(?P<submitter>[^/]+)/solution\.py$"
)


@dataclass(frozen=True)
class PythonClassification:
    should_grade: bool
    valid: bool
    week: str | None
    submitter: str | None
    reason: str


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--event-path", required=True)
    parser.add_argument("--base-dir", required=True)
    parser.add_argument("--head-dir", required=True)
    parser.add_argument("--config", required=True)
    args = parser.parse_args()

    try:
        event = load_json(Path(args.event_path))
        base_dir = Path(args.base_dir)
        head_dir = Path(args.head_dir)
        if has_github_token():
            changed_paths = changed_paths_from_event(event)
        else:
            changed_paths = diff_tracked_files(base_dir=base_dir, head_dir=head_dir)
        classification = classify_python_changed_files(changed_paths)

        if not classification.should_grade:
            write_step_summary("Python Grade", classification.reason)
            print(classification.reason)
            return 0

        if not classification.valid:
            write_step_summary("Python Grade Failed", classification.reason)
            print(classification.reason, file=sys.stderr)
            return 1

        config = load_simple_yaml(Path(args.config))
        pass_score = float(config.get("pass_score", 70))
        with tempfile.TemporaryDirectory(prefix="python-autograde-") as temp_dir_name:
            temp_dir = Path(temp_dir_name)
            grade = run_python_grader(
                base_dir=base_dir,
                head_dir=head_dir,
                classification=classification,
                temp_dir=temp_dir,
            )

        evaluated = evaluate_grade(grade, pass_score)
        write_grade_summary(evaluated, pass_score, classification)
        return 0 if evaluated["pass"] else 1
    except subprocess.TimeoutExpired as exc:
        message = f"Python grader timed out: {exc}"
        write_step_summary("Python Grade Failed", message)
        print(message, file=sys.stderr)
        return 1
    except Exception as exc:
        write_step_summary("Python Grade Failed", str(exc))
        print(str(exc), file=sys.stderr)
        return 1


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, dict):
        raise AutogradeError(f"Expected JSON object in {path}")
    return data


def changed_paths_from_event(event: dict[str, Any]) -> list[str]:
    context = build_context(event)
    paths: set[str] = set()
    for file_info in list_pull_request_files(context):
        filename = file_info.get("filename")
        previous_filename = file_info.get("previous_filename")
        if isinstance(filename, str) and filename:
            paths.add(filename)
        if isinstance(previous_filename, str) and previous_filename:
            paths.add(previous_filename)
    return sorted(paths)


def has_github_token() -> bool:
    return bool(os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN"))


def diff_tracked_files(*, base_dir: Path, head_dir: Path) -> list[str]:
    base_files = tracked_files(base_dir)
    head_files = tracked_files(head_dir)
    changed: list[str] = []
    for path in sorted(base_files | head_files):
        base_path = base_dir / path
        head_path = head_dir / path
        if path not in base_files or path not in head_files:
            changed.append(path)
        elif base_path.read_bytes() != head_path.read_bytes():
            changed.append(path)
    return changed


def tracked_files(root: Path) -> set[str]:
    completed = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z"],
        text=False,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        raise AutogradeError(f"git ls-files failed in {root}: {detail}")
    return {
        item.decode("utf-8")
        for item in completed.stdout.split(b"\0")
        if item
    }


def classify_python_changed_files(changed_paths: list[str]) -> PythonClassification:
    if not changed_paths:
        return PythonClassification(False, True, None, None, "No changed files; skipped.")

    python_submission_paths = [
        path for path in changed_paths if is_python_submission_path(path)
    ]
    if not python_submission_paths:
        return PythonClassification(False, True, None, None, "No Python solution.py submission changed.")

    invalid_paths = [path for path in changed_paths if not is_python_submission_path(path)]
    if invalid_paths:
        unique_paths = ", ".join(sorted(invalid_paths)[:10])
        return PythonClassification(
            True,
            False,
            None,
            None,
            f"Python submission PRs may only change solution.py. Invalid path(s): {unique_paths}",
        )

    weeks = {path.split("/", 1)[0] for path in python_submission_paths}
    submitters = {path.split("/")[3] for path in python_submission_paths}
    if len(weeks) != 1 or len(submitters) != 1:
        return PythonClassification(
            True,
            False,
            None,
            None,
            "Python submission PRs must target exactly one week and one submitter.",
        )

    week = next(iter(weeks))
    submitter = next(iter(submitters))
    return PythonClassification(
        True,
        True,
        week,
        submitter,
        f"Detected Python submission for {week} by {submitter}.",
    )


def is_python_submission_path(path: str) -> bool:
    return PYTHON_SUBMISSION_RE.match(path) is not None


def run_python_grader(
    *,
    base_dir: Path,
    head_dir: Path,
    classification: PythonClassification,
    temp_dir: Path,
) -> dict[str, Any]:
    week = classification.week or ""
    submitter = classification.submitter or ""
    grader_path = base_dir / week / "exercises" / "grader.py"
    submission_dir = head_dir / week / "exercises" / "submissions" / submitter
    output_path = temp_dir / "grade.json"

    if not grader_path.exists():
        raise AutogradeError(f"{grader_path} does not exist.")
    if not (submission_dir / PYTHON_SUBMISSION_NAME).exists():
        raise AutogradeError(f"{submission_dir / PYTHON_SUBMISSION_NAME} does not exist.")

    env = {
        "PATH": os.environ.get("PATH", ""),
        "PYTHONPATH": str(base_dir),
        "PYTHONUTF8": "1",
    }
    completed = subprocess.run(
        [
            sys.executable,
            str(grader_path),
            "--mode",
            "python",
            "--submission-dir",
            str(submission_dir),
            "--config",
            str(base_dir / ".github" / "autograde" / "config.yml"),
            "--output",
            str(output_path),
        ],
        cwd=base_dir,
        env=env,
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise AutogradeError(f"{grader_path} failed: {detail}")
    if not output_path.exists():
        raise AutogradeError(f"{grader_path} did not write {output_path}.")
    return load_json(output_path)


def write_grade_summary(
    grade: dict[str, Any],
    pass_score: float,
    classification: PythonClassification,
) -> None:
    status = "PASS" if grade["pass"] else "FAIL"
    lines = [
        "## Python Grade",
        "",
        f"- Result: **{status}**",
        f"- Week: `{classification.week}`",
        f"- Submitter: `{classification.submitter}`",
        f"- Score: **{grade['score']:.2f} / 100**",
        f"- Pass score: **{pass_score:.2f}**",
        "",
        "### Summary",
        "",
        str(grade["summary"]).strip(),
    ]

    items = grade.get("items", [])
    if items:
        lines.extend(["", "### Test Items", ""])
        for item in items:
            if isinstance(item, dict):
                name = item.get("name", "item")
                points = item.get("points", "?")
                max_points = item.get("max_points", "?")
                comment = item.get("comment", "")
                lines.append(f"- **{name}**: {points}/{max_points} - {comment}")
    write_step_summary_lines(lines)


def write_step_summary(title: str, message: str) -> None:
    write_step_summary_lines([f"## {title}", "", message])


def write_step_summary_lines(lines: list[str]) -> None:
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    content = "\n".join(lines) + "\n"
    if summary_path:
        with Path(summary_path).open("a", encoding="utf-8") as file:
            file.write(content)
    else:
        print(content)


if __name__ == "__main__":
    raise SystemExit(main())
