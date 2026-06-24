from __future__ import annotations

from sympy import mod_inverse as sympy_mod_inverse


def mod_pow(base: int, exponent: int, modulus: int) -> int:
    """Return base**exponent modulo modulus."""
    return pow(base, exponent, modulus)


def mod_inverse(a: int, modulus: int) -> int:
    """Return x such that (a * x) % modulus == 1.

    Raise ValueError when the inverse does not exist.
    """
    try:
        return int(sympy_mod_inverse(a, modulus))
    except ValueError as error:
        raise ValueError("inverse does not exist") from error
