import unittest

import solution


class SumCheckTests(unittest.TestCase):

    def test_success_with_fixed_challenges(self):
        # f(x, y) = xy + x + 2
        polynomial = solution.Polynomial(
            terms={
                (1, 1): 1,
                (1, 0): 1,
                (0, 0): 2,
            },
            p=17,
        )

        sumcheck = solution.SumCheck(polynomial)

        claimed_sum = sumcheck.calc_total_sum()

        proof = sumcheck.prove(
            challenges=[3, 5]
        )

        assert claimed_sum == 11
        assert len(proof) == 2
        assert proof[0][0].coefficients == [4, 3]
        assert proof[0][1] == 3
        assert proof[1][0].coefficients == [5, 3]
        assert proof[1][1] == 5
        assert sumcheck.verify(claimed_sum, proof)

    def test_success_with_random_challenges(self):
        # f(x, y) = xy + x + 2
        polynomial = solution.Polynomial(
            terms={
                (1, 1): 1,
                (1, 0): 1,
                (0, 0): 2,
            },
            p=17,
        )

        sumcheck = solution.SumCheck(polynomial)

        claimed_sum = sumcheck.calc_total_sum()

        proof = sumcheck.prove()

        assert claimed_sum == 11
        assert sumcheck.verify(claimed_sum, proof)

    def test_failure_wrong_claim(self):
        # f(x, y) = xy + x + 2
        polynomial = solution.Polynomial(
            terms={
                (1, 1): 1,
                (1, 0): 1,
                (0, 0): 2,
            },
            p=17,
        )

        sumcheck = solution.SumCheck(polynomial)

        proof = sumcheck.prove(
            challenges=[3, 5]
        )

        assert not sumcheck.verify(12, proof)

    def test_failure_invalid_proof(self):
        # f(x, y) = xy + x + 2
        polynomial = solution.Polynomial(
            terms={
                (1, 1): 1,
                (1, 0): 1,
                (0, 0): 2,
            },
            p=17,
        )

        sumcheck = solution.SumCheck(polynomial)

        claimed_sum = sumcheck.calc_total_sum()

        invalid_proof = [
            (solution.UnivariatePolynomial([4, 3], 17), 3),
            (solution.UnivariatePolynomial([5, 2], 17), 5),
        ]

        assert not sumcheck.verify(claimed_sum, invalid_proof)

    def test_success_example_on_slides(self):
        # (1-a)b(8+4a+4b) = 8b - 4ab + 4b^2 - 4a^2b - 4ab^2
        polynomial = solution.Polynomial(
            terms={
                (0, 1): 8,
                (1, 1): -4,
                (0, 2): 4,
                (2, 1): -4,
                (1, 2): -4
            },
            p=11
        )

        sumcheck = solution.SumCheck(polynomial)

        claimed_sum = sumcheck.calc_total_sum()

        proof = sumcheck.prove(
            challenges=[2, 3]
        )

        assert claimed_sum == 1
        assert len(proof) == 2
        assert proof[0][0].coefficients == [1, 3, 7]
        assert proof[0][1] == 2
        assert proof[1][0].coefficients == [0, 6, 7]
        assert proof[1][1] == 3
        assert sumcheck.verify(claimed_sum, proof)

    def test_failure_example_on_slides(self):
        # (1-a)b(8+4a+4b) = 8b - 4ab + 4b^2 - 4a^2b - 4ab^2
        polynomial = solution.Polynomial(
            terms={
                (0, 1): 8,
                (1, 1): -4,
                (0, 2): 4,
                (2, 1): -4,
                (1, 2): -4
            },
            p=11
        )

        sumcheck = solution.SumCheck(polynomial)

        proof = sumcheck.prove(
            challenges=[2, 3]
        )

        assert not sumcheck.verify(7, proof)
