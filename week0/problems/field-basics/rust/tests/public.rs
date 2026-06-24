use ark_bn254::Fr;
use ark_ff::{One, Zero};

use submission::*;

fn f(x: u64) -> Fr {
    Fr::from(x)
}

#[test]
fn test_add_mul_basic() {
    assert_eq!(add_mul(f(1), f(2), f(3)), f(7));
    assert_eq!(add_mul(f(10), f(0), f(999)), f(10));
}

#[test]
fn test_checked_div_basic() {
    assert_eq!(checked_div(f(6), f(3)), Some(f(2)));
    assert_eq!(checked_div(f(0), f(5)), Some(Fr::zero()));
    assert_eq!(checked_div(f(1), Fr::zero()), None);
}

#[test]
fn test_checked_div_inverse_property() {
    let a = f(123);
    let b = f(456);

    let q = checked_div(a, b).unwrap();
    assert_eq!(q * b, a);
}

#[test]
fn test_eval_poly_basic() {
    // 1 + 2x + 3x^2 at x = 10
    // = 1 + 20 + 300 = 321
    let coeffs = vec![f(1), f(2), f(3)];
    assert_eq!(eval_poly(&coeffs, f(10)), f(321));
}

#[test]
fn test_eval_poly_empty() {
    let coeffs = vec![];
    assert_eq!(eval_poly(&coeffs, f(10)), Fr::zero());
}

#[test]
fn test_eval_poly_constant() {
    let coeffs = vec![f(42)];
    assert_eq!(eval_poly(&coeffs, f(999)), f(42));
}

#[test]
fn test_eval_poly_at_zero() {
    let coeffs = vec![f(7), f(8), f(9)];
    assert_eq!(eval_poly(&coeffs, Fr::zero()), f(7));
}

#[test]
fn test_eval_poly_at_one() {
    let coeffs = vec![f(7), f(8), f(9)];
    assert_eq!(eval_poly(&coeffs, Fr::one()), f(24));
}
