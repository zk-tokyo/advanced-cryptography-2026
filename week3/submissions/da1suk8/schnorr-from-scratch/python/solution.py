"""Week 3 課題「schnorr-from-scratch」の解答ファイルです。

編集してよいのはこのファイルと requirements.txt だけです。
先に problems/schnorr-from-scratch/README.md を読んでください。
曲線のパラメータや拡張ユークリッドの互除法などの道具は tests/given.py に
あります。

課題はひとつなぎです:
    Part 1 有限体 F_p の演算
      -> Part 2 その上の楕円曲線の群演算
        -> Part 3 その群を使ったシグマプロトコルと Schnorr 署名

点は (x, y) のタプルで表し、無限遠点は INFINITY(= None)で表します。
"""

from __future__ import annotations

from given import INFINITY, Curve, Point, challenge_hash, extended_gcd, is_on_curve

# =================================================================== Part 1
# 有限体 F_p です。要素は 0..p-1 の整数で表します。入力には範囲外(負や
# p 以上)の整数が来ることもあるので、結果は必ず 0..p-1 に正規化して
# 返してください。


def field_add(a: int, b: int, p: int) -> int:
    """F_p での足し算です。(a + b) mod p を 0..p-1 の範囲で返してください。"""
    return (a + b) % p


def field_mul(a: int, b: int, p: int) -> int:
    """F_p での掛け算です。(a * b) mod p を 0..p-1 の範囲で返してください。"""
    return (a * b) % p


def field_inv(a: int, p: int) -> int:
    """F_p での逆元です。(a * x) mod p == 1 となる x を 0..p-1 の範囲で返してください。

    a が p の倍数(つまり F_p で 0)のときは逆元が存在しないので、
    ValueError を送出してください。

    ヒント: extended_gcd(a % p, p) は (g, x, y) を返し、
        (a % p) * x + p * y == g
    を満たします。g == 1 なら x が逆元です。ただし x は負のことが
    あるので注意してください。
    """
    g, x, _ = extended_gcd(a % p, p)
    if g != 1:
        raise ValueError
    x %= p

    return x


# =================================================================== Part 2
# 楕円曲線 y^2 = x^3 + a*x + b over F_p の群演算です。
# curve.p, curve.a, curve.b, curve.G, curve.n が使えます(tests/given.py 参照)。


def ec_add(P: Point, Q: Point, curve: Curve) -> Point:
    """楕円曲線上の点の足し算 P + Q です。

    この課題の Point は (x, y) という 2 要素のタプル、または無限遠点を
    表す None です。したがって、まず P と Q が INFINITY (= None) でない
    ことを確認してから、次のように座標を取り出せます。

        x_P, y_P = P  # アンパック: P[0], P[1] と書いても同じ
        x_Q, y_Q = Q

    逆に、計算した座標 x_R, y_R から Point を作るには、タプルにします。
    座標は F_p の要素なので、剰余を取って 0..p-1 に正規化してください。

        R: Point = (x_R % curve.p, y_R % curve.p)
        return R

    None かもしれない P や Q を先にアンパックするとエラーになるため、
    下記 1. の無限遠点の処理を座標の取り出しより先に行うのが重要です。

    場合分けは次のとおりです。
      1. P が無限遠点なら Q を、Q が無限遠点なら P を返します
         (無限遠点が単位元です)。
      2. x_P == x_Q かつ y_P + y_Q == 0 (mod p) なら INFINITY を返します
         (P と Q が互いの逆元の場合です。P == Q で y == 0 の場合もここに
         含まれます)。
      3. P == Q なら 2 倍算です。接線の傾き
             lam = (3*x_P**2 + a) / (2*y_P)
         を使います。
      4. それ以外は弦の傾き
             lam = (y_Q - y_P) / (x_Q - x_P)
         を使います。
    3. と 4. はどちらも、傾き lam から
             x_R = lam**2 - x_P - x_Q
             y_R = lam * (x_P - x_R) - y_P
    で (x_R, y_R) が求まります。割り算には Part 1 の field_inv を使って
    ください。

    計算結果が曲線から外れていたら、公式のどこか(たいていは y_R の符号)が
    間違っています。is_on_curve(P, curve) で確かめられます。
    """

    if P is INFINITY:
        return Q
    if Q is INFINITY:
        return P

    x_P, y_P = P
    x_Q, y_Q = Q
    if x_P == x_Q and (y_P + y_Q) % curve.p == 0:
        return INFINITY

    if P == Q:
        lam = (3 * x_P**2 + curve.a) * field_inv(2 * y_P, curve.p)
    else:
        lam = (y_Q - y_P) * field_inv(x_Q - x_P, curve.p)

    x_R = lam**2 - x_P - x_Q
    y_R = lam * (x_P - x_R) - y_P
    R = x_R % curve.p, y_R % curve.p

    return R


def ec_scalar_mul(k: int, P: Point, curve: Curve) -> Point:
    """スカラー倍 k * P です(k は 0 以上の整数)。

    ec_add を k 回繰り返す素朴な方法だと、kに比例した計算時間がかかってしまいます。
    代わりにdouble-and-add 法を使うと高速化できます。k を 2 進数で
    見て下位ビットから順に、ビットが 1 なら答えに P の 2^i 倍を足します。
    P の 2^i 倍は 2 倍算の繰り返しで作れます。これで足し算の回数は
    O(log k) に収まります。k == 0 のときは INFINITY (None) を返してください。

    ヒント: k を 2 で割った商と余りは、次のように同時に計算できます。

        quotient, remainder = divmod(k, 2)

    これは quotient = k // 2、remainder = k % 2 と同じです。
    """
    current = P
    result = INFINITY
    while k:
        if k & 1:
            result = ec_add(result, current, curve)
        current = ec_add(current, current, curve)
        k >>= 1
    return result


# =================================================================== Part 3
# 離散対数の知識のシグマプロトコル(Schnorr の対話証明)と、Fiat-Shamir
# 変換による Schnorr 署名です。
#
# 記号: 秘密鍵 x、公開鍵 pubkey = x * G。スカラーの計算は mod curve.n で
# 行います。
#
# 対話版(シグマプロトコル)は次の 3 手です。
#   1. 証明者: ランダムな r を選び、コミットメント R = r * G を送る
#   2. 検証者: ランダムなチャレンジ e を送る
#   3. 証明者: レスポンス s = r + e * x (mod n) を送る
#   検証者は s * G == R + e * pubkey を確認する


def sigma_commit(r: int, curve: Curve) -> Point:
    """手番 1: ノンス r からコミットメント R = r * G を計算します。

    ヒント: 生成元 G には curve.G としてアクセスできます。
    """
    scalar = r % curve.n
    return ec_scalar_mul(scalar, curve.G, curve)


def sigma_response(x: int, r: int, e: int, curve: Curve) -> int:
    """手番 3: レスポンス s = r + e * x (mod n) を計算します。

    秘密鍵 x を使うのはここだけです。s は 0..n-1 の範囲で返してください。
    mod は curve.n(G の位数)で取ります。curve.p と取り違えやすいので
    注意してください。
    """

    return (r + e * x) % curve.n


def sigma_verify(pubkey: Point, R: Point, e: int, s: int, curve: Curve) -> bool:
    """検証者の確認です。s * G == R + e * pubkey が成り立つかを返します。

    これで確認になっている理由(完全性):
        s * G = (r + e*x) * G = r*G + e*(x*G) = R + e * pubkey
    """
    return ec_scalar_mul(s % curve.n, curve.G, curve) == ec_add(
        R, ec_scalar_mul(e, pubkey, curve), curve
    )


def schnorr_sign(x: int, message: bytes, nonce: int, curve: Curve) -> tuple[Point, int]:
    """Schnorr 署名を作り、(R, s) を返します。

    Fiat-Shamir 変換では、検証者が選んでいたランダムなチャレンジ e を
        e = challenge_hash(R, pubkey, message, curve.n)
    で置き換えます。これで対話が要らなくなり、そのまま署名方式に
    なります。

    手順:
      1. R = nonce * G
      2. pubkey = x * G
      3. e = challenge_hash(R, pubkey, message, curve.n)
      4. s = nonce + e * x (mod n)      # sigma_response がそのまま使えます
      5. (R, s) を返す

    nonce は実運用では毎回新しい乱数にします。使い回すと秘密鍵が漏れます
    (tests/public.py の nonce 再利用テスト参照)。この課題ではテストの
    再現性のため、引数で受け取る作りにしています。
    """
    R = sigma_commit(nonce, curve)
    pubkey = ec_scalar_mul(x, curve.G, curve)
    e = challenge_hash(R, pubkey, message, curve.n)
    s = sigma_response(x, nonce, e, curve)
    return (R, s)


def schnorr_verify(
    pubkey: Point, message: bytes, signature: tuple[Point, int], curve: Curve
) -> bool:
    """Schnorr 署名を検証します。

    signature = (R, s) について、
        e = challenge_hash(R, pubkey, message, curve.n)
    を自分で計算し直し、s * G == R + e * pubkey を確認してください
    (sigma_verify がそのまま使えます)。
    """
    R, s = signature
    e = challenge_hash(R, pubkey, message, curve.n)
    return sigma_verify(pubkey, R, e, s, curve)


# =================================================================== 簡易チェック
# 実装しながらの動作確認用です(採点は tests/public.py で行われます)。
# 実行方法は README の「手元での動かし方」を参照してください。上から順に
# 埋めていくと、[ ] が [o] に変わっていきます。

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
    _check(
        "Part2 ec_add(G, G, TOY) = 2G", lambda: ec_add(TOY.G, TOY.G, TOY), (818, 800)
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
    _check("Part3 sigma_commit(456, TOY)", lambda: sigma_commit(456, TOY), (822, 106))
    _check(
        "Part3 sigma_response(x=123, r=456, e=77, TOY)",
        lambda: sigma_response(123, 456, 77, TOY),
        257,
    )
    _check(
        "Part3 sigma_verify(正直なトランスクリプト)",
        lambda: sigma_verify((376, 128), (822, 106), 77, 257, TOY),
        True,
    )
    _check(
        "Part3 schnorr_sign -> schnorr_verify (TOY)",
        lambda: schnorr_verify(
            ec_scalar_mul(123, TOY.G, TOY),
            b"hello week3",
            schnorr_sign(123, b"hello week3", 456, TOY),
            TOY,
        ),
        True,
    )
