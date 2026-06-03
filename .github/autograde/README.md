# 自動採点

このリポジトリでは、課題提出PRだけをGitHub Actionsで自動採点します。
採点処理は信頼できるbase branch側のコードだけを実行し、PR側の提出物は
「読むだけのデータ」として扱います。

## 提出PRの形式

課題提出PRでは、次の1ディレクトリ配下だけを変更してください。

```text
weekN/exercises/submissions/<submitter>/
```

提出ディレクトリを変更していないPRでは採点をスキップします。
提出物とそれ以外のファイルを混ぜたPRは `auto-grade` check が失敗します。

## 週ごとのgrader

各weekの担当教員は、次のファイルを用意します。

```text
weekN/exercises/grader.py
```

まず `.github/autograde/examples/grader.py` をコピーして、`PROBLEM_STATEMENT`,
`RUBRIC`, `REFERENCE_ANSWER` と必要な追加チェックだけを書き換えてください。
CLI引数、設定読み込み、OpenRouter呼び出し、JSON出力は `tools.grader_base` が
処理します。

最小例:

```python
from __future__ import annotations

from tools.grader_base import Grade, Submission, run_llm_grader

PROBLEM_STATEMENT = """
問題文、前提、使ってよい定理、提出形式を書く。
"""

RUBRIC = """
100点満点で採点してください。
- 正しさ: 60点
- 説明の明瞭さ: 30点
- 形式: 10点
"""

REFERENCE_ANSWER = """
模範回答、期待する証明方針、重要な論点を書く。
"""


def adjust_grade(grade: Grade, submission: Submission) -> Grade:
    return grade


if __name__ == "__main__":
    raise SystemExit(
        run_llm_grader(
            problem_statement=PROBLEM_STATEMENT,
            rubric=RUBRIC,
            reference_answer=REFERENCE_ANSWER,
            adjust_grade=adjust_grade,
        )
    )
```

内部的には次のCLIとして実行されます。

```bash
PYTHONPATH=. python3 weekN/exercises/grader.py \
  --submission-dir <dir> \
  --config <json> \
  --output <json>
```

CIでは `PYTHONPATH` は自動設定されます。ローカルで試すときだけ
`PYTHONPATH=.` を付けてください。

graderの出力JSONは次の形式です。

```json
{
  "score": 70,
  "summary": "採点結果の短い説明",
  "items": [
    {
      "name": "Correctness",
      "points": 40,
      "max_points": 50,
      "comment": "概ね正しい"
    }
  ],
  "needs_human_review": false
}
```

ただし通常はこのJSONを直接書く必要はありません。

`PROBLEM_STATEMENT` と `REFERENCE_ANSWER` は公開の採点ガイドとして扱います。
学生に見せたくない模範回答はこのリポジトリに置かないでください。

## モデル設定

デフォルトのprovider/model/pass scoreは `.github/autograde/config.yml` にあります。
モデルは全week共通です。
モデルだけ一時的に変えたい場合は、GitHub repository variable の
`AUTOGRADE_MODEL` を設定してください。workflowを書き換える必要はありません。

LLM採点を使う場合は、GitHub Secret `OPENROUTER_API_KEY` が必要です。
