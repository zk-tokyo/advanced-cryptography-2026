"""Week 1 課題「proof-of-exploit」の解答ファイル。

編集してよいのはこのファイルと requirements.txt だけです。
先に problems/proof-of-exploit/README.md と tests/challenge.py を読んでください。
制約 DSL は tests/aclib.py にあります。

回路は「すべて 0 になるべき制約の集合」です。信号は、制約で縛らない限り
どんな値にもなれます（＝自由）。ここがこの課題の肝です。
"""

from __future__ import annotations

from aclib import ConstraintSystem
from spec import ROLE_OK, CLEARANCE_OK, REGION_OK
import challenge


# ------------------------------------------------------------------ Part A
def build(cs: ConstraintSystem, role: int, clearance: int, region: int):
    """健全かつ完全なアクセス制御回路を組む。

    満たすべき性質:
        granted == 1 にできる  <=>  role in ROLE_OK かつ clearance in CLEARANCE_OK
                                      かつ region in REGION_OK

    ルール:
      * 資格の信号は必ず "role", "clearance", "region" の名前で
        cs.input(name, value) として宣言する。
      * 補助信号は cs.aux(name, value)、制約は cs.assert_zero(expr)、
        出力は cs.set_output(granted) で宣言する。
      * 信号・制約の集合は入力の値に依存させない（許可リストにのみ依存）。

    ヒント: 許可リスト S = {a1, a2, ...} について、ビットのフラグ f に
        f * (x - a1) * (x - a2) * ... == 0
    を課すと、f == 1 のとき x in S が保証される。3 つのフラグの AND を
    granted にする。フラグをビットに縛る制約を忘れないこと。
    """
    role_in = cs.input("role", role)
    cle_in = cs.input("clearance", clearance)
    reg_in = cs.input("region", region)

    role_au = cs.aux("f_role", 1)
    cle_au = cs.aux("f_cle", 1)
    reg_au = cs.aux("f_reg", 1)
    cs.assert_zero(role_au * (role_au - 1))
    cs.assert_zero(cle_au * (cle_au - 1))
    cs.assert_zero(reg_au * (reg_au - 1))

    poly_role = 1
    for a in ROLE_OK:
    poly_role *= (role_in - a)
    cs.assert_zero(role_au * poly_role)

    poly_cle = 1
    for a in CLEARANCE_OK:
        poly_cle *= (cle_in - a)
    cs.assert_zero(cle_au * poly_cle)

    poly_reg = 1
    for a in REGION_OK:
        poly_reg *= (reg_in - a)
    cs.assert_zero(reg_au * poly_reg)

    granted = cs.aux("granted", 0)
    cs.assert_zero(granted * (granted - 1))
    cs.assert_zero(granted - role_au * cle_au * reg_au)
    cs.set_output(granted)

# ------------------------------------------------------------------ Part B
def attack() -> dict[str, int]:
    """tests/challenge.py を破る witness を返す。

    返す dict は、challenge 回路の全信号名 -> 値。次を満たすこと:
      * challenge の全制約を満たす
      * granted == 1
      * ただし資格は authorized ではない（＝不正アクセス）

    ヒント: 適当な authorized 資格で
        w = challenge.honest_witness(role, clearance, region)
    を作り、抜けている制約を突くように改ざんする。
    """
    w = challenge.honest_witness(2, 3, 4)
    w["f_region"] = 1
    w["granted"] = 1
    return w
