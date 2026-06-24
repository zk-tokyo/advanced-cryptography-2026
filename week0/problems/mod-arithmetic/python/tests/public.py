from __future__ import annotations

import unittest

from sympy import mod_inverse as expected_mod_inverse

import solution


class ModArithmeticTests(unittest.TestCase):
    def test_mod_pow_basic(self) -> None:
        self.assertEqual(solution.mod_pow(2, 10, 17), 4)
        self.assertEqual(solution.mod_pow(5, 0, 19), 1)
        self.assertEqual(solution.mod_pow(-2, 5, 13), pow(-2, 5, 13))

    def test_mod_pow_large_inputs(self) -> None:
        cases = [
            (123456789, 12345, 1_000_000_007),
            (987654321, 54321, 2_147_483_647),
            (42, 999, 101),
        ]

        for base, exponent, modulus in cases:
            with self.subTest(base=base, exponent=exponent, modulus=modulus):
                self.assertEqual(
                    solution.mod_pow(base, exponent, modulus),
                    pow(base, exponent, modulus),
                )

    def test_mod_inverse_basic(self) -> None:
        cases = [
            (3, 11, 4),
            (10, 17, 12),
            (7, 40, 23),
            (-3, 11, 7),
        ]

        for a, modulus, expected in cases:
            with self.subTest(a=a, modulus=modulus):
                actual = solution.mod_inverse(a, modulus)
                self.assertEqual(actual, expected)
                self.assertEqual((a * actual) % modulus, 1)

    def test_mod_inverse_raises_when_inverse_does_not_exist(self) -> None:
        for a, modulus in [(2, 4), (6, 9), (0, 7)]:
            with self.subTest(a=a, modulus=modulus):
                with self.assertRaises(ValueError):
                    solution.mod_inverse(a, modulus)

    def test_mod_inverse_larger_inputs(self) -> None:
        for a, modulus in [(17, 3120), (37, 101), (65537, 99991)]:
            with self.subTest(a=a, modulus=modulus):
                actual = solution.mod_inverse(a, modulus)
                self.assertEqual(actual, int(expected_mod_inverse(a, modulus)))
                self.assertEqual((a * actual) % modulus, 1)


if __name__ == "__main__":
    unittest.main()
