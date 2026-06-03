#!/usr/bin/env python3
"""Week 1 dummy grader for validating the autograding workflow."""

from __future__ import annotations

from tools.grader_base import Grade, Submission, cap_score, run_llm_grader


PROBLEM_STATEMENT = """
Explain why the toy commitment Com(m; r) = H(m || r) is binding only as long as
the hash function H is collision resistant.

The answer should:
1. State the binding property for this construction.
2. Explain how two different valid openings imply a collision in H.
3. Mention at least one limitation of the toy construction.

The expected submitted file is answer.md.
"""


RUBRIC = """
Grade out of 100 points.

- Binding definition: 25 points
- Reduction from two openings to a hash collision: 40 points
- Clear explanation of assumptions and limitations: 20 points
- Organization and notation: 15 points

Award partial credit for substantially correct reasoning even if notation is not
perfect. Do not require the exact wording of the reference answer.
"""


REFERENCE_ANSWER = """
A commitment is binding if, after publishing c = H(m || r), it is infeasible for
an adversary to find two distinct openings (m, r) and (m', r') such that both
verify against the same commitment c.

For this construction, two distinct valid openings satisfy
H(m || r) = c = H(m' || r'). If the encoded strings m || r and m' || r' are
different, this is a collision in H. Therefore, an adversary who breaks binding
can be used to find a collision in the hash function, assuming the encoding is
unambiguous.

Limitations include that this toy construction does not by itself prove hiding,
depends on collision resistance and unambiguous encoding, and may need domain
separation or length-prefixing in real protocols.
"""


EXTRA_INSTRUCTIONS = """
Be strict about answers that only say "because hashes are secure" without
showing the collision argument.
"""


def adjust_grade(grade: Grade, submission: Submission) -> Grade:
    if not submission.has_file_named("answer.md"):
        return cap_score(grade, 80, reason="The required answer.md file is missing.")
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
