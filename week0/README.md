# Week 0

Week 0 is for practice and sample submissions. Use it to learn the repository
workflow before submitting later coursework.

The Week 0 problem is `field-basics`.

## Submission Path

Submit your Rust solution here:

```text
week0/submissions/<github-username>/field-basics/rust/
```

Only edit files under:

```text
week0/submissions/<github-username>/
```

Do not edit `problems/`, `.github/`, or `scripts/`.

Each submission directory must contain:

```text
Cargo.toml
src/lib.rs
```

## Copy the Rust Template

```bash
mkdir -p week0/submissions/<github-username>/field-basics/rust
cp -R week0/problems/field-basics/rust/template/. \
  week0/submissions/<github-username>/field-basics/rust/
```

## Local Test

```bash
bash scripts/test-rust-submission.sh week0 field-basics <github-username>
```

## Pull Request

Use this PR title:

```text
[week0] <github-username>
```

When CI is green, your sample submission is complete.
