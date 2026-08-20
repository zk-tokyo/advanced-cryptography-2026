# SumCheck is All You Need

## 1. 概要

GKRをはじめ、さまざまな（ゼロ知識）証明スキームで使われている**SumCheckプロトコル**をPythonで実装してみましょう。

## 2. 課題

`solution.py` 内の5個のメソッドを実装してください。

#### ルール

- 編集してよいのは `week4/submissions/<github-username>/` 以下だけです（`problems/`、`.github/`、`scripts/` は編集しないでください）。
- Pythonの標準パッケージのみで実装してください（i.e., 追加パッケージは不要）。
- メソッド名や引数は変更せず、コメントや型定義に沿ってメソッドの中身を実装してください。
- 型定義に沿っていれば、細かい実装方法は自由です。

> [!TIP]
> 1から番号順に実装していく方法が一番わかりやすいです。

1. `Polynomial.evaluate()`: 多変数多項式を評価するメソッド
2. `UnivariatePolynomial.evaluate()`: 一変数多項式を評価するメソッド
3. `SumCheck.construct_round_polynomial()`: SumCheckのラウンド毎に用いる一変数多項式を計算するメソッド
4. `SumCheck.prove()`: 証明を生成するメソッド（今回の実装では、全てのラウンド分の証明をまとめて生成します）
5. `SumCheck.verify()`: 証明を検証するメソッド（今回の実装では、全てのラウンド分の証明をまとめて検証します）

## 3. 進め方（スクリプト）

github-username は自動判定されます。

```bash
# 1. 提出フォルダとテンプレートを用意
bash scripts/new-submission.sh week4 sumcheck-is-all-you-need

# 2. solution.py を実装し、テスト
bash scripts/test-python-submission.sh week4 sumcheck-is-all-you-need <github-username>

# 3. 提出（テストが通れば commit・push・PR 作成まで自動）
bash scripts/submit.sh week4 sumcheck-is-all-you-need
```

## 4. 手元での動かし方

`<github-username>` は自分のものに置き換えてください。

```bash
# パスを通す
export PYTHONPATH="week4/problems/sumcheck-is-all-you-need/python/tests:week4/submissions/<github-username>/sumcheck-is-all-you-need/python"

# 簡易的に実装をチェックする
python3 week4/submissions/<github-username>/sumcheck-is-all-you-need/python/solution.py
```