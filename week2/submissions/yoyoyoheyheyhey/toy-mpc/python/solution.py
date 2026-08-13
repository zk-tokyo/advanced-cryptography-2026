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

    # randomnessの各要素を、それぞれ1人のpartyが持つshareとして使う。
    # さらに、全shareの合計がsecretになるよう、最後の1人分を後で追加する。
    #
    # e.g.
    #   randomness=[5]     → [5, 計算したshare]     → 2-party
    #   randomness=[5, 11] → [5, 11, 計算したshare] → 3-party
    #
    # 空リストでは最後の1人しかおらず秘密分散にならないため拒否する。
    if not randomness:
        raise ValueError("at least two parties are required")

    # ここで扱うshareは有限体 F_p の要素なので、負数やp以上の整数も
    # 0..p-1の標準的な表現へ直しておく。
    shares = [value % modulus for value in randomness]

    # 全shareの和が secret (mod p) になるよう、最後のshareを逆算する。
    #
    #   secret = share_0 + ... + share_n  (mod p)
    #   share_n = secret - (share_0 + ... + share_{n-1})  (mod p)
    last_share = (secret - sum(shares)) % modulus
    return [*shares, last_share]


def reconstruct(shares: ShareVector, modulus: int) -> int:
    """Open additive shares and return the canonical field element."""
    _validate_modulus(modulus)
    _validate_same_share_count(shares)

    # 加法的秘密分散では、全partyのshareを足すと元の秘密を復元できる。
    # 「openする」とは、このようにshareを集めて秘密値を復元すること。
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

    # [x] + [y] は、同じpartyが持つshare同士を足すだけで計算できる。
    # reconstruct() を呼ばないので、どのpartyも x や y の全体を知らない。
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
    if len(triple) != 3:
        raise ValueError("a Beaver triple must contain [a], [b], and [c]")

    a_shares, b_shares, c_shares = triple
    party_count = _validate_same_share_count(
        x_shares,
        y_shares,
        a_shares,
        b_shares,
        c_shares,
    )

    # a, b は事前にランダムに作られ、c = a*b を満たす秘密値。
    # x, y そのものではなく、ランダム値との差だけを公開する。
    #
    #   [d] = [x] - [a]
    #   [e] = [y] - [b]
    d_shares = sub_shares(x_shares, a_shares, modulus)
    e_shares = sub_shares(y_shares, b_shares, modulus)

    # このプロトコルでopenするのは、マスクされた d と e の2値だけ。
    # a, b が未知のランダム値なので、単発の d, e から x, y は分からない。
    # ただし同じtripleを再利用すると差分が漏れるため、必ず一回限りで使う。
    d = reconstruct(d_shares, modulus)
    e = reconstruct(e_shares, modulus)

    # 次の恒等式をshare上で計算する。
    #
    #   xy = (a+d)(b+e)
    #      = ab + db + ea + de
    #      = c  + db + ea + de
    #
    # c_i, b_i, a_i は各partyが持つ秘密share。
    # d, e は公開済みなので、各partyがlocalに掛け算できる。
    product_shares = [
        (c_shares[i] + d * b_shares[i] + e * a_shares[i]) % modulus
        for i in range(party_count)
    ]

    # de は公開値なので、全partyへ d*e を足すと、復元時にparty数回足されてしまう。
    # 加法的shareとして合計に一度だけ現れるよう、party 0だけへ足す。
    product_shares[0] = (product_shares[0] + d * e) % modulus
    return product_shares


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

    # sender_public A = g^a に対し、receiverは秘密のchoiceをBの形へ埋め込む。
    #
    #   choice = 0: B = g^b
    #   choice = 1: B = A * g^b
    #
    # bを0も含む範囲からランダムに選ぶため、Bの分布だけを見てもsenderは
    # receiverがどちらを選んだか区別できない。
    blinded = pow(OT_G, receiver_secret, OT_P)
    if choice == 0:
        return blinded
    return (sender_public * blinded) % OT_P


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
        raise ValueError("OT messages must have the same length")

    sender_public = pow(OT_G, sender_secret, OT_P)

    # senderはreceiverのchoiceを知らないまま、2つの候補鍵を作る。
    #
    #   branch 0: B^a
    #   branch 1: (B/A)^a
    #
    # receiverがchoice=0なら branch 0だけがA^bと一致し、choice=1なら
    # branch 1だけがA^bと一致する。したがってreceiverは選んだ側だけを
    # 復号できる。
    shared_0 = pow(request, sender_secret, OT_P)

    # 有限群での「B / A」は B * A^{-1} mod p として計算する。
    sender_public_inverse = pow(sender_public, -1, OT_P)
    branch_1_base = (request * sender_public_inverse) % OT_P
    shared_1 = pow(branch_1_base, sender_secret, OT_P)

    pad_0 = derive_pad(shared_0, 0, len(message_0))
    pad_1 = derive_pad(shared_1, 1, len(message_1))
    return (
        xor_bytes(message_0, pad_0),
        xor_bytes(message_1, pad_1),
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
        raise ValueError("ciphertexts must contain exactly two values")
    if len(ciphertexts[0]) != len(ciphertexts[1]):
        raise ValueError("OT ciphertexts must have the same length")

    # receiverが計算できる共有値は A^b = g^(ab) の1つだけ。
    # sender側では、receiverが選んだbranchの共有値だけがこれと一致する。
    shared = pow(sender_public, receiver_secret, OT_P)
    selected_ciphertext = ciphertexts[choice]
    selected_pad = derive_pad(shared, choice, len(selected_ciphertext))
    return xor_bytes(selected_ciphertext, selected_pad)


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
    if len(ot_secrets) != 2 or any(len(session) != 2 for session in ot_secrets):
        raise ValueError("ot_secrets must contain two (sender, receiver) pairs")

    x_0, x_1 = x_shares
    y_0, y_1 = y_shares
    r_01, r_10 = masks
    (sender_01, receiver_01), (sender_10, receiver_10) = ot_secrets

    # XOR秘密分散では、元のbitは次のように表される。
    #
    #   x = x_0 XOR x_1
    #   y = y_0 XOR y_1
    #
    # GF(2)ではANDを掛け算として展開できる。
    #
    #   x AND y
    #     = (x_0 XOR x_1) AND (y_0 XOR y_1)
    #     = x_0*y_0 XOR x_0*y_1 XOR x_1*y_0 XOR x_1*y_1
    #
    # x_0*y_0はP0、x_1*y_1はP1がlocalに計算できるが、交差項
    # x_0*y_1 と x_1*y_0 は相手のshareが必要なのでOTを使う。

    # Session 01: P0がsender、P1がreceiver。
    # P1はchoice=y_1により、次の値を相手へchoiceを明かさず受け取る。
    #
    #   t_01 = r_01 XOR (x_0 AND y_1)
    t_01 = _ot_transfer_bit(
        r_01,
        r_01 ^ x_0,
        y_1,
        sender_01,
        receiver_01,
    )

    # Session 10: P1がsender、P0がreceiver。
    #
    #   t_10 = r_10 XOR (x_1 AND y_0)
    t_10 = _ot_transfer_bit(
        r_10,
        r_10 ^ x_1,
        y_0,
        sender_10,
        receiver_10,
    )

    # 出力も z = z_0 XOR z_1 というXOR shareにする。
    # 2つをXORするとr_01とr_10が打ち消され、4つのAND項だけが残る。
    z_0 = (x_0 & y_0) ^ r_01 ^ t_10
    z_1 = (x_1 & y_1) ^ t_01 ^ r_10
    return z_0, z_1
