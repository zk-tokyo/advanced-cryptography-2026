# Advanced Cryptography 2026

## 課題の確認方法

各週の課題は次の場所にあります。

```text
weekN/exercises/exercises.md
```

例:

```text
week1/exercises/exercises.md
```

まず該当週の `exercises.md` を読み、提出ファイル名や回答形式を確認してください。

## 提出先

提出物は、該当週の `submissions` ディレクトリの下に、自分専用のディレクトリを作って置きます。

```text
weekN/exercises/submissions/<your-name>/
```

例:

```text
week1/exercises/submissions/alice/answer.md
```

`<your-name>` には、GitHub username など、教員が誰の提出か分かる名前を使ってください。

## 提出PRの作り方

課題提出は、自分のGitHubアカウントにこのリポジトリをforkして行います。

### 1. リポジトリをforkする

GitHub上でこのリポジトリを開き、右上の **Fork** ボタンから自分のアカウントにforkしてください。

### 2. forkしたリポジトリをcloneする

`<your-github-name>` を自分のGitHub usernameに置き換えてください。

```bash
git clone git@github.com:<your-github-name>/advanced-cryptography-2026.git
cd advanced-cryptography-2026
```

HTTPSを使う場合は、次のようにcloneしても構いません。

```bash
git clone https://github.com/<your-github-name>/advanced-cryptography-2026.git
cd advanced-cryptography-2026
```

### 3. upstreamを設定する

fork元のリポジトリを `upstream` として登録しておくと、課題の更新を取り込めます。

```bash
git remote add upstream https://github.com/zk-tokyo/advanced-cryptography-2026.git
git fetch upstream
```

### 4. 提出用branchを作る

提出ごとに新しいbranchを作ってください。

```bash
git switch main
git pull --ff-only upstream main
git switch -c submit/week1-<your-name>
```

例:

```bash
git switch -c submit/week1-alice
```

### 5. 提出ファイルを作成する

該当週の提出ディレクトリを作り、課題で指定されたファイルを置きます。

```bash
mkdir -p week1/exercises/submissions/<your-name>
code week1/exercises/submissions/<your-name>/answer.md
```

`code` コマンドが使えない場合は、好きなエディタで `answer.md` を作成してください。

### 6. commitしてpushする

```bash
git status
git add week1/exercises/submissions/<your-name>/answer.md
git commit -m "submit week1"
git push -u origin submit/week1-<your-name>
```

### 7. Pull Requestを作成する

GitHubで自分のforkを開き、提出branchからPull Requestを作成してください。

Pull Requestの向きは次のようにしてください。

```text
base repository: zk-tokyo/advanced-cryptography-2026
base branch: main
head repository: <your-github-name>/advanced-cryptography-2026
compare branch: submit/week1-<your-name>
```

Pull Requestのbase branchは必ず `main` にしてください。

## 重要なルール

1つのPull Requestでは、1つの週・1人分の提出だけを変更してください。

良い例:

```text
week1/exercises/submissions/alice/answer.md
```

避ける例:

```text
week1/exercises/submissions/alice/answer.md
week2/exercises/submissions/alice/answer.md
```

```text
week1/exercises/submissions/alice/answer.md
week1/exercises/submissions/bob/answer.md
```

また、提出PRでは次のようなファイルを変更しないでください。

```text
.github/
tools/
weekN/exercises/grader.py
weekN/exercises/exercises.md
```

提出物以外のファイルを同じPRで変更すると、自動採点が失敗します。

## 自動採点

課題提出PRを作成すると、自動採点CIが実行されます。

自動採点は次のタイミングで走ります。

- Pull Requestを作成したとき
- Pull Requestのbranchに新しいcommitをpushしたとき

採点結果はPRコメントとして投稿されます。コメントには点数、合否、採点理由が表示されます。

合格点は現在 `70点` です。70点以上の場合、`auto-grade` check がpassします。

## 再提出

採点結果を見て修正したい場合は、同じPRのbranchに追加commitをpushしてください。

新しいcommitをpushすると、自動採点が再実行され、PRコメントも更新されます。

## 提出前チェックリスト

- 該当週の `exercises.md` を読んだ。
- 提出先が `weekN/exercises/submissions/<your-name>/` になっている。
- 1つのPRで1つの週・1人分だけを提出している。
- 課題で指定されたファイル名を使っている。
- `.github/`, `tools/`, `grader.py`, `exercises.md` を変更していない。
- PRのbase branchが `main` になっている。
