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
    # modulusが有効な値か確認する
    _validate_modulus(modulus)

    # shareは最低2つ必要
    if len(randomness) < 1:
        raise ValueError("at least two parties are required")

    # 各値を0..modulus-1の範囲にそろえる
    shares = [value % modulus for value in randomness]

    # 全shareの和がsecretとmodulusを法として一致するように最後のshareを求める
    last_share = (secret - sum(shares)) % modulus
    shares.append(last_share)

    return shares


def reconstruct(shares: ShareVector, modulus: int) -> int:
    """Open additive shares and return the canonical field element."""
    # modulusとshare数が正しいか確認する
    _validate_modulus(modulus)
    _validate_same_share_count(shares)

    # shareをすべて足し、secretをmodulusで表した値を復元する
    return sum(shares) % modulus


# ================================================================ Part A2
def add_shares(
    left_shares: ShareVector,
    right_shares: ShareVector,
    modulus: int,
) -> ShareVector:
    """Add two shared values component-wise without opening them."""
    # modulusが正しくかつ2つのshareの要素数が一致するか確認する
    _validate_modulus(modulus)
    _validate_same_share_count(left_shares, right_shares)

    # 対応するshare同士を足し、modulusで割った余りにする
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
    # modulusと、すべてのshareのparty数が正しいか確認する
    _validate_modulus(modulus)

    a_shares, b_shares, c_shares = triple
    _validate_same_share_count(
        x_shares,
        y_shares,
        a_shares,
        b_shares,
        c_shares,
    )

    # d = x - a, e = y - bのshareを作る
    d_shares = [
        (x - a) % modulus
        for x, a in zip(x_shares, a_shares)
    ]

    e_shares = [
        (y - b) % modulus
        for y, b in zip(y_shares, b_shares)
    ]

    # xとy自体は公開せず、dとeだけを復元する
    d = reconstruct(d_shares, modulus)
    e = reconstruct(e_shares, modulus)

    # 各partyごとに[c] + d[b] + e[a]を計算する
    result = [
        (c + d * b + e * a) % modulus
        for a, b, c in zip(a_shares, b_shares, c_shares)
    ]

    # d*eを全partyに加えるとparty数分加算されるため、party0にだけ加える
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
    """Build receiver request B.

    B = g^b for choice 0, and B = A*g^b for choice 1.
    The receiver secret b is sampled from 0..q-1, including zero.
    """
    # 入力値が正しいか確認する
    validate_group_element(sender_public, "sender_public")
    validate_choice(choice)
    validate_receiver_scalar(receiver_secret, "receiver_secret")

    # choiceに応じてrequest Bを作る
    if choice == 0:
        # B = g^b for choice 0
        B = pow(OT_G, receiver_secret, OT_P)
    else:
        # B = A*g^b for choice 1
        B = (sender_public * pow(OT_G, receiver_secret, OT_P)) % OT_P

    validate_group_element(B, "request")

    return B


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
    # 入力値が正しいか確認する
    validate_sender_scalar(sender_secret, "sender_secret")
    validate_group_element(request, "request")

    if len(message_0) != len(message_1):
        raise ValueError("messages must have the same length")

    # A = g^a
    sender_public = pow(OT_G, sender_secret, OT_P)

    # branch-0用の共有値B^a
    shared_0 = pow(request, sender_secret, OT_P)

    # branch-1用にB/Aを求める
    sender_public_inv = pow(sender_public, -1, OT_P)
    request_over_a = (request * sender_public_inv) % OT_P
    validate_group_element(request_over_a, "B/A")

    # branch-1用の共有値(B/A)^a
    shared_1 = pow(request_over_a, sender_secret, OT_P)

    # それぞれの共有値からpadを作る
    pad_0 = derive_pad(shared_0, 0, len(message_0))
    pad_1 = derive_pad(shared_1, 1, len(message_1))

    # messageをpadとXORして暗号化する
    ciphertext_0 = xor_bytes(message_0, pad_0)
    ciphertext_1 = xor_bytes(message_1, pad_1)

    return ciphertext_0, ciphertext_1


def ot_receiver_decrypt(
    sender_public: int,
    choice: int,
    receiver_secret: int,
    ciphertexts: tuple[bytes, bytes],
) -> bytes:
    """Decrypt the selected OT ciphertext using A^b."""
    # 入力値が正しいか確認する
    validate_group_element(sender_public, "sender_public")
    validate_choice(choice)
    validate_receiver_scalar(receiver_secret, "receiver_secret")

    # Receiver側の共有値 A^b
    shared = pow(sender_public, receiver_secret, OT_P)

    # 選択したciphertextと同じ長さのpadを作る
    ciphertext = ciphertexts[choice]
    pad = derive_pad(shared, choice, len(ciphertext))

    # XORして選択したmessageを復号する
    return xor_bytes(ciphertext, pad)


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
    # 入力されたshareとmaskがbitとして正しいか確認する
    _validate_bit_shares(x_shares, "x_shares")
    _validate_bit_shares(y_shares, "y_shares")
    _validate_bit(masks[0], "masks[0]")
    _validate_bit(masks[1], "masks[1]")

    # OTの秘密値はsession 01とsession 10の2組必要
    if len(ot_secrets) != 2:
        raise ValueError("ot_secrets must contain two sessions")

    x0, x1 = x_shares
    y0, y1 = y_shares
    r01, r10 = masks

    # session 01:
    # P0が(r01, r01 XOR x0)を送り、P1がy1をchoiceとして選ぶ
    sender_secret_01, receiver_secret_01 = ot_secrets[0]
    received_01 = _ot_transfer_bit(
        r01,
        r01 ^ x0,
        y1,
        sender_secret_01,
        receiver_secret_01,
    )

    # session 10:
    # P1が(r10, r10 XOR x1)を送り、P0がy0をchoiceとして選ぶ
    sender_secret_10, receiver_secret_10 = ot_secrets[1]
    received_10 = _ot_transfer_bit(
        r10,
        r10 ^ x1,
        y0,
        sender_secret_10,
        receiver_secret_10,
    )

    # 各partyが自分だけで計算できる項とOTの結果を組み合わせる
    z0 = (x0 & y0) ^ r01 ^ received_10
    z1 = (x1 & y1) ^ r10 ^ received_01

    return z0, z1
