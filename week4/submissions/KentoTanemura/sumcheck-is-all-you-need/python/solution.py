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

    def reduce(self, x: int) -> int:
        """Calculates x (mod p).
        
        Args:
            x: target number
        
        Returns:
            x (mod p)
        """
        return x % self.p

    def evaluate(self, point: tuple[int, ...]) -> int:
        """Evaluates polynomial at `point`.
        
        Args:
            point: evaluation point
        
        Returns:
            Evaluation result
        """
        total = 0
        for exponents, coefficient in self.terms.items():
            monomial = coefficient
            for value, exponent in zip(point, exponents):
                monomial = monomial * pow(value, exponent, self.p)
            total += monomial
        return self.reduce(total)


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
        # Horner's method: c_0 + x*(c_1 + x*(c_2 + ...))
        result = 0
        for coefficient in reversed(self.coefficients):
            result = self.reduce(result * x + coefficient)
        return result


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

    def degree_of(self, index: int) -> int:
        """Returns the maximum degree of the `index`-th variable in `f`.

        Args:
            index: variable index (0-origin)

        Returns:
            Maximum degree of the variable
        """
        return max(exponents[index] for exponents in self.f.terms)

    def construct_round_polynomial(self, challenges: list[int]) -> UnivariatePolynomial:
        """Constructs the round polynomial g_i(t) = Σf(r_1, ..., r_{i-1}, t, x_{i+1}, ..., x_n).

        Args:
            challenges: fixed random challenge values
        
        Returns:
            Univariate polynomial for a single round
        """
        index = len(challenges)          # 0-origin index of the free variable t
        n_free = self.n - index - 1      # number of variables summed over {0,1}

        coefficients = [0] * (self.degree_of(index) + 1)

        for point in self.gen_boolean_points(n_free):
            for exponents, coefficient in self.f.terms.items():
                monomial = coefficient
                # substitute the challenges fixed in the previous rounds
                for value, exponent in zip(challenges, exponents[:index]):
                    monomial = monomial * pow(value, exponent, self.p)
                # substitute the boolean point for the remaining variables
                for value, exponent in zip(point, exponents[index + 1:]):
                    monomial = monomial * pow(value, exponent, self.p)
                # the exponent of t decides which coefficient this term belongs to
                degree = exponents[index]
                coefficients[degree] = self.f.reduce(coefficients[degree] + monomial)

        return UnivariatePolynomial(coefficients=coefficients, p=self.p)

    def prove(self, challenges:list[int] | None = None) -> list[tuple[UnivariatePolynomial, int]]:
        """Generates a proof.

        Args:
            challenges: random challenge values
        
        Returns:
            Proof (a list of tuples of round polynomial g_i(t) and random challenge r_i)
        """
        proof: list[tuple[UnivariatePolynomial, int]] = []
        fixed: list[int] = []

        for i in range(self.n):
            round_polynomial = self.construct_round_polynomial(fixed)
            if challenges is None:
                challenge = random.randrange(self.p)
            else:
                challenge = self.f.reduce(challenges[i])
            proof.append((round_polynomial, challenge))
            fixed.append(challenge)

        return proof

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
        if len(proof) != self.n:
            return False

        expected = self.f.reduce(claimed_sum)
        challenges: list[int] = []

        for index, (round_polynomial, challenge) in enumerate(proof):
            # the round polynomial must not exceed the degree of the variable in f
            if len(round_polynomial.coefficients) - 1 > self.degree_of(index):
                return False
            # g_i(0) + g_i(1) must reproduce the sum claimed by the previous round
            if self.f.reduce(round_polynomial.evaluate(0) + round_polynomial.evaluate(1)) != expected:
                return False
            expected = round_polynomial.evaluate(challenge)
            challenges.append(challenge)

        # final check against a single oracle evaluation of f
        return expected == self.f.evaluate(tuple(challenges))


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
