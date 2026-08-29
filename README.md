# Advanced Cryptography 2026

Advanced Cryptographyはゼロ知識証明の理論と実装の理解を促し、Ethereumエコシステムや実社会にコミットする技術者を養成する学習プログラムです。このレポジトリは、各週の教材と演習問題を管理しています。

- 初めて課題を提出する方は、[「1. 初回だけ行う準備」](#1-初回だけ行う準備)から進めてください。
- 2回目以降は、[「2. 課題ごとの提出手順」](#2-課題ごとの提出手順)から始めてください。

## 0. 必要な環境

GitHub を使うのが初めてでも進められるよう、最初に次を用意します。用意できたら
「1. 初回だけ行う準備」へ進んでください。

- **GitHub アカウント**: [github.com](https://github.com/) で無料作成できます。
- **Git**（バージョン管理ツール）
  - macOS: `xcode-select --install`、または `brew install git`
  - Ubuntu / Debian: `sudo apt install git`
  - Windows: [Git for Windows](https://gitforwindows.org/) を入れ、付属の **Git Bash** を使います
  - 確認: `git --version`
- **Python 3.10 以上**（課題は Python で解きます）
  - macOS: `brew install python`、または [python.org](https://www.python.org/downloads/) のインストーラ
  - Ubuntu / Debian: `sudo apt install python3 python3-venv`
  - Windows: [python.org](https://www.python.org/downloads/) のインストーラ（"Add python.exe to PATH" にチェック）
  - 確認: `python3 --version`
- **GitHub CLI (`gh`)**（推奨）: 提出スクリプトが username の自動判定と PR 作成に使います
  - インストール: [cli.github.com](https://cli.github.com/)、認証: `gh auth login`、確認: `gh --version`
  - 無くても提出できます（username を引数で渡し、PR は GitHub の画面から作成）
- **シェル**: 提出スクリプトは bash 用です。macOS / Linux はターミナルをそのまま使えます。
  Windows は **Git Bash** または **WSL** を使ってください。

## 1. 初回だけ行う準備

この章の操作は、最初の1回だけ行います。

### 1.1. リポジトリを fork する

fork は、公式リポジトリを自分の GitHub アカウントへコピーする操作です。

1. [公式リポジトリ](https://github.com/zk-tokyo/advanced-cryptography-2026)を開く
2. 画面右上の **Fork** を選ぶ
3. 内容を変更せず **Create fork** を選ぶ

自分の GitHub アカウントに `advanced-cryptography-2026` が作成されれば完了です。

### 1.2. fork を clone する

clone は、fork したリポジトリを自分のPCへコピーする操作です。ターミナルで次のコマンドを1行ずつ実行してください。

```bash
git clone https://github.com/{YOUR_GITHUB_USERNAME}/advanced-cryptography-2026.git
cd advanced-cryptography-2026
```

これ以降のコマンドは、`advanced-cryptography-2026` ディレクトリの中で実行します。自分の fork は、Git では `origin` という名前で扱います。

### 1.3. 公式リポジトリを登録する

課題の更新を受け取れるように、公式リポジトリを `upstream` という名前で登録します。

```bash
git remote add upstream https://github.com/zk-tokyo/advanced-cryptography-2026.git
git remote -v
```

`origin` と `upstream` の両方が表示され、`upstream` が `https://github.com/zk-tokyo/advanced-cryptography-2026.git` を指していれば、初回の準備は完了です。

## 2. 課題ごとの提出手順

ここからは、課題を提出するたびに行う操作です。

### 2.1. 最新の状態から branch を作る

branch は、課題ごとに作る作業場所です。次のコマンドで `main` を最新にしてから、提出用 branch を作ります。

```bash
git switch main
git pull --ff-only upstream main
git switch -c submit/weekN-{YOUR_GITHUB_USERNAME}
```

Week 1 を `alice` さんが提出する場合、branch 名は `submit/week1-alice` です。`main` のまま課題を編集しないでください。同じ週に問題が複数ある場合は、同じ branch と Pull Request に含めて構いません。

### 2.2. 課題に取り組み、テストする

1. 取り組む週の README（例: `week1/README.md`）を開く
2. 問題の README に書かれたコマンドで、テンプレートをコピーする
3. コピーしたファイルに解答を実装する
4. 問題の README に書かれたローカルテストを実行する

編集してよいのは、次の自分専用ディレクトリ以下だけです。

```text
weekN/submissions/{YOUR_GITHUB_USERNAME}/
```

問題文、テンプレート、テスト、README、`.github/`、`scripts/` は編集しないでください。

### 2.3. 解答を commit して push する

まず、変更したファイルを確認します。

```bash
git status --short
```

自分の提出ディレクトリ以外が表示された場合は、ここで止まり、変更内容を確認してください。問題がなければ、提出するファイルだけを記録して GitHub へ送ります。

```bash
git add weekN/submissions/{YOUR_GITHUB_USERNAME}/
git status --short
git commit -m "submit weekN"
git push -u origin submit/weekN-{YOUR_GITHUB_USERNAME}
```

`git add .` は、関係のないファイルまで追加しやすいため使わないでください。

### 2.4. Pull Request を作る

Pull Request（PR）は、GitHub上で課題を提出する操作です。

1. GitHubで自分の `advanced-cryptography-2026` を開く
2. **Compare & pull request** を選ぶ
3. Pull Request の向きを確認する

**Compare & pull request** が表示されない場合は、公式リポジトリの **Pull requests** → **New pull request** → **compare across forks** の順に選んでください。

```text
base repository: zk-tokyo/advanced-cryptography-2026
base branch: main
head repository: {YOUR_GITHUB_USERNAME}/advanced-cryptography-2026
compare branch: submit/weekN-{YOUR_GITHUB_USERNAME}
```

タイトルを `[weekN] {YOUR_GITHUB_USERNAME}` にして、**Create pull request** を選べば提出完了です。

### 2.5. CI とレビューを確認する

CI は、提出内容を自動で確認する仕組みです。Pull Request を作成すると自動で実行されます。

- CI が成功した場合は、レビューをお待ちください。
- CI が失敗した場合は、チェック結果のエラーメッセージを確認してください。

修正するときは、同じ branch でファイルを直してテストし、次のコマンドを実行します。

```bash
git add weekN/submissions/{YOUR_GITHUB_USERNAME}/
git commit -m "fix weekN"
git push
```

同じ Pull Request が更新されるため、branch や Pull Request を作り直す必要はありません。

## 3. ライセンス / License

本リポジトリは、**教材（文章・スライド・図）** と **コード** で異なるライセンスを適用します。

| 対象 | ライセンス | 全文 |
|---|---|---|
| 教材 — `weekN/README.md`、`weekN/problems/**/README.md`、スライド、補助教材、`Output-Themes.md` などの文章・図 | **CC BY 4.0** | [`LICENSE-docs`](LICENSE-docs) |
| コード — `scripts/`、`.github/`、`weekN/problems/**` 配下のテンプレート・テスト・参照実装 | **MIT** | [`LICENSE`](LICENSE) |

### 適用されないもの

- **`weekN/submissions/` 配下の提出物は、各提出者に著作権が帰属します。** 本リポジトリのライセンスは適用されません。第三者が利用する場合は提出者本人に確認してください。
- 教材内で引用している論文・図版・外部資料は、それぞれの原著作者の権利に従います。

### 再利用について

CC BY 4.0 / MIT のいずれも、**出典の表示（クレジット）**を条件に、複製・改変・再配布・商用利用ができます。勉強会での利用、翻訳、他プログラムへの流用を歓迎します。表示の例:

> Advanced Cryptography Program 2026 — 東京大学ブロックチェーンイノベーション寄附講座 / Merkle Japan (ZK Tokyo), CC BY 4.0

### 貢献について

誤植の修正、説明の改善、課題の追加などの貢献を歓迎します。**Issue を立ててから Pull Request を作成してください。**

貢献いただいた内容は、上記のライセンス（教材は CC BY 4.0、コードは MIT）で公開されます。commit に `Signed-off-by:` を付けて（`git commit -s`）、ご自身が書いたものであり、このライセンスで公開する権利があることを表明してください。

企業に所属している方は、業務外の貢献であっても所属先の規定を確認してください。
