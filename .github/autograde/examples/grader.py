#!/usr/bin/env python3
"""週ごとの grader.py の例。

このファイルを weekN/exercises/grader.py にコピーして、下の定数を書き換えます。
"""

from __future__ import annotations

from tools.grader_base import Grade, Submission, cap_score, run_llm_grader


# PROBLEM_STATEMENT:
# LLMが問題の前提を取り違えないように、問題文・前提・提出形式を書く。
# 配布用の長い問題文を丸ごと貼る必要はなく、採点に必要な条件が入っていればよい。
PROBLEM_STATEMENT = """
トイコミットメント `Com(m; r) = H(m || r)` が、ハッシュ関数 `H` の衝突困難性に
依存してbindingであることを説明してください。

答案では次の点に触れてください。

1. この構成におけるbinding性の意味を述べる。
2. 2つの異なる有効なopeningが存在すると、`H` の衝突が得られることを説明する。
3. このトイ構成の限界を少なくとも1つ述べる。

提出ファイルは `answer.md` とします。
"""


# RUBRIC:
# 点数配分と部分点の方針を書く。合計は100点にするとCIの合否判定と合わせやすい。
RUBRIC = """
100点満点で採点してください。

- binding性の定義: 25点
- 2つのopeningからハッシュ衝突を導く説明: 40点
- 仮定と限界の説明: 20点
- 構成・記法・読みやすさ: 15点

表記が完全でなくても、実質的に正しい推論には部分点を与えてください。
模範回答と同じ言い回しである必要はありません。
"""


# REFERENCE_ANSWER:
# 模範回答や期待する証明方針を書く。LLMはこの文章との完全一致ではなく、
# 正しさ・重要論点・部分点判断の基準として使う。
REFERENCE_ANSWER = """
コミットメントがbindingであるとは、コミットメント値 `c = H(m || r)` を公開した後に、
同じ `c` に対して検証が通る2つの異なるopening `(m, r)` と `(m', r')` を見つけることが
困難である、という意味である。

この構成で2つの異なる有効なopeningが存在するなら、
`H(m || r) = c = H(m' || r')` が成り立つ。`m || r` と `m' || r'` のエンコードが
曖昧でなく、2つの入力文字列が異なるなら、これは `H` の衝突である。
したがってbinding性を破る攻撃者から、ハッシュ関数の衝突を見つける攻撃者を構成できる。

限界として、この構成だけではhiding性は示されないこと、衝突困難性と曖昧でない
エンコードに依存すること、実際のプロトコルではlength-prefixingやdomain separationが
必要になり得ることなどが挙げられる。
"""


# EXTRA_INSTRUCTIONS:
# 採点時の注意、厳しく見るポイント、人間レビューに回す条件を書く。
EXTRA_INSTRUCTIONS = """
「ハッシュは安全だからbindingである」とだけ述べ、衝突への帰着を示していない答案には
厳しく採点してください。採点結果の説明と各rubric項目のコメントは日本語で書いてください。
"""


def adjust_grade(grade: Grade, submission: Submission) -> Grade:
    if not submission.has_file_prefix("answer"):
        return cap_score(
            grade,
            80,
            reason="必須の answer.* ファイルが見つかりません。",
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
