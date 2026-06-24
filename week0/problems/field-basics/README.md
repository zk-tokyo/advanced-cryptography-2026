# field-basics

## 概要

このサンプル問題では、arkworks の `ark_bn254::Fr` を使って、Rust で有限体の基本演算を扱います。

BN254 のスカラー体上で、加算、乗算、ゼロ除算を避ける除算、多項式評価を実装します。

## 目標

`ark_bn254::Fr` と `ark_ff` の trait、特に `Field` と `Zero` を使って、有限体の要素を扱う方法を学びます。

## 課題

`src/lib.rs` で次の 3 つの関数を実装してください。

- `add_mul`
- `checked_div`
- `eval_poly`

公開されている関数シグネチャは変更しないでください。

## Rust API

テンプレートでは次のように型が定義されています。

```rust
use ark_bn254::Fr;
use ark_ff::{Field, Zero};

pub type F = Fr;
```

次の関数を実装してください。

```rust
pub fn add_mul(a: F, b: F, c: F) -> F
```

`a + b * c` を返します。

次の関数を実装してください。

```rust
pub fn checked_div(a: F, b: F) -> Option<F>
```

`b` がゼロでないときは `Some(a / b)` を返します。`b` がゼロのときは `None` を返します。

次の関数を実装してください。

```rust
pub fn eval_poly(coeffs: &[F], x: F) -> F
```

次の多項式を評価します。

```text
coeffs[0] + coeffs[1] * x + coeffs[2] * x^2 + ...
```

例えば `coeffs = [1, 2, 3]` は `1 + 2x + 3x^2` を意味します。

## 提出先

Rust の解答は次の場所に提出してください。

```text
week0/submissions/<github-username>/field-basics/rust/
```

このディレクトリには、必ず次のファイルを置いてください。

```text
Cargo.toml
src/lib.rs
```

## ローカルテスト

リポジトリのルートで次を実行してください。

```bash
bash scripts/test-rust-submission.sh week0 field-basics <github-username>
```

## ルール

- この問題は Rust のみです。
- 有限体の型として `ark_bn254::Fr` を使ってください。
- `ark_ff::{Field, Zero}` を使ってください。
- `week0/problems/`、`.github/`、`scripts/` 以下のファイルは編集しないでください。
- 編集してよいのは `week0/submissions/<github-username>/` 以下だけです。
- 関数シグネチャは変更しないでください。

## 例

`add_mul` の例:

```text
add_mul(1, 2, 3) = 1 + 2 * 3 = 7
```

`checked_div` の例:

```text
checked_div(6, 3) = Some(2)
checked_div(1, 0) = None
```

`eval_poly` の例:

```text
coeffs = [1, 2, 3], x = 10
1 + 2 * 10 + 3 * 10^2 = 321
```

## エッジケース

- `checked_div(a, 0)` は `None` を返してください。
- `b` がゼロでないとき、`checked_div(0, b)` は `Some(0)` を返してください。
- `eval_poly(&[], x)` はゼロを返してください。
- `eval_poly(&[c], x)` は `c` を返してください。
- `coeffs` が空でないとき、`eval_poly(coeffs, 0)` は `coeffs[0]` を返してください。
- `eval_poly(coeffs, 1)` はすべての係数の和を返してください。
