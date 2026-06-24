# Week 0

Week 0 は練習用・サンプル提出用です。以降の課題を提出する前に、このリポジトリでの提出手順を確認するために使います。

Week 0 の問題は次の 2 つです。

- `field-basics`: Rust で有限体 `ark_bn254::Fr` の基本演算を実装する問題
- `mod-arithmetic`: Python で剰余累乗と剰余逆元を実装する問題

## 提出先

Rust の `field-basics` は次の場所に提出してください。

```text
week0/submissions/<github-username>/field-basics/rust/
```

Python の `mod-arithmetic` は次の場所に提出してください。

```text
week0/submissions/<github-username>/mod-arithmetic/python/
```

編集してよいのは次のディレクトリ以下だけです。

```text
week0/submissions/<github-username>/
```

`problems/`、`.github/`、`scripts/` は編集しないでください。

Rust の提出ディレクトリには、必ず次のファイルを置いてください。

```text
Cargo.toml
src/lib.rs
```

Python の提出ディレクトリには、必ず次のファイルを置いてください。

```text
solution.py
requirements.txt
```

Python 課題の依存関係は、Rust の `Cargo.toml` と同じように提出ディレクトリ内の
`requirements.txt` で宣言します。Week 0 では `sympy` のみ許可されています。

## Rust テンプレートのコピー

```bash
mkdir -p week0/submissions/<github-username>/field-basics/rust
cp -R week0/problems/field-basics/rust/template/. \
  week0/submissions/<github-username>/field-basics/rust/
```

## Python テンプレートのコピー

```bash
mkdir -p week0/submissions/<github-username>/mod-arithmetic/python
cp -R week0/problems/mod-arithmetic/python/template/. \
  week0/submissions/<github-username>/mod-arithmetic/python/
```

## ローカルテスト

Rust:

```bash
bash scripts/test-rust-submission.sh week0 field-basics <github-username>
```

Python:

```bash
bash scripts/test-python-submission.sh week0 mod-arithmetic <github-username>
```

## Pull Request

PR title は次の形式にしてください。

```text
[week0] <github-username>
```

CI が成功すれば、サンプル提出は完了です。
