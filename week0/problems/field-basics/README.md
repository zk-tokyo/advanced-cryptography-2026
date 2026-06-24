# field-basics

## Overview

This sample problem introduces basic finite field arithmetic in Rust with
`ark_bn254::Fr` from arkworks.

You will implement addition, multiplication, checked division, and polynomial
evaluation over the BN254 scalar field.

## Goal

Learn how to work with field elements using `ark_bn254::Fr` and the traits from
`ark_ff`, especially `Field` and `Zero`.

## Task

Implement the following three functions in `src/lib.rs`:

- `add_mul`
- `checked_div`
- `eval_poly`

Do not change the public function signatures.

## Rust API

The template defines:

```rust
use ark_bn254::Fr;
use ark_ff::{Field, Zero};

pub type F = Fr;
```

Implement:

```rust
pub fn add_mul(a: F, b: F, c: F) -> F
```

Return `a + b * c`.

Implement:

```rust
pub fn checked_div(a: F, b: F) -> Option<F>
```

Return `Some(a / b)` when `b` is nonzero. Return `None` when `b` is zero.

Implement:

```rust
pub fn eval_poly(coeffs: &[F], x: F) -> F
```

Evaluate:

```text
coeffs[0] + coeffs[1] * x + coeffs[2] * x^2 + ...
```

For example, `coeffs = [1, 2, 3]` means `1 + 2x + 3x^2`.

## Submission Path

Submit your Rust solution here:

```text
week0/submissions/<github-username>/field-basics/rust/
```

The directory must contain:

```text
Cargo.toml
src/lib.rs
```

## Local Test

From the repository root, run:

```bash
bash scripts/test-rust-submission.sh week0 field-basics <github-username>
```

## Rules

- This problem is Rust only.
- Use `ark_bn254::Fr` as the field type.
- Use `ark_ff::{Field, Zero}`.
- Do not edit files under `week0/problems/`, `.github/`, or `scripts/`.
- Only edit files under `week0/submissions/<github-username>/`.
- Keep the function signatures unchanged.

## Examples

For `add_mul`:

```text
add_mul(1, 2, 3) = 1 + 2 * 3 = 7
```

For `checked_div`:

```text
checked_div(6, 3) = Some(2)
checked_div(1, 0) = None
```

For `eval_poly`:

```text
coeffs = [1, 2, 3], x = 10
1 + 2 * 10 + 3 * 10^2 = 321
```

## Edge Cases

- `checked_div(a, 0)` must return `None`.
- `checked_div(0, b)` should return `Some(0)` when `b` is nonzero.
- `eval_poly(&[], x)` must return zero.
- `eval_poly(&[c], x)` must return `c`.
- `eval_poly(coeffs, 0)` must return `coeffs[0]` when `coeffs` is nonempty.
- `eval_poly(coeffs, 1)` must return the sum of all coefficients.
