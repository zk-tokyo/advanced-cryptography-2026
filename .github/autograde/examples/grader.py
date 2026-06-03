#!/usr/bin/env python3
"""Example weekly grader.

Copy this file to weekN/exercises/grader.py and customize the constants below.
"""

from __future__ import annotations

from tools.grader_base import Grade, Submission, cap_score, run_llm_grader


PROBLEM_STATEMENT = """
Write the assignment prompt, assumptions, allowed tools or theorems, and expected
submission format here. This text is used only to help the LLM grade correctly.
"""


RUBRIC = """
Grade this assignment out of 100 points.

- Correctness and mathematical soundness: 50 points
- Clarity of explanation and notation: 25 points
- Completeness of required answers: 15 points
- Reproducibility or code quality, if code is submitted: 10 points

Assign partial credit when the reasoning is substantially correct but incomplete.
Set needs_human_review=true for ambiguous proofs, possible academic integrity
concerns, or answers that depend on course-specific context not present here.
"""


REFERENCE_ANSWER = """
Write the reference answer, expected proof strategy, important lemmas, common
pitfalls, and partial-credit guidance here.

The submitted answer does not need to match this wording exactly. Use this as a
grading guide for correctness and completeness.
"""


EXTRA_INSTRUCTIONS = """
Be strict about unsupported claims. Do not reward answers that only repeat
definitions without applying them to the exercise.
"""


def adjust_grade(grade: Grade, submission: Submission) -> Grade:
    if not submission.has_file_prefix("answer"):
        return cap_score(
            grade,
            80,
            reason="No answer.* file was found.",
        )
    return grade


if __name__ == "__main__":
    raise SystemExit(
        run_llm_grader(
            problem_statement=PROBLEM_STATEMENT,
            rubric=RUBRIC,
            reference_answer=REFERENCE_ANSWER,
            extra_instructions=EXTRA_INSTRUCTIONS,
            adjust_grade=adjust_grade,
        )
    )
