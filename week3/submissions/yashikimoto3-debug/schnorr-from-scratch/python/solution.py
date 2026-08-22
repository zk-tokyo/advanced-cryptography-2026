"""Week 3 課題「schnorr-from-scratch」の解答ファイルです。

編集してよいのはこのファイルと requirements.txt だけです。
先に problems/schnorr-from-scratch/README.md を読んでください。
"""

from __future__ import annotations

from given import (
    INFINITY,
    Curve,
    Point,
    challenge_hash,
    extended_gcd,
    is_on_curve,
)


# =================================================================== Part 1

def field_add(a: int, b: int, p: int) -> int:
    """F_p での足し算。"""
    if p <= 0:
        raise ValueError("p must be positive")
    return (a + b) % p


def field_mul(a: int, b: int, p: int) -> int:
    """F_p での掛け算。"""
    if p <= 0:
        raise ValueError("p must be positive")
    return (a * b) % p


def field_inv(a: int, p: int) -> int:
    """F_p での逆元。"""
    if p <= 1:
        raise ValueError("p must be greater than 1")

    a_mod = a % p

    if a_mod == 0:
        raise ValueError("zero has no inverse")

    g, x, _ = extended_gcd(a_mod, p)

    if g != 1:
        raise ValueError("inverse does not exist")

    return x % p


# =================================================================== Part 2

def ec_add(P: Point, Q: Point, curve: Curve) -> Point:
    """楕円曲線上の点の足し算 P + Q。"""

    # 1. 無限遠点
    if P is INFINITY:
        return Q

    if Q is INFINITY:
        return P

    x_p, y_p = P
    x_q, y_q = Q

    p = curve.p
    a = curve.a

    # 2. P と Q が互いに逆元
    if x_p == x_q and (y_p + y_q) % p == 0:
        return INFINITY

    # 3. P == Q : doubling
    if P == Q:
        denominator = (2 * y_p) % p
        lam = (
            (3 * x_p * x_p + a) % p
            * field_inv(denominator, p)
        ) % p

    # 4. P != Q : addition
    else:
        numerator = (y_q - y_p) % p
        denominator = (x_q - x_p) % p

        lam = (
            numerator * field_inv(denominator, p)
        ) % p

    x_r = (lam * lam - x_p - x_q) % p
    y_r = (lam * (x_p - x_r) - y_p) % p

    return (x_r, y_r)


def ec_scalar_mul(k: int, P: Point, curve: Curve) -> Point:
    """double-and-add によるスカラー倍。"""

    if k < 0:
        raise ValueError("k must be non-negative")

    if k == 0 or P is INFINITY:
        return INFINITY

    result = INFINITY
    current = P

    while k > 0:
        k, bit = divmod(k, 2)

        if bit == 1:
            result = ec_add(result, current, curve)

        current = ec_add(current, current, curve)

    return result


# =================================================================== Part 3

def sigma_commit(r: int, curve: Curve) -> Point:
    """R = r * G。"""
    return ec_scalar_mul(r % curve.n, curve.G, curve)


def sigma_response(x: int, r: int, e: int, curve: Curve) -> int:
    """s = r + e*x mod n。"""
    return (r + e * x) % curve.n


def sigma_verify(
    pubkey: Point,
    R: Point,
    e: int,
    s: int,
    curve: Curve,
) -> bool:
    """s*G == R + e*pubkey を確認する。"""

    left = ec_scalar_mul(s % curve.n, curve.G, curve)
    right = ec_add(
        R,
        ec_scalar_mul(e % curve.n, pubkey, curve),
        curve,
    )

    return left == right


def schnorr_sign(
    x: int,
    message: bytes,
    nonce: int,
    curve: Curve,
) -> tuple[Point, int]:
    """Schnorr 署名を作る。"""

    R = sigma_commit(nonce, curve)

    pubkey = ec_scalar_mul(
        x % curve.n,
        curve.G,
        curve,
    )

    e = challenge_hash(
        R,
        pubkey,
        message,
        curve.n,
    )

    s = sigma_response(
        x,
        nonce,
        e,
        curve,
    )

    return R, s


def schnorr_verify(
    pubkey: Point,
    message: bytes,
    signature: tuple[Point, int],
    curve: Curve,
) -> bool:
    """Schnorr 署名を検証する。"""

    R, s = signature

    # 署名の形を最低限チェック
    if R is not INFINITY:
        if not is_on_curve(R, curve):
            return False

    if not isinstance(s, int):
        return False

    e = challenge_hash(
        R,
        pubkey,
        message,
        curve.n,
    )

    return sigma_verify(
        pubkey,
        R,
        e,
        s,
        curve,
    )


# =================================================================== 簡易チェック

if __name__ == "__main__":
    from given import TOY

    def _check(label, fn, expected):
        try:
            got = fn()
        except NotImplementedError:
            print(f"[ ] {label}: 未実装")
            return
        except Exception as exc:
            print(f"[x] {label}: 例外 {exc!r}")
            return

        mark = "o" if got == expected else "x"
        suffix = "OK" if got == expected else f"{got!r} (期待値 {expected!r})"
        print(f"[{mark}] {label}: {suffix}")

    _check(
        "Part1 field_add(3, 4, 7)",
        lambda: field_add(3, 4, 7),
        0,
    )

    _check(
        "Part1 field_mul(3, 4, 7)",
        lambda: field_mul(3, 4, 7),
        5,
    )

    _check(
        "Part1 field_inv(3, 11)",
        lambda: field_inv(3, 11),
        4,
    )

    _check(
        "Part2 ec_add(G, G, TOY) = 2G",
        lambda: ec_add(TOY.G, TOY.G, TOY),
        (818, 800),
    )

    _check(
        "Part2 ec_add(G, 2G, TOY) = 3G",
        lambda: ec_add(TOY.G, (818, 800), TOY),
        (851, 516),
    )

    _check(
        "Part2 ec_scalar_mul(123, G, TOY)",
        lambda: ec_scalar_mul(123, TOY.G, TOY),
        (376, 128),
    )

    _check(
        "Part3 sigma_commit(456, TOY)",
        lambda: sigma_commit(456, TOY),
        (822, 106),
    )

    _check(
        "Part3 sigma_response(x=123, r=456, e=77, TOY)",
        lambda: sigma_response(123, 456, 77, TOY),
        257,
    )

    _check(
        "Part3 sigma_verify(正直なトランスクリプト)",
        lambda: sigma_verify(
            (376, 128),
            (822, 106),
            77,
            257,
            TOY,
        ),
        True,
    )

    _check(
        "Part3 schnorr_sign -> schnorr_verify (TOY)",
        lambda: schnorr_verify(
            ec_scalar_mul(123, TOY.G, TOY),
            b"hello week3",
            schnorr_sign(
                123,
                b"hello week3",
                456,
                TOY,
            ),
            TOY,
        ),
        True,
    )