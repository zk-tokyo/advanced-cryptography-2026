#!/usr/bin/env python3
"""Convenience wrapper for weekly grader.py files."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from tools.llm_grade import grade_submission


Grade = dict[str, Any]
AdjustGrade = Callable[[Grade, "Submission"], Grade]


@dataclass(frozen=True)
class Submission:
    """Read-only helper around a student's submitted files."""

    root: Path

    def files(self) -> list[Path]:
        return sorted(path for path in self.root.rglob("*") if path.is_file())

    def is_empty(self) -> bool:
        return not self.files()

    def has_file_named(self, name: str) -> bool:
        return any(path.name == name for path in self.files())

    def has_file_prefix(self, prefix: str) -> bool:
        return any(path.name.startswith(prefix) for path in self.files())

    def read_text(self, relative_path: str) -> str:
        path = self.root / relative_path
        return path.read_text(encoding="utf-8")


def run_llm_grader(
    *,
    problem_statement: str = "",
    rubric: str,
    reference_answer: str = "",
    extra_instructions: str = "",
    adjust_grade: AdjustGrade | None = None,
) -> int:
    """Run a weekly LLM grader with the standard CLI and JSON output contract."""
    args = parse_args()
    config = load_json(Path(args.config))
    submission = Submission(Path(args.submission_dir))

    if submission.is_empty():
        write_grade(Path(args.output), empty_submission_grade())
        return 0

    grade = grade_submission(
        submission_dir=submission.root,
        problem_statement=problem_statement,
        rubric=rubric,
        reference_answer=reference_answer,
        config=config,
        extra_instructions=extra_instructions,
    )
    if adjust_grade is not None:
        grade = adjust_grade(grade, submission)

    write_grade(Path(args.output), grade)
    return 0


def cap_score(grade: Grade, max_score: float, *, reason: str) -> Grade:
    """Cap a score and append a visible rubric item explaining why."""
    grade["score"] = min(float(grade.get("score", 0)), max_score)
    add_item(
        grade,
        name="Programmatic adjustment",
        points=0,
        max_points=0,
        comment=f"Score capped at {max_score:g}. {reason}",
    )
    return grade


def add_item(
    grade: Grade,
    *,
    name: str,
    points: float,
    max_points: float,
    comment: str,
) -> Grade:
    items = grade.get("items")
    if not isinstance(items, list):
        items = []
        grade["items"] = items
    items.append(
        {
            "name": name,
            "points": points,
            "max_points": max_points,
            "comment": comment,
        }
    )
    return grade


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("llm",), default="llm")
    parser.add_argument("--submission-dir", required=True)
    parser.add_argument("--config", required=True)
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object.")
    return data


def write_grade(path: Path, grade: Grade) -> None:
    path.write_text(json.dumps(grade, ensure_ascii=False, indent=2), encoding="utf-8")


def empty_submission_grade() -> Grade:
    return {
        "score": 0,
        "summary": "Submission directory is empty.",
        "items": [],
        "needs_human_review": True,
    }
