from __future__ import annotations

import unittest

from tools.llm_grade import (
    build_grading_messages,
    build_reasoning_config,
    normalize_grade,
    parse_json_object,
)


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
        self.assertIn("問題文:", user_message)
        self.assertIn("Problem text", user_message)
        self.assertIn("模範回答 / 採点ガイド:", user_message)
        self.assertIn("Reference answer text", user_message)
        self.assertIn("Submitted answer", user_message)
        self.assertIn("日本語で書いてください", messages[0]["content"])


class BuildReasoningConfigTest(unittest.TestCase):
    def test_builds_reasoning_config_from_autograde_config(self) -> None:
        reasoning = build_reasoning_config(
            {
                "reasoning_effort": "minimal",
                "reasoning_exclude": True,
            }
        )

        self.assertEqual(reasoning, {"effort": "minimal", "exclude": True})


class ParseJsonObjectTest(unittest.TestCase):
    def test_parses_fenced_json_object(self) -> None:
        parsed = parse_json_object('```json\n{"score": 100}\n```')

        self.assertEqual(parsed, {"score": 100})

    def test_parses_json_object_with_prefix(self) -> None:
        parsed = parse_json_object('結果:\n{"score": 80}\n以上')

        self.assertEqual(parsed, {"score": 80})


class NormalizeGradeTest(unittest.TestCase):
    def test_normalizes_common_model_schema_drift(self) -> None:
        normalized = normalize_grade(
            {
                "total": 98,
                "summary": "ok",
                "items": [
                    {
                        "name": "定義",
                        "score": 25,
                        "max_score": 25,
                        "comment": "ok",
                    }
                ],
            }
        )

        self.assertEqual(normalized["score"], 98)
        self.assertFalse(normalized["needs_human_review"])
        self.assertEqual(normalized["items"][0]["points"], 25)
        self.assertEqual(normalized["items"][0]["max_points"], 25)


if __name__ == "__main__":
    unittest.main()
