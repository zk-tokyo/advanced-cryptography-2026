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
#秘密値secretを有限体上の加法的シェアへ分割
def share(secret: int, randomness: list[int], modulus: int) -> ShareVector:
    """Split `secret` into len(randomness) + 1 additive shares.

    The values in `randomness` are the first shares. Return canonical field
    elements in 0..modulus-1. At least two parties are required.
    """
    _validate_modulus(modulus)
    if len(randomness) < 1:
        #modulusが1以下の場合有限体上の計算として扱えないためエラー
        raise ValueError("at least two parties are required")
    #randomnessをmodulusで割った余りを計算し、最初のシェアとして使用
    first_shares = [value % modulus for value in randomness]
    #secretからすべてのシェアを足した数をmodulusで割った余りを引いて、最後のシェアとして追加
    return first_shares + [(secret - sum(first_shares)) % modulus]

#加法的シェアを足し合わせて、元の秘密値を復元する
def reconstruct(shares: ShareVector, modulus: int) -> int:
    """Open additive shares and return the canonical field element."""
    _validate_modulus(modulus)
    _validate_same_share_count(shares)
    return sum(shares) % modulus


# ================================================================ Part A2
#2つの秘密値のシェアを、秘密値に復元せずに加算する
def add_shares(
    left_shares: ShareVector,
    right_shares: ShareVector,
    modulus: int,
) -> ShareVector:
    """Add two shared values component-wise without opening them."""
    #modulusが2以上か確認
    _validate_modulus(modulus)
    #2つのシェアの数が同じか確認
    _validate_same_share_count(left_shares, right_shares)
    #対応するシェアを加算
    return [(left + right) % modulus for left, right in zip(left_shares, right_shares)]



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
#秘密値x,y を復元せずに、Beaver tripleで積 x × y のシェアを計算する
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
    #modulusが2以上か確認
    _validate_modulus(modulus)
    if len(triple) != 3:
        raise ValueError("triple must contain shares of a, b, and c")
    a_shares, b_shares, c_shares = triple
    party_count = _validate_same_share_count(
        x_shares, y_shares, a_shares, b_shares, c_shares
    )
    d = reconstruct(sub_shares(x_shares, a_shares, modulus), modulus)
    e = reconstruct(sub_shares(y_shares, b_shares, modulus), modulus)
    result = [
        (c_shares[i] + d * b_shares[i] + e * a_shares[i]) % modulus
        for i in range(party_count)
    ]
    result[0] = (result[0] + d * e) % modulus
    #積のシェアを返す
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
#1-out-of-2 OTで受信者が選択したいメッセージを表すリクエストBを生成する
def ot_receiver_request(
    sender_public: int,
    choice: int,
    receiver_secret: int,
) -> int:
    """Build receiver request B.

    B = g^b for choice 0, and B = A*g^b for choice 1.
    The receiver secret b is sampled from 0..q-1, including zero.
    """
    #sender_publicがOTで使用する有限群の正しい要素か検証する
    validate_group_element(sender_public, "sender_public")
    #choice が0 or 1であることを確認する
    validate_choice(choice)
    #receiver_secretがOTで使用する有限群の正しいスカラーか検証する
    validate_receiver_scalar(receiver_secret, "receiver_secret")
    #リクエストBを計算する。choiceが0の場合はB = g^b mod p、choiceが1の場合はB = A * g^b mod p
    request = pow(OT_G, receiver_secret, OT_P)
    if choice == 1:
        request = (sender_public * request) % OT_P
    return request

#1-out-of-2 OTにおいて、送信者が持つ2つのメッセージを別々の鍵で暗号化する
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
    #sender_secretがOTで使用する有限群の正しいスカラーか検証する
    validate_sender_scalar(sender_secret, "sender_secret")
    #requestがOTで使用する有限群の正しい要素か検証する
    validate_group_element(request, "request")
    #message_0とmessage_1がbytes型であることを確認する
    if not isinstance(message_0, bytes) or not isinstance(message_1, bytes):
        raise ValueError("OT messages must be bytes")
    #message_0とmessage_1が同じ長さであることを確認する
    if len(message_0) != len(message_1):
        raise ValueError("OT messages must have equal length")

    sender_public = pow(OT_G, sender_secret, OT_P)
    shared_0 = pow(request, sender_secret, OT_P)
    request_over_public = (request * pow(sender_public, -1, OT_P)) % OT_P
    shared_1 = pow(request_over_public, sender_secret, OT_P)

    #derive_padを使用して、shared_0とshared_1からそれぞれのパッドを生成する
    pad_0 = derive_pad(shared_0, 0, len(message_0))
    pad_1 = derive_pad(shared_1, 1, len(message_1))
    #xor_bytesを使用して、message_0とpad_0、message_1とpad_1をそれぞれXORして暗号化する
    return xor_bytes(message_0, pad_0), xor_bytes(message_1, pad_1)

#1-out-of-2 OTで、受信者が選択した暗号文だけを復号する
def ot_receiver_decrypt(
    sender_public: int,
    choice: int,
    receiver_secret: int,
    ciphertexts: tuple[bytes, bytes],
) -> bytes:
    """Decrypt the selected OT ciphertext using A^b."""
    #sender_publicがOTで使用する有限群の正しい要素か検証する
    validate_group_element(sender_public, "sender_public")
    #choiceが有効な値であることを確認する
    validate_choice(choice)
    #receiver_secretがOTで使用する有限群の正しいスカラーか検証する
    validate_receiver_scalar(receiver_secret, "receiver_secret")
    #ciphertextsが2つの値を含むことを確認する
    if len(ciphertexts) != 2:
        raise ValueError("ciphertexts must contain exactly two values")
    #ciphertextsの各要素がbytes型であることを確認する
    if not all(isinstance(ciphertext, bytes) for ciphertext in ciphertexts):
        raise ValueError("OT ciphertexts must be bytes")
    ciphertext = ciphertexts[choice]
    shared = pow(sender_public, receiver_secret, OT_P)
    #sharedとchoiceからパッドを生成する
    pad = derive_pad(shared, choice, len(ciphertext))
    #ciphertextとpadをXORして復号する
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
#XOR秘密分散された2つのビットx,y について、秘密を公開せずにANDを計算する
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
    #ot_secrets must contain two secret pairs, each with two elements
    if len(ot_secrets) != 2 or any(len(pair) != 2 for pair in ot_secrets):
        raise ValueError("ot_secrets must contain two secret pairs")
    x0, x1 = x_shares
    y0, y1 = y_shares
    r01, r10 = masks
    sender_01, receiver_01 = ot_secrets[0]
    sender_10, receiver_10 = ot_secrets[1]
    #OTを使用してP0がr01とr01 XOR x0を送信し、P1がy1を選択するセッション01を実行
    transfer_01 = _ot_transfer_bit(r01, r01 ^ x0, y1, sender_01, receiver_01)
    #OTを使用してP1がr10とr10 XOR x1を送信し、P0がy0を選択するセッション10を実行
    transfer_10 = _ot_transfer_bit(r10, r10 ^ x1, y0, sender_10, receiver_10)
    #ANDの結果を計算する
    z0 = (x0 & y0) ^ r01 ^ transfer_10
    z1 = (x1 & y1) ^ r10 ^ transfer_01
    return z0, z1
