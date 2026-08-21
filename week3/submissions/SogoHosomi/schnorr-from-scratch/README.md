# schnorr-from-scratch

## 概要

有限体 → 楕円曲線 → Schnorr プロトコルと、下から順に積み上げて、最後に
Bitcoin でも使われている曲線 secp256k1 上の Schnorr 署名を完成させる、
ひとつなぎの課題です。

- **Part 1**: 有限体 F_p の足し算・掛け算・逆元
- **Part 2**: Part 1 を使って、楕円曲線の点の足し算とスカラー倍
- **Part 3**: Part 2 を使って、シグマプロトコル（対話証明）の穴埋めと、
  Fiat-Shamir 変換による Schnorr 署名

下の Part が正しくないと上の Part は動きません。テストも Part 1 から順に
通していくのがおすすめです。

## 課題

`solution.py` の 10 個の関数を実装します。編集するのはこのファイルと
`requirements.txt` だけです。曲線パラメータ・拡張ユークリッドの互除法・
ハッシュ関数は `tests/given.py` に用意してあり、`from given import ...` で
使えます（このファイルは編集しません）。

デバッグ用の小さな曲線 `TOY`（y² = x³ + 11 over F₁₀₀₉、位数 967）と、
本物の曲線 `SECP256K1` の 2 本が与えられます。関数はどちらでも動くように
書きます（曲線は引数 `curve` で渡ってきます）。

### Part 1 — 有限体 F_p

```python
field_add(a, b, p)   # (a + b) mod p
field_mul(a, b, p)   # (a * b) mod p
field_inv(a, p)      # (a * x) mod p == 1 となる x。a ≡ 0 なら ValueError
```

逆元には、与えてある `extended_gcd(a, b)` を使います。これは
`a*x + b*y == g`（g = gcd(a, b)）となる `(g, x, y)` を返すので、
`extended_gcd(a % p, p)` で g == 1 なら x が逆元です。x は負のことが
あるので、必ず 0..p-1 に正規化してください。

### Part 2 — 楕円曲線

曲線 y² = x³ + ax + b over F_p 上の点は `(x, y)` のタプル、単位元
（無限遠点）は `INFINITY`（= `None`）で表します。

```python
ec_add(P, Q, curve)         # 点の足し算
ec_scalar_mul(k, P, curve)  # スカラー倍 k*P（k >= 0）
```

足し算の場合分け（詳しい式は `solution.py` の docstring にあります）:

1. どちらかが無限遠点 → もう片方を返す
2. x が同じで y が互いに逆符号 → 無限遠点（P + (−P) = O）
3. P == Q → 2 倍算（接線の傾き λ = (3x² + a) / 2y）
4. それ以外 → 弦の傾き λ = (y_Q − y_P) / (x_Q − x_P)

「割り算」は Part 1 の `field_inv` で行います。

スカラー倍は **double-and-add 法**で実装してください。secp256k1 の
スカラーは最大 256 ビットあるので、ec_add を k 回繰り返す実装ではテストが
終わりません（テストには k = n ≈ 2²⁵⁶ のケースがあります）。テストが
いつまでも返ってこないときは、まずここを疑ってください。

デバッグには `given.is_on_curve(P, curve)` が使えます。正しい実装なら
計算結果は必ず曲線上に乗ります。乗らないときは公式のどこか（特に y_R の
符号）が間違っています。

**検算例**（TOY 曲線: G = (1, 298)）:

| k | k·G |
|---|-----|
| 2 | (818, 800) |
| 3 | (851, 516) |
| 123 | (376, 128) |
| 967 (= n) | 無限遠点 |

### Part 3 — シグマプロトコルと Schnorr 署名

秘密鍵 x、公開鍵 P = x·G について「x を知っている」ことを証明する
3 手の対話プロトコル（シグマプロトコル）を穴埋めします。スカラーの計算は
mod n（G の位数）で行うことに注意してください。

```text
証明者                                検証者
r ← ランダム
R = r·G          ──── R ────▶
                 ◀─── e ────          e ← ランダム
s = r + e·x      ──── s ────▶         s·G == R + e·P を確認
```

```python
sigma_commit(r, curve)              # R = r*G
sigma_response(x, r, e, curve)      # s = r + e*x mod n
sigma_verify(pubkey, R, e, s, curve)  # s*G == R + e*pubkey ?
```

**検算例**（TOY 曲線）: 秘密鍵 x = 123（公開鍵 P = (376, 128)）、
r = 456 とすると R = (822, 106)。チャレンジ e = 77 に対して
s = 456 + 77·123 mod 967 = **257** で、検証等式が成り立ちます。

次に **Fiat-Shamir 変換**です。検証者の仕事はランダムな e を選ぶこと
だけなので、e をハッシュ `e = H(R || P || message)`（与えてある
`challenge_hash`）で置き換えれば対話が不要になり、そのまま**署名方式**に
なります。これが Schnorr 署名です。

```python
schnorr_sign(x, message, nonce, curve)         # -> (R, s)
schnorr_verify(pubkey, message, (R, s), curve)  # -> bool
```

検証側は e を `challenge_hash` で計算し直してから `sigma_verify` と同じ
確認をします。

> **nonce の使い回しは厳禁**: 同じ r を 2 つの異なるチャレンジ e₁, e₂ に
> 使うと、s₁ − s₂ = (e₁ − e₂)·x から誰でも秘密鍵 x を解けてしまいます
> （special soundness — 証明としては「本当に x を知っている」ことの根拠で
> あり、署名としては nonce 再利用が致命的である理由）。テストにはこの
> 攻撃を実演するケースが含まれています。この課題では再現性のため nonce を
> 引数で受け取りますが、実運用では毎回新しい乱数にします。

## 手元での動かし方

正式な採点スクリプト（後述の「進め方」）は毎回まっさらな環境を作るため
少し時間がかかります。実装中は次の方法が手軽です。いずれもリポジトリ直下で
実行し、`<github-username>` は自分のものに置き換えてください。

```bash
# solution.py と given.py（tests/ 内）を import できるようにする
export PYTHONPATH="week3/problems/schnorr-from-scratch/python/tests:week3/submissions/<github-username>/schnorr-from-scratch/python"

# 1. 簡易チェック（solution.py 末尾のチェック。埋めた分だけ [ ] が [o] になる）
python3 week3/submissions/<github-username>/schnorr-from-scratch/python/solution.py

# 2. 対話的に試す（簡易チェックのあと REPL に入る）
python3 -i week3/submissions/<github-username>/schnorr-from-scratch/python/solution.py
>>> ec_add(TOY.G, TOY.G, TOY)
>>> field_inv(3, 11)

# 3. 採点テストを一部だけ実行（クラス名で絞り込み、-v で詳細表示）
python3 -m unittest public.Part1Field -v
python3 -m unittest public.Part2AToyCurve -v
```

テストのクラスは学習順に `Part1Field` → `Part2AToyCurve` →
`Part2BSecp256k1` → `Part3ASigmaProtocol` → `Part3BSchnorrSignature` の
5 つです。提出前には必ず正式なテストも実行してください。

## 採点（`tests/public.py`、内容は公開）

1. **Part 1**: F_p の演算が正しい（負の入力の正規化、0 の逆元で ValueError を含む）。
2. **Part 2**: TOY 曲線でのテストベクトル、単位元・逆元の扱い、準同型性
   (k₁+k₂)G = k₁G + k₂G、secp256k1 での大きなスカラー倍と nG = O。
3. **Part 3**: 完全性（正直なトランスクリプトは受理）、不正なトランスクリプトの
   拒否、nonce 再利用からの鍵復元、secp256k1 上の署名の固定テストベクトルと
   改ざん検知。

## 提出先

```text
week3/submissions/<github-username>/schnorr-from-scratch/python/
```

このディレクトリに、必ず次を置きます。

```text
solution.py
requirements.txt
```

## 進め方（スクリプト）

github-username は自動判定されます。

```bash
# 1. 提出フォルダとテンプレートを用意
bash scripts/new-submission.sh week3 schnorr-from-scratch

# 2. solution.py を実装し、テスト
bash scripts/test-python-submission.sh week3 schnorr-from-scratch <github-username>

# 3. 提出（テストが通れば commit・push・PR 作成まで自動）
bash scripts/submit.sh week3 schnorr-from-scratch
```

## ルール

- Python のみです。標準ライブラリだけで解けます（追加パッケージは不要）。
- 編集してよいのは `week3/submissions/<github-username>/` 以下だけです。
- `problems/`、`.github/`、`scripts/` は編集しないでください。
- 関数名と引数の並びは変更しないでください。
- `pow(a, -1, p)` や外部ライブラリの逆元・楕円曲線実装をそのまま使うのではなく、
  この課題の趣旨（自分で組む）に沿って実装してください。
