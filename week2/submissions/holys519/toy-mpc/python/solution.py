"""Week 2課題「toy-mpc」の解答ファイルです。

`NotImplementedError`のある8関数を実装してください。
`PROVIDED`と書かれた補助関数は、課題側から与える道具です。

このコードは教育用の集中シミュレータであり、実用上の安全性はありません。
"""

from __future__ import annotations

from given import (
    OT_G,
    OT_P,
    derive_pad,
    validate_choice,
    validate_group_element,
    validate_receiver_scalar,
    validate_sender_scalar,
    xor_bytes,
)

ShareVector = list[int]
BeaverTriple = tuple[ShareVector, ShareVector, ShareVector]


# ========================================================== PROVIDED helpers
def _validate_modulus(modulus: int) -> None:
    if modulus <= 1:
        raise ValueError("modulus must be greater than 1")


def _validate_same_share_count(*vectors: ShareVector) -> int:
    """Return the common party count, or raise ValueError."""
    if not vectors or len(vectors[0]) < 2:
        raise ValueError("a share vector must contain at least two parties")
    count = len(vectors[0])
    if any(len(vector) != count for vector in vectors):
        raise ValueError("share vectors must have the same number of parties")
    return count


def _validate_bit(value: int, name: str = "bit") -> None:
    if value not in (0, 1):
        raise ValueError(f"{name} must be 0 or 1")


def _validate_bit_shares(shares: tuple[int, int], name: str) -> None:
    if len(shares) != 2:
        raise ValueError(f"{name} must contain exactly two shares")
    _validate_bit(shares[0], f"{name}[0]")
    _validate_bit(shares[1], f"{name}[1]")


# ================================================================ Part A1
def share(secret: int, randomness: list[int], modulus: int) -> ShareVector:
    """Split `secret` into len(randomness) + 1 additive shares.

    The values in `randomness` are the first shares. Return canonical field
    elements in 0..modulus-1. At least two parties are required.
    """
    _validate_modulus(modulus)

    # 最初の n-1 個は与えられた乱数そのもの。最後の 1 個を
    #     last = secret - sum(randomness)
    # にすると、全部の和が secret に戻る。
    first_shares = [value % modulus for value in randomness]
    # _validate_same_share_count は「2 party 未満」を弾くので、randomness が
    # 空（= 1 party）のケースはここで拒否される。
    _validate_same_share_count(first_shares + [0])

    last_share = (secret - sum(first_shares)) % modulus
    return first_shares + [last_share]


def reconstruct(shares: ShareVector, modulus: int) -> int:
    """Open additive shares and return the canonical field element."""
    _validate_modulus(modulus)
    _validate_same_share_count(shares)

    # 加法的秘密分散なので、単に全 share を足すだけで秘密に戻る。
    return sum(shares) % modulus


# ================================================================ Part A2
def add_shares(
    left_shares: ShareVector,
    right_shares: ShareVector,
    modulus: int,
) -> ShareVector:
    """Add two shared values component-wise without opening them."""
    _validate_modulus(modulus)
    _validate_same_share_count(left_shares, right_shares)

    # 加算は各 party が自分の share を足すだけで済む（通信も開示も不要）。
    # これが加法的秘密分散の線形性。
    return [
        (left + right) % modulus
        for left, right in zip(left_shares, right_shares)
    ]


# ---------------------------------------------------------- PROVIDED helpers
def sub_shares(
    left_shares: ShareVector,
    right_shares: ShareVector,
    modulus: int,
) -> ShareVector:
    """Subtract two shared values component-wise. This is local."""
    _validate_modulus(modulus)
    _validate_same_share_count(left_shares, right_shares)
    return [
        (left - right) % modulus
        for left, right in zip(left_shares, right_shares)
    ]


def scale_shares(
    shares: ShareVector,
    scalar: int,
    modulus: int,
) -> ShareVector:
    """Multiply a shared value by a public scalar. This is local."""
    _validate_modulus(modulus)
    _validate_same_share_count(shares)
    return [(value * scalar) % modulus for value in shares]


# ================================================================ Part A3
def beaver_multiply(
    x_shares: ShareVector,
    y_shares: ShareVector,
    triple: BeaverTriple,
    modulus: int,
) -> ShareVector:
    """Return additive shares of x*y using one Beaver triple.

    If triple = ([a], [b], [c]) with c = a*b, open exactly

        d = x-a,  e = y-b

    and compute

        [xy] = [c] + d[b] + e[a] + de.

    Add the public term d*e to party 0 only.
    """
    _validate_modulus(modulus)
    a_shares, b_shares, c_shares = triple
    # x, y, a, b, c の 5 本すべてで party 数が揃っていることを確認する。
    _validate_same_share_count(x_shares, y_shares, a_shares, b_shares, c_shares)

    # x, y を直接開くと秘密が漏れる。a, b でマスクした差だけを開示する。
    # d = x - a, e = y - b は a, b が一様乱数なので x, y の情報を漏らさない。
    d = reconstruct(sub_shares(x_shares, a_shares, modulus), modulus)
    e = reconstruct(sub_shares(y_shares, b_shares, modulus), modulus)

    # 恒等式 xy = c + d*b + e*a + d*e （c = a*b を使う）:
    #   c + (x-a)b + (y-b)a + (x-a)(y-b)
    #     = ab + xb - ab + ya - ab + xy - xb - ya + ab = xy
    # d, e は公開値なので、各項は share 上でローカルに計算できる。
    product = add_shares(
        c_shares,
        add_shares(
            scale_shares(b_shares, d, modulus),
            scale_shares(a_shares, e, modulus),
            modulus,
        ),
        modulus,
    )

    # 定数項 d*e は share ではなく公開値。全 party に足すと party 数の倍だけ
    # 乗ってしまうので、party 0 のみに足して合計をちょうど d*e 増やす。
    product[0] = (product[0] + d * e) % modulus
    return product


# ========================================================== PROVIDED XOR MPC
def xor_share(bit: int, mask: int) -> tuple[int, int]:
    """Split a bit into two XOR shares: bit = mask XOR (bit XOR mask)."""
    _validate_bit(bit, "bit")
    _validate_bit(mask, "mask")
    return mask, bit ^ mask


def xor_reconstruct(shares: tuple[int, int]) -> int:
    """Open two XOR shares."""
    _validate_bit_shares(shares, "shares")
    return shares[0] ^ shares[1]


def xor_shares(
    left_shares: tuple[int, int],
    right_shares: tuple[int, int],
) -> tuple[int, int]:
    """XOR two XOR-shared bits locally."""
    _validate_bit_shares(left_shares, "left_shares")
    _validate_bit_shares(right_shares, "right_shares")
    return (
        left_shares[0] ^ right_shares[0],
        left_shares[1] ^ right_shares[1],
    )


# ========================================================== PROVIDED OT setup
def ot_sender_setup(sender_secret: int) -> int:
    """Return A = g^a mod p for sender secret a."""
    validate_sender_scalar(sender_secret, "sender_secret")
    return pow(OT_G, sender_secret, OT_P)


# ================================================================ Part B1
def ot_receiver_request(
    sender_public: int,
    choice: int,
    receiver_secret: int,
) -> int:
    """Build receiver request B.

    B = g^b for choice 0, and B = A*g^b for choice 1.
    The receiver secret b is sampled from 0..q-1, including zero.
    """
    validate_group_element(sender_public, "sender_public")
    validate_choice(choice)
    validate_receiver_scalar(receiver_secret, "receiver_secret")

    # b が 0..q-1 の一様乱数なので g^b は部分群上の一様分布。よって B も、
    # A を掛けたかどうか（= choice）に関係なく同じ分布になり、sender は
    # receiver がどちらを選んだか分からない。
    masked = pow(OT_G, receiver_secret, OT_P)
    if choice == 1:
        masked = (sender_public * masked) % OT_P
    return masked


def ot_sender_encrypt(
    sender_secret: int,
    request: int,
    message_0: bytes,
    message_1: bytes,
) -> tuple[bytes, bytes]:
    """Encrypt two equal-length messages for the 1-out-of-2 OT.

    Derive the branch-0 key from B^a and the branch-1 key from (B/A)^a.
    Use derive_pad(shared, branch, length), then xor_bytes(message, pad).
    """
    validate_sender_scalar(sender_secret, "sender_secret")
    validate_group_element(request, "request")
    if len(message_0) != len(message_1):
        raise ValueError("messages must have the same length")

    # 2 つの鍵を作る。receiver は choice に対応する方しか導出できない:
    #   choice 0 では B = g^b なので B^a = g^ab = A^b が求まるが、
    #   branch 1 の鍵 (B/A)^a = (g^(b-a))^a は CDH のため計算できない。
    #   choice 1 では逆に (B/A)^a = g^ab = A^b だけが求まる。
    shared_0 = pow(request, sender_secret, OT_P)
    inverse_public = pow(pow(OT_G, sender_secret, OT_P), -1, OT_P)
    shared_1 = pow((request * inverse_public) % OT_P, sender_secret, OT_P)

    length = len(message_0)
    return (
        xor_bytes(message_0, derive_pad(shared_0, 0, length)),
        xor_bytes(message_1, derive_pad(shared_1, 1, length)),
    )


def ot_receiver_decrypt(
    sender_public: int,
    choice: int,
    receiver_secret: int,
    ciphertexts: tuple[bytes, bytes],
) -> bytes:
    """Decrypt the selected OT ciphertext using A^b."""
    validate_group_element(sender_public, "sender_public")
    validate_choice(choice)
    validate_receiver_scalar(receiver_secret, "receiver_secret")
    if len(ciphertexts) != 2:
        raise ValueError("ciphertexts must contain exactly two entries")

    # どちらの choice でも、receiver が導出できる共有値は A^b = g^ab。
    # branch 番号を pad の導出に混ぜているので、選んだ側の pad だけが一致する。
    shared = pow(sender_public, receiver_secret, OT_P)
    ciphertext = ciphertexts[choice]
    return xor_bytes(ciphertext, derive_pad(shared, choice, len(ciphertext)))


# ---------------------------------------------------------- PROVIDED OT glue
def _ot_transfer_bit(
    message_0: int,
    message_1: int,
    choice: int,
    sender_secret: int,
    receiver_secret: int,
) -> int:
    """Run the student OT functions for a one-bit message."""
    _validate_bit(message_0, "message_0")
    _validate_bit(message_1, "message_1")
    validate_choice(choice)

    sender_public = ot_sender_setup(sender_secret)
    request = ot_receiver_request(sender_public, choice, receiver_secret)
    ciphertexts = ot_sender_encrypt(
        sender_secret,
        request,
        bytes([message_0]),
        bytes([message_1]),
    )
    plaintext = ot_receiver_decrypt(
        sender_public,
        choice,
        receiver_secret,
        ciphertexts,
    )
    if len(plaintext) != 1 or plaintext[0] not in (0, 1):
        raise ValueError("bit OT must return one byte equal to 0 or 1")
    return plaintext[0]


# ================================================================ Part B2
def gmw_and(
    x_shares: tuple[int, int],
    y_shares: tuple[int, int],
    masks: tuple[int, int],
    ot_secrets: tuple[tuple[int, int], tuple[int, int]],
) -> tuple[int, int]:
    """AND two XOR-shared bits using two 1-out-of-2 OTs.

    x_shares = (x0, x1), y_shares = (y0, y1)
    masks = (r01, r10)

    Session 01: P0 sends (r01, r01 XOR x0), P1 chooses y1.
    Session 10: P1 sends (r10, r10 XOR x1), P0 chooses y0.

    `ot_secrets` contains (sender_secret, receiver_secret) for session 01 and
    session 10, in that order.
    """
    _validate_bit_shares(x_shares, "x_shares")
    _validate_bit_shares(y_shares, "y_shares")
    _validate_bit_shares(masks, "masks")
    if len(ot_secrets) != 2:
        raise ValueError("ot_secrets must contain exactly two sessions")

    x0, x1 = x_shares
    y0, y1 = y_shares
    r01, r10 = masks

    # AND を XOR share 上で展開する:
    #   x & y = (x0^x1) & (y0^y1) = x0y0 ^ x0y1 ^ x1y0 ^ x1y1
    # 対角項 x0y0 と x1y1 は各 party がローカルに計算できる。
    # 交差項 x0y1 と x1y0 は相手の share が必要なので、OT で 1 回ずつ処理する。

    # セッション 01: P0 が sender、P1 が receiver（選択ビットは y1）。
    # P0 は (r01, r01^x0) を送る。P1 が受け取るのは r01 ^ (x0 & y1) で、
    # P0 が持つ r01 と合わせて x0y1 の XOR share になる。y1 は P0 に伝わらず、
    # P1 は選ばなかった方（= x0 そのもの）を知り得ない。
    sender_secret_01, receiver_secret_01 = ot_secrets[0]
    p1_cross = _ot_transfer_bit(
        r01,
        r01 ^ x0,
        y1,
        sender_secret_01,
        receiver_secret_01,
    )

    # セッション 10: 役割を入れ替える。P1 が (r10, r10^x1) を送り、
    # P0 が y0 を選択ビットとして r10 ^ (x1 & y0) を得る。
    sender_secret_10, receiver_secret_10 = ot_secrets[1]
    p0_cross = _ot_transfer_bit(
        r10,
        r10 ^ x1,
        y0,
        sender_secret_10,
        receiver_secret_10,
    )

    # 各 party は「ローカルな対角項」と「2 つの交差項の自分の持ち分」を XOR する。
    #   z0 = x0y0 ^ r01        ^ (r10 ^ x1y0)
    #   z1 = x1y1 ^ (r01^x0y1) ^ r10
    # XOR を取ると z0^z1 = x0y0 ^ x0y1 ^ x1y0 ^ x1y1 = x & y。
    z0 = (x0 & y0) ^ r01 ^ p0_cross
    z1 = (x1 & y1) ^ p1_cross ^ r10
    return z0, z1
