# 本を1冊サイトに追加する手順（定期実行用）

この手順は、`mochi-to-shio` リポジトリの `news-book/RUN.md` で本（画像 01.png〜）を作り終えたあとに行う。
1回の実行で、作った本を1冊だけこのサイトに追加して push する。

## 0. 前提

- このリポジトリ：`ryotarouchid4-tech/mochi-news-book`（ブランチ `main`）
- 公開URL：https://mochi-news-book.pages.dev （push すると Cloudflare Pages が自動でビルドして公開する）
- 本の画像：`news-book/output/年月日/01.png〜`（3枚か4枚。`overview.png` は使わない）
- 文章：`news-book/news.json` の内容をそのまま使う（画像と同じ文章にする）

## 1. 最新にする

```
git pull --rebase origin main
```

## 2. 追加する本の JSON を作る

作業用のファイル（例：`/tmp/book.json`）を作る。**このファイルはリポジトリの中に置かない。**

```json
{
  "date": "2026-10-15",
  "time": "0800",
  "title": "先生の書類仕事を、国産AIがお手伝い",
  "topic": "ai",
  "summary": "茨木市とNTT西日本が、一部の小中学校で先生の書類仕事にAIを使う実証について。",
  "description": "茨木市とNTT西日本の校務AIの実証を、2026年10月15日の本で紹介。資料探しや要約、文章作成を手伝うAIについて読めます。",
  "body": ["news.json の what", "news.json の shio"],
  "afterword": "news.json の matome",
  "mochi": "news.json の mochi",
  "source": {
    "name": "ITmedia NEWS",
    "title": "記事の見出し",
    "url": "記事のURL",
    "date": "2026-10-14",
    "status": "2026年10月15日に記事名と本文を確認。"
  },
  "images": [".../01.png", ".../02.png", ".../03.png", ".../04.png"]
}
```

各項目の決め方：

- `date`：日本時間の今日。`2026-10-15` の形
- `time`：今回の枠。`0800` / `1100` / `1700` のどれか（本のURLが `/books/2026-10-15-0800/` になる）
- `title`：`news.json` の `title`。`\n` は取りのぞく
- `topic`：`content/topics.json` を読み、合うテーマの `id` を入れる
  - 合うテーマがないときだけ、新しいテーマを作る。そのときは次の2つも入れる
    - `topic_title`：日本語のテーマ名（例：`仕事・はたらき方`、`くらし・制度`）
    - `topic_en`：英語の大文字表記（例：`WORK`、`LIFE & RULES`）
    - `topic` の `id` は半角英小文字（例：`work`、`life`）
  - なるべく既存のテーマに入れる。似たテーマを増やしすぎない
- `summary`：何のニュースかを1文で（40〜60文字くらい）。「〜について。」で終える。記事に書いてあることだけ
- `description`：検索結果に出る説明。「〇〇を、2026年10月15日の本で紹介。」＋ひとこと（60〜90文字くらい）
- `body`：`news.json` の `what` と `shio` を、この順にそのまま入れる
- `afterword`：`news.json` の `matome` をそのまま
- `mochi`：`news.json` の `mochi` をそのまま
- `source`：
  - `name`：NHK のときは `NHKニュース`、ITmedia のときは `ITmedia NEWS`
  - `title`：記事の見出し（`history.json` に入れたものと同じ）
  - `url`：記事のURL
  - `date`：記事の公開日がわかるときだけ入れる（わからなければ項目ごと省く）
  - `status`：ITmedia は `2026年10月15日に記事名と本文を確認。`、NHK は `2026年10月15日に記事名とリード文を確認。`（日付は今日）
- `images`：`output/年月日/` の `01.png` から順に、できた枚数ぶん（3枚か4枚）

## 3. 本を追加する

```
python3 scripts/add_book.py /tmp/book.json
```

- 画像が WebP に変換されて `public/assets/book-番号-ページ.webp` に入り、`content/books.json` の先頭に1冊追加される
- 新しいテーマのときは `content/topics.json` にも追加される
- 「エラー:」が出たら、内容を直してもう一度実行する（エラーのときはファイルは何も変わらない）
  - 「同じタイトルの本がもうあります」と出たときは、push せずに理由を伝えて終わる（タイトルは勝手に変えない）

## 4. ビルドと検査

```
python3 scripts/build.py
python3 scripts/validate.py
```

- 両方とも最後まで通ったときだけ次へ進む
- どちらかが失敗したら、**push しない**。`git checkout -- content public && git clean -fd public` で元に戻し、エラーの内容を伝えて終わる
- `node scripts/check-interactions.cjs` は Node.js があれば実行する（なければ省いてよい）
- `dist/` は Git 管理しない（Cloudflare 側でビルドする）

## 5. commit して push

```
git add content/books.json public/assets/book-*.webp
git add content/topics.json   # 新しいテーマを作ったときだけ
git status                    # 追加した本の画像と JSON だけになっているか確認
git commit -m "本を追加（本のタイトル）"
git push origin main
```

- コミットするのは `content/books.json`、追加した `public/assets/book-番号-*.webp`、（新しいテーマのときだけ）`content/topics.json` だけ
- ほかのファイル（`scripts/`、`templates/`、CSS、JS など）は変更しない
- コミットメッセージの末尾には、定期実行の指示文にある Co-Authored-By などの行を入れる
- push が「先に進んでいる」と拒否されたら、`git pull --rebase origin main` してからもう一度 push する

## 6. 伝える

- 公開される本のページURL（`https://mochi-news-book.pages.dev/books/2026-10-15-0800/` の形）を伝える
- 新しいテーマを作ったときは、そのテーマ名と、そのテーマのページの説明文が仮の文章になっていることも伝える
- 反映まで1〜2分かかる
