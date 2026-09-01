from __future__ import annotations

import itertools
import random


class Polynomial:
    """Class representing a multivariate polynomial.

    terms: terms of a polynomial
    p: order of finite field (a prime number)

    e.g.)
        x*y + x + 2 = {
            (1,1): 1,
            (1,0): 1,
            (0,0): 2
        }
    """
    def __init__(
        self,
        terms: dict[tuple[int, ...], int],
        p: int
    ) -> None:
        """Initializes `Polynomial` instance.

        Args:
            terms: terms of a polynomial
            p: order of finite field (a prime number)

        Returns:
            None
        """
        self.terms = terms
        self.p = p
        self.n = len(next(iter(terms)))

    def reduce(self, x: int) -> int:
        """Calculates x (mod p).

        Args:
            x: target number

        Returns:
            x (mod p)
        """
        return x % self.p

    def substitute(self, index: int, value: int):
        terms: dict[tuple[int, ...], int] = {}
        for k, v in self.terms.items():
            new_k = k[:index] + k[index+1:]
            new_v = pow(value, k[index], self.p) * v
            terms[new_k] = self.reduce(terms.get(new_k, 0) + new_v)

        return Polynomial(
            terms=terms,
            p=self.p
        )

    def add(self, other: Polynomial) -> Polynomial:
        terms: dict[tuple[int, ...], int] = dict(self.terms)
        for k, v in other.terms.items():
            terms[k] = self.reduce(terms.get(k, 0) + v)

        return Polynomial(
            terms=terms,
            p=self.p
        )

    def evaluate(self, point: tuple[int, ...]) -> int:
        """Evaluates polynomial at `point`.

        Args:
            point: evaluation point

        Returns:
            Evaluation result
        """
        result = 0
        for variables, coefficient in self.terms.items():
            sum = 1
            for (v, p) in zip(variables, point):
                sum *= pow(p, v, self.p)
            result += sum * coefficient
        return self.reduce(result)

    def to_univariate(self):
        if self.n != 1:
            raise ValueError("not univariate")

        degree = max(k[0] for k in self.terms)
        coefficients = [0] * (degree + 1)
        for k, v in self.terms.items():
            coefficients[k[0]] = v

        return UnivariatePolynomial(
            coefficients = coefficients,
            p = self.p
        )


class UnivariatePolynomial(Polynomial):
    """Class representing a univariate polynomial.

    terms: coefficients of a univariate polynomial
    p: order of finite field (a prime number)

    e.g.)
        [c_0, c_, ..., c_d] = c_0 + c_*x + ... + c_d*x^d
    """
    def __init__(
        self,
        coefficients: list[int],
        p: int
    ) -> None:
        """Initializes `UnivariatePolynomial` instance.

        Args:
            coefficients: coefficients of a univariate polynomial
            p: order of finite field (a prime number)

        Returns:
            None
        """
        self.coefficients = coefficients
        self.p = p

    def evaluate(self, x: int) -> int:
        """Evaluates polynomial at `x`.

        Args:
            x: evaluation point

        Returns:
            Evaluation result
        """
        sum = 0
        for i, c in enumerate(self.coefficients):
            sum += c * pow(x, i, self.p)
        return self.reduce(sum)


class SumCheck:
    """Class representing SumCheck protocol.

    f: target function (i.e., polynomial or computation)
    p: order of finite field of `f`
    n: number of variables of `f`
    """

    def __init__(
        self,
        polynomial: Polynomial
    ) -> None:
        """Initializes `SumCheck` instance.

        Args:
            polynomial: target polynomial

        Returns:
            None
        """
        self.f = polynomial
        self.p = polynomial.p
        self.n = len(next(iter(polynomial.terms)))

    def gen_boolean_points(self, n: int) -> list[tuple[int, ...]]:
        """Generates all the combinations of {0,1}^n.

        Args:
            n: bit length

        Returns:
            A set of all the vertices of n-dimensional boolean hypercube
        """
        return itertools.product([0, 1], repeat=n)

    def calc_total_sum(self) -> int:
        """Calculates Σf(x), ∀x ∈ {0,1}^n.

        Args:
            None

        Returns:
            Total sum
        """
        return self.f.reduce(
            sum(self.f.evaluate(point) for point in self.gen_boolean_points(self.n))
        )

    def construct_round_polynomial(self, challenges: list[int]) -> UnivariatePolynomial:
        """Constructs the round polynomial g_i(t) = Σf(r_1, ..., r_{i-1}, t, x_{i+1}, ..., x_n).

        Args:
            challenges: fixed random challenge values

        Returns:
            Univariate polynomial for a single round
        """

        # Fill r values
        g = self.f
        for r in challenges:
            g = g.substitute(0, r)

        result = None
        for case in self.gen_boolean_points(g.n - 1):
            # Fill x values
            h = g
            for i, v in enumerate(case):
                h = h.substitute(1, v)

            result = h if result is None else result.add(h)

        return result.to_univariate()


    def prove(self, challenges:list[int] | None = None) -> list[tuple[UnivariatePolynomial, int]]:
        """Generates a proof.

        Args:
            challenges: random challenge values

        Returns:
            Proof (a list of tuples of round polynomial g_i(t) and random challenge r_i)
        """
        if challenges is None:
            challenges = [random.randrange(self.p) for _ in range(self.f.n)]

        result = []
        for i, r in enumerate(challenges):
            case = challenges[:i]
            up = self.construct_round_polynomial(case)
            result.append((up, r))

        return result

    def verify(
        self,
        claimed_sum: int,
        proof: list[tuple[UnivariatePolynomial, int]]
    ) -> bool:
        """Verifies a proof.

        Args:
            claimed_sum: Claimed sum of target function
            proof: proof of the claimed sum

        Returns:
            True if succeeded, false otherwise
        """
        target = claimed_sum
        for k, v in proof:
            if k.evaluate(0) + k.evaluate(1) != target:
                return False
            target = k.evaluate(v)

        return self.f.evaluate(tuple(p[1] for p in proof)) == target


if __name__ == "__main__":
    # f = x*y + x + 2
    polynomial = Polynomial(
        terms={
            (1, 1): 1,
            (1, 0): 1,
            (0, 0): 2
        },
        p=17
    )

    sc = SumCheck(polynomial=polynomial)

    # f([0, 0]) + f([0, 1]) + f([1, 0]) + f([1, 0])
    claimed_sum = sc.calc_total_sum()

    proof = sc.prove(
        challenges=[3, 5]
    )

    print("Claimed sum:", claimed_sum)
    print("Proof verified?:", sc.verify(claimed_sum, proof))
