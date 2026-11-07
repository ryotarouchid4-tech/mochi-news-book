#!/usr/bin/env python3
"""公開するファイル（dist/）の数を数えて、Cloudflare Pages の上限に近づいていないかを表示する（提案No.12）。

- 表示するだけで、失敗（終了コード1など）にはしない。毎日の本作りを止めないため。
- 上限の 20,000 は「無料プランなら」の仮の数字（今のプランは未確認）。
- 「1日あたりの増え方」は、content/books.json の webPublished（サイトに載せた日）で
  直近7日に何冊増えたかを数え、1冊あたりのファイル数を掛けた「概算」。
単体でも動く：python3 scripts/file_count.py
"""
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import json

LIMIT = 20000   # 無料プランの上限（仮）
NOTICE = 15000  # 注意
URGENT = 19000  # 緊急
EARLY_DAYS = 30  # 上限まで30日以内なら早めの注意
JST = timezone(timedelta(hours=9))


def count_files(out):
    """dist/ の中のふつうのファイルを、フォルダの奥まで数える。"""
    return sum(1 for p in Path(out).rglob('*') if p.is_file())


def books_last_7_days(books, today):
    """webPublished が (today-7日, today] の本の数。日付がない・読めない・未来の本は数えない。"""
    start = today - timedelta(days=7)
    n = 0
    for b in books:
        try:
            d = date.fromisoformat(str(b.get('webPublished', ''))[:10])
        except ValueError:
            continue
        if start < d <= today:
            n += 1
    return n


def status(files, books_total, recent_books):
    """段階と、上限までの日数の目安を返す。"""
    level = 'urgent' if files >= URGENT else 'notice' if files >= NOTICE else 'ok'
    per_book = files / books_total if books_total else 0
    per_day = recent_books / 7 * per_book
    days_left = None if per_day <= 0 else max(0, (LIMIT - files) / per_day)
    early = days_left is not None and days_left <= EARLY_DAYS
    return {'level': level, 'per_book': per_book, 'per_day': per_day, 'days_left': days_left, 'early': early}


def report(out, books, today=None):
    today = today or datetime.now(JST).date()
    files = count_files(out)
    recent = books_last_7_days(books, today)
    s = status(files, len(books), recent)
    label = {'ok': 'ok', 'notice': '注意', 'urgent': '緊急'}[s['level']]
    if s['level'] == 'ok' and s['early']:
        label = '注意（上限まで30日以内の見込み）'
    left = '推定できない（直近7日に増えた本が0冊）' if s['days_left'] is None else f"約{s['days_left']:.0f}日（推定）"
    print(f"FILES: 公開するファイル {files:,}個 / 上限 {LIMIT:,}個（無料プランなら・仮） [{label}]")
    print(f"       直近7日（webPublished）に {recent}冊、1冊あたり約{s['per_book']:.1f}個 → 1日約{s['per_day']:.0f}個（概算）、上限まで {left}")
    return s


if __name__ == '__main__':
    root = Path(__file__).resolve().parent.parent
    report(root / 'dist', json.loads((root / 'content/books.json').read_text()))
