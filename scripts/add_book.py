#!/usr/bin/env python3
"""本を1冊、本棚に追加する。

使い方:
    python3 scripts/add_book.py 追加する本.json

追加する本.json の形（くわしくは PUBLISH.md）:
{
  "date": "2026-10-15",            本の日付（日本時間の今日）
  "time": "0700",                  今回の枠: 0700 / 1100 / 1500 / 1900 / 2300（国内）、0900 / 1300 / 1700 / 2100（海外）
  "title": "表紙の見出し",          改行(\\n)は入れない
  "topic": "ai",                   テーマのID（半角英小文字・数字・ハイフン）
  "topic_title": "AI・テクノロジー", 新しいテーマのときだけ必要
  "topic_en": "AI & TECHNOLOGY",    新しいテーマのときだけ必要
  "summary": "一覧や本のページの紹介文（1文）",
  "description": "検索結果に出る説明文（1〜2文）",
  "body": ["その一の文章", "くわしい説明1", "…", "シオの話"],  2〜8個
  "afterword": "あとがきの一文",
  "mochi": "モチの一言",
  "source": {"name": "ITmedia NEWS", "title": "記事の見出し", "url": "https://...", "date": "2026-10-14",
             "status": "2026年10月15日に記事名と本文を確認。"},
  "tags": [{"id": "google", "name": "グーグル"}],  （任意）話題のタグ。1〜5個
  "images": ["/path/to/01.png", "/path/to/02.png", "/path/to/03.png", "/path/to/04.png"],
  "webPublished": "2026-10-16"     （省略可）サイトに載せた日。省略すると date と同じ
}

やること:
  - 画像（3〜10枚）を WebP に変換して public/assets/book-{番号}-{ページ}.webp に置く
  - content/books.json の先頭に1冊分を追加する（URL は /books/{日付}-{時間}/）
  - 新しいテーマなら content/topics.json にも追加する
"""
from pathlib import Path
import json, re, sys
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
BOOKS_FILE = ROOT / 'content/books.json'
TOPICS_FILE = ROOT / 'content/topics.json'
TAGS_FILE = ROOT / 'content/tags.json'
ASSETS = ROOT / 'public/assets'
# 定期実行の枠（2時間ごと。国内: 0700/1100/1500/1900/2300、海外: 0900/1300/1700/2100）
# 0800 は前の時間割の名残り（過去の本のため）
TIMES = ('0700', '0800', '0900', '1100', '1300', '1500', '1700', '1900', '2100', '2300')


def fail(message):
    raise SystemExit('エラー: ' + message)


def text(data, key):
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        fail(f'「{key}」が空です')
    return value.strip()


def save_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def main():
    if len(sys.argv) != 2:
        fail('使い方: python3 scripts/add_book.py 追加する本.json')
    data = json.loads(Path(sys.argv[1]).read_text())
    books = json.loads(BOOKS_FILE.read_text())
    topics = json.loads(TOPICS_FILE.read_text())

    # 日付・時間・URL
    date = text(data, 'date')
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', date):
        fail('「date」は 2026-10-15 の形にしてください')
    time = text(data, 'time')
    if time not in TIMES:
        fail('「time」は ' + ' / '.join(TIMES) + ' のどれかにしてください')
    slug = f'{date}-{time}'
    if any(b['slug'] == slug for b in books):
        fail(f'{slug} の本はもう登録されています')

    # 文章
    title = text(data, 'title').replace('\n', '')
    if any(b['title'] == title for b in books):
        fail(f'「{title}」と同じタイトルの本がもうあります。見出しを少し変えてください')
    summary = text(data, 'summary')
    description = text(data, 'description')
    afterword = text(data, 'afterword')
    mochi = text(data, 'mochi')
    body = data.get('body')
    if not (isinstance(body, list) and 2 <= len(body) <= 8 and all(isinstance(x, str) and x.strip() for x in body)):
        fail('「body」は ["その一", くわしい説明…, "シオの話"] の2〜8個の文章にしてください')
    body = [x.strip() for x in body]

    # 出典
    source = data.get('source')
    if not isinstance(source, dict):
        fail('「source」がありません')
    for key in ('name', 'title', 'url', 'status'):
        text(source, key)
    if not source['url'].startswith('https://'):
        fail('出典の「url」は https:// から始まる形にしてください')
    if any(b['source']['url'] == source['url'] for b in books):
        fail('この記事の本はもう登録されています')
    if source.get('date') and not re.fullmatch(r'\d{4}-\d{2}-\d{2}', source['date']):
        fail('出典の「date」は 2026-10-14 の形にしてください')
    source = {k: source[k] for k in ('name', 'title', 'url', 'date', 'status') if source.get(k)}

    # テーマ
    topic = text(data, 'topic')
    if not re.fullmatch(r'[a-z0-9]+(-[a-z0-9]+)*', topic):
        fail('「topic」は半角英小文字・数字・ハイフンにしてください（例: work, life）')
    found = next((t for t in topics if t['id'] == topic), None)
    new_topic = None
    if found:
        category = found['title']
    else:
        category = text(data, 'topic_title')
        en = text(data, 'topic_en')
        if any(t['title'] == category for t in topics):
            fail(f'「{category}」は別のIDで登録されています')
        new_topic = {
            'id': topic,
            'title': category,
            'en': en,
            'card': f'{category}にまつわるニュースを集めました。',
            'lead': f'{category}にまつわるニュースを、短い本にまとめて紹介しています。',
            'sections': [],
        }

    # 話題のタグ（任意）: [{"id": "google", "name": "グーグル"}, ...]。1〜5個
    tag_list = json.loads(TAGS_FILE.read_text()) if TAGS_FILE.exists() else []
    known = {t['id']: t['name'] for t in tag_list}
    tags, new_tags = [], []
    for t in data.get('tags') or []:
        tid, name = (t.get('id'), t.get('name')) if isinstance(t, dict) else (t, None)
        if not isinstance(tid, str) or not re.fullmatch(r'[a-z0-9]+(-[a-z0-9]+)*', tid):
            fail(f'タグの id は半角英小文字・数字・ハイフンにしてください: {tid}')
        if tid not in known:
            if not (isinstance(name, str) and name.strip()):
                fail(f'新しいタグ「{tid}」には name（日本語の名前）が必要です')
            if name.strip() in known.values():
                fail(f'タグ「{name}」は別の id で登録されています（content/tags.json を見てください）')
            known[tid] = name.strip()
            new_tags.append({'id': tid, 'name': name.strip()})
        if tid not in tags:
            tags.append(tid)
    if len(tags) > 5:
        fail('タグは5個までにしてください')

    # 画像
    images = data.get('images')
    if not (isinstance(images, list) and 3 <= len(images) <= 10):
        fail('「images」は3〜10枚の画像のパスにしてください')
    opened = []
    for path in images:
        if not Path(path).is_file():
            fail(f'画像が見つかりません: {path}')
        im = Image.open(path)
        w, h = im.size
        if abs(w * 4 - h * 3) > 4:
            fail(f'画像の縦横比が 3:4 ではありません: {path}（{w}x{h}）')
        opened.append(im)

    # ここから書き込み（ここまでで止まった場合は何も変わらない）
    number = max(b['id'] for b in books) + 1
    pages = []
    for page, im in enumerate(opened, 1):
        name = f'assets/book-{number}-{page}.webp'
        target = ROOT / 'public' / name
        if target.exists():
            fail(f'{name} がもうあります')
        im.convert('RGB').save(target, 'WEBP', quality=85, method=6)
        pages.append(name)

    book = {
        'id': number,
        'title': title,
        'date': date,
        'category': category,
        'pages': pages,
        'slug': slug,
        'description': description,
        'summary': summary,
        'body': body,
        'afterword': afterword,
        'mochi': mochi,
        'source': source,
        'topic': topic,
        'url': f'/books/{slug}/',
        'webPublished': data.get('webPublished') or date,
        'tags': tags,
        'time': time,
    }
    if new_topic:
        topics.append(new_topic)
        save_json(TOPICS_FILE, topics)
    if new_tags:
        TAGS_FILE.write_text(json.dumps(tag_list + new_tags, ensure_ascii=False, indent=2) + '\n')
    books.insert(0, book)
    # 新しい日付・時間が先頭になるように並べる（あとから古い本を足したときのため）
    books.sort(key=lambda b: (b['date'], b.get('time', '')), reverse=True)
    save_json(BOOKS_FILE, books)

    # 一覧用の小さい表紙と、SNS用のシェア画像を作る
    import subprocess
    subprocess.run([sys.executable, str(ROOT / 'scripts/make_images.py'), str(number)], check=True)

    print(f'追加しました: {title}')
    print(f'  URL: /books/{slug}/  画像: {len(pages)}枚  テーマ: {category}' + ('（新しいテーマ）' if new_topic else ''))
    print('  変更したファイル: content/books.json' + (', content/topics.json' if new_topic else '') + ', ' + ', '.join('public/' + p for p in pages)
          + f', public/assets/book-{number}-thumb.webp, public/assets/book-{number}-og.jpg')


if __name__ == '__main__':
    main()
