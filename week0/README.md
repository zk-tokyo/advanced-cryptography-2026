# Week 0

Week 0 は練習用・サンプル提出用です。以降の課題を提出する前に、このリポジトリでの提出手順を確認するために使います。

Week 0 の問題は `field-basics` です。

## 提出先

Rust の解答は次の場所に提出してください。

```text
week0/submissions/<github-username>/field-basics/rust/
```

編集してよいのは次のディレクトリ以下だけです。

```text
week0/submissions/<github-username>/
```

`problems/`、`.github/`、`scripts/` は編集しないでください。

各提出ディレクトリには、必ず次のファイルを置いてください。

```text
Cargo.toml
src/lib.rs
```

## Rust テンプレートのコピー

```bash
mkdir -p week0/submissions/<github-username>/field-basics/rust
cp -R week0/problems/field-basics/rust/template/. \
  week0/submissions/<github-username>/field-basics/rust/
```

## ローカルテスト

```bash
bash scripts/test-rust-submission.sh week0 field-basics <github-username>
```

## Pull Request

PR title は次の形式にしてください。

```text
[week0] <github-username>
```

CI が成功すれば、サンプル提出は完了です。
