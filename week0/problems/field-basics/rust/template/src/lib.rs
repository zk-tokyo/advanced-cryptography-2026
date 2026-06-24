use ark_bn254::Fr;
use ark_ff::{Field, Zero};

pub type F = Fr;

/// Return a + b * c.
pub fn add_mul(a: F, b: F, c: F) -> F {
    todo!()
}

/// Return a / b if b is nonzero.
/// Return None if b is zero.
pub fn checked_div(a: F, b: F) -> Option<F> {
    todo!()
}

/// Evaluate coeffs[0] + coeffs[1] * x + coeffs[2] * x^2 + ...
pub fn eval_poly(coeffs: &[F], x: F) -> F {
    todo!()
}
