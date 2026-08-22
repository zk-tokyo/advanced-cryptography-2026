"""Week 3課題「schnorr-from-scratch」の解答ファイルです。

課題はひとつなぎです:
    Part 1 有限体 F_p の演算
      -> Part 2 その上の楕円曲線の群演算
        -> Part 3 その群を使ったシグマプロトコルと Schnorr 署名

点は (x, y) のタプルで表し、無限遠点は INFINITY(= None)で表します。
座標の計算は mod p、スカラーの計算は mod n(G の位数)で行います。
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
# 有限体 F_p です。要素は 0..p-1 の整数で表します。入力には範囲外(負や
# p 以上)の整数が来ることもあるので、結果は必ず 0..p-1 に正規化して
# 返してください。


def field_add(a: int, b: int, p: int) -> int:
    """F_p での足し算です。(a + b) mod p を 0..p-1 の範囲で返します。"""
    # Python の % は法が正なら必ず 0..p-1 を返すので、負の入力もこれだけで
    # 正規化できる（C 系の % と違って符号が被除数に引きずられない）。
    return (a + b) % p


def field_mul(a: int, b: int, p: int) -> int:
    """F_p での掛け算です。(a * b) mod p を 0..p-1 の範囲で返します。"""
    return (a * b) % p


def field_inv(a: int, p: int) -> int:
    """F_p での逆元です。(a * x) mod p == 1 となる x を 0..p-1 の範囲で返します。

    a が p の倍数(つまり F_p で 0)のときは逆元が存在しないので、
    ValueError を送出します。
    """
    # 先に 0..p-1 に落としてから 0 を弾く。a = 2018, p = 1009 のように
    # 「見た目は非ゼロだが F_p では 0」というケースを取りこぼさないため。
    residue = a % p
    if residue == 0:
        raise ValueError("0 has no multiplicative inverse in F_p")

    # 拡張ユークリッドは residue * x + p * y == gcd(residue, p) を満たす
    # (g, x, y) を返す。g == 1 なら両辺を mod p して p * y の項が消え、
    #     residue * x ≡ 1 (mod p)
    # となるので x がそのまま逆元。
    g, x, _ = extended_gcd(residue, p)
    if g != 1:
        # p が素数ならここには来ない（residue != 0 なら必ず互いに素）。
        # 合成数を渡された場合の保険。
        raise ValueError(f"{a} is not invertible modulo {p}")

    # x は負のことがある（例: extended_gcd(3, 11) -> (1, 4, -1)）ので正規化する。
    return x % p


# =================================================================== Part 2
# 楕円曲線 y^2 = x^3 + a*x + b over F_p の群演算です。
# curve.p, curve.a, curve.b, curve.G, curve.n が使えます(tests/given.py 参照)。


def ec_add(P: Point, Q: Point, curve: Curve) -> Point:
    """楕円曲線上の点の足し算 P + Q です。

    場合分けは次のとおりです。
      1. どちらかが無限遠点(単位元)なら、もう片方を返す
      2. x が等しく y が互いに逆符号なら INFINITY（P と Q が互いの逆元）
      3. P == Q なら 2 倍算。接線の傾き lam = (3*x_P^2 + a) / (2*y_P)
      4. それ以外は弦の傾き lam = (y_Q - y_P) / (x_Q - x_P)
    3. と 4. はどちらも lam から
        x_R = lam^2 - x_P - x_Q
        y_R = lam * (x_P - x_R) - y_P
    で (x_R, y_R) が求まります。
    """
    p = curve.p

    # 1. 無限遠点は単位元。None をアンパックすると死ぬので、座標を取り出す前に処理する。
    if P is INFINITY:
        return Q
    if Q is INFINITY:
        return P

    x_P, y_P = P
    x_Q, y_Q = Q

    if (x_P - x_Q) % p == 0:
        # x が同じ点は、y^2 = x^3 + ax + b から y = ±(同じ値) の 2 つしかない。
        # つまりここに来た時点で Q は P か -P のどちらか。
        if field_add(y_P, y_Q, p) == 0:
            # 2. Q == -P。直線が y 軸に平行になり、第 3 の交点が無限遠点に飛ぶ。
            #    P == Q かつ y == 0（接線が垂直）の場合もこの分岐に入る。
            return INFINITY
        # 3. 残りは Q == P なので 2 倍算。曲線を陰関数微分して
        #        2y dy = (3x^2 + a) dx
        #    より接線の傾きは (3x^2 + a) / (2y)。y != 0 は上で保証済み。
        numerator = field_add(field_mul(3, field_mul(x_P, x_P, p), p), curve.a, p)
        denominator = field_mul(2, y_P, p)
    else:
        # 4. 相異なる 2 点を通る弦の傾き。x_P != x_Q なので分母は非ゼロ。
        numerator = (y_Q - y_P) % p
        denominator = (x_Q - x_P) % p

    # 有限体に「割り算」はないので、逆元を掛けることで割る。
    lam = field_mul(numerator, field_inv(denominator, p), p)

    # 直線 y = lam*(x - x_P) + y_P を曲線に代入すると x の 3 次式になり、
    # 根の和 = lam^2（3 次の係数で正規化した 2 次の係数の符号反転）。
    # 既知の根が x_P, x_Q なので第 3 の交点は x_R = lam^2 - x_P - x_Q。
    x_R = (lam * lam - x_P - x_Q) % p
    # 第 3 の交点を x 軸で折り返したものが P + Q なので、直線の式で得た
    # y 座標に負号を付ける（-(lam*(x_R - x_P) + y_P) を整理した形）。
    y_R = (lam * (x_P - x_R) - y_P) % p
    return (x_R, y_R)


def ec_scalar_mul(k: int, P: Point, curve: Curve) -> Point:
    """スカラー倍 k * P です(k は 0 以上の整数)。

    double-and-add 法で計算するので、足し算の回数は O(log k) に収まります。
    k == 0 のときは INFINITY を返します。
    """
    if k < 0:
        raise ValueError("k must be non-negative")

    # k を 2 進展開して k = sum(bit_i * 2^i) と見ると
    #     k*P = sum(bit_i * (2^i * P))
    # なので、2^i * P を 2 倍算で作りながら、bit が 1 の分だけ足せばよい。
    # 素朴に P を k 回足すと secp256k1 の 256 ビットスカラーでは終わらない。
    result = INFINITY  # 空の和は単位元 = 無限遠点
    addend = P         # ループ i 週目には 2^i * P が入っている
    while k > 0:
        k, bit = divmod(k, 2)
        if bit:
            result = ec_add(result, addend, curve)
        addend = ec_add(addend, addend, curve)
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
    """手番 1: ノンス r からコミットメント R = r * G を計算します。"""
    # G の位数が n なので n*G = O、つまりスカラーは mod n で潰しても同じ点になる。
    # ここで正規化しておけば ec_scalar_mul に負の値が渡ることもない。
    return ec_scalar_mul(r % curve.n, curve.G, curve)


def sigma_response(x: int, r: int, e: int, curve: Curve) -> int:
    """手番 3: レスポンス s = r + e * x (mod n) を計算します。

    秘密鍵 x を使うのはここだけです。s は 0..n-1 の範囲で返します。
    """
    # mod は座標の素数 p ではなく G の位数 n。指数（スカラー）の世界は
    # Z_n なので、ここを p にすると検証等式が成立しなくなる。
    # r は一様乱数なので、s は x の情報を漏らさない（perfect hiding）。
    return (r + e * x) % curve.n


def sigma_verify(pubkey: Point, R: Point, e: int, s: int, curve: Curve) -> bool:
    """検証者の確認です。s * G == R + e * pubkey が成り立つかを返します。

    これで確認になっている理由(完全性):
        s * G = (r + e*x) * G = r*G + e*(x*G) = R + e * pubkey
    """
    # 検証者は秘密を持たないので、公開されている G と pubkey へのスカラー倍だけで
    # 等式を確かめられる。逆に等式を満たす s を作るには離散対数 x が必要
    # （e を見る前に R を固定させているため、当て推量の成功確率は 1/n）。
    left = ec_scalar_mul(s % curve.n, curve.G, curve)
    right = ec_add(R, ec_scalar_mul(e % curve.n, pubkey, curve), curve)
    # 点はタプル（または None）なので == で座標ごとの比較になる。
    return left == right


def schnorr_sign(
    x: int, message: bytes, nonce: int, curve: Curve
) -> tuple[Point, int]:
    """Schnorr 署名を作り、(R, s) を返します。

    Fiat-Shamir 変換では、検証者が選んでいたランダムなチャレンジ e を
        e = challenge_hash(R, pubkey, message, curve.n)
    で置き換えます。これで対話が要らなくなり、そのまま署名方式になります。
    """
    R = sigma_commit(nonce, curve)
    pubkey = ec_scalar_mul(x % curve.n, curve.G, curve)

    # e をハッシュから作るのが Fiat-Shamir 変換。R を入力に含めるので、
    # 証明者は e を見てから R を選び直せない（= 検証者のランダム性の代役）。
    # message も入力に含まれるため、この s は「このメッセージ専用」になる。
    e = challenge_hash(R, pubkey, message, curve.n)

    # 対話版のレスポンスがそのまま署名になる。nonce を 2 回使うと
    # s1 - s2 = (e1 - e2)*x から x が解けてしまうので、実運用では毎回新しい乱数。
    s = sigma_response(x, nonce, e, curve)
    return R, s


def schnorr_verify(
    pubkey: Point, message: bytes, signature: tuple[Point, int], curve: Curve
) -> bool:
    """Schnorr 署名を検証します。"""
    R, s = signature

    # e は署名に含めず、検証側が同じ入力から計算し直す。これにより
    # (R, s) を別メッセージへ流用しても e が変わって等式が崩れる。
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

    # 実装が正しければ、計算結果は必ず曲線上に乗る（is_on_curve で確認できる）。
    _check("Part2 is_on_curve(20G, TOY)",
           lambda: is_on_curve(ec_scalar_mul(20, TOY.G, TOY), TOY), True)
