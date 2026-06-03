from __future__ import annotations

import unittest

from tools.llm_grade import build_grading_messages


class BuildGradingMessagesTest(unittest.TestCase):
    def test_includes_problem_statement_and_reference_answer(self) -> None:
        messages = build_grading_messages(
            problem_statement="Problem text",
            rubric="Rubric text",
            reference_answer="Reference answer text",
            extra_instructions="Extra instructions",
            submission_text="Submitted answer",
        )

        user_message = messages[1]["content"]
        self.assertIn("Problem statement:", user_message)
        self.assertIn("Problem text", user_message)
        self.assertIn("Reference answer / grading guide:", user_message)
        self.assertIn("Reference answer text", user_message)
        self.assertIn("Submitted answer", user_message)


if __name__ == "__main__":
    unittest.main()
