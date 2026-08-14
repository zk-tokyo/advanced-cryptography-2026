"""Week 2課題「toy-mpc」の解答ファイルです。"""

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
    """Split secret into additive shares."""

    _validate_modulus(modulus)

    if len(randomness) < 1:
        raise ValueError("at least two parties are required")

    shares = [value % modulus for value in randomness]

    last_share = (secret - sum(shares)) % modulus
    shares.append(last_share)

    return shares


def reconstruct(shares: ShareVector, modulus: int) -> int:
    """Open additive shares and return the canonical field element."""

    _validate_modulus(modulus)
    _validate_same_share_count(shares)

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

    return [
        (value * scalar) % modulus
        for value in shares
    ]


# ================================================================ Part A3
def beaver_multiply(
    x_shares: ShareVector,
    y_shares: ShareVector,
    triple: BeaverTriple,
    modulus: int,
) -> ShareVector:
    """Return additive shares of x*y using one Beaver triple."""

    _validate_modulus(modulus)

    party_count = _validate_same_share_count(
        x_shares,
        y_shares,
        triple[0],
        triple[1],
        triple[2],
    )

    a_shares, b_shares, c_shares = triple

    # Open exactly:
    # d = x - a
    # e = y - b
    d_shares = sub_shares(x_shares, a_shares, modulus)
    e_shares = sub_shares(y_shares, b_shares, modulus)

    d = reconstruct(d_shares, modulus)
    e = reconstruct(e_shares, modulus)

    # [xy] = [c] + d[b] + e[a] + de
    result = []

    for i in range(party_count):
        value = (
            c_shares[i]
            + d * b_shares[i]
            + e * a_shares[i]
        ) % modulus

        result.append(value)

    # Public de is added only to party 0.
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
    """Build receiver request B."""

    validate_group_element(sender_public, "sender_public")
    validate_choice(choice)
    validate_receiver_scalar(receiver_secret, "receiver_secret")

    gb = pow(OT_G, receiver_secret, OT_P)

    if choice == 0:
        return gb

    return (sender_public * gb) % OT_P


def ot_sender_encrypt(
    sender_secret: int,
    request: int,
    message_0: bytes,
    message_1: bytes,
) -> tuple[bytes, bytes]:
    """Encrypt two equal-length messages for 1-out-of-2 OT."""

    validate_sender_scalar(sender_secret, "sender_secret")
    validate_group_element(request, "request")

    if len(message_0) != len(message_1):
        raise ValueError("messages must have the same length")

    sender_public = pow(OT_G, sender_secret, OT_P)

    # Branch 0:
    # request = g^b
    # shared = B^a = g^(ab)
    shared_0 = pow(request, sender_secret, OT_P)

    # Branch 1:
    # request / A = g^b
    # shared = (B/A)^a = g^(ab)
    inverse_a = pow(sender_public, -1, OT_P)
    request_without_a = (request * inverse_a) % OT_P
    shared_1 = pow(request_without_a, sender_secret, OT_P)

    pad_0 = derive_pad(shared_0, 0, len(message_0))
    pad_1 = derive_pad(shared_1, 1, len(message_1))

    ciphertext_0 = xor_bytes(message_0, pad_0)
    ciphertext_1 = xor_bytes(message_1, pad_1)

    return ciphertext_0, ciphertext_1


def ot_receiver_decrypt(
    sender_public: int,
    choice: int,
    receiver_secret: int,
    ciphertexts: tuple[bytes, bytes],
) -> bytes:
    """Decrypt the selected OT ciphertext."""

    validate_group_element(sender_public, "sender_public")
    validate_choice(choice)
    validate_receiver_scalar(receiver_secret, "receiver_secret")

    if len(ciphertexts) != 2:
        raise ValueError("ciphertexts must contain two messages")

    # Receiver knows:
    # A^b = g^(ab)
    shared = pow(sender_public, receiver_secret, OT_P)

    ciphertext = ciphertexts[choice]

    pad = derive_pad(shared, choice, len(ciphertext))

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

    request = ot_receiver_request(
        sender_public,
        choice,
        receiver_secret,
    )

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
        raise ValueError(
            "bit OT must return one byte equal to 0 or 1"
        )

    return plaintext[0]


# ================================================================ Part B2
def gmw_and(
    x_shares: tuple[int, int],
    y_shares: tuple[int, int],
    masks: tuple[int, int],
    ot_secrets: tuple[tuple[int, int], tuple[int, int]],
) -> tuple[int, int]:
    """AND two XOR-shared bits using two 1-out-of-2 OTs."""

    _validate_bit_shares(x_shares, "x_shares")
    _validate_bit_shares(y_shares, "y_shares")

    if len(masks) != 2:
        raise ValueError("masks must contain exactly two values")

    _validate_bit(masks[0], "masks[0]")
    _validate_bit(masks[1], "masks[1]")

    if len(ot_secrets) != 2:
        raise ValueError("ot_secrets must contain two sessions")

    # Session 01:
    #
    # P0 sends:
    #   (r01, r01 XOR x0)
    #
    # P1 chooses y1.
    r01 = masks[0]

    transfer_01 = _ot_transfer_bit(
        r01,
        r01 ^ x_shares[0],
        y_shares[1],
        ot_secrets[0][0],
        ot_secrets[0][1],
    )

    # Session 10:
    #
    # P1 sends:
    #   (r10, r10 XOR x1)
    #
    # P0 chooses y0.
    r10 = masks[1]

    transfer_10 = _ot_transfer_bit(
        r10,
        r10 ^ x_shares[1],
        y_shares[0],
        ot_secrets[1][0],
        ot_secrets[1][1],
    )

    # The two OT results give:
    #
    # transfer_01 = r01 XOR (x0 & y1)
    # transfer_10 = r10 XOR (x1 & y0)
    #
    # We need shares whose XOR equals:
    #
    # (x0 XOR x1) & (y0 XOR y1)
    #
    # = (x0&y0) XOR (x0&y1) XOR (x1&y0) XOR (x1&y1)
    #
    # The local terms x0&y0 and x1&y1 can be computed directly.

    local_0 = x_shares[0] & y_shares[0]
    local_1 = x_shares[1] & y_shares[1]

    # P0's output share
    output_0 = local_0 ^ transfer_01 ^ r01

    # P1's output share
    output_1 = local_1 ^ transfer_10 ^ r10

    return output_0, output_1
    