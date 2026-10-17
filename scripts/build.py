#!/usr/bin/env python3
"""Build the static bookshelf. SITE_URL selects the deployment origin."""
from pathlib import Path
from html import escape as esc
import json,os,re,shutil,xml.etree.ElementTree as ET
from urllib.parse import urlparse
from design import header_html,footer_html,hero_html,extras_html,dialogs_html
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'dist';PUBLIC=ROOT/'public';CONFIG=json.loads((ROOT/'site.config.json').read_text())
BASE=os.environ.get('SITE_URL',CONFIG['url']).rstrip('/')
u=urlparse(BASE)
if u.scheme!='https' or not u.netloc or u.path not in ('','/'):raise SystemExit('SITE_URL must be an https origin, without a path.')
GSV=f'<meta name="google-site-verification" content="{CONFIG["googleSiteVerification"]}">' if CONFIG.get('googleSiteVerification') else ''
NAME=CONFIG['name'];DESCRIPTION=CONFIG['description'];BOOKS=json.loads((ROOT/'content/books.json').read_text())
PUBLISHED='2026-10-15'
TOPICS=json.loads((ROOT/'content/topics.json').read_text())
for b in BOOKS:assert b['topic'] in [t['id'] for t in TOPICS],('topics.json にないテーマ',b['topic'])
# 日本・海外の振り分け（出典のサイト名で自動で決める）
WORLD_SOURCES=('TechCrunch','Engadget','Axios')
REGIONS=[('japan','日本のニュース','JAPAN',''),('world','海外のニュース','WORLD','')]
def region(b):return 'world' if b['source']['name'] in WORLD_SOURCES else 'japan'
LIST_LIMIT=60   # 一覧ページに並べる冊数（それより古い本は月ごとのページへ）
FEED_LIMIT=50
DATA_LIMIT=30   # ページに埋めこむ「立ち読み」用のデータ（新しい本）
_USED=[]        # このページで表示した本（立ち読み用データに入れる）
def thumb(b):return b.get('thumb') or b['pages'][0]
def og_image(b):return b.get('ogImage') or b['pages'][0]
TAGS={t['id']:t['name'] for t in json.loads((ROOT/'content/tags.json').read_text())} if (ROOT/'content/tags.json').exists() else {}
def book_tags(b):return [t for t in b.get('tags',[]) if t in TAGS]
TAG_COUNT={}
for _b in BOOKS:
 for _t in book_tags(_b):TAG_COUNT[_t]=TAG_COUNT.get(_t,0)+1
TAG_PAGES=[t for t in TAGS if TAG_COUNT.get(t,0)>=2]   # 2冊以上あるタグだけページを作る
def tag_links(b):
 out=''.join(f'<a class="tag-chip" href="/tags/{t}/">#{H(TAGS[t])}</a>' if t in TAG_PAGES else f'<span class="tag-chip">#{H(TAGS[t])}</span>' for t in book_tags(b))
 return f'<div class="tag-chips" aria-label="この本の話題">{out}</div>' if out else ''
def n_books(topic):return sum(1 for b in BOOKS if b['topic']==topic)
UPDATED=max(b['webPublished'] for b in BOOKS)
_pc=sorted({len(b['pages']) for b in BOOKS});PAGE_RANGE=str(_pc[0]) if len(_pc)==1 else f'{_pc[0]}〜{_pc[-1]}'
if OUT.exists():shutil.rmtree(OUT)
shutil.copytree(PUBLIC,OUT)
INDEXABLE=[]
def H(v):return esc(str(v),quote=True)
def url(path):return BASE+path
def write(path,text):
 target=OUT/('index.html' if path=='/' else path.strip('/')+'/index.html' if path.endswith('/') else path.lstrip('/'))
 target.parent.mkdir(parents=True,exist_ok=True);target.write_text(text)
def ld(data):return '<script type="application/ld+json">'+json.dumps(data,ensure_ascii=False).replace('<','\\u003c')+'</script>'
def organization():return {'@type':'Organization','@id':url('/#publisher'),'name':NAME+' 運営者','url':url('/about/'),'logo':{'@type':'ImageObject','url':url('/assets/icon.png'),'width':512,'height':512}}
def breadcrumbs(items):return {'@type':'BreadcrumbList','@id':url(items[-1][1]+'#breadcrumb'),'itemListElement':[{'@type':'ListItem','position':i+1,'name':name,'item':url(path)} for i,(name,path) in enumerate(items)]}
def header(path):return header_html(path)
def footer():return footer_html()
def page_books():
 seen={};out=[]
 for b in BOOKS[:DATA_LIMIT]+_USED:
  if b['id'] not in seen:seen[b['id']]=1;out.append(b)
 _USED.clear();return out
def shell(path,title,description,body,*,kind='WebPage',extra=None,crumb=None,image=None,noindex=False,wide=False,main_class=None):
 if not noindex:INDEXABLE.append(path)
 image=image or '/'+og_image(BOOKS[0])
 og_size='<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">' if image.endswith('-og.jpg') else ''
 page={'@type':kind,'@id':url(path+'#webpage'),'url':url(path),'name':title,'description':description,'inLanguage':'ja','isPartOf':{'@id':url('/#website')}}
 graph=[organization(),{'@type':'WebSite','@id':url('/#website'),'url':url('/'),'name':NAME,'description':DESCRIPTION,'inLanguage':'ja','publisher':{'@id':url('/#publisher')}},page]
 if crumb:
  graph.append(breadcrumbs(crumb));page['breadcrumb']={'@id':url(path+'#breadcrumb')}
 if extra:graph.extend(extra)
 fulltitle=title if title==NAME else title+'｜'+NAME
 head=f'''<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">{GSV}<title>{H(fulltitle)}</title><meta name="description" content="{H(description)}"><link rel="canonical" href="{H(url(path))}"><meta name="robots" content="{'noindex,follow' if noindex else 'index,follow,max-image-preview:large'}"><meta property="og:locale" content="ja_JP"><meta property="og:type" content="{'article' if kind=='Article' or path.startswith('/books/') and path!='/books/' else 'website'}"><meta property="og:site_name" content="{H(NAME)}"><meta property="og:title" content="{H(title)}"><meta property="og:description" content="{H(description)}"><meta property="og:url" content="{H(url(path))}"><meta property="og:image" content="{H(url(image))}">{og_size}<meta property="og:image:alt" content="もちとしおのニュース本の表紙"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{H(title)}"><meta name="twitter:description" content="{H(description)}"><meta name="twitter:image" content="{H(url(image))}"><link rel="icon" href="/assets/icon.png" type="image/png"><link rel="apple-touch-icon" href="/assets/icon.png"><link rel="alternate" type="application/atom+xml" title="もちとしおの新しい本" href="/feed.xml"><link rel="stylesheet" href="/site.css"><link rel="stylesheet" href="/experience.css"><link rel="stylesheet" href="/typography.css"><link rel="stylesheet" href="/warm.css"><link rel="stylesheet" href="/a11y.css"><script src="/site.js" defer></script>'''
 bc=''
 if crumb:
  bc='<nav class="breadcrumb" aria-label="パンくずリスト">'+'<span aria-hidden="true">/</span>'.join(f'<span aria-current="page">{H(n)}</span>' if i==len(crumb)-1 else f'<a href="{p}">{H(n)}</a>' for i,(n,p) in enumerate(crumb))+'</nav>'
 cls=main_class if main_class is not None else 'content'+(' content--wide' if wide else '')
 write(path,f'<!doctype html><html lang="ja"><head>{head}{ld({"@context":"https://schema.org","@graph":graph})}</head><body id="top" class="{'is-home' if path=='/' else 'is-inner'}"><div class="wrap">{header(path)}{bc}<main id="main" class="{cls}">{body}</main>{footer()}</div>{dialogs_html(page_books())}</body></html>')
def card(b):
 _USED.append(b)
 return f'''<article class="book" data-book-id="{b['id']}" data-topic="{b['topic']}" data-region="{region(b)}" data-search="{H(b['title']+' '+b['date']+' '+b['date'].replace('-','.')+' '+b['category'])}"><a class="book__cover" href="{b['url']}" tabindex="-1" aria-hidden="true"><img src="/{thumb(b)}" alt="" loading="lazy" width="480" height="640"></a><div class="book__meta"><time datetime="{b['date']}">{b['date'].replace('-','. ')}</time><span>{b['category']}</span>{'<b class="book__region">WORLD</b>' if region(b)=='world' else ''}</div><h3 class="book__title"><a href="{b['url']}">{H(b['title'])}</a></h3><div class="book__actions"><a class="book__read" href="{b['url']}">この本を読む ↗</a><button type="button" class="book__preview" data-preview="{b['id']}" hidden>立ち読み ＋</button></div></article>'''
def cards(books):return '<div class="books">'+''.join(card(b) for b in books)+'</div>'
def item_list(books,identifier):return {'@type':'ItemList','@id':url(identifier+'#list'),'numberOfItems':len(books),'itemListElement':[{'@type':'ListItem','position':i+1,'url':url(b['url']),'name':b['title']} for i,b in enumerate(books)]}
def intro(eyebrow,title,lead=''):return f'<h1>{title}</h1>'+(f'<p class="lead">{lead}</p>' if lead else '')
KANJI='一二三四五六七八'
def pager_html(b):
 i=next(k for k,x in enumerate(BOOKS) if x['id']==b['id'])
 older=BOOKS[i+1] if i+1<len(BOOKS) else None;newer=BOOKS[i-1] if i>0 else None
 def link(x,cls,label):
  if not x:return f'<span class="pager__item pager__item--empty {cls}"></span>'
  return f'<a class="pager__item {cls}" href="{x["url"]}"><small>{label}</small><span>{H(x["title"])}</span></a>'
 return '<nav class="pager" aria-label="前後の本">'+link(older,'pager__item--prev','← 前の本')+link(newer,'pager__item--next','次の本 →')+'</nav>'
def transcript_html(b):
 parts=b['body'];out=''
 for i,t in enumerate(parts):
  kind='ニュースのお話' if i==0 else '読んで考えたこと' if i==len(parts)-1 else 'くわしく'
  out+=f'<section class="transcript"><h3>その{KANJI[i]} — {kind}</h3><p>{H(t)}</p></section>'
 return out
def sources_html(b):
 s=b['source'];result=f'<li><span class="source-kind">本に記載された出典：{H(s["name"])}</span><a href="{H(s["url"])}" target="_blank" rel="noopener noreferrer">{H(s["title"])} <span class="sr-only">（外部サイト・新しいタブ）</span>↗</a>'
 if s.get('date'):result+=f'<small>記事公開日：<time datetime="{s["date"]}">{s["date"].replace("-",".")}</time></small>'
 if b['id']==0:result+='<small>本に記載された記事名に対応するリンクです。記事本文は今回再確認できていません。公開状況は掲載元でご確認ください。</small>'
 result+='</li>'
 if b.get('primary'):
  s=b['primary'];result+=f'<li><span class="source-kind">関連する公式発表：{H(s["name"])}</span><a href="{H(s["url"])}" target="_blank" rel="noopener noreferrer">{H(s["title"])} ↗</a></li>'
 return '<ul class="source-list">'+result+'</ul>'
# Home: all books and navigation links are present in the initial HTML.
latest=BOOKS[0]
hero=hero_html(BOOKS)
# 日付の見出し（2026-10-15 → 10月15日（木））
WEEK='月火水木金土日'
import datetime as _dt
def jdate(d):
 x=_dt.date.fromisoformat(d);return f'{x.month}月{x.day}日（{WEEK[x.weekday()]}）'
def dated_cards(books,tiles=False):
 """日付ごとに見出しをつけて並べる（tiles=True なら表紙の並び）"""
 out='';days=list(dict.fromkeys(b['date'] for b in books))
 for d in days:
  group=[b for b in books if b['date']==d]
  out+=f'<section class="date-group" data-date-group><h3 class="date-head"><time datetime="{d}">{jdate(d)}</time><span>{len(group)}冊</span></h3>'+(('<div class="cover-grid">'+''.join(cover_tile(b) for b in group)+'</div>') if tiles else cards(group))+'</section>'
 return out
MONTHS=list(dict.fromkeys(b['date'][:7] for b in BOOKS))
def month_label(m):return f'{int(m[:4])}年{int(m[5:7])}月'
def week_id(d):
 y,w,_=_dt.date.fromisoformat(d).isocalendar();return f'{y}-w{w:02d}'
def week_range(wid):
 y,w=int(wid[:4]),int(wid[6:]);a=_dt.date.fromisocalendar(y,w,1);z=_dt.date.fromisocalendar(y,w,7);return a,z
def week_label(wid):
 a,z=week_range(wid);return f'{a.month}月{a.day}日〜{z.month}月{z.day}日'
month_links='<nav class="month-links" aria-label="月ごとに見る">'+''.join(f'<a href="/books/{m}/">{month_label(m)}<small>{sum(1 for b in BOOKS if b["date"][:7]==m)}冊</small></a>' for m in MONTHS)+'</nav>'
TOOLBAR='<div class="toolbar" data-shelf-tools hidden><div class="tabs" aria-label="テーマを絞り込む"><button class="tab" aria-pressed="true" data-filter="all">すべて</button>'+''.join(f'<button class="tab" aria-pressed="false" data-filter="{t['id']}">{H(t['title'])}</button>' for t in TOPICS)+'<span class="tabs__divider" aria-hidden="true"></span><button class="tab" aria-pressed="true" data-region-filter="all">日本と海外</button><button class="tab" aria-pressed="false" data-region-filter="japan">日本</button><button class="tab" aria-pressed="false" data-region-filter="world">海外</button></div><label class="search"><span aria-hidden="true">⌕</span><input type="search" id="search" aria-label="タイトルや日付で本を探す" placeholder="タイトルや日付で探す"></label></div>'
# 本棚ページの案内役：モチとシオがしゃべる（読み上げソフトにも伝える）。JS がないときは出さない
GUIDE=('<div class="shelf-guide" data-shelf-guide hidden><img class="shelf-guide__face" src="/assets/mochi-face.webp" alt="" width="64" height="64" data-guide-face>'
 '<p class="shelf-guide__line" id="shelf-message" role="status"><span data-guide-name>モチ</span>「<span data-guide-text>どれ読む？</span>」</p>'
 '<button type="button" class="shelf-pick" data-shelf-pick>シオのおすすめ</button>'
 '<img class="shelf-guide__peek" src="/assets/mochi-peek.webp" alt="" width="120" height="114"></div>')
def cover_tile(b):
 _USED.append(b)
 return f'''<a class="cover-tile" href="{b['url']}"><span class="cover-tile__img"><img src="/{thumb(b)}" alt="" loading="lazy" width="480" height="640">{'<b class="book__region cover-tile__badge">WORLD</b>' if region(b)=='world' else ''}</span><span class="cover-tile__meta">{H(b['category'])} ・ {len(b['pages'])}ページ</span><span class="cover-tile__title">{H(b['title'])}</span></a>'''
TODAY=[b for b in BOOKS if b['date']==BOOKS[0]['date']]
RECENT=[b for b in BOOKS if b['date']!=BOOKS[0]['date']][:12]
today_html=f'''<section class="today" id="today"><div class="section-head"><h2>{'きょうの本' if True else ''}</h2><span class="count"><time datetime="{BOOKS[0]['date']}">{jdate(BOOKS[0]['date'])}</time></span></div><div class="cover-grid">'''+''.join(cover_tile(b) for b in TODAY)+'</div></section>'
shelf=f'''<section class="shelf" id="shelf"><div class="section-head"><h2>最近の本</h2></div>'''+dated_cards(RECENT,tiles=True)+f'''<div class="home-links"><a href="/books/">すべての本を見る（{len(BOOKS)}冊）→</a><a href="/weeks/{week_id(BOOKS[0]['date'])}/">今週のまとめ →</a><a href="/search/">本をさがす →</a><a href="/sources/">本で参考にした記事を見る →</a></div></section>'''
topics_html='<div class="topic-grid">'+''.join(f'<a class="topic-card" href="/topics/{t['id']}/"><h3>{H(t['title'])}</h3><span>読む →</span></a>' for t in TOPICS)+'</div>'
shell('/',NAME,DESCRIPTION,hero+today_html+shelf+extras_html(BOOKS)+'<section class="home-section"><h2>テーマから探す</h2><p></p>'+topics_html+'</section><section class="about" id="about"><h2>このサイトについて</h2><div><p>毎日のニュースを、小さな本に。</p><div class="home-links"><a href="/about/">このサイトについて →</a><a href="/guide/">初めての方へ →</a><a href="/editorial/">制作・掲載方針 →</a></div></div></section>',kind='CollectionPage',extra=[item_list(TODAY+RECENT,'/')],main_class='')
# Book archive and topic pages.
shell('/books/','本棚','もちとしおのニュース本',intro('ALL BOOKS','本棚')+'<div class="topic-list">'+''.join(f'<a href="/topics/{t["id"]}/">{H(t["title"])}</a>' for t in TOPICS)+''.join(f'<a href="/{r}/">{t}</a>' for r,t,_,_ in REGIONS)+'</div>'+month_links+'<section class="shelf shelf--archive shelf--wood" id="shelf"><div class="section-head"><h2 class="sr-only">本棚</h2><span class="count" id="count">'+str(len(BOOKS))+'冊</span></div>'+TOOLBAR+GUIDE+dated_cards(BOOKS[:LIST_LIMIT])+('<p class="more-by-month">もっと前の本 → '+''.join(f'<a class="text-link" href="/books/{m}/">{month_label(m)}</a> ' for m in MONTHS)+'</p>' if len(BOOKS)>LIST_LIMIT else '')+'</section>',kind='CollectionPage',extra=[item_list(BOOKS[:LIST_LIMIT],'/books/')],crumb=[('ホーム','/'),('本棚','/books/')],wide=True)
for m in MONTHS:
 selected=[b for b in BOOKS if b['date'][:7]==m];path=f'/books/{m}/'
 shell(path,month_label(m)+'の本',month_label(m)+'の、もちとしおのニュース本',intro('MONTHLY / '+str(len(selected))+' BOOKS',month_label(m)+'の本')+month_links+dated_cards(selected)+'<p><a class="text-link" href="/books/">すべての本を見る →</a></p>',kind='CollectionPage',extra=[item_list(selected,path)],crumb=[('ホーム','/'),('本棚','/books/'),(month_label(m),path)],wide=True)
shell('/topics/','テーマから探す','もちとしおのニュース本 テーマ別',intro('TOPICS','テーマから探す')+topics_html,kind='CollectionPage',crumb=[('ホーム','/'),('テーマから探す','/topics/')],wide=True)
for topic,title,lead,sections in [(t['id'],t['title'],t['lead'],t['sections']) for t in TOPICS]:
 allbooks=[b for b in BOOKS if b['topic']==topic];selected=allbooks[:LIST_LIMIT];path=f'/topics/{topic}/'
 body=intro('TOPIC / '+str(len(allbooks))+' BOOKS',H(title))+cards(selected)+'<p><a class="text-link" href="/topics/">ほかのテーマ →</a></p>'
 shell(path,title,f'{title}の、もちとしおのニュース本',body,kind='CollectionPage',extra=[item_list(selected,path)],crumb=[('ホーム','/'),('テーマから探す','/topics/'),(title,path)],wide=True)
# 日本のニュース・海外のニュースの一覧ページ
for r,title,en,lead in REGIONS:
 allbooks=[b for b in BOOKS if region(b)==r];selected=allbooks[:LIST_LIMIT];path=f'/{r}/'
 body=intro(en+' / '+str(len(allbooks))+' BOOK'+('S' if len(allbooks)!=1 else ''),title,lead)+(cards(selected) if selected else '<p>まだありません。</p>')+'<p><a class="text-link" href="/books/">本棚へ →</a></p>'
 shell(path,title,f'{title}の、もちとしおのニュース本',body,kind='CollectionPage',extra=[item_list(selected,path)],crumb=[('ホーム','/'),('本棚','/books/'),(title,path)],wide=True)
# Individual books: real text, source links and citations accompany the images.
for b in BOOKS:
 path=b['url'];topicpath='/topics/'+b['topic']+'/'
 reading=''.join(f'<figure class="reading-page"><img src="/{f}" alt="{H(b["title"])} {n}ページ目" width="1367" height="1823" loading="lazy"><figcaption>{n} / {len(b['pages'])} ページ</figcaption></figure>' for n,f in enumerate(b['pages'],1))
 related=[x for x in BOOKS if x['id']!=b['id'] and x['topic']==b['topic']][:2]
 if not related:related=[x for x in BOOKS if x['id']!=b['id']][:2]
 body=intro(f"NEWS BOOK / {len(b['pages'])} PAGES",H(b['title']),H(b['summary']))+f'''<div class="meta"><span>本の日付：<time datetime="{b['date']}">{b['date'].replace('-','.')}</time></span><a href="{topicpath}">{b['category']}</a><a href="/{region(b)}/">{'海外のニュース' if region(b)=='world' else '日本のニュース'}</a><span>制作・掲載：<a href="/about/">{NAME} 運営者</a></span><span>ページ公開日：<time datetime="{b['webPublished']}">{b['webPublished'].replace('-','.')}</time></span></div>{tag_links(b)}<nav class="toc" aria-label="このページの目次"><strong>目次</strong><ol><li><a href="#read">本を読む</a></li><li><a href="#text">文章で読む</a></li><li><a href="#afterword">あとがき</a></li><li><a href="#sources">参考記事</a></li></ol></nav><section id="read" class="section-anchor"><h2>{len(b['pages'])}ページの本を読む</h2><div class="reading-frame" data-reader><div class="reading-pages" tabindex="0" role="region" aria-label="{H(b['title'])}のページ。左右キーでもページを移動できます">{reading}</div><div class="reading-controls" hidden><button type="button" data-prev aria-label="前のページ">← 前へ</button><span class="reading-counter" aria-live="polite">1 / {len(b['pages'])}</span><button type="button" data-next aria-label="次のページ">次へ →</button></div></div></section><section id="text" class="section-anchor"><h2>文章で読む</h2>{transcript_html(b)}</section><section id="afterword" class="section-anchor"><h2>あとがき</h2><div class="afterword"><blockquote>{H(b['afterword'])}</blockquote><div class="character-line">モチ「{H(b['mochi'])}」</div></div></section><section id="sources" class="section-anchor"><h2>参考にした記事・関連する発表</h2>{sources_html(b)}<p><a class="text-link" href="/editorial/">制作・掲載方針を見る →</a></p></section>{pager_html(b)}<div class="actions"><button class="action action--secondary" type="button" data-share hidden>この本のURLをコピー</button><a class="action action--secondary" href="/books/">本棚に戻る</a></div><p class="share-status" aria-live="polite"></p><section><h2>{'同じテーマの本' if b['topic']=='ai' else 'ほかの本'}</h2>{cards(related)}</section>'''
 article={'@type':'BlogPosting','@id':url(path+'#article'),'headline':b['title'],'description':b['summary'],'url':url(path),'mainEntityOfPage':{'@id':url(path+'#webpage')},'image':[url('/'+og_image(b)),url('/'+b['pages'][0])],'datePublished':b['webPublished'],'dateModified':b.get('modified') or b['webPublished'],'author':{'@id':url('/#publisher')},'publisher':{'@id':url('/#publisher')},'inLanguage':'ja','articleSection':b['category'],'articleBody':'\n'.join(b['body']+[b['afterword']]),'citation':[b['source']['url']]+([b['primary']['url']] if b.get('primary') else [])}
 shell(path,b['title'],b['description'],body,extra=[article],crumb=[('ホーム','/'),('本棚','/books/'),(b['title'],path)],image='/'+og_image(b))
# Site and editorial information grounded in the supplied work, without invented credentials.
shell('/about/','このサイトについて','もちとしおのニュース本棚について',intro('ABOUT','このサイトについて')+'''<div class="prose"><img class="about-character" src="/assets/icon.webp" alt="しろいねこのモチと、ちいさいとりのシオ" width="1254" height="1254" loading="lazy"><h2>どんなサイト</h2><p>毎日のニュースを、もちとしおが小さな本にしています。1冊は3〜10ページ。本と同じ中身を、文字でものせています。</p><h2>本に出てくるふたり</h2><p>しろいねこのモチと、ちいさいとりのシオ。<a class="text-link" href="/characters/">ふたりのこと →</a></p><h2>運営・連絡先</h2><p>もちとしおのニュース本棚 運営者<br>感想やまちがいのご指摘は、<a href="/contact/">お問い合わせ</a>から。</p><p>元記事の報道機関・会社とは関係ありません。</p><div class="home-links"><a href="/guide/">使い方 →</a><a href="/editorial/">制作・掲載方針 →</a><a href="/sources/">参考記事一覧 →</a></div></div>''',kind='AboutPage',crumb=[('ホーム','/'),('このサイトについて','/about/')])
shell('/guide/','使い方','もちとしおのニュース本棚の使い方',intro('READING GUIDE','使い方')+'''<ol class="step-list"><li><h2>本をえらぶ</h2><p><a class="text-link" href="/books/">本棚</a>は新しい順。<a class="text-link" href="/topics/">テーマ</a>、<a class="text-link" href="/tags/">話題</a>、<a class="text-link" href="/weeks/">週のまとめ</a>、<a class="text-link" href="/search/">さがす</a>からも。</p></li><li><h2>読む</h2><p>本はスワイプか、前・次のボタンでめくります。パソコンは左右キーでも。文字が小さいときは「文章で読む」へ。</p></li><li><h2>ニュースと感想</h2><p>「その一」と、そのあとのくわしいページは元の記事にあること。最後の「その」は、シオが読んで思ったこと。</p></li><li><h2>元の記事へ</h2><p>本のページの下のほうに、参考にした記事のリンクがあります。</p></li></ol>''',crumb=[('ホーム','/'),('使い方','/guide/')])
shell('/editorial/','制作・掲載方針','もちとしおのニュース本棚の制作・掲載方針',intro('EDITORIAL POLICY','制作・掲載方針')+'''<div class="prose"><h2>ニュースと感想は分けています</h2><p>「その一」と、そのあとのくわしいページは、元の記事にあることだけ。最後の「その」は、シオが読んで思ったことです。</p><h2>出典</h2><p>本のページに、参考にした記事の名前とリンクをのせています。本文を確かめられなかった記事は、そう書いています。</p><h2>日付</h2><p>「本の日付」は本を作った日、「ページ公開日」はこのサイトにのせた日です。ニュースが起きた日とはちがうことがあります。</p><h2>お金や法律の話</h2><p>投資や手続きのアドバイスではありません。くわしくは発表元を見てください。</p><h2>まちがいを見つけたら</h2><p><a href="/contact/">お問い合わせ</a>から、本のタイトルと場所を教えてください。確かめて直します。</p><h2>元の記事について</h2><p>元の記事の著作権は、それぞれの権利者のものです。全文はのせていません。</p></div>''',crumb=[('ホーム','/'),('制作・掲載方針','/editorial/')])
body=intro('SOURCES','参考記事一覧')
for b in BOOKS[:LIST_LIMIT]:body+=f'<section><h2><a class="text-link" href="{b["url"]}">{H(b["title"])}</a></h2><p class="meta">本の日付：{b["date"].replace("-",".")}</p>{sources_html(b)}</section>'
shell('/sources/','参考記事一覧','もちとしおのニュース本で参考にした記事',body,kind='CollectionPage',crumb=[('ホーム','/'),('参考記事一覧','/sources/')])
# Preserve forms and legal copy, with shared navigation and new canonical paths.
for filename,title,kind in [('contact.html','お問い合わせ','ContactPage'),('privacy.html','プライバシーポリシー','WebPage'),('thanks.html','送信完了','WebPage')]:
 raw=(ROOT/'templates'/filename).read_text();match=re.search(r'<main class="page">(.*?)</main>',raw,re.S);body=match.group(1)
 body=re.sub(r'<div class="breadcrumb">.*?</div>','',body,count=1,flags=re.S)
 body=body.replace('https://mochi-shio-news.satinyvenus.chatgpt.site',BASE).replace('/contact.html','/contact/').replace('/privacy.html','/privacy/').replace('/thanks.html','/thanks/').replace('/#shelf','/books/')
 path='/'+filename.replace('.html','')+'/'
 desc={'contact.html':'本の感想や掲載内容へのご連絡、制作のご相談を受け付けています。','privacy.html':'個人情報とお問い合わせフォームでお預かりする情報の取り扱いについて。','thanks.html':'お問い合わせを受け付けました。'}[filename]
 # Forms need only the small existing form styles; the shared chrome remains in site.css.
 shell(path,title,desc,'<link rel="stylesheet" href="/forms.css">'+body,kind=kind,crumb=[('ホーム','/'),(title,path)],noindex=filename=='thanks.html',main_class='page')
 # Existing external links to .html continue to work; canonical points at the new directory URL.
 legacy=OUT/filename;legacy.write_text((OUT/path.strip('/')/'index.html').read_text())
shell('/404.html','ページが見つかりません','ページが見つかりません',intro('PAGE NOT FOUND','この本は、見つかりませんでした。')+'<div class="actions"><a class="action" href="/books/">本棚へ →</a></div>',noindex=True)
# ---- 話題のタグページ（2冊以上の本があるタグ）
for t in TAG_PAGES:
 allbooks=[b for b in BOOKS if t in book_tags(b)];selected=allbooks[:LIST_LIMIT];path=f'/tags/{t}/';name=TAGS[t]
 shell(path,f'#{name}',f'「{name}」の、もちとしおのニュース本',intro('TAG / '+str(len(allbooks))+' BOOKS',f'#{H(name)}')+dated_cards(selected,tiles=True)+'<p><a class="text-link" href="/tags/">ほかの話題 →</a></p>',kind='CollectionPage',extra=[item_list(selected,path)],crumb=[('ホーム','/'),('話題から探す','/tags/'),(name,path)],wide=True)
if TAG_PAGES:
 chips=''.join(f'<a class="tag-chip tag-chip--big" href="/tags/{t}/">#{H(TAGS[t])}<small>{TAG_COUNT[t]}冊</small></a>' for t in sorted(TAG_PAGES,key=lambda x:-TAG_COUNT[x]))
 shell('/tags/','話題から探す','もちとしおのニュース本 話題別',intro('TAGS','話題から探す')+f'<div class="tag-chips tag-chips--cloud">{chips}</div>',kind='CollectionPage',crumb=[('ホーム','/'),('話題から探す','/tags/')],wide=True)
# ---- 週ごとのまとめページ
WEEKS=list(dict.fromkeys(week_id(b['date']) for b in BOOKS))
for i,wid in enumerate(WEEKS):
 selected=[b for b in BOOKS if week_id(b['date'])==wid];path=f'/weeks/{wid}/';a,z=week_range(wid)
 by_topic={}
 for b in selected:by_topic[b['category']]=by_topic.get(b['category'],0)+1
 n_world=sum(1 for b in selected if region(b)=='world')
 summary='、'.join(f'{k} {v}冊' for k,v in sorted(by_topic.items(),key=lambda x:-x[1]))
 lead=f'{len(selected)}冊（日本{len(selected)-n_world}・海外{n_world}）'
 titles='<ul class="week-titles">'+''.join(f'<li><a href="{b["url"]}">{H(b["title"])}</a><span>{H(b["summary"])}</span></li>' for b in selected)+'</ul>'
 nav='<nav class="pager" aria-label="前後の週">'+(f'<a class="pager__item pager__item--prev" href="/weeks/{WEEKS[i+1]}/"><small>← 前の週</small><span>{week_label(WEEKS[i+1])}</span></a>' if i+1<len(WEEKS) else '<span class="pager__item pager__item--empty"></span>')+(f'<a class="pager__item pager__item--next" href="/weeks/{WEEKS[i-1]}/"><small>次の週 →</small><span>{week_label(WEEKS[i-1])}</span></a>' if i>0 else '<span class="pager__item pager__item--empty"></span>')+'</nav>'
 shell(path,f'{week_label(wid)}の本',f'{a.year}年{week_label(wid)}の、もちとしおのニュース本',intro('WEEKLY / '+str(len(selected))+' BOOKS',f'{week_label(wid)}の本',lead)+'<section><h2>この週の本</h2>'+titles+'</section><section><h2>表紙</h2>'+dated_cards(selected,tiles=True)+'</section>'+nav,kind='CollectionPage',extra=[item_list(selected,path)],crumb=[('ホーム','/'),('週のまとめ','/weeks/'),(week_label(wid),path)],wide=True)
shell('/weeks/','週のまとめ','もちとしおのニュース本 週ごと',intro('WEEKLY','週のまとめ')+'<ul class="week-list">'+''.join(f'<li><a href="/weeks/{w}/">{week_label(w)}<small>{sum(1 for b in BOOKS if week_id(b["date"])==w)}冊</small></a></li>' for w in WEEKS)+'</ul>',kind='CollectionPage',crumb=[('ホーム','/'),('週のまとめ','/weeks/')],wide=True)
# ---- キャラクター紹介（公式サイト「もちとしお」の設定にもとづく）
shell('/characters/','モチとシオ','しろいねこのモチと、ちいさいとりのシオ',intro('CHARACTERS','モチとシオ')+f'''<div class="prose"><img class="about-character" src="/assets/icon.webp" alt="赤いパーカーを着たしろいねこのモチと、ちいさいとりのシオ" width="1254" height="1254" loading="lazy">
<section class="character"><h2>モチ</h2><dl class="character__facts"><dt>どんな子</dt><dd>しろいねこ</dd><dt>せいかく</dt><dd>めんどくさがり。なんでも明日に回しがち</dd><dt>ふくそう</dt><dd>お気に入りの赤いパーカー</dd><dt>くちぐせ</dt><dd>「あと5分だけ…」</dd></dl><p>本では、あとがきでひとこと。</p></section>
<section class="character"><h2>シオ</h2><dl class="character__facts"><dt>どんな子</dt><dd>ちいさいとり</dd><dt>せいかく</dt><dd>冷静。いつもモチをしずかに見守っている</dd><dt>とくぎ</dt><dd>的確なひとこと</dd><dt>くちぐせ</dt><dd>「…」</dd></dl><p>本では、最後の「その」で、読んで思ったことを話す。</p></section>
<h2>ふたりの関係</h2><p>モチとシオは、一緒に暮らす同居人のような関係です。モチが行動する側、シオがそれを静かに見守る側。けんかをするわけでも、いつも仲良しこよしというわけでもない、少し距離感のある関係です。</p>
<div class="home-links"><a href="/books/">ニュースの本を読む →</a><a href="/about/">このサイトについて →</a></div></div>''',crumb=[('ホーム','/'),('モチとシオ','/characters/')])
# ---- サイト内検索（全部の本が対象。ページは検索結果用なので noindex）
SEARCH=[{'t':b['title'],'u':b['url'],'d':b['date'],'c':b['category'],'r':region(b),'s':b['summary'],'g':[TAGS[t] for t in book_tags(b)],'n':b['source']['name'],'i':'/'+thumb(b)} for b in BOOKS]
shell('/search/','本をさがす','もちとしおのニュース本をさがす',intro('SEARCH','本をさがす')+'''<form class="site-search" role="search" action="/search/" method="get"><label class="search"><span aria-hidden="true">⌕</span><input type="search" name="q" id="site-search-q" aria-label="さがす言葉" placeholder="例：AI、アップル、物価"></label></form><p class="search-status" id="search-status" aria-live="polite"></p><div class="search-results" id="search-results"></div><noscript><p><a class="text-link" href="/books/">本棚へ →</a></p></noscript><script src="/search.js" defer></script>''',crumb=[('ホーム','/'),('本をさがす','/search/')],noindex=True)
(OUT/'search-index.json').write_text(json.dumps(SEARCH,ensure_ascii=False,separators=(',',':')))
# Machine-readable discovery documents contain only canonical, indexable content pages.
ns='http://www.sitemaps.org/schemas/sitemap/0.9';ET.register_namespace('',ns)
root=ET.Element('{'+ns+'}urlset')
BOOK_DATES={b['url']:(b.get('modified') or b['webPublished']) for b in BOOKS}
MONTH_DATES={f'/books/{m}/':max(b.get('modified') or b['webPublished'] for b in BOOKS if b['date'][:7]==m) for m in MONTHS}
FIXED_PAGES=('/about/','/guide/','/editorial/','/contact/','/privacy/')
for path in INDEXABLE:
 entry=ET.SubElement(root,'{'+ns+'}url');ET.SubElement(entry,'{'+ns+'}loc').text=url(path)
 if path in FIXED_PAGES:continue
 ET.SubElement(entry,'{'+ns+'}lastmod').text=BOOK_DATES.get(path) or MONTH_DATES.get(path) or UPDATED
(OUT/'sitemap.xml').write_bytes(ET.tostring(root,encoding='utf-8',xml_declaration=True))
(OUT/'robots.txt').write_text('User-agent: *\nAllow: /\n\nSitemap: '+url('/sitemap.xml')+'\n')
# Atom feed: web publication date is distinct from the date printed on each book.
ns='http://www.w3.org/2005/Atom';ET.register_namespace('',ns)
feed=ET.Element('{'+ns+'}feed')
def atom(parent,k,value):ET.SubElement(parent,'{'+ns+'}'+k).text=value
atom(feed,'id',url('/'));atom(feed,'title',NAME);atom(feed,'updated',UPDATED+'T00:00:00+09:00')
ET.SubElement(feed,'{'+ns+'}link',{'href':url('/feed.xml'),'rel':'self'});ET.SubElement(feed,'{'+ns+'}link',{'href':url('/')})
for b in BOOKS[:FEED_LIMIT]:
 e=ET.SubElement(feed,'{'+ns+'}entry');atom(e,'id',url(b['url']));atom(e,'title',b['title']);atom(e,'updated',b['webPublished']+'T00:00:00+09:00');atom(e,'summary',b['summary']);a=ET.SubElement(e,'{'+ns+'}author');atom(a,'name',NAME+' 運営者');ET.SubElement(e,'{'+ns+'}link',{'href':url(b['url'])})
(OUT/'feed.xml').write_bytes(ET.tostring(feed,encoding='utf-8',xml_declaration=True))
# AI 向けの案内（llms.txt）：サイトの説明と、主なページ・新しい本
llms=[f'# {NAME}','',f'> {DESCRIPTION}','',
 'ニュース記事をもとに、キャラクター「もちとしお」が3〜10ページの小さな本にまとめたサイトです。各本のページには、本の画像と同じ内容の文章、あとがき、参考にした記事（出典）へのリンクがあります。「その一」と、くわしい説明のページは元の記事にもとづく内容、最後の「その」は読んで考えた感想です。',
 '','## 主なページ',f'- [本棚（新しい本の一覧）]({url("/books/")})',f'- [日本のニュース]({url("/japan/")})',f'- [海外のニュース]({url("/world/")})',f'- [テーマから探す]({url("/topics/")})',f'- [参考記事一覧]({url("/sources/")})',f'- [このサイトについて]({url("/about/")})',f'- [制作・掲載方針]({url("/editorial/")})',f'- [キャラクター紹介（モチとシオ）]({url("/characters/")})',f'- [週のまとめ]({url("/weeks/")})',f'- [話題から探す]({url("/tags/")})',
 '','## 月ごとの本']+[f'- [{month_label(m)}の本]({url(f"/books/{m}/")})' for m in MONTHS]+['','## 新しい本']+[f'- [{b["title"]}]({url(b["url"])})：{b["summary"]}（{b["date"]}、出典：{b["source"]["name"]}）' for b in BOOKS[:30]]+['','## そのほか',f'- [RSS（Atom）]({url("/feed.xml")})',f'- [サイトマップ]({url("/sitemap.xml")})','']
(OUT/'llms.txt').write_text('\n'.join(llms))
(OUT/'books.json').write_text(json.dumps(BOOKS,ensure_ascii=False,indent=2)+'\n')
# Cloudflare Pages understands this file; the physical legacy pages also work on Sites.
(OUT/'_redirects').write_text('/contact.html /contact/ 301\n/privacy.html /privacy/ 301\n/thanks.html /thanks/ 301\n')
print(f'Built {len(INDEXABLE)} canonical indexable pages, {len(BOOKS)} book pages, sitemap, robots and feed for {BASE}')
