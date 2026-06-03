from __future__ import annotations

import unittest

from tools.python_autograde_pr import classify_python_changed_files


class ClassifyPythonChangedFilesTest(unittest.TestCase):
    def test_skips_non_python_submission(self) -> None:
        result = classify_python_changed_files(
            ["week0/exercises/submissions/alice/answer.md"]
        )

        self.assertFalse(result.should_grade)
        self.assertTrue(result.valid)

    def test_accepts_solution_submission(self) -> None:
        result = classify_python_changed_files(
            ["week0/exercises/submissions/alice/solution.py"]
        )

        self.assertTrue(result.should_grade)
        self.assertTrue(result.valid)
        self.assertEqual(result.week, "week0")
        self.assertEqual(result.submitter, "alice")

    def test_rejects_mixed_solution_and_other_file(self) -> None:
        result = classify_python_changed_files(
            [
                "week0/exercises/submissions/alice/solution.py",
                "week0/exercises/submissions/alice/helper.py",
            ]
        )

        self.assertTrue(result.should_grade)
        self.assertFalse(result.valid)

    def test_ignores_invalid_week_number_shape(self) -> None:
        result = classify_python_changed_files(
            ["week00/exercises/submissions/alice/solution.py"]
        )

        self.assertFalse(result.should_grade)


if __name__ == "__main__":
    unittest.main()
