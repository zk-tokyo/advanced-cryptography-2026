from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.grader_base import Submission, add_item, cap_score, run_llm_grader


class SubmissionTest(unittest.TestCase):
    def test_file_helpers(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "answer.md").write_text("hello", encoding="utf-8")
            submission = Submission(root)

            self.assertFalse(submission.is_empty())
            self.assertTrue(submission.has_file_named("answer.md"))
            self.assertTrue(submission.has_file_prefix("answer"))
            self.assertEqual(submission.read_text("answer.md"), "hello")


class GradeAdjustmentTest(unittest.TestCase):
    def test_add_item_initializes_items(self) -> None:
        grade = {"score": 90}

        add_item(grade, name="Format", points=0, max_points=0, comment="ok")

        self.assertEqual(len(grade["items"]), 1)

    def test_cap_score_appends_reason(self) -> None:
        grade = {"score": 95, "items": []}

        result = cap_score(grade, 80, reason="Missing required file.")

        self.assertEqual(result["score"], 80)
        self.assertEqual(len(result["items"]), 1)


class RunLlmGraderTest(unittest.TestCase):
    def test_passes_problem_statement_and_reference_answer(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            submission_dir = root / "submission"
            submission_dir.mkdir()
            (submission_dir / "answer.md").write_text("answer", encoding="utf-8")
            config_path = root / "config.json"
            output_path = root / "grade.json"
            config_path.write_text(json.dumps({"model": "test-model"}), encoding="utf-8")

            returned_grade = {
                "score": 100,
                "summary": "ok",
                "items": [],
                "needs_human_review": False,
            }
            argv = [
                "grader.py",
                "--submission-dir",
                str(submission_dir),
                "--config",
                str(config_path),
                "--output",
                str(output_path),
            ]

            with patch.object(sys, "argv", argv), patch(
                "tools.grader_base.grade_submission",
                return_value=returned_grade,
            ) as grade_submission_mock:
                result = run_llm_grader(
                    problem_statement="problem",
                    rubric="rubric",
                    reference_answer="reference",
                )

            self.assertEqual(result, 0)
            grade_submission_mock.assert_called_once()
            kwargs = grade_submission_mock.call_args.kwargs
            self.assertEqual(kwargs["problem_statement"], "problem")
            self.assertEqual(kwargs["rubric"], "rubric")
            self.assertEqual(kwargs["reference_answer"], "reference")
            self.assertEqual(json.loads(output_path.read_text(encoding="utf-8")), returned_grade)


if __name__ == "__main__":
    unittest.main()
