# もちとしおのニュース本：ChatGPT への引き継ぎ

2026年10月16日に作成。Claude（Claude Code）で動かしていた「毎日の本作り」と「サイトへのアップ」を、ChatGPT（Codex）に移すための資料。
Claude のプランは2027年1月で終わる予定。それまでに ChatGPT 側で動くことを確かめてから切り替える。

---

## 1. 全体の仕組み

```
ニュースのサイト（RSS など）
   ↓ 記事を1本選んで、日本語の文章を書く（news.json）
mochi-to-shio リポジトリの news-book/
   ↓ build_news_page.py で本の画像（3〜10ページ）を作る
   ↓ history.json に記録して push
mochi-news-book リポジトリ（このリポジトリ）
   ↓ scripts/add_book.py で本を追加 → build / validate → push
Cloudflare Pages が自動でビルドして公開
   → https://mochi-news-book.pages.dev/books/日付-時間/
```

| もの | 場所 |
|---|---|
| 本を作るプログラムと手順書 | GitHub `ryotarouchid4-tech/mochi-to-shio`（非公開）の `news-book/` |
| サイト | GitHub `ryotarouchid4-tech/mochi-news-book`（公開）。ブランチ `main` |
| 公開 | Cloudflare Pages のプロジェクト `mochi-news-book`（GitHub 連携。ビルドコマンド `python3 scripts/build.py`、出力 `dist`） |
| 公開URL | https://mochi-news-book.pages.dev/ |

`mochi-to-shio` のルートは、もちとしおの公式サイト（4コマ漫画。Vercel）。ニュース本の作業では `news-book/` 以外を触らない。

## 2. 手順書（AIはこれを読んで動く）

| ファイル | 中身 |
|---|---|
| `mochi-to-shio/news-book/AGENTS.md` | 本作りの入口。読む順番と守ること |
| `mochi-to-shio/news-book/WRITING_RULES.md` | 文章のルール（ページ数の決め方、海外ニュースのとき、使わない言葉） |
| `mochi-to-shio/news-book/RUN.md` | 国内のニュースの本を作る手順 |
| `mochi-to-shio/news-book/RUN_WORLD.md` | 海外のニュースの本を作る手順 |
| `mochi-to-shio/news-book/setup.sh` | 新しい環境の準備（Python のライブラリと日本語フォント） |
| `mochi-news-book/AGENTS.md` | サイトの入口。サイトの方針 |
| `mochi-news-book/PUBLISH.md` | 本を1冊サイトに追加する手順 |

## 3. 時間割

日本時間で、7時から23時まで2時間ごと（1日9冊）。

| 枠 | 種類 | ニュースの取り先 |
|---|---|---|
| 7・11・15・19・23時 | 国内 | NHK、ITmedia NEWS、Impress Watch、GIGAZINE |
| 9・13・17・21時 | 海外 | TechCrunch、Engadget、Axios（英語の記事を日本語で書く） |

本のURLは `/books/2026-10-16-0700/` の形（日付-枠）。

## 4. これまでに決めたこと

本の中身

- ニュース1本＝1冊。3〜10ページ（表紙、その一、くわしい説明 0〜6ページ、シオの話、あとがき）
- 記事が短ければ短い本でいい。長ければくわしく解説する。水増ししない
- 文章はAIっぽくしない。短い文、ふだんの話し言葉。大げさな言い方・たとえ話・キャッチコピーのような見出しはだめ
- 出典は必ず入れる。海外の記事は `出典：TechCrunch「英語の見出し」`（見出しは英語のまま）
- カテゴリーは絞らない。重い事件・事故・災害・犯罪・訃報・戦争・政治の争いは選ばない
- X には投稿しない（前は X 用の投稿文と zip を作っていたが、やめた）
- キャラは2人だけ：モチ（白いねこ、赤いパーカー）とシオ（小さい灰色の鳥）

サイト

- `mochi-news-book/AGENTS.md` の「サイトの方針」を参照（枠で囲まない、AIっぽい言葉を使わない、テーマを固定しない、SNSリンクなし、など）
- お問い合わせは Googleフォーム（https://forms.gle/2Qsi6MR94ZKBQFkR6 ）を `/contact/` に埋め込み
- Search Console は登録済み（確認用のタグは `site.config.json`）。sitemap も送信済み

## 5. ChatGPT 側の準備

### 5-1. Codex に GitHub をつなぐ

1. ChatGPT の Codex（https://chatgpt.com/codex ）を開いて、GitHub を接続する
2. 環境（Environment）を作り、リポジトリに `mochi-news-book` と `mochi-to-shio` を選ぶ（両方選べない場合は `mochi-news-book` だけでよい。もう1つは指示文の中で clone する）
3. 環境のインターネット接続を「すべて（All）」にする（ニュースのサイトと GitHub を読むため）
4. セットアップのスクリプトに次を入れる：

   ```
   bash news-book/setup.sh 2>/dev/null || true
   ```

   （`mochi-to-shio` が作業フォルダにないときは、指示文の中で clone したあとに実行される）

### 5-2. push するためのトークン

Codex のクラウド作業は、ふつうは変更を「PR（プルリクエスト）」にして返す。今の Claude と同じように main へ直接 push させるために、GitHub のトークンを渡す。

1. GitHub → Settings → Developer settings → Fine-grained personal access tokens → Generate new token
2. Repository access：`mochi-to-shio` と `mochi-news-book` の2つだけ
3. Permissions：Contents を Read and write（ほかはいらない）
4. 有効期限：1年など
5. Codex の環境のシークレット（Secrets）に `GH_TOKEN` という名前で登録する

トークンはパスワードと同じ。チャットやファイルに貼らない。

### 5-3. ChatGPT のカスタム指示（任意）

ChatGPT の「カスタマイズ」→「ChatGPT にどのように応答してほしいですか？」に入れると、Claude と同じような話し方になる。

```
・やわらかい、ふだんの日本語で話してください。
・私はプログラミングを勉強中です。専門用語は少なめにしてください。
・コードを変える前に、計画を見せて私の OK をもらってください（計画→実行前の確認→完了の報告）。
・変更は必要なところだけにしてください。コードは省略せずに全部見せてください。
・言い切りすぎる言い方は避けてください。
```

## 6. 定期実行の指示文（ChatGPT 用）

Plus の定期タスクは5つまで。国内と海外を1つにまとめて、**2時間ごとに動く1つのタスク**にする。

- スケジュール：毎日、日本時間 6:48 / 8:48 / 10:48 / … / 22:48（2時間ごと、9回）。「2時間ごと」が選べなければ、近い設定にする（下の「うまくいかないとき」も参照）
- 作業場所：Codex（クラウド）、5-1 で作った環境

### 指示文（そのまま貼る）

```
もちとしお「きょうのニュース」の本を1冊（ニュース1本）作って、サイトに載せてください。
日本時間 7時〜23時の2時間ごとに動く定期タスクです。X には投稿しません。返答はやわらかい日本語で、短めに。

0. 今回の枠を決める
   - 日本時間の今の時刻にいちばん近い、7・9・11・13・15・17・19・21・23時のどれかを「今回の枠」にする
   - 7・11・15・19・23時なら「国内」、9・13・17・21時なら「海外」

1. 準備
   - GitHub の ryotarouchid4-tech/mochi-to-shio と ryotarouchid4-tech/mochi-news-book（どちらもブランチ main）を用意する。
     作業フォルダにないほうは、次の形で clone する：
     git clone https://x-access-token:${GH_TOKEN}@github.com/ryotarouchid4-tech/リポジトリ名.git
   - push に使う remote も同じ形の URL にする（git remote set-url origin ...）
   - git の user.name / user.email が未設定なら、mochi-news-bot / mochi-news-bot@users.noreply.github.com にする
   - mochi-to-shio で bash news-book/setup.sh を実行する（MOCHI_FONT_DIR を表示されたら設定する）

2. 本を作る
   - mochi-to-shio の news-book/AGENTS.md と news-book/WRITING_RULES.md を読む
   - 国内なら news-book/RUN.md、海外なら news-book/RUN_WORLD.md の手順どおりに、本を1冊作る
   - 本の長さ（3〜10ページ）は記事の情報量に合わせる。水増ししない
   - できた画像は全部開いて、文字のはみ出し・重なり・おかしな改行がないか確認する

3. 記録して push（mochi-to-shio）
   - 手順書どおり history.json に1件追加し、news-book/history.json だけをコミットして main に push する

4. サイトに載せる（mochi-news-book）
   - mochi-news-book の AGENTS.md と PUBLISH.md を読み、手順どおりに今回の本を1冊追加する
     （文章は今回の news.json、画像は今回の output の 01.png〜、time は今回の枠を 4桁にしたもの。例：0700）
   - scripts/build.py と scripts/validate.py が両方通ったときだけ、PUBLISH.md に書かれたファイルだけをコミットして main に push する

5. 報告する（この返答に書く）
   - 選んだ記事の見出しと URL（海外なら英語の見出しと日本語訳）、本のページ数
   - 公開される本のページの URL（https://mochi-news-book.pages.dev/books/日付-枠/）
   - overview.png が添付できれば添付する

守ること
   - mochi-to-shio では news-book/ 以外のファイルを変更しない。mochi-news-book では PUBLISH.md に書かれたファイル以外を変更しない
   - PR は作らない。main に直接 push する。push できないときは、PR を作らずに理由を報告して終わる
   - 条件に合う記事がない、サイトが読めない、build / validate が通らないときは、push せずに理由を報告して終わる
   - 読めないサイトを、curl やミラーなど別の方法で読みにいかない
```

## 7. 切り替えの手順

1. 5-1〜5-3 を準備する
2. ChatGPT で、6 の指示文を**定期タスクにせず1回だけ**実行してみる（実際に本が1冊増える）
3. 次を確認する
   - mochi-to-shio に `news-book/history.json` のコミットが増えている
   - mochi-news-book に `本を追加（…）` のコミットが増えている
   - https://mochi-news-book.pages.dev/ に本が出ている（1〜2分かかる）
   - 本の画像の日本語がきれいに出ている（フォントが入っていないと文字化けやエラーになる）
4. うまくいったら、6 の定期タスクを作る
5. **同じ日に、Claude の定期タスク2つ（「もちとしおニュースの本」「もちとしお海外ニュースの本」）を一時停止する**。両方動くと、同じ枠の本を2つが作ろうとする（2つ目は「もう登録されています」で止まるが、むだに動く）
   - Claude のアプリ → 定期タスク（Scheduled tasks）→ それぞれ一時停止
6. 数日ようすを見て、問題なければ Claude 側のタスクを削除する

## 8. うまくいかないとき

| こまったこと | どうするか |
|---|---|
| main に push できない（PR しか作れない） | トークン（5-2）がシークレットとして渡っているか確認する。それでもだめなら、次の「B案」にする |
| 「2時間ごと」の定期タスクが作れない | 国内と海外で2つのタスクに分ける。それもだめなら、回数を減らす（例：7・12・17・22時の4回） |
| 使える量（Codex の利用上限）が足りない | 1日の回数を減らす。上限は https://chatgpt.com/codex/settings/usage で確認できる |
| フォントのエラー | `bash news-book/setup.sh` の表示を見る。`MOCHI_FONT_DIR` の設定もれが多い |
| ニュースのサイトが読めない | 環境のインターネット接続が「すべて」になっているか確認する |

B案：GitHub Actions ＋ OpenAI API

- GitHub の上で決まった時間に動かす方法。ChatGPT のプランとは別に、OpenAI API の利用料（使った分だけ）がかかる
- `openai/codex-action` を使えば、6 の指示文をほぼそのまま使える
- A案がどうしても動かないときに、ChatGPT（Codex）に「MIGRATION.md の B案で作って」と頼む

## 9. 遼太朗さんが自分でやること（残り）

- [ ] Googleフォーム：「回答」→ ︙ →「新しい回答についてのメール通知を受け取る」をオン
- [ ] Googleフォーム：「お問い合わせ内容」を必須・段落にする
- [ ] お問い合わせのテスト送信（本文に「テスト送信・返信不要」）。通知メールと回答のコピーが届くか確認
- [ ] 両方のリポジトリに残っているテスト用のブランチ（test/…、push-check など）を削除
- [ ] Cloudflare に残っている Workers 版（mochi-news-book.ryotarouchid4.workers.dev）を削除
- [ ] （任意）Bing Webmaster Tools に登録（Search Console から読みこめる）
- [ ] 5〜7 の切り替え

## 10. 参考：Claude 側の定期タスク（2026年10月16日時点）

| 名前 | 時間（日本時間） | 状態 |
|---|---|---|
| もちとしおニュースの本 | 6:48 / 10:48 / 14:48 / 18:48 / 22:48（7・11・15・19・23時の枠） | 動いている |
| もちとしお海外ニュースの本 | 8:48 / 12:48 / 16:48 / 20:48（9・13・17・21時の枠） | 動いている |
| もちとしおニュースの本（古い時間割） | — | 停止中（削除してよい） |

指示文の中身は、6 の指示文とほぼ同じ（Claude の機能で画像とメッセージを送る部分だけちがう）。
