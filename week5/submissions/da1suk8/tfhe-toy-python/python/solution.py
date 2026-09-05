from __future__ import annotations

from dataclasses import dataclass
import random

# データ型の宣言


@dataclass(frozen=True)
class ToyTFHEParams:
    """TFHE HomNAND を追うための小さな整数パラメータ。

    本物の TFHE はトーラス上で動くが、この実装ではすべてを非負整数で表す。
    """

    # k: LWE 秘密鍵 s=(s_0,...,s_{k-1}) の長さ
    k: int = 4
    # p: LWE/RLWE の平文空間 Z_p の法
    p: int = 8
    # n: 多項式環 Z_q[X]/(X^n+1) の次数
    n: int = 16
    # q: LWE/RLWE 暗号文の係数を計算する法
    q: int = 32
    # delta: 平文を暗号文空間へ配置するスケーリングファクター q/p
    delta: int = 4
    # noise_bound: この toy 実装で加えるノイズ e の上限
    noise_bound: int = 1
    # evaluation_key_noise_bound: BSK/KSK の暗号化で加えるノイズの上限
    evaluation_key_noise_bound: int = 0
    # B: Gadget Decomposition の基数
    B: int = 2
    # l: Gadget Decomposition の桁数
    l: int = 5
    # hom_nand_constant: Z_p 上の HomNAND の線形前処理で使う定数 1
    hom_nand_constant: int = 1
    # nand_test_polynomial: Z_p 上の HomNAND 用テスト多項式 v(X) の係数
    nand_test_polynomial: tuple[int, ...] = (
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
    )


@dataclass(frozen=True)
class LWECiphertext:
    """LWE 暗号文 c = (a, b)。"""

    a: list[int]
    b: int


@dataclass(frozen=True)
class RLWECiphertext:
    """RLWE 暗号文 (a(X), b(X))。"""

    a: list[int]
    b: list[int]


@dataclass(frozen=True)
class RGSWCiphertext:
    """1 bit を暗号化する、ナイーブな RGSW 暗号文。

    rows_for_a[j] は RGSW_s(m)=Z+mG^T のうち、RLWE 暗号文の
    a(X) 側に対応する行である。
    rows_for_b[j] は b(X) 側に対応する行である。
    """

    rows_for_a: list[RLWECiphertext]
    rows_for_b: list[RLWECiphertext]


@dataclass(frozen=True)
class BootstrappingKey:
    """入力 LWE 秘密鍵の各 bit を RGSW で暗号化した鍵。"""

    encrypted_lwe_key_bits: list[RGSWCiphertext]


@dataclass(frozen=True)
class KeySwitchingKey:
    """Sample Extraction 後の LWE 鍵を、元の LWE 鍵へ戻すための鍵。"""

    encrypted_extracted_key: list[list[LWECiphertext]]


@dataclass(frozen=True)
class EvaluationKey:
    """HomNAND に必要な評価鍵。"""

    bootstrapping_key: BootstrappingKey
    key_switching_key: KeySwitchingKey


# データの処理

# 補助関数セット


def normalize(value: int, q: int) -> int:
    """値を 0 以上 q 未満の剰余に直す。"""
    return value % q


def scale_plaintext(message: int, params: ToyTFHEParams) -> int:
    """Z_p の平文 m を Z_q の Delta*m に変換する。"""
    plaintext = normalize(message, params.p)
    return normalize(plaintext * params.delta, params.q)


def scale_plaintext_poly(
    message: list[int],
    params: ToyTFHEParams,
) -> list[int]:
    """Z_p の平文多項式の各係数に Delta を掛けて Z_q へ変換する。"""
    scaled_message: list[int] = []
    for coefficient in message:
        scaled_coefficient = scale_plaintext(coefficient, params)
        scaled_message.append(scaled_coefficient)
    return scaled_message


def rescale_q_to_2n(value: int, params: ToyTFHEParams) -> int:
    """Z_q の値を最も近い Z_{2N} の値へリスケーリングする。"""
    target_modulus = 2 * params.n
    normalized_value = normalize(value, params.q)
    numerator = normalized_value * target_modulus
    rounded = (numerator + params.q // 2) // params.q
    return normalize(rounded, target_modulus)


def rescale_lwe_ciphertext(
    ciphertext: LWECiphertext,
    params: ToyTFHEParams,
) -> LWECiphertext:
    """LWE 暗号文の a と b を Z_q から Z_{2N} へ移す。"""
    rescaled_a: list[int] = []
    for value in ciphertext.a:
        rescaled_value = rescale_q_to_2n(value, params)
        rescaled_a.append(rescaled_value)
    return LWECiphertext(
        a=rescaled_a,
        b=rescale_q_to_2n(ciphertext.b, params),
    )


def bit_plaintext_candidates(params: ToyTFHEParams) -> list[int]:
    """bit の復号で使う平文候補を返す。"""
    return [params.p - 1, 1]


def zero_poly(params: ToyTFHEParams) -> list[int]:
    """零多項式を返す。"""
    poly: list[int] = []
    for _ in range(params.n):
        poly.append(0)
    return poly


def constant_poly(value: int, params: ToyTFHEParams) -> list[int]:
    """定数多項式 value を返す。"""
    poly = zero_poly(params)
    poly[0] = normalize(value, params.q)
    return poly


def monomial_poly(exponent: int, params: ToyTFHEParams) -> list[int]:
    """X^exponent を Z_q[X] / (X^n + 1) の多項式として返す。"""
    poly = zero_poly(params)
    reduced = exponent % (2 * params.n)
    if reduced < params.n:
        poly[reduced] = 1
    else:
        poly[reduced - params.n] = params.q - 1
    return poly


def dot_mod(left: list[int], right: list[int], q: int) -> int:
    """2 つのベクトルの内積を q で割った剰余として返す。"""
    total = 0
    for index in range(len(left)):
        left_value = left[index]
        right_value = right[index]
        total += left_value * right_value
    return normalize(total, q)


def poly_add(left: list[int], right: list[int], params: ToyTFHEParams) -> list[int]:
    """多項式の和を返す。"""
    result: list[int] = []
    for index in range(len(left)):
        coefficient = normalize(left[index] + right[index], params.q)
        result.append(coefficient)
    return result


def poly_sub(left: list[int], right: list[int], params: ToyTFHEParams) -> list[int]:
    """多項式の差を返す。"""
    result: list[int] = []
    for index in range(len(left)):
        coefficient = normalize(left[index] - right[index], params.q)
        result.append(coefficient)
    return result


def poly_scalar_mul(poly: list[int], scalar: int, params: ToyTFHEParams) -> list[int]:
    """多項式にスカラーを掛ける。"""
    result: list[int] = []
    for coefficient in poly:
        product = normalize(scalar * coefficient, params.q)
        result.append(product)
    return result


def poly_mul(left: list[int], right: list[int], params: ToyTFHEParams) -> list[int]:
    """mod (X^n + 1) で多項式を掛ける。

    多項式の乗算には FFT/NTT を使った高速化手法があるが、
    この課題では処理を追いやすくするためにナイーブな二重ループで計算する。
    """
    degree = params.n
    result = zero_poly(params)
    for left_index in range(len(left)):
        left_value = left[left_index]
        for right_index in range(len(right)):
            right_value = right[right_index]
            power = left_index + right_index
            term = left_value * right_value
            if power < degree:
                result[power] += term
            else:
                result[power - degree] -= term
    normalized_result: list[int] = []
    for coefficient in result:
        normalized_result.append(normalize(coefficient, params.q))
    return normalized_result


# FHE のための関数


def encode_bit(bit: int, params: ToyTFHEParams) -> int:
    """真理値の bit を Z_p の平文値に変換する。0 -> p-1, 1 -> 1。"""
    if bit not in (0, 1):
        raise ValueError("bit は 0 または 1 である必要があります")
    if bit == 0:
        return params.p - 1
    return 1


def decode_bit(message: int, params: ToyTFHEParams) -> int:
    """Z_p の平文を bit に戻す。p-1 は bit 0、1 は bit 1 とする。"""
    plaintext = normalize(message, params.p)
    if plaintext == params.p - 1:
        return 0
    if plaintext == 1:
        return 1
    raise ValueError("message は有効な bit エンコードではありません")


def generate_lwe_secret_key(params: ToyTFHEParams, rng: random.Random) -> list[int]:
    """LWE 秘密鍵を生成する。"""
    secret_key: list[int] = []
    for _ in range(params.k):
        secret_key.append(rng.randrange(2))
    return secret_key


def generate_rlwe_secret_key(params: ToyTFHEParams, rng: random.Random) -> list[int]:
    """RLWE 秘密鍵 s(X) を生成する。"""
    secret_key: list[int] = []
    for _ in range(params.n):
        secret_key.append(rng.randrange(2))
    return secret_key


def encrypt_lwe(
    scaled_message: int,
    secret_key: list[int],
    params: ToyTFHEParams,
    rng: random.Random,
) -> LWECiphertext:
    """delta*m を LWE 暗号文として暗号化する。"""
    # TODO:
    # LWE暗号の暗号化を実装する
    a = []
    for _ in range(params.k):
        a.append(rng.randrange(params.q))
    e = rng.randrange(params.noise_bound + 1)
    b = normalize((dot_mod(a, secret_key, params.q) + scaled_message + e), params.q)

    return LWECiphertext(a, b)


def decrypt_lwe(
    ciphertext: LWECiphertext,
    secret_key: list[int],
    params: ToyTFHEParams,
) -> int:
    """LWE 暗号文を復号する。"""
    # TODO:
    # LWE暗号の復号を実装する
    scaled_message_with_noise = normalize(
        ciphertext.b - dot_mod(ciphertext.a, secret_key, params.q), params.q
    )
    message = ((scaled_message_with_noise) // params.delta) % params.p

    return message


def lwe_add(
    left: LWECiphertext,
    right: LWECiphertext,
    params: ToyTFHEParams,
) -> LWECiphertext:
    """LWE 暗号文同士を足す。"""
    # TODO:
    # LWE 暗号文同士の加算を実装する
    new_a: list[int] = []
    for index in range(len(left.a)):
        value = normalize(left.a[index] + right.a[index], params.q)
        new_a.append(value)
    new_b = normalize(left.b + right.b, params.q)
    return LWECiphertext(a=new_a, b=new_b)


def lwe_sub(
    left: LWECiphertext,
    right: LWECiphertext,
    params: ToyTFHEParams,
) -> LWECiphertext:
    """LWE 暗号文同士を引く。"""
    new_a: list[int] = []
    for index in range(len(left.a)):
        value = normalize(left.a[index] - right.a[index], params.q)
        new_a.append(value)
    new_b = normalize(left.b - right.b, params.q)
    return LWECiphertext(a=new_a, b=new_b)


def lwe_scalar_mul(
    ciphertext: LWECiphertext,
    scalar: int,
    params: ToyTFHEParams,
) -> LWECiphertext:
    """LWE 暗号文にスカラーを掛ける。"""
    # TODO:
    # LWE 暗号文のスカラー倍を実装する
    new_a: list[int] = []
    for index in range(len(ciphertext.a)):
        value = normalize(ciphertext.a[index] * scalar, params.q)
        new_a.append(value)
    new_b = normalize(ciphertext.b * scalar, params.q)
    return LWECiphertext(a=new_a, b=new_b)


def encrypt_rlwe(
    scaled_message: list[int],
    secret_key: list[int],
    params: ToyTFHEParams,
    rng: random.Random,
) -> RLWECiphertext:
    """delta*m を RLWE 暗号文として暗号化する。"""
    a_poly: list[int] = []
    error_poly: list[int] = []
    for _ in range(params.n):
        a_poly.append(rng.randrange(params.q))
        error_poly.append(rng.randrange(params.noise_bound + 1))
    b_poly = poly_add(poly_mul(a_poly, secret_key, params), scaled_message, params)
    b_poly = poly_add(b_poly, error_poly, params)
    return RLWECiphertext(a=a_poly, b=b_poly)


def decrypt_rlwe(
    ciphertext: RLWECiphertext,
    secret_key: list[int],
    params: ToyTFHEParams,
) -> list[int]:
    """RLWE 暗号文を復号する。"""
    scaled_message_with_noise = poly_sub(
        ciphertext.b,
        poly_mul(ciphertext.a, secret_key, params),
        params,
    )

    plaintext: list[int] = []
    for scaled_coefficient in scaled_message_with_noise:
        rounded_plaintext = (scaled_coefficient + params.delta // 2) // params.delta
        plaintext.append(normalize(rounded_plaintext, params.p))
    return plaintext


def rlwe_add(
    left: RLWECiphertext,
    right: RLWECiphertext,
    params: ToyTFHEParams,
) -> RLWECiphertext:
    """RLWE 暗号文同士を足す。"""
    return RLWECiphertext(
        a=poly_add(left.a, right.a, params),
        b=poly_add(left.b, right.b, params),
    )


def rlwe_sub(
    left: RLWECiphertext,
    right: RLWECiphertext,
    params: ToyTFHEParams,
) -> RLWECiphertext:
    """RLWE 暗号文同士を引く。"""
    return RLWECiphertext(
        a=poly_sub(left.a, right.a, params),
        b=poly_sub(left.b, right.b, params),
    )


def rlwe_scalar_mul(
    ciphertext: RLWECiphertext,
    scalar: int,
    params: ToyTFHEParams,
) -> RLWECiphertext:
    """RLWE 暗号文にスカラーを掛ける。"""
    return RLWECiphertext(
        a=poly_scalar_mul(ciphertext.a, scalar, params),
        b=poly_scalar_mul(ciphertext.b, scalar, params),
    )


def rlwe_plain_mul(
    ciphertext: RLWECiphertext,
    plain_poly: list[int],
    params: ToyTFHEParams,
) -> RLWECiphertext:
    """RLWE 暗号文に平文多項式を掛ける。"""
    return RLWECiphertext(
        a=poly_mul(ciphertext.a, plain_poly, params),
        b=poly_mul(ciphertext.b, plain_poly, params),
    )


def rlwe_monomial_mul(
    ciphertext: RLWECiphertext,
    exponent: int,
    params: ToyTFHEParams,
) -> RLWECiphertext:
    """RLWE 暗号文に X^exponent を掛ける。"""
    monomial = monomial_poly(exponent, params)
    return RLWECiphertext(
        a=poly_mul(ciphertext.a, monomial, params),
        b=poly_mul(ciphertext.b, monomial, params),
    )


def trivial_lwe(message: int, params: ToyTFHEParams) -> LWECiphertext:
    """Z_q に配置済みの値からノイズなしの LWE 暗号文を作る。"""
    a_vector: list[int] = []
    for _ in range(params.k):
        a_vector.append(0)
    return LWECiphertext(
        a=a_vector,
        b=normalize(message, params.q),
    )


def trivial_lwe_plaintext(message: int, params: ToyTFHEParams) -> LWECiphertext:
    """Z_p の平文からノイズなしの LWE 暗号文を作る。"""
    return trivial_lwe(scale_plaintext(message, params), params)


def trivial_rlwe(message: list[int], params: ToyTFHEParams) -> RLWECiphertext:
    """Z_q に配置済みの多項式からノイズなしの RLWE 暗号文を作る。"""
    return RLWECiphertext(a=zero_poly(params), b=list(message))


def trivial_rlwe_plaintext(
    message: list[int],
    params: ToyTFHEParams,
) -> RLWECiphertext:
    """Z_p の平文多項式からノイズなしの RLWE 暗号文を作る。"""
    return trivial_rlwe(scale_plaintext_poly(message, params), params)


def gadget_weights(params: ToyTFHEParams) -> list[int]:
    """Gadget decomposition で使う q/B, q/B^2, ..., q/B^l のリストを返す。

    この課題では q = B^l になるようにパラメータが選ばれている。
    """
    if params.B**params.l != params.q:
        raise ValueError("B ** l は q と一致する必要があります")

    weights: list[int] = []
    for j in range(params.l):
        weight = params.q // (params.B ** (j + 1))
        weights.append(weight)
    return weights


def gadget_decompose(value: int, params: ToyTFHEParams) -> list[int]:
    """整数 value を g^{-1}(value) として分解する。

    例として q=32, B=2, l=5 なら、
    29 = 1*(32/2) + 1*(32/4) + 1*(32/8) + 0*(32/16) + 1*(32/32)
    なので g^{-1}(29) = [1, 1, 1, 0, 1] になる。
    """
    # TODO: value を q/B, q/B^2, ..., q/B^l の各桁に分解する。
    # 各桁は 0 以上 B 未満にし、上位の桁から順番に返す。
    digits = []
    for weight in gadget_weights(params):
        digits.append(value // weight)
        value = value % weight
        weight //= params.B

    return digits


def gadget_decompose_poly(poly: list[int], params: ToyTFHEParams) -> list[list[int]]:
    """多項式の各係数を gadget decomposition する。

    戻り値の result[j][coefficient_index] が、j 番目の digit 多項式の
    係数になる。j は Gadget Decomposition の添字である。
    """
    decomposed: list[list[int]] = []
    for _ in range(params.l):
        decomposed.append(zero_poly(params))

    for coefficient_index in range(len(poly)):
        coefficient = poly[coefficient_index]
        digits = gadget_decompose(coefficient, params)
        for j in range(len(digits)):
            digit = digits[j]
            decomposed[j][coefficient_index] = digit
    return decomposed


def encrypt_rlwe_q_message_with_noise_bound(
    scaled_message: list[int],
    secret_key: list[int],
    params: ToyTFHEParams,
    rng: random.Random,
    noise_bound: int,
) -> RLWECiphertext:
    """今回のToy実装でRGSWの補助関数として使用するRLWE暗号化関数"""
    a_poly: list[int] = []
    error_poly: list[int] = []
    for _ in range(params.n):
        a_poly.append(rng.randrange(params.q))
        error_poly.append(rng.randrange(noise_bound + 1))
    b_poly = poly_add(poly_mul(a_poly, secret_key, params), scaled_message, params)
    b_poly = poly_add(b_poly, error_poly, params)
    return RLWECiphertext(a=a_poly, b=b_poly)


def rgsw_encrypt_bit(
    bit: int,
    rlwe_secret_key: list[int],
    params: ToyTFHEParams,
    rng: random.Random,
) -> RGSWCiphertext:
    """bit を RGSW 暗号文として暗号化する。

    RLWE の復号式は b(X)-a(X)s(X) なので、
    a(X) 側の gadget 行には a 成分へ m*q/B^{j+1} を足す。
    b(X) 側の gadget 行には b 成分へ m*q/B^{j+1} を足す。
    """
    if bit not in (0, 1):
        raise ValueError("bit は 0 または 1 である必要があります")

    rows_for_a: list[RLWECiphertext] = []
    rows_for_b: list[RLWECiphertext] = []
    zero_message = zero_poly(params)
    for weight in gadget_weights(params):
        gadget_message = constant_poly(bit * weight, params)

        row_for_a = encrypt_rlwe_q_message_with_noise_bound(
            zero_message,
            rlwe_secret_key,
            params,
            rng,
            params.evaluation_key_noise_bound,
        )
        row_for_a = RLWECiphertext(
            a=poly_add(row_for_a.a, gadget_message, params),
            b=row_for_a.b,
        )
        rows_for_a.append(row_for_a)

        row_for_b = encrypt_rlwe_q_message_with_noise_bound(
            zero_message,
            rlwe_secret_key,
            params,
            rng,
            params.evaluation_key_noise_bound,
        )
        row_for_b = RLWECiphertext(
            a=row_for_b.a,
            b=poly_add(row_for_b.b, gadget_message, params),
        )
        rows_for_b.append(row_for_b)
    return RGSWCiphertext(rows_for_a=rows_for_a, rows_for_b=rows_for_b)


def external_product(
    control: RGSWCiphertext,
    ciphertext: RLWECiphertext,
    params: ToyTFHEParams,
) -> RLWECiphertext:
    """RGSW 暗号文と RLWE 暗号文の external product を計算する。

    G^{-1}(RLWE_s(m')) RGSW_s(m) に対応する。

    入力 RLWE が平文 M(X) を暗号化し、RGSW が bit を暗号化しているなら、
    出力は bit * M(X) の RLWE 暗号文になる。
    """
    # TODO:
    # 1. ciphertext の a(X) と b(X) を Gadget Decomposition する。
    # 2. 各桁の多項式を、対応する RGSW 暗号文の行に掛ける。
    # 3. 得られた RLWE 暗号文をすべて加算する。
    a_digits = gadget_decompose_poly(ciphertext.a, params)
    b_digits = gadget_decompose_poly(ciphertext.b, params)
    acc = RLWECiphertext(a=zero_poly(params), b=zero_poly(params))

    for j in range(params.l):
        acc = rlwe_add(
            acc,
            rlwe_plain_mul(control.rows_for_a[j], a_digits[j], params),
            params,
        )
        acc = rlwe_add(
            acc,
            rlwe_plain_mul(control.rows_for_b[j], b_digits[j], params),
            params,
        )

    return acc


def cmux(
    control: RGSWCiphertext,
    false_ciphertext: RLWECiphertext,
    true_ciphertext: RLWECiphertext,
    params: ToyTFHEParams,
) -> RLWECiphertext:
    """暗号化された bit によって 2 つの RLWE 暗号文を選ぶ。"""
    # TODO: CMUX(c_b,c_0,c_1)=c_b external_product (c_1-c_0)+c_0
    # に対応する暗号文演算を実装する。
    difference = rlwe_sub(true_ciphertext, false_ciphertext, params)
    gated_difference = external_product(control, difference, params)
    return rlwe_add(gated_difference, false_ciphertext, params)


def make_bootstrapping_key(
    lwe_secret_key: list[int],
    rlwe_secret_key: list[int],
    params: ToyTFHEParams,
    rng: random.Random,
) -> BootstrappingKey:
    """LWE 秘密鍵の各 bit を RGSW で暗号化する。"""
    encrypted_bits: list[RGSWCiphertext] = []
    for bit in lwe_secret_key:
        encrypted_bit = rgsw_encrypt_bit(bit, rlwe_secret_key, params, rng)
        encrypted_bits.append(encrypted_bit)
    return BootstrappingKey(encrypted_lwe_key_bits=encrypted_bits)


def extracted_lwe_key_from_rlwe_key(
    rlwe_secret_key: list[int],
    params: ToyTFHEParams,
) -> list[int]:
    """Sample Extraction 後の LWE 秘密鍵を作る。

    Sample Extraction 後の LWE 暗号文を
    a''=(a'_0,-a'_{N-1},..., -a'_1), s''=(s'_0,...,s'_{N-1})
    として表している。この関数は s'' を返す。
    """
    extracted_key: list[int] = []
    for coefficient in rlwe_secret_key:
        extracted_key.append(coefficient)
    return extracted_key


def make_key_switching_key(
    extracted_key: list[int],
    target_lwe_key: list[int],
    params: ToyTFHEParams,
    rng: random.Random,
) -> KeySwitchingKey:
    """Key Switching Key を作る。

    ksk[i,j]=LWE_s(s''_i q/B^{j+1}) に対応する。
    """
    encrypted_key: list[list[LWECiphertext]] = []
    for coefficient in extracted_key:
        rows_for_coefficient: list[LWECiphertext] = []
        for weight in gadget_weights(params):
            message = normalize(coefficient * weight, params.q)
            a_vector: list[int] = []
            for _ in range(params.k):
                a_vector.append(rng.randrange(params.q))
            error = rng.randrange(params.evaluation_key_noise_bound + 1)
            inner = dot_mod(a_vector, target_lwe_key, params.q)
            b_value = normalize(inner + message + error, params.q)
            rows_for_coefficient.append(LWECiphertext(a=a_vector, b=b_value))
        encrypted_key.append(rows_for_coefficient)
    return KeySwitchingKey(encrypted_extracted_key=encrypted_key)


def make_evaluation_key(
    lwe_secret_key: list[int],
    rlwe_secret_key: list[int],
    params: ToyTFHEParams,
    rng: random.Random,
) -> EvaluationKey:
    """Blind Rotation と Key Switching に必要な評価鍵を作る。"""
    bootstrapping_key = make_bootstrapping_key(
        lwe_secret_key,
        rlwe_secret_key,
        params,
        rng,
    )
    extracted_key = extracted_lwe_key_from_rlwe_key(rlwe_secret_key, params)
    key_switching_key = make_key_switching_key(
        extracted_key,
        lwe_secret_key,
        params,
        rng,
    )
    return EvaluationKey(
        bootstrapping_key=bootstrapping_key,
        key_switching_key=key_switching_key,
    )


def blind_rotate(
    ciphertext: LWECiphertext,
    test_polynomial: list[int],
    bootstrapping_key: BootstrappingKey,
    params: ToyTFHEParams,
) -> RLWECiphertext:
    """Blind Rotation をナイーブに実行する。

    最初に入力 c=(a,b) の各係数を Z_q から Z_{2N} へ
    リスケーリングする。
    テスト多項式は Z_p 上で与えられるため、各係数に Delta を掛けて
    Z_q 上へ配置する。その後、X^(-b_hat + <a_hat,s>) v(X) の
    RLWE 暗号文を作る。
    """
    # TODO:
    # 1. LWE 暗号文を Z_q から Z_{2N} へリスケーリングする。
    # 2. テスト多項式を X^{-b_hat} 倍した自明な RLWE 暗号文を作る。
    # 3. 各 a_hat_i について、暗号化された s_i を制御bitとする
    #    CMUXを適用し、X^{a_hat_i}倍するかどうかを選ぶ。
    rescaled = rescale_lwe_ciphertext(ciphertext, params)
    scaled_test_polynomial = scale_plaintext_poly(test_polynomial, params)
    acc = trivial_rlwe(scaled_test_polynomial, params)
    acc = rlwe_monomial_mul(acc, -rescaled.b, params)
    for i in range(params.k):
        rotated = rlwe_monomial_mul(acc, rescaled.a[i], params)
        acc = cmux(
            bootstrapping_key.encrypted_lwe_key_bits[i],
            acc,
            rotated,
            params,
        )
    return acc


def sample_extract(
    ciphertext: RLWECiphertext,
    params: ToyTFHEParams,
) -> LWECiphertext:
    """RLWE 暗号文の定数項を LWE 暗号文として取り出す。"""
    # TODO:
    # a''=(a'_0,-a'_{N-1},...,-a'_1), b''=b'_0
    # に対応する LWE 暗号文を作る。
    extracted_a = [ciphertext.a[0]]
    for index in range(1, params.n):
        extracted_a.append(normalize(-ciphertext.a[params.n - index], params.q))
    return LWECiphertext(extracted_a, ciphertext.b[0])


def key_switch(
    ciphertext: LWECiphertext,
    key_switching_key: KeySwitchingKey,
    params: ToyTFHEParams,
) -> LWECiphertext:
    """Sample Extraction 後の LWE 暗号文を元の LWE 鍵へ変換する。"""
    # TODO:
    # 1. (0,b'') から計算を始める。
    # 2. a'' の各係数を Gadget Decomposition する。
    # 3. 各桁と対応する Key Switching Key を掛け、結果から引く。
    result = trivial_lwe(ciphertext.b, params)
    for i in range(params.n):
        digits = gadget_decompose(ciphertext.a[i], params)
        for j in range(params.l):
            term = lwe_scalar_mul(
                key_switching_key.encrypted_extracted_key[i][j], digits[j], params
            )
            result = lwe_sub(result, term, params)
    return result


def programmable_bootstrap(
    ciphertext: LWECiphertext,
    evaluation_key: EvaluationKey,
    params: ToyTFHEParams,
) -> LWECiphertext:
    """Blind Rotation、Sample Extraction、Key Switching を順に行う。"""
    result = blind_rotate(
        ciphertext,
        list(params.nand_test_polynomial),
        evaluation_key.bootstrapping_key,
        params,
    )
    result = sample_extract(result, params)
    result = key_switch(result, evaluation_key.key_switching_key, params)
    return result


def hom_nand(
    left: LWECiphertext,
    right: LWECiphertext,
    evaluation_key: EvaluationKey,
    params: ToyTFHEParams,
) -> LWECiphertext:
    """TFHE の HomNAND をナイーブに実行する。"""
    # TODO:
    # 1. 暗号文のまま Z_p 上の 1-m_1-m_2 を行う。
    # 2. 線形前処理後の暗号文を Programmable Bootstrapping へ渡す。
    preprocessed = trivial_lwe_plaintext(params.hom_nand_constant, params)
    preprocessed = lwe_sub(preprocessed, left, params)
    preprocessed = lwe_sub(preprocessed, right, params)

    return programmable_bootstrap(preprocessed, evaluation_key, params)


if __name__ == "__main__":
    params = ToyTFHEParams()
    rng = random.Random(2026)
    lwe_key = generate_lwe_secret_key(params, rng)
    rlwe_key = generate_rlwe_secret_key(params, rng)
    evaluation_key = make_evaluation_key(lwe_key, rlwe_key, params, rng)

    message = encode_bit(1, params)
    c1 = encrypt_lwe(params.delta * message, lwe_key, params, rng)
    out = hom_nand(c1, c1, evaluation_key, params)
    out_message = decrypt_lwe(out, lwe_key, params)
    print("NAND(1, 1) =", decode_bit(out_message, params))
