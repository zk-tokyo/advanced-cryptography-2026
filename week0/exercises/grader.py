#!/usr/bin/env python3
"""Week 0 sample grader for validating the autograding workflow."""

from __future__ import annotations

import argparse

from tools.grader_base import run_llm_grader
from tools.python_grader_base import PythonTestCase, run_python_grader


# 問題文:
# LLMが課題の前提や提出形式を取り違えないように、採点に必要な問題内容を書く。
PROBLEM_STATEMENT = """
提出者は次の3問のうち、いずれか1問を選んで回答します。答案の冒頭には
`選択: 問題1`、`選択: 問題2`、または `選択: 問題3` のように、選んだ問題番号を
明記するよう案内しています。

問題1: 難易度 低
コミットメント方式におけるbinding性とhiding性について説明してください。

答案では、次の点に触れる必要があります。
1. binding性が何を保証する性質かを述べる。
2. hiding性が何を保証する性質かを述べる。
3. それぞれの性質が、コミットメントのどの段階で重要になるかを説明する。

問題2: 難易度 中
トイコミットメント `Com(m; r) = H(m || r)` が、ハッシュ関数 `H` の衝突困難性に
依存してbindingである理由を説明してください。

答案では、次の点に触れる必要があります。
1. この構成におけるbinding性の意味を述べる。
2. 2つの異なる有効なopeningが存在すると、`H` の衝突が得られることを説明する。
3. このトイ構成の限界を少なくとも1つ述べる。

問題3: 難易度 高
素数位数群 `G` の生成元 `g, h` を用いたPedersenコミットメント
`Com(m; r) = g^m h^r` について説明してください。ただし、`log_g h` はコミッターに
知られていないものとします。

答案では、次の点に触れる必要があります。
1. この構成がperfect hidingである理由を説明する。
2. `log_g h` を知っているとbinding性を破れる理由を説明する。
3. 離散対数問題の困難性とcomputational bindingの関係を説明する。

提出ファイルは `answer.md` とします。
複数の問題に回答している場合でも、採点対象は1問分だけです。
"""


# 採点基準:
# 配点と部分点の方針を書く。合計は100点にする。
RUBRIC = """
選択された1問について100点満点で採点してください。
答案が選択した問題番号を明記していない場合は、答案内容から最も自然に対応する問題を
推定して採点してください。複数の問題に回答している場合は、最もよく回答できている
1問だけを採点対象にしてください。

共通配点:

- 問題で問われている主要概念の正確な説明: 35点
- 問題固有の中心的な論証または比較: 35点
- 仮定・限界・必要条件への言及: 15点
- 構成・記法・読みやすさ: 15点

表記が完全でなくても、実質的に正しい推論には部分点を与えてください。
模範回答と同じ言い回しである必要はありません。
"""


# 模範回答:
# 正答性・重要論点・部分点判断の基準として使う。完全一致は要求しない。
REFERENCE_ANSWER = """
問題1: 難易度 低の模範回答
binding性とは、コミット後に同じコミットメント値を2つの異なる値として有効にopenする
ことが困難である、という性質である。これはコミッターが後から内容を都合よく変えられない
ことを保証する。hiding性とは、コミットメント値を見ただけでは、コミットされたメッセージの
情報が受け手に漏れない、という性質である。これはcommit段階で内容を隠しておくために重要で
ある。binding性は主にopen段階で、公開されたopeningがコミット時の内容から変わっていない
ことを保証するために重要である。

問題2: 難易度 中の模範回答
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

問題3: 難易度 高の模範回答
Pedersenコミットメント `Com(m; r) = g^m h^r` は、固定された `m` に対して `r` が一様なら
`h^r` が群上で一様に分布するため、コミットメント値の分布が `m` に依存しない。したがって
perfect hidingである。

一方、`log_g h = alpha` を知っていると、`h = g^alpha` なので
`Com(m; r) = g^{m + alpha r}` と書ける。攻撃者は同じ指数を保つように
`m + alpha r = m' + alpha r'` を満たす別の `(m', r')` を作れるため、同じコミットメントを
異なるメッセージにopenできる。

したがってbinding性は、`g` に対する `h` の離散対数を知らないこと、より形式的には
離散対数問題の困難性に依存するcomputational bindingである。binding性を破る2つの異なる
openingからは、`g^{m-m'} = h^{r'-r}` の関係を使って `log_g h` を求められる場合がある。
"""


# 追加採点指示:
# 厳しく見るポイントや、人間レビューに回すべき条件を書く。
EXTRA_INSTRUCTIONS = """
選択した問題に対応しない内容を主に書いている答案は、該当問題の答案として低く評価して
ください。ただし、選択の明記がなくても内容から対応する問題が明らかな場合は、その問題の
答案として採点してください。

難易度 中については、「ハッシュは安全だからbindingである」とだけ述べ、衝突への帰着を
示していない答案には厳しく採点してください。

難易度 高については、perfect hidingとcomputational bindingを混同している答案や、
`log_g h` を知っている場合の攻撃を説明できていない答案には厳しく採点してください。

採点結果の説明と各rubric項目のコメントは日本語で書いてください。
"""


PYTHON_TEST_CASES = [
    PythonTestCase(
        name="提出形式と関数定義",
        max_points=10,
        code="""
        assert callable(getattr(student, "mod_pow", None)), "mod_pow が定義されていません。"
        assert callable(getattr(student, "mod_inverse", None)), "mod_inverse が定義されていません。"
        """,
    ),
    PythonTestCase(
        name="mod_pow の基本ケース",
        max_points=20,
        code="""
        assert student.mod_pow(2, 10, 17) == 4
        assert student.mod_pow(5, 0, 19) == 1
        assert student.mod_pow(-2, 5, 13) == pow(-2, 5, 13)
        """,
    ),
    PythonTestCase(
        name="mod_pow の大きな入力",
        max_points=20,
        code="""
        cases = [
            (123456789, 12345, 1000000007),
            (987654321, 54321, 2147483647),
            (42, 999, 101),
        ]
        for base, exponent, modulus in cases:
            assert student.mod_pow(base, exponent, modulus) == pow(base, exponent, modulus)
        """,
    ),
    PythonTestCase(
        name="mod_inverse の基本ケース",
        max_points=25,
        code="""
        cases = [
            (3, 11, 4),
            (10, 17, 12),
            (7, 40, 23),
            (-3, 11, 7),
        ]
        for a, modulus, expected in cases:
            assert student.mod_inverse(a, modulus) == expected
            assert (a * student.mod_inverse(a, modulus)) % modulus == 1
        """,
    ),
    PythonTestCase(
        name="mod_inverse の例外ケース",
        max_points=25,
        code="""
        for a, modulus in [(2, 4), (6, 9), (0, 7)]:
            try:
                student.mod_inverse(a, modulus)
            except ValueError:
                pass
            else:
                raise AssertionError("逆元が存在しない場合は ValueError を投げてください。")
        for a, modulus in [(17, 3120), (37, 101), (65537, 99991)]:
            inverse = student.mod_inverse(a, modulus)
            assert (a * inverse) % modulus == 1
        """,
    ),
]


def selected_mode() -> str:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--mode", choices=("llm", "python"), default="llm")
    args, _ = parser.parse_known_args()
    return str(args.mode)


if __name__ == "__main__":
    if selected_mode() == "python":
        raise SystemExit(run_python_grader(test_cases=PYTHON_TEST_CASES))

    raise SystemExit(
        run_llm_grader(
            problem_statement=PROBLEM_STATEMENT,
            rubric=RUBRIC,
            reference_answer=REFERENCE_ANSWER,
            extra_instructions=EXTRA_INSTRUCTIONS,
        )
    )
