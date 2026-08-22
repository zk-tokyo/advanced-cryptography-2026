"""Week 3 課題「schnorr-from-scratch」の解答ファイルです。

Part 1 有限体 F_p の演算
  -> Part 2 その上の楕円曲線の群演算
    -> Part 3 その群を使ったシグマプロトコルと Schnorr 署名

点は (x, y) のタプルで表し、無限遠点は INFINITY(= None)で表します。
"""

from __future__ import annotations

from given import (
    INFINITY,
    Curve,
    Point,
    challenge_hash,
    extended_gcd,
    is_on_curve
)


# =================================================================== Part 1
def field_add(a: int, b: int, p: int) -> int:
    """F_p での足し算です。(a + b) mod p を 0..p-1 の範囲で返します。"""
    return (a + b) % p


def field_mul(a: int, b: int, p: int) -> int:
    """F_p での掛け算です。(a * b) mod p を 0..p-1 の範囲で返します。"""
    return (a * b) % p


def field_inv(a: int, p: int) -> int:
    """F_p での逆元です。(a * x) mod p == 1 となる x を 0..p-1 で返します。

    a ≡ 0 (mod p) のときは逆元が存在しないので ValueError を送出します。
    """
    a_reduced = a % p
    if a_reduced == 0:
        raise ValueError("0 has no inverse in F_p")
    g, x, _ = extended_gcd(a_reduced, p)
    if g != 1:
        raise ValueError("inverse does not exist")
    return x % p


# =================================================================== Part 2
def ec_add(P: Point, Q: Point, curve: Curve) -> Point:
    """楕円曲線上の点の足し算 P + Q です。"""
    p = curve.p

    # 1. 無限遠点(単位元)の処理は、座標を取り出すより先に行う。
    if P is INFINITY:
        return Q
    if Q is INFINITY:
        return P

    x_P, y_P = P
    x_Q, y_Q = Q

    # 2. 互いに逆元(x が同じで y の和が 0)なら無限遠点。
    #    P == Q かつ y == 0 の場合もここに含まれる。
    if x_P % p == x_Q % p and (y_P + y_Q) % p == 0:
        return INFINITY

    if x_P % p == x_Q % p and y_P % p == y_Q % p:
        # 3. 2 倍算: 接線の傾き lam = (3*x^2 + a) / (2*y)
        numerator = field_add(field_mul(3, field_mul(x_P, x_P, p), p), curve.a, p)
        denominator = field_mul(2, y_P, p)
    else:
        # 4. 弦の傾き lam = (y_Q - y_P) / (x_Q - x_P)
        numerator = (y_Q - y_P) % p
        denominator = (x_Q - x_P) % p

    lam = field_mul(numerator, field_inv(denominator, p), p)

    x_R = (field_mul(lam, lam, p) - x_P - x_Q) % p
    y_R = (field_mul(lam, (x_P - x_R) % p, p) - y_P) % p
    return (x_R, y_R)


def ec_scalar_mul(k: int, P: Point, curve: Curve) -> Point:
    """スカラー倍 k * P です(double-and-add 法)。"""
    if k < 0:
        raise ValueError("k must be non-negative")
    result: Point = INFINITY
    addend: Point = P
    while k > 0:
        k, bit = divmod(k, 2)
        if bit:
            result = ec_add(result, addend, curve)
        addend = ec_add(addend, addend, curve)
    return result


# =================================================================== Part 3
def sigma_commit(r: int, curve: Curve) -> Point:
    """手番 1: ノンス r からコミットメント R = r * G を計算します。"""
    return ec_scalar_mul(r % curve.n, curve.G, curve)


def sigma_response(x: int, r: int, e: int, curve: Curve) -> int:
    """手番 3: レスポンス s = r + e * x (mod n) を計算します。"""
    return (r + e * x) % curve.n


def sigma_verify(pubkey: Point, R: Point, e: int, s: int, curve: Curve) -> bool:
    """検証者の確認です。s * G == R + e * pubkey が成り立つかを返します。"""
    left = ec_scalar_mul(s % curve.n, curve.G, curve)
    right = ec_add(R, ec_scalar_mul(e % curve.n, pubkey, curve), curve)
    return left == right


def schnorr_sign(
    x: int, message: bytes, nonce: int, curve: Curve
) -> tuple[Point, int]:
    """Schnorr 署名を作り、(R, s) を返します(Fiat-Shamir 変換)。"""
    R = sigma_commit(nonce, curve)
    pubkey = ec_scalar_mul(x % curve.n, curve.G, curve)
    e = challenge_hash(R, pubkey, message, curve.n)
    s = sigma_response(x, nonce, e, curve)
    return (R, s)


def schnorr_verify(
    pubkey: Point, message: bytes, signature: tuple[Point, int], curve: Curve
) -> bool:
    """Schnorr 署名を検証します。e は自分で計算し直します。"""
    R, s = signature
    e = challenge_hash(R, pubkey, message, curve.n)
    return sigma_verify(pubkey, R, e, s, curve)


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

    _check("Part1 field_add(3, 4, 7)", lambda: field_add(3, 4, 7), 0)
    _check("Part1 field_mul(3, 4, 7)", lambda: field_mul(3, 4, 7), 5)
    _check("Part1 field_inv(3, 11)", lambda: field_inv(3, 11), 4)
    _check("Part2 ec_add(G, G, TOY) = 2G",
           lambda: ec_add(TOY.G, TOY.G, TOY), (818, 800))
    _check("Part2 ec_add(G, 2G, TOY) = 3G",
           lambda: ec_add(TOY.G, (818, 800), TOY), (851, 516))
    _check("Part2 ec_scalar_mul(123, G, TOY)",
           lambda: ec_scalar_mul(123, TOY.G, TOY), (376, 128))
    _check("Part3 sigma_commit(456, TOY)",
           lambda: sigma_commit(456, TOY), (822, 106))
    _check("Part3 sigma_response(x=123, r=456, e=77, TOY)",
           lambda: sigma_response(123, 456, 77, TOY), 257)
    _check("Part3 sigma_verify(正直なトランスクリプト)",
           lambda: sigma_verify((376, 128), (822, 106), 77, 257, TOY), True)
    _check("Part3 schnorr_sign -> schnorr_verify (TOY)",
           lambda: schnorr_verify(
               ec_scalar_mul(123, TOY.G, TOY),
               b"hello week3",
               schnorr_sign(123, b"hello week3", 456, TOY),
               TOY,
           ), True)