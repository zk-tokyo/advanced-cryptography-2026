# Week 5

Week 5 の課題では主にTFHEのProgrammable BootstrappingとHomNANDのtoy実装を行ないます。

詳細な課題内容については `problems/tfhe-toy-python`を参照してください。

## 講義スライド

以下のslidevを参照してください。当日(8/29)まで随時修正や補足情報の追加を加えて行きますが、予習用として活用いただいて構いません。

https://acp26-week5-presentation-agent.zk-tokyo-japan.workers.dev/1

## 提出先

```text
week5/submissions/<github-username>/tfhe-toy-python/python/
```

このディレクトリに、必ず次を置きます。

```text
solution.py
requirements.txt
```

## 提出方法

まず、提出用ディレクトリを作成します。`<github-username>` は自分の GitHub ユーザー名に
置き換えてください。

```bash
bash scripts/new-submission.sh week5 tfhe-toy-python <github-username>
```

作成された `week5/submissions/<github-username>/tfhe-toy-python/python/solution.py`
の `NotImplementedError` を埋めます。

ローカルで公開テストを実行します。

```bash
bash scripts/test-python-submission.sh week5 tfhe-toy-python <github-username>
```

テストが通ったら、提出用スクリプトを実行します。

```bash
bash scripts/submit.sh week5 tfhe-toy-python
```

このスクリプトは提出ディレクトリをテストし、問題がなければブランチ作成、commit、push、
Pull Request 作成まで行います。

自分で手動提出する場合も、PR に含めるのは原則として
`week5/submissions/<github-username>/` 以下だけにしてください。

## ルール

- Python のみです。
- 標準ライブラリのみ使用できます。サードパーティ製パッケージは使用しません。
- `week5/problems/`、`.github/`、`scripts/` 以下のファイルは提出時に編集しないでください。
- 編集してよいのは `week5/submissions/<github-username>/` 以下だけです。
- 関数名と引数の並びは変更しないでください。

## 発展的な参考先

この課題の完全版を配布リポジトリには置きません。実用的なパラメータ、評価鍵にもノイズを含む構成、最適化された実装を確認する場合は、次を参照してください。

- [TFHE論文](https://eprint.iacr.org/2018/421.pdf): TFHEの方式と論文中のパラメータ
- [TFHE-rs](https://github.com/zama-ai/tfhe-rs): RustによるTFHE実装
- [OpenFHE](https://github.com/openfheorg/openfhe-development): FHE方式を扱うライブラリ

## 参考文献

- Chillotti, Gama, Georgieva, Izabachene, "TFHE: Fast Fully Homomorphic Encryption over the Torus", Journal of Cryptology 2020.
- Ducas and Micciancio, "FHEW: Bootstrapping Homomorphic Encryption in Less Than a Second", EUROCRYPT 2015.
- Micciancio and Polyakov, "Bootstrapping in FHEW-like Cryptosystems", WAHC 2021.
