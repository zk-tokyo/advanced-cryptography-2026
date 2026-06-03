from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.python_grader_base import PythonTestCase, run_python_grader


class RunPythonGraderTest(unittest.TestCase):
    def test_grades_successful_solution(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            submission_dir = root / "submission"
            submission_dir.mkdir()
            (submission_dir / "solution.py").write_text(
                "def answer():\n    return 42\n",
                encoding="utf-8",
            )
            output_path = root / "grade.json"
            argv = [
                "python_grader.py",
                "--submission-dir",
                str(submission_dir),
                "--output",
                str(output_path),
            ]

            with patch.object(sys, "argv", argv):
                result = run_python_grader(
                    test_cases=[
                        PythonTestCase(
                            name="answer",
                            max_points=100,
                            code="assert student.answer() == 42",
                        )
                    ]
                )

            grade = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(result, 0)
            self.assertEqual(grade["score"], 100)

    def test_missing_solution_gets_zero(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            submission_dir = root / "submission"
            submission_dir.mkdir()
            output_path = root / "grade.json"
            argv = [
                "python_grader.py",
                "--submission-dir",
                str(submission_dir),
                "--output",
                str(output_path),
            ]

            with patch.object(sys, "argv", argv):
                result = run_python_grader(
                    test_cases=[
                        PythonTestCase(
                            name="answer",
                            max_points=100,
                            code="assert student.answer() == 42",
                        )
                    ]
                )

            grade = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(result, 0)
            self.assertEqual(grade["score"], 0)

    def test_timeout_is_recorded_as_failed_item(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            submission_dir = root / "submission"
            submission_dir.mkdir()
            (submission_dir / "solution.py").write_text(
                "def loop():\n    while True:\n        pass\n",
                encoding="utf-8",
            )
            output_path = root / "grade.json"
            argv = [
                "python_grader.py",
                "--submission-dir",
                str(submission_dir),
                "--output",
                str(output_path),
            ]

            with patch.object(sys, "argv", argv):
                result = run_python_grader(
                    test_cases=[
                        PythonTestCase(
                            name="timeout",
                            max_points=100,
                            code="student.loop()",
                        )
                    ],
                    timeout_seconds=1,
                )

            grade = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(result, 0)
            self.assertEqual(grade["score"], 0)
            self.assertIn("終了しませんでした", grade["items"][0]["comment"])


if __name__ == "__main__":
    unittest.main()
