#!/usr/bin/env python3
"""本ごとの「一覧用の小さい表紙」と「SNS用のシェア画像（1200x630）」を作る。

使い方:
    python3 scripts/make_images.py          … まだ作っていない本の分だけ作る
    python3 scripts/make_images.py 12 13    … 本の番号（id）を指定して作り直す

作るファイル（content/books.json にもパスを書きこむ）:
    public/assets/book-{id}-thumb.webp … 一覧用の表紙（幅480）
    public/assets/book-{id}-og.jpg     … シェア画像（1200x630）

Pillow が必要（サイトのビルドには不要。Cloudflare では動かさない）。
"""
from pathlib import Path
import json, os, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
BOOKS_FILE = ROOT / 'content/books.json'
PUBLIC = ROOT / 'public'
# Noto CJK フォントの場所。ほかの環境では MOCHI_FONT_DIR で変えられる
FONT_DIR = Path(os.environ.get('MOCHI_FONT_DIR', '/usr/share/fonts/opentype/noto'))
THUMB_W = 480
OG_W, OG_H = 1200, 630
BG = (247, 240, 228)
BROWN = (94, 65, 48)
GRAY = (150, 132, 118)
RED = (182, 92, 74)
NO_LINE_START = '、。，．・：；？！ー）」』】〉》ぁぃぅぇぉっゃゅょゎァィゥェォッャュョヮ…'


def font(weight, size):
    path = FONT_DIR / f'NotoSansCJK-{weight}.ttc'
    if path.exists():
        return ImageFont.truetype(str(path), size, index=0)
    return ImageFont.load_default()


def wrap(text, fnt, max_w):
    lines, cur = [], ''
    for ch in text:
        if fnt.getlength(cur + ch) <= max_w or not cur:
            cur += ch
        elif ch in NO_LINE_START:
            lines.append(cur + ch)
            cur = ''
        else:
            lines.append(cur)
            cur = ch
    if cur:
        lines.append(cur)
    return lines


def make_thumb(b):
    src = Image.open(PUBLIC / b['pages'][0]).convert('RGB')
    h = round(src.height * THUMB_W / src.width)
    name = f"assets/book-{b['id']}-thumb.webp"
    src.resize((THUMB_W, h), Image.LANCZOS).save(PUBLIC / name, 'WEBP', quality=82, method=6)
    return name


def make_og(b):
    img = Image.new('RGB', (OG_W, OG_H), BG)
    d = ImageDraw.Draw(img)
    # 左：表紙（少し傾けて、影をつける）
    cover = Image.open(PUBLIC / b['pages'][0]).convert('RGBA')
    ch = 520
    cw = round(cover.width * ch / cover.height)
    cover = cover.resize((cw, ch), Image.LANCZOS).rotate(3, expand=True, resample=Image.BICUBIC)
    shadow = Image.new('RGBA', (cover.width + 60, cover.height + 60), (0, 0, 0, 0))
    shadow.paste((121, 88, 64, 70), (30, 40), cover.split()[3])
    shadow = shadow.filter(ImageFilter.GaussianBlur(14))
    x0, y0 = 60, (OG_H - cover.height) // 2
    img.paste(shadow, (x0 - 30, y0 - 30), shadow)
    img.paste(cover, (x0, y0), cover)
    # 右：ロゴ・見出し・日付
    left = x0 + cover.width + 60
    right = OG_W - 70
    logo_path = PUBLIC / 'assets/logo.png'
    y = 92
    if logo_path.exists():
        logo = Image.open(logo_path).convert('RGBA')
        lw = 300
        logo = logo.resize((lw, round(logo.height * lw / logo.width)), Image.LANCZOS)
        img.paste(logo, (left, y), logo)
        y += logo.height + 34
    f_title = font('Bold', 54)
    lines = wrap(b['title'], f_title, right - left)
    if len(lines) > 4:
        lines = lines[:4]
        lines[-1] = lines[-1][:-1] + '…'
    for line in lines:
        d.text((left, y), line, font=f_title, fill=BROWN)
        y += 78
    y += 18
    meta = b['date'].replace('-', '.') + '  ・  ' + b['category'] + '  ・  ' + f"{len(b['pages'])}ページの本"
    d.text((left, y), meta, font=font('Medium', 26), fill=RED)
    d.text((left, OG_H - 78), 'もちとしおのニュース本棚', font=font('Medium', 24), fill=GRAY)
    name = f"assets/book-{b['id']}-og.jpg"
    img.save(PUBLIC / name, 'JPEG', quality=86, optimize=True, progressive=True)
    return name


def main():
    books = json.loads(BOOKS_FILE.read_text())
    wanted = {int(x) for x in sys.argv[1:]}
    done = []
    for b in books:
        missing = not (b.get('thumb') and (PUBLIC / b['thumb']).exists() and b.get('ogImage') and (PUBLIC / b['ogImage']).exists())
        if (wanted and b['id'] in wanted) or (not wanted and missing):
            b['thumb'] = make_thumb(b)
            b['ogImage'] = make_og(b)
            done.append(b['id'])
    BOOKS_FILE.write_text(json.dumps(books, ensure_ascii=False, indent=2) + '\n')
    print('作りました:', done if done else 'なし（全部そろっています）')


if __name__ == '__main__':
    main()
