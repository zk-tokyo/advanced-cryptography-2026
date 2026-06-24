# mod-arithmetic

## 概要

このサンプル問題では、Python と `sympy` を使って、暗号実装の基礎になる剰余演算を扱います。

剰余累乗と剰余逆元を実装し、有限体や群演算でよく出てくる基本操作を学びます。

## 目標

Python の関数と提出ディレクトリ内の `requirements.txt` を使って、依存関係のある課題の提出方法を学びます。

## 課題

`solution.py` で次の 2 つの関数を実装してください。

- `mod_pow`
- `mod_inverse`

公開されている関数シグネチャは変更しないでください。

## Python API

テンプレートでは次のように `sympy` を読み込めます。

```python
from sympy import mod_inverse as sympy_mod_inverse
```

次の関数を実装してください。

```python
def mod_pow(base: int, exponent: int, modulus: int) -> int:
```

`base ** exponent mod modulus` を返します。

次の関数を実装してください。

```python
def mod_inverse(a: int, modulus: int) -> int:
```

`(a * x) % modulus == 1` を満たす `x` を返します。逆元が存在しない場合は `ValueError` を送出してください。

## 提出先

Python の解答は次の場所に提出してください。

```text
week0/submissions/<github-username>/mod-arithmetic/python/
```

このディレクトリには、必ず次のファイルを置いてください。

```text
solution.py
requirements.txt
```

## ローカルテスト

リポジトリのルートで次を実行してください。

```bash
bash scripts/test-python-submission.sh week0 mod-arithmetic <github-username>
```

## ルール

- この問題は Python のみです。
- `sympy` を使えます。
- `requirements.txt` には、この課題で許可された依存だけを書いてください。
- `week0/problems/`、`.github/`、`scripts/` 以下のファイルは編集しないでください。
- 編集してよいのは `week0/submissions/<github-username>/` 以下だけです。
- 関数シグネチャは変更しないでください。
- 逆元が存在しない場合は `ValueError` を送出してください。

## 例

`mod_pow` の例:

```text
mod_pow(2, 10, 17) = 4
mod_pow(5, 0, 19) = 1
```

`mod_inverse` の例:

```text
mod_inverse(3, 11) = 4
mod_inverse(10, 17) = 12
```

逆元が存在しない例:

```text
mod_inverse(2, 4) は ValueError
```

## エッジケース

- `exponent == 0` のとき、`mod_pow` は `1 mod modulus` を返してください。
- `base` や `a` が負の場合も、Python の剰余演算として正しく扱ってください。
- `a` と `modulus` が互いに素でない場合、`mod_inverse` は `ValueError` を送出してください。
- `a == 0` の場合、`mod_inverse` は `ValueError` を送出してください。
