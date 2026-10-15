# もちとしおのニュース本棚

ニュースを4ページの本にまとめた静的サイトです。Python 3でHTMLを生成します。追加パッケージやデータベースは不要です。

## Cloudflare Pages

- フレームワーク：なし（None）
- 本番ブランチ：main
- ルートディレクトリ：リポジトリのルート
- ビルドコマンド：python3 scripts/build.py
- 出力ディレクトリ：dist
- 環境変数：SITE_URL=https://mochi-to-shio.pages.dev

GitHubのリポジトリ直下に、このフォルダの中身を登録してください。mochi-to-shioというフォルダごと一段深く登録した場合は、Cloudflareのルートディレクトリも合わせる必要があります。

## 編集する場所

- content/books.json：本の日付、本文、あとがき、出典
- public/assets/：本の画像、ロゴ、アイコン
- scripts/build.py：各ページのHTMLと構造化データ
- scripts/design.py：ヘッダー、フッター、トップ画面
- public/site.css / experience.css / typography.css / warm.css：スタイル
- public/site.js：本の切り替え、立ち読み、メニューなど
- templates/：お問い合わせとプライバシーポリシー等

## ローカルでのビルド・検査

```sh
python3 scripts/build.py
python3 scripts/validate.py
node scripts/check-interactions.cjs
```

Node.jsは操作テストにのみ使用します。公開用のビルドにはPython 3だけが必要です。ビルドするとdistを作り直します。distを直接編集しないでください。

公開URLを変更する場合はSITE_URLを変更してビルドしてください。canonical、OGP、構造化データ、サイトマップ、フォームの完了URLも更新されます。

## お問い合わせ

FormSubmitを利用し、ryotarouchid4@gmail.comに通知します。受付の自動返信を設定しています。公開元が変わったら、テスト送信で認証メールや配信状況を確認してください。通知先とは別のメールアドレスをフォームに入力し、通知・受付メール・サンクスページを確認します。

## 既存のCloudflare Pagesプロジェクトについて

Direct Uploadで作成したプロジェクトは、あとからGit連携に切り替えられません。既存プロジェクトを削除せず、設定と公開URLの引き継ぎ方法を先に確認してください。GitHub Actionsから既存のDirect Uploadプロジェクトへ自動デプロイする方法もありますが、別途Cloudflareの認証設定が必要です。

新しくGit連携で作成する場合、同じプロジェクト名・pages.dev URLをそのまま利用できるとは限りません。実際に表示される公開URLを確認してSITE_URLを合わせます。

## 公開後

- 新URLの表示とフォームを確認
- 旧サイトからの転送・重複公開の扱いを確認
- Search Consoleで所有権確認・sitemap.xml送信・URL検査

検索順位やAI検索への掲載は保証されません。ブラウザの表示検査、メール配信、Search Console登録はこのソース一式の検査には含みません。
