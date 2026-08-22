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

    randomness の各値が先頭側の share。最後の share は
    (secret - sum(randomness)) を体の元にしたもの。全 share を 0..modulus-1 に正規化。
    party 数は最低 2（＝ randomness は 1 個以上）。
    """
    _validate_modulus(modulus)
    if len(randomness) < 1:
        raise ValueError("at least two parties are required")
    last = (secret - sum(randomness)) % modulus
    return [r % modulus for r in randomness] + [last]


def reconstruct(shares: ShareVector, modulus: int) -> int:
    """加法的 share を開いて体の元を返す（＝総和 mod modulus）。"""
    _validate_modulus(modulus)
    if len(shares) < 2:
        raise ValueError("at least two parties are required")
    return sum(shares) % modulus


# ================================================================ Part A2
def add_shares(
    left_shares: ShareVector,
    right_shares: ShareVector,
    modulus: int,
) -> ShareVector:
    """share を開かずに、成分ごとに加算する（local な演算）。"""
    _validate_modulus(modulus)
    _validate_same_share_count(left_shares, right_shares)
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
    """Beaver triple 1 個で x*y の加法的 share を返す。

        d = x-a, e = y-b を開き、
        [xy] = [c] + d[b] + e[a] + d*e
    公開項 d*e は party 0 にだけ足す。
    """
    _validate_modulus(modulus)
    a_shares, b_shares, c_shares = triple
    _validate_same_share_count(x_shares, y_shares, a_shares, b_shares, c_shares)

    # マスク差を開く（この 2 つだけを公開）。d を先、e を後の順で開く。
    d = reconstruct(sub_shares(x_shares, a_shares, modulus), modulus)
    e = reconstruct(sub_shares(y_shares, b_shares, modulus), modulus)

    # [c] + d[b] + e[a]
    result = add_shares(
        add_shares(c_shares, scale_shares(b_shares, d, modulus), modulus),
        scale_shares(a_shares, e, modulus),
        modulus,
    )
    # 公開項 d*e は party 0 のみに加算
    result[0] = (result[0] + d * e) % modulus
    return result


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
    """受信者リクエスト B を作る。

    choice 0 なら B = g^b、choice 1 なら B = A*g^b。b は 0..q-1（0 を含む）。
    """
    validate_choice(choice)
    validate_receiver_scalar(receiver_secret, "receiver_secret")
    validate_group_element(sender_public, "sender_public")
    base = pow(OT_G, receiver_secret, OT_P)
    if choice == 1:
        return (sender_public * base) % OT_P
    return base


def ot_sender_encrypt(
    sender_secret: int,
    request: int,
    message_0: bytes,
    message_1: bytes,
) -> tuple[bytes, bytes]:
    """1-out-of-2 OT の 2 メッセージを暗号化する。

    branch 0 の鍵は B^a、branch 1 の鍵は (B/A)^a から導出する。
    """
    validate_sender_scalar(sender_secret, "sender_secret")
    validate_group_element(request, "request")
    if len(message_0) != len(message_1):
        raise ValueError("messages must have equal length")

    a_public = pow(OT_G, sender_secret, OT_P)
    a_inverse = pow(a_public, -1, OT_P)
    shared_0 = pow(request, sender_secret, OT_P)
    shared_1 = pow((request * a_inverse) % OT_P, sender_secret, OT_P)

    length = len(message_0)
    cipher_0 = xor_bytes(message_0, derive_pad(shared_0, 0, length))
    cipher_1 = xor_bytes(message_1, derive_pad(shared_1, 1, length))
    return cipher_0, cipher_1


def ot_receiver_decrypt(
    sender_public: int,
    choice: int,
    receiver_secret: int,
    ciphertexts: tuple[bytes, bytes],
) -> bytes:
    """選んだ側の暗号文を A^b の鍵で復号する。"""
    validate_choice(choice)
    validate_receiver_scalar(receiver_secret, "receiver_secret")
    validate_group_element(sender_public, "sender_public")
    shared = pow(sender_public, receiver_secret, OT_P)
    cipher = ciphertexts[choice]
    pad = derive_pad(shared, choice, len(cipher))
    return xor_bytes(cipher, pad)


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
    """2 回の 1-out-of-2 OT で、XOR 共有されたビットの AND をとる。

    x = x0^x1, y = y0^y1 のとき
        x AND y = x0y0 ^ x0y1 ^ x1y0 ^ x1y1
    自分だけで作れる x0y0（P0）と x1y1（P1）はローカル、
    交差項 x0y1 と x1y0 を OT で分散計算する。
    """
    _validate_bit_shares(x_shares, "x_shares")
    _validate_bit_shares(y_shares, "y_shares")
    x0, x1 = x_shares
    y0, y1 = y_shares

    if len(masks) != 2:
        raise ValueError("masks must contain exactly two bits")
    r01, r10 = masks
    _validate_bit(r01, "masks[0]")
    _validate_bit(r10, "masks[1]")

    if len(ot_secrets) != 2:
        raise ValueError("ot_secrets must contain two (sender, receiver) pairs")
    (sender_01, receiver_01), (sender_10, receiver_10) = ot_secrets

    # Session 01: P0 が送信者 (r01, r01^x0)、P1 が y1 を選ぶ。
    #   受信結果 t01 = r01 ^ (x0 AND y1)。P0 側の share は r01。
    t01 = _ot_transfer_bit(r01, r01 ^ x0, y1, sender_01, receiver_01)

    # Session 10: P1 が送信者 (r10, r10^x1)、P0 が y0 を選ぶ。
    #   受信結果 t10 = r10 ^ (x1 AND y0)。P1 側の share は r10。
    t10 = _ot_transfer_bit(r10, r10 ^ x1, y0, sender_10, receiver_10)

    z0 = (x0 & y0) ^ r01 ^ t10
    z1 = (x1 & y1) ^ t01 ^ r10
    return z0, z1