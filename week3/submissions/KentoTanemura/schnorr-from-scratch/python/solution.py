"""Week 3 課題「schnorr-from-scratch」の解答ファイル。

有限体 F_p -> 楕円曲線の群 -> シグマプロトコル / Schnorr 署名、と下から
積み上げる。点は (x, y) のタプル、無限遠点は INFINITY (= None)。
座標の計算は mod p、スカラーの計算は mod n（G の位数）。
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
# 入力が負や p 以上でも構わないよう、返す前に必ず mod を取る。


def field_add(a: int, b: int, p: int) -> int:
    """F_p での足し算 (a + b) mod p。"""
    return (a + b) % p


def field_mul(a: int, b: int, p: int) -> int:
    """F_p での掛け算 (a * b) mod p。"""
    return (a * b) % p


def field_inv(a: int, p: int) -> int:
    """F_p での逆元。(a * x) mod p == 1 となる x を 0..p-1 で返す。

    a ≡ 0 (mod p) のときは逆元が存在しないので ValueError。
    """
    a %= p
    if a == 0:
        raise ValueError("0 has no inverse in F_p")

    g, x, _ = extended_gcd(a, p)
    if g != 1:
        # p が素数ならここには来ないが、念のため。
        raise ValueError(f"{a} is not invertible modulo {p}")
    return x % p


# =================================================================== Part 2
# y^2 = x^3 + a*x + b over F_p の群演算。


def ec_add(P: Point, Q: Point, curve: Curve) -> Point:
    """楕円曲線上の点の足し算 P + Q。

    無限遠点が単位元。P と Q が互いの逆元（x が同じで y の和が 0）なら
    無限遠点。それ以外は、2 倍算なら接線、異なる点なら弦の傾き lam から
        x_R = lam^2 - x_P - x_Q,  y_R = lam * (x_P - x_R) - y_P
    で求まる。割り算は field_inv。
    """
    if P is INFINITY:
        return Q
    if Q is INFINITY:
        return P

    p = curve.p
    x_P, y_P = P
    x_Q, y_Q = Q

    if x_P == x_Q and (y_P + y_Q) % p == 0:
        return INFINITY

    if P == Q:
        # 接線の傾き。y_P == 0 の場合は上で処理済みなので分母は 0 にならない。
        numerator = field_add(field_mul(3, field_mul(x_P, x_P, p), p), curve.a, p)
        denominator = field_mul(2, y_P, p)
    else:
        numerator = (y_Q - y_P) % p
        denominator = (x_Q - x_P) % p

    lam = field_mul(numerator, field_inv(denominator, p), p)
    x_R = (field_mul(lam, lam, p) - x_P - x_Q) % p
    y_R = (field_mul(lam, x_P - x_R, p) - y_P) % p
    return (x_R, y_R)


def ec_scalar_mul(k: int, P: Point, curve: Curve) -> Point:
    """スカラー倍 k * P（k >= 0）を double-and-add で計算する。

    k を下位ビットから見て、立っているビットのところで addend（P の 2^i 倍）
    を足す。足し算の回数は O(log k)。
    """
    if k < 0:
        raise ValueError("k must be non-negative")

    result: Point = INFINITY
    addend = P
    while k > 0:
        k, bit = divmod(k, 2)
        if bit:
            result = ec_add(result, addend, curve)
        addend = ec_add(addend, addend, curve)
    return result


# =================================================================== Part 3
# 離散対数の知識のシグマプロトコルと、Fiat-Shamir 変換による Schnorr 署名。
# 秘密鍵 x、公開鍵 pubkey = x * G。スカラーは mod curve.n。


def sigma_commit(r: int, curve: Curve) -> Point:
    """手番 1: ノンス r からコミットメント R = r * G。"""
    return ec_scalar_mul(r % curve.n, curve.G, curve)


def sigma_response(x: int, r: int, e: int, curve: Curve) -> int:
    """手番 3: レスポンス s = r + e * x (mod n)。"""
    return (r + e * x) % curve.n


def sigma_verify(pubkey: Point, R: Point, e: int, s: int, curve: Curve) -> bool:
    """検証: s * G == R + e * pubkey かどうか。

    正直な証明者なら s*G = (r + e*x)*G = R + e*pubkey となって必ず通る。
    """
    lhs = ec_scalar_mul(s % curve.n, curve.G, curve)
    rhs = ec_add(R, ec_scalar_mul(e % curve.n, pubkey, curve), curve)
    return lhs == rhs


def schnorr_sign(
    x: int, message: bytes, nonce: int, curve: Curve
) -> tuple[Point, int]:
    """Schnorr 署名 (R, s) を作る。

    検証者が選んでいたチャレンジを e = H(R || pubkey || message) に置き換える
    のが Fiat-Shamir 変換で、これで対話が不要になる。
    """
    R = sigma_commit(nonce, curve)
    pubkey = ec_scalar_mul(x % curve.n, curve.G, curve)
    e = challenge_hash(R, pubkey, message, curve.n)
    s = sigma_response(x, nonce, e, curve)
    return (R, s)


def schnorr_verify(
    pubkey: Point, message: bytes, signature: tuple[Point, int], curve: Curve
) -> bool:
    """Schnorr 署名の検証。e を自分で計算し直してから検証式を確認する。"""
    R, s = signature
    e = challenge_hash(R, pubkey, message, curve.n)
    return sigma_verify(pubkey, R, e, s, curve)


# =================================================================== 簡易チェック
# 実装しながらの動作確認用（採点は tests/public.py）。

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

    # 曲線から外れていないかの確認（Part 2 のデバッグ用）。
    assert is_on_curve(ec_scalar_mul(500, TOY.G, TOY), TOY)
