from __future__ import annotations

# =========================================================================
# PROVIDED MPC TOOLKIT — DO NOT EDIT.
#
# These are the additive secret-sharing primitives you already studied in the
# MPC material. In this problem they are handed to you as a black box: you are
# NOT implementing MPC here. You build a co-SNARK *prover* on top of them.
#
# Every value below is a field element in [0, modulus). A "share vector" is a
# list of one share per party; the secret is `sum(shares) % modulus`.
# =========================================================================


def share(secret: int, randomness: list[int], modulus: int) -> list[int]:
    """Split `secret` into len(randomness) + 1 additive shares mod `modulus`."""
    shares = [r % modulus for r in randomness]
    shares.append((secret - sum(randomness)) % modulus)
    return shares


def reconstruct(shares: list[int], modulus: int) -> int:
    """Open all shares to recover the secret: sum(shares) % modulus."""
    return sum(shares) % modulus


def add_shares(shares_a: list[int], shares_b: list[int], modulus: int) -> list[int]:
    """Component-wise sum of two share vectors. Local: no communication."""
    return [(x + y) % modulus for x, y in zip(shares_a, shares_b)]


def scale_shares(shares: list[int], scalar: int, modulus: int) -> list[int]:
    """Multiply each share by the public `scalar`. Local: no communication."""
    return [(x * scalar) % modulus for x in shares]


def beaver_multiply(
    x_shares: list[int],
    y_shares: list[int],
    a_shares: list[int],
    b_shares: list[int],
    c_shares: list[int],
    modulus: int,
) -> list[int]:
    """Shares of x * y using a pre-shared Beaver triple (a, b, c = a*b).

    This is the ONLY step that needs communication (two openings, d and e).
    """
    d = (reconstruct(x_shares, modulus) - reconstruct(a_shares, modulus)) % modulus
    e = (reconstruct(y_shares, modulus) - reconstruct(b_shares, modulus)) % modulus
    z = [
        (c_shares[i] + d * b_shares[i] + e * a_shares[i]) % modulus
        for i in range(len(c_shares))
    ]
    z[0] = (z[0] + d * e) % modulus
    return z


# =========================================================================
# YOUR TASK — implement the prover computation that runs on the shared witness.
#
# The toy prover proves knowledge of a witness w = (w_0, ..., w_{n-1}) and
# outputs the proof triple (A, B, C) where, for public coefficient vectors
# `coeffs_a` and `coeffs_b`:
#
#     A = sum_j coeffs_a[j] * w_j        (a linear form  -> local on shares)
#     B = sum_j coeffs_b[j] * w_j        (a linear form  -> local on shares)
#     C = A * B                          (secret x secret -> one Beaver round)
#
# This is the essential shape of a real SNARK prover: many field-linear
# combinations (MSM / FFT) that are free on shares, plus a few products that
# each cost one Beaver multiplication. A correct co-SNARK prover NEVER calls
# `reconstruct` on the witness — only the final proof elements are opened.
# =========================================================================


def linear_combination_shares(
    coeffs: list[int],
    wire_shares: list[list[int]],
    modulus: int,
) -> list[int]:
    """Share vector of sum_j coeffs[j] * w_j.

    `wire_shares[j]` is the share vector of wire w_j (all wires share the same
    number of parties). Build the result with `scale_shares` / `add_shares`
    only — this is entirely local, no communication.
    """
    party_count = len(wire_shares[0])
    result = [0 for _ in range(party_count)]
    for coefficient, shares in zip(coeffs, wire_shares):
        scaled = scale_shares(shares, coefficient, modulus)
        result = add_shares(result, scaled, modulus)
    return result


def mpc_prove(
    coeffs_a: list[int],
    coeffs_b: list[int],
    wire_shares: list[list[int]],
    beaver_triple: tuple[list[int], list[int], list[int]],
    modulus: int,
) -> tuple[list[int], list[int], list[int]]:
    """Run the prover on the shared witness and return share vectors (A, B, C).

    `beaver_triple` is `(a_shares, b_shares, c_shares)` with c = a * b, used for
    the single A * B multiplication.
    """
    # Linear forms: each party computes these locally on its own shares.
    a_shares = linear_combination_shares(coeffs_a, wire_shares, modulus)
    b_shares = linear_combination_shares(coeffs_b, wire_shares, modulus)

    # The only interactive step: secret x secret needs one Beaver round.
    triple_a, triple_b, triple_c = beaver_triple
    c_shares = beaver_multiply(
        a_shares,
        b_shares,
        triple_a,
        triple_b,
        triple_c,
        modulus,
    )
    return (a_shares, b_shares, c_shares)
