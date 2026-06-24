use ark_bn254::Fr;
use ark_ff::{Field, Zero};

pub type F = Fr;

/// Return a + b * c.
pub fn add_mul(a: F, b: F, c: F) -> F {
    a + b * c
}

/// Return a / b if b is nonzero.
/// Return None if b is zero.
pub fn checked_div(a: F, b: F) -> Option<F> {
    if b.is_zero() {
        None
    } else {
        Some(a * b.inverse().expect("nonzero field element has an inverse"))
    }
}

/// Evaluate coeffs[0] + coeffs[1] * x + coeffs[2] * x^2 + ...
pub fn eval_poly(coeffs: &[F], x: F) -> F {
    coeffs
        .iter()
        .rev()
        .fold(F::zero(), |accumulator, coefficient| {
            accumulator * x + coefficient
        })
}
