from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from tools.autograde_pr import (
    classify_changed_files,
    evaluate_grade,
    has_python_solution_submission,
    load_simple_yaml,
    prepare_runtime_config,
)


class ClassifyChangedFilesTest(unittest.TestCase):
    def test_skips_non_submission_pr(self) -> None:
        result = classify_changed_files([{"filename": "README.md"}])

        self.assertFalse(result.should_grade)
        self.assertTrue(result.valid)

    def test_accepts_single_week_single_submitter(self) -> None:
        result = classify_changed_files(
            [{"filename": "week1/exercises/submissions/alice/answer.md"}]
        )

        self.assertTrue(result.should_grade)
        self.assertTrue(result.valid)
        self.assertEqual(result.week, "week1")
        self.assertEqual(result.submitter, "alice")

    def test_accepts_week_zero_sample_submission(self) -> None:
        result = classify_changed_files(
            [{"filename": "week0/exercises/submissions/alice/answer.md"}]
        )

        self.assertTrue(result.should_grade)
        self.assertTrue(result.valid)
        self.assertEqual(result.week, "week0")
        self.assertEqual(result.submitter, "alice")

    def test_ignores_submission_gitkeep(self) -> None:
        result = classify_changed_files(
            [
                {"filename": "week0/exercises/submissions/.gitkeep"},
                {"filename": "README.md"},
            ]
        )

        self.assertFalse(result.should_grade)
        self.assertTrue(result.valid)

    def test_rejects_mixed_submission_and_non_submission_paths(self) -> None:
        result = classify_changed_files(
            [
                {"filename": "week1/exercises/submissions/alice/answer.md"},
                {"filename": "week1/exercises/grader.py"},
            ]
        )

        self.assertTrue(result.should_grade)
        self.assertFalse(result.valid)

    def test_rejects_multiple_submitters(self) -> None:
        result = classify_changed_files(
            [
                {"filename": "week1/exercises/submissions/alice/answer.md"},
                {"filename": "week1/exercises/submissions/bob/answer.md"},
            ]
        )

        self.assertTrue(result.should_grade)
        self.assertFalse(result.valid)

    def test_rejects_multiple_weeks(self) -> None:
        result = classify_changed_files(
            [
                {"filename": "week1/exercises/submissions/alice/answer.md"},
                {"filename": "week2/exercises/submissions/alice/answer.md"},
            ]
        )

        self.assertTrue(result.should_grade)
        self.assertFalse(result.valid)

    def test_detects_python_solution_submission(self) -> None:
        result = has_python_solution_submission(
            [{"filename": "week0/exercises/submissions/alice/solution.py"}]
        )

        self.assertTrue(result)


class EvaluateGradeTest(unittest.TestCase):
    def test_score_at_threshold_passes(self) -> None:
        result = evaluate_grade(
            {
                "score": 70,
                "summary": "ok",
                "items": [],
                "needs_human_review": False,
            },
            70,
        )

        self.assertTrue(result["pass"])

    def test_score_below_threshold_fails(self) -> None:
        result = evaluate_grade(
            {
                "score": 69.99,
                "summary": "almost",
                "items": [],
                "needs_human_review": False,
            },
            70,
        )

        self.assertFalse(result["pass"])

    def test_blank_summary_gets_fallback(self) -> None:
        result = evaluate_grade(
            {
                "score": 70,
                "summary": "",
                "items": [],
                "needs_human_review": False,
            },
            70,
        )

        self.assertEqual(result["summary"], "No grading summary was provided.")


class ConfigTest(unittest.TestCase):
    def test_loads_simple_yaml_and_runtime_config(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "config.yml"
            path.write_text(
                "\n".join(
                    [
                        "provider: openrouter",
                        "model: shared-model",
                        "pass_score: 70",
                    ]
                ),
                encoding="utf-8",
            )

            raw = load_simple_yaml(path)
            self.assertEqual(raw["model"], "shared-model")

            classification = classify_changed_files(
                [{"filename": "week1/exercises/submissions/alice/answer.md"}]
            )
            old_model = os.environ.pop("AUTOGRADE_MODEL", None)
            old_provider = os.environ.pop("AUTOGRADE_PROVIDER", None)
            try:
                config = prepare_runtime_config(path, classification)
            finally:
                if old_model is not None:
                    os.environ["AUTOGRADE_MODEL"] = old_model
                if old_provider is not None:
                    os.environ["AUTOGRADE_PROVIDER"] = old_provider

            self.assertEqual(config["model"], "shared-model")
            self.assertEqual(config["week"], "week1")
            self.assertEqual(config["submitter"], "alice")


if __name__ == "__main__":
    unittest.main()
