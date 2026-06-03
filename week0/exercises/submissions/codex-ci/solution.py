from __future__ import annotations


def mod_pow(base: int, exponent: int, modulus: int) -> int:
    return pow(base, exponent, modulus)


def mod_inverse(a: int, modulus: int) -> int:
    try:
        return pow(a, -1, modulus)
    except ValueError as exc:
        raise ValueError("inverse does not exist") from exc
