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
NAME=CONFIG['name'];DESCRIPTION=CONFIG['description'];BOOKS=json.loads((ROOT/'content/books.json').read_text())
PUBLISHED='2026-10-15'
if OUT.exists():shutil.rmtree(OUT)
shutil.copytree(PUBLIC,OUT)
INDEXABLE=[]
def H(v):return esc(str(v),quote=True)
def url(path):return BASE+path
def write(path,text):
 target=OUT/('index.html' if path=='/' else path.strip('/')+'/index.html' if path.endswith('/') else path.lstrip('/'))
 target.parent.mkdir(parents=True,exist_ok=True);target.write_text(text)
def ld(data):return '<script type="application/ld+json">'+json.dumps(data,ensure_ascii=False).replace('<','\\u003c')+'</script>'
def organization():return {'@type':'Organization','@id':url('/#publisher'),'name':NAME+' 運営者','url':url('/about/')}
def breadcrumbs(items):return {'@type':'BreadcrumbList','@id':url(items[-1][1]+'#breadcrumb'),'itemListElement':[{'@type':'ListItem','position':i+1,'name':name,'item':url(path)} for i,(name,path) in enumerate(items)]}
def header(path):return header_html(path)
def footer():return footer_html()
def shell(path,title,description,body,*,kind='WebPage',extra=None,crumb=None,image=None,noindex=False,wide=False,main_class=None):
 if not noindex:INDEXABLE.append(path)
 image=image or '/assets/book-3-1.webp'
 page={'@type':kind,'@id':url(path+'#webpage'),'url':url(path),'name':title,'description':description,'inLanguage':'ja','isPartOf':{'@id':url('/#website')}}
 graph=[organization(),{'@type':'WebSite','@id':url('/#website'),'url':url('/'),'name':NAME,'description':DESCRIPTION,'inLanguage':'ja','publisher':{'@id':url('/#publisher')}},page]
 if crumb:
  graph.append(breadcrumbs(crumb));page['breadcrumb']={'@id':url(path+'#breadcrumb')}
 if extra:graph.extend(extra)
 fulltitle=title if title==NAME else title+'｜'+NAME
 head=f'''<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{H(fulltitle)}</title><meta name="description" content="{H(description)}"><link rel="canonical" href="{H(url(path))}"><meta name="robots" content="{'noindex,follow' if noindex else 'index,follow,max-image-preview:large'}"><meta property="og:locale" content="ja_JP"><meta property="og:type" content="{'article' if kind=='Article' or path.startswith('/books/') and path!='/books/' else 'website'}"><meta property="og:site_name" content="{H(NAME)}"><meta property="og:title" content="{H(title)}"><meta property="og:description" content="{H(description)}"><meta property="og:url" content="{H(url(path))}"><meta property="og:image" content="{H(url(image))}"><meta property="og:image:alt" content="もちとしおのニュース本の表紙"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{H(title)}"><meta name="twitter:description" content="{H(description)}"><meta name="twitter:image" content="{H(url(image))}"><link rel="icon" href="/assets/icon.png" type="image/png"><link rel="apple-touch-icon" href="/assets/icon.png"><link rel="alternate" type="application/atom+xml" title="もちとしおの新しい本" href="/feed.xml"><link rel="stylesheet" href="/site.css"><link rel="stylesheet" href="/experience.css"><link rel="stylesheet" href="/typography.css"><link rel="stylesheet" href="/warm.css"><script src="/site.js" defer></script>'''
 bc=''
 if crumb:
  bc='<nav class="breadcrumb" aria-label="パンくずリスト">'+'<span aria-hidden="true">/</span>'.join(f'<span aria-current="page">{H(n)}</span>' if i==len(crumb)-1 else f'<a href="{p}">{H(n)}</a>' for i,(n,p) in enumerate(crumb))+'</nav>'
 cls=main_class if main_class is not None else 'content'+(' content--wide' if wide else '')
 write(path,f'<!doctype html><html lang="ja"><head>{head}{ld({"@context":"https://schema.org","@graph":graph})}</head><body id="top" class="{'is-home' if path=='/' else 'is-inner'}"><div class="wrap">{header(path)}{bc}<main id="main" class="{cls}">{body}</main>{footer()}</div>{dialogs_html(BOOKS)}</body></html>')
def card(b):
 return f'''<article class="book" data-book-id="{b['id']}" data-topic="{b['topic']}" data-search="{H(b['title']+' '+b['date']+' '+b['date'].replace('-','.')+' '+b['category'])}"><a class="book__cover" href="{b['url']}" tabindex="-1" aria-hidden="true"><img src="/{b['pages'][0]}" alt="" loading="lazy" width="1367" height="1823"></a><div class="book__meta"><time datetime="{b['date']}">{b['date'].replace('-','. ')}</time><span>{b['category']}</span></div><h3 class="book__title"><a href="{b['url']}">{H(b['title'])}</a></h3><div class="book__actions"><a class="book__read" href="{b['url']}">この本を読む ↗</a><button type="button" class="book__preview" data-preview="{b['id']}" hidden>立ち読み ＋</button></div></article>'''
def cards(books):return '<div class="books">'+''.join(card(b) for b in books)+'</div>'
def item_list(books,identifier):return {'@type':'ItemList','@id':url(identifier+'#list'),'numberOfItems':len(books),'itemListElement':[{'@type':'ListItem','position':i+1,'url':url(b['url']),'name':b['title']} for i,b in enumerate(books)]}
def intro(eyebrow,title,lead):return f'<div class="eyebrow">{eyebrow}</div><h1>{title}</h1><p class="lead">{lead}</p>'
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
shelf=f'''<section class="shelf" id="shelf"><div class="section-head"><h2><small>THE BOOKSHELF</small>ニュースの本棚</h2><span class="count" id="count">全{len(BOOKS)}冊 / 各4ページ</span></div><div class="toolbar" data-shelf-tools hidden><div class="tabs" aria-label="テーマを絞り込む"><button class="tab" aria-pressed="true" data-filter="all">すべて</button><button class="tab" aria-pressed="false" data-filter="ai">AI・テクノロジー</button><button class="tab" aria-pressed="false" data-filter="money">お金・くらし</button></div><label class="search"><span aria-hidden="true">⌕</span><input type="search" id="search" aria-label="タイトルや日付で本を探す" placeholder="タイトルや日付で探す"></label></div>'''+cards(BOOKS)+'''<p class="shelf-message" id="shelf-message" aria-live="polite"></p><div class="home-links"><a href="/books/">すべての本を見る →</a><a href="/sources/">本で参考にした記事を見る →</a></div></section>'''
topics_html='''<div class="topic-grid"><a class="topic-card" href="/topics/ai/"><span class="tag">AI & TECHNOLOGY / 4 BOOKS</span><h3>AI・テクノロジー</h3><p>学校の仕事、アプリ、音楽、声。身近になったAIのニュースを集めました。</p><span>このテーマを読む →</span></a><a class="topic-card" href="/topics/money/"><span class="tag">MONEY & LIFE / 1 BOOK</span><h3>お金・くらし</h3><p>お金にまつわる出来事を、生活や仕組みの側から読みます。</p><span>このテーマを読む →</span></a></div>'''
shell('/',NAME,DESCRIPTION,hero+shelf+extras_html(BOOKS)+'<section class="home-section"><h2>テーマから探す</h2><p></p>'+topics_html+'</section><section class="about" id="about"><h2><small>ABOUT THIS BOOKSHELF</small>このサイトについて</h2><div><p>ニュースをもとに作った4ページの本を掲載しています。<br>各本のページに、本文・あとがき・参考記事をまとめています。</p><div class="home-links"><a href="/about/">このサイトについて →</a><a href="/guide/">初めての方へ →</a><a href="/editorial/">制作・掲載方針 →</a></div></div></section>',kind='CollectionPage',extra=[item_list(BOOKS,'/')],main_class='')
# Book archive and topic pages.
shell('/books/','ニュース本一覧｜AI・お金・くらしの4ページの本','もちとしおのニュース本を日付順に掲載。AI・テクノロジー、お金・くらしの話題を、画像と本文、あとがき、参考記事から読めます。',intro('ALL BOOKS','ニュース本一覧','公開中の5冊を、新しい日付から並べています。同じ日の本も、それぞれのテーマから選べます。')+'<div class="topic-list"><a href="/topics/ai/">AI・テクノロジー</a><a href="/topics/money/">お金・くらし</a></div>'+cards(BOOKS),kind='CollectionPage',extra=[item_list(BOOKS,'/books/')],crumb=[('ホーム','/'),('本棚','/books/')],wide=True)
shell('/topics/','テーマから探す｜もちとしおのニュース本','AI・テクノロジーとお金・くらし。テーマから探す、もちとしおの4ページのニュース本を選べます。',intro('TOPICS','テーマから探す','掲載している本をテーマ別にまとめています。')+topics_html,kind='CollectionPage',crumb=[('ホーム','/'),('テーマから探す','/topics/')],wide=True)
for topic,title,lead,sections in [
 ('ai','AI・テクノロジー','AIが身近な場所で使われるようになると、便利さだけでなく、作り方や情報の扱い方も気になります。この本棚では、学校・アプリ・音楽・声のニュースを紹介しています。',[('仕事を手伝うAI','先生の書類仕事と、自分用のアプリづくり。AIで何が変わるのか、身近な作業から読みます。'),('作る人・使われる人のこと','AIで作った曲だと分かる表示や、声を使う前の許諾。使う側だけではない立場にも目を向けた本です。')]),
 ('money','お金・くらし','お金のニュースを、数字だけでなく「何が起きたか」「どんな仕組みだったか」から読みます。現在は、SBI証券のFXのシステム障害を取り上げた一冊を掲載しています。',[('システムのミスを、身近な言葉で','担保の株の評価額が反映されなかったことで、何が起きたのか。本の本文と、読んで気になったことを分けて確認できます。'),('個別の対応は、発表元で確認を','この本棚はニュースを読むための制作物です。投資商品の推奨や個別口座の案内は行っていません。対象となった方は、詳細ページに掲載した公式発表をご確認ください。')])]:
 selected=[b for b in BOOKS if b['topic']==topic];path=f'/topics/{topic}/'
 body=intro('TOPIC / '+str(len(selected))+' BOOKS',title+'のニュース本',lead)+''.join('<section><h2>'+h+'</h2><p>'+p+'</p></section>' for h,p in sections)+cards(selected)+'<p><a class="text-link" href="/topics/">ほかのテーマを見る →</a></p>'
 shell(path,title+'をやさしく読む｜ニュース本まとめ',lead,body,kind='CollectionPage',extra=[item_list(selected,path)],crumb=[('ホーム','/'),('テーマから探す','/topics/'),(title,path)],wide=True)
# Individual books: real text, source links and citations accompany the images.
for b in BOOKS:
 path=b['url'];topicpath='/topics/'+b['topic']+'/'
 reading=''.join(f'<figure class="reading-page"><img src="/{f}" alt="{H(b["title"])} {n}ページ目" width="1367" height="1823" loading="lazy"><figcaption>{n} / 4 ページ</figcaption></figure>' for n,f in enumerate(b['pages'],1))
 related=[x for x in BOOKS if x['id']!=b['id'] and x['topic']==b['topic']][:2]
 if not related:related=[x for x in BOOKS if x['id']!=b['id']][:2]
 body=intro('NEWS BOOK / 4 PAGES',H(b['title']),H(b['summary']))+f'''<div class="meta"><span>本の日付：<time datetime="{b['date']}">{b['date'].replace('-','.')}</time></span><a href="{topicpath}">{b['category']}</a><span>制作・掲載：<a href="/about/">{NAME} 運営者</a></span><span>ページ公開日：<time datetime="2026-10-15">2026.10.15</time></span></div><nav class="toc" aria-label="このページの目次"><strong>この一冊の中身</strong><ol><li><a href="#read">本を読む</a></li><li><a href="#text">文章で読む</a></li><li><a href="#afterword">あとがき</a></li><li><a href="#sources">参考記事</a></li></ol></nav><section id="read" class="section-anchor"><h2>4ページの本を読む</h2><div class="reading-frame" data-reader tabindex="0" aria-label="{H(b['title'])}のページ。左右キーでもページを移動できます"><div class="reading-pages">{reading}</div><div class="reading-controls" hidden><button type="button" data-prev aria-label="前のページ">← 前へ</button><span class="reading-counter" aria-live="polite">1 / 4</span><button type="button" data-next aria-label="次のページ">次へ →</button></div></div><p class="reader-note">横にスワイプしてページを送れます。下には文章でも同じ内容を掲載しています。</p></section><section id="text" class="section-anchor"><h2>文章で読む</h2><p class="hint">本に書かれた内容を、読みやすい文字で掲載しています。内容は本の日付時点のものです。</p><section class="transcript"><h3>その一 — ニュースのお話</h3><p>{H(b['body'][0])}</p></section><section class="transcript"><h3>その二 — 読んで考えたこと</h3><p>{H(b['body'][1])}</p></section></section><section id="afterword" class="section-anchor"><h2>あとがき</h2><div class="afterword"><span class="transcript__label">本の最後に、ひとこと。</span><blockquote>{H(b['afterword'])}</blockquote><div class="character-line">モチ「{H(b['mochi'])}」</div></div></section><section id="sources" class="section-anchor"><h2>参考にした記事・関連する発表</h2><p>本の最後に記載された参考記事です。本文中の出来事と、当サイトで読んで考えたことは区別して掲載しています。</p>{sources_html(b)}<p><a class="text-link" href="/editorial/">制作・掲載方針を見る →</a></p></section><div class="actions"><button class="action action--secondary" type="button" data-share hidden>この本のURLをコピー</button><a class="action action--secondary" href="/books/">本棚に戻る</a></div><p class="share-status" aria-live="polite"></p><section><h2>{'同じテーマの本' if b['topic']=='ai' else 'あわせて読みたい本'}</h2>{cards(related)}</section>'''
 article={'@type':'BlogPosting','@id':url(path+'#article'),'headline':b['title'],'description':b['summary'],'url':url(path),'mainEntityOfPage':{'@id':url(path+'#webpage')},'image':[url('/'+b['pages'][0])],'datePublished':b['webPublished'],'author':{'@id':url('/#publisher')},'publisher':{'@id':url('/#publisher')},'inLanguage':'ja','articleSection':b['category'],'articleBody':'\n'.join(b['body']+[b['afterword']]),'citation':[b['source']['url']]+([b['primary']['url']] if b.get('primary') else [])}
 shell(path,b['title'],b['description'],body,extra=[article],crumb=[('ホーム','/'),('本棚','/books/'),(b['title'],path)],image='/'+b['pages'][0])
# Site and editorial information grounded in the supplied work, without invented credentials.
shell('/about/','もちとしおについて｜毎日のニュースを小さな本に','もちとしおのニュース本棚は、毎日のニュースを4ページの本にまとめた作品を集めるサイトです。掲載内容と運営窓口を紹介します。',intro('ABOUT','もちとしおについて','毎日のニュースを4ページの本にまとめています。制作した本を掲載するためのサイトです。')+'''<div class="prose"><img class="about-character" src="/assets/icon.webp" alt="白い猫と灰色の鳥、もちとしお" width="1254" height="1254" loading="lazy"><h2>掲載している内容</h2><p>このサイトでは、毎日のニュースをもとに制作した「もちとしお」の本を掲載しています。表紙、ニュースのお話、読んで考えたこと、あとがきの4ページが一冊です。</p><h2>画像でも、文章でも</h2><p>本の見た目を楽しみたいときは、4ページの画像を。文字で読みたいときは、それぞれの本の「文章で読む」をご利用ください。参考にした記事へのリンクも、本のページにまとめています。</p><h2>もちとしおがいる本棚</h2><p>本には、赤い服を着た白い猫と、小さな灰色の鳥が登場します。ニュースのお話のあとには、モチのひとことも。</p><h2>制作・掲載と連絡先</h2><p>掲載：もちとしおのニュース本棚 運営者<br>本の感想、掲載内容へのご指摘、制作のご相談は、<a href="/contact/">お問い合わせフォーム</a>へお寄せください。</p><p>元記事の報道機関・企業と、当サイトの運営者は別です。当サイトは各媒体の公式サイトではありません。</p><div class="home-links"><a href="/guide/">本棚の楽しみ方 →</a><a href="/editorial/">制作・掲載方針 →</a><a href="/sources/">参考記事一覧 →</a></div></div>''',kind='AboutPage',crumb=[('ホーム','/'),('このサイトについて','/about/')])
shell('/guide/','本棚の楽しみ方｜ニュース本の読み方と探し方','もちとしおのニュース本棚の使い方。日付やテーマから本を選び、4ページの画像や本文を読み、元のニュース記事を確認できます。',intro('READING GUIDE','サイトの使い方','本の探し方と、ページの操作方法をまとめています。')+'''<ol class="step-list"><li><h2>日付か、気になるテーマで選ぶ</h2><p><a class="text-link" href="/books/">すべての本</a>は、新しい日付から並んでいます。<a class="text-link" href="/topics/">テーマから探す</a>では、AI・テクノロジーと、お金・くらしに分けて探せます。トップページでは、タイトルや日付での絞り込みも使えます。</p></li><li><h2>表紙やタイトルを押して、本のページへ</h2><p>各ページには、本の紹介、画像、本文、あとがき、参考記事を掲載しています。ページ上の目次から、読みたい場所へ移動できます。</p></li><li><h2>画像か、文章で読む</h2><p>「4ページの本を読む」では、横へのスワイプや前後のボタンでページを送れます。パソコンでは読書画面にフォーカスした状態で、左右キーでも操作できます。文字が小さいときは、下の「文章で読む」をご利用ください。</p></li><li><h2>ニュースと感想を分けて読む</h2><p>「その一」は出来事の紹介、「その二」は読んで考えたことです。本の日付と記事の公開日が異なる場合があります。最新の状況を知りたいときは、掲載元の情報もご確認ください。</p></li><li><h2>気になったら、元記事へ</h2><p>各本の参考記事から掲載元へ移動できます。ほかの本を続けて読みたい場合は、ページ末尾の関連する本へ。URLのコピーボタンから、本のページを共有することもできます。</p></li></ol><p><a class="text-link" href="/books/">最初の一冊を選ぶ →</a></p>''',crumb=[('ホーム','/'),('本棚の楽しみ方','/guide/')])
shell('/editorial/','制作・掲載方針｜出典・日付・訂正について','もちとしおのニュース本棚の制作・掲載方針。ニュースと感想の区別、出典の掲載、日付の扱い、訂正の連絡先について説明します。',intro('EDITORIAL POLICY','ニュースと、<br>読んで考えたことを分けて。','本を読むときに、何が元のニュースで、何がこの本の感想なのかが分かるように掲載します。')+'''<div class="prose"><h2>本の構成</h2><p>一冊は4ページです。表紙に日付と題名、本文の「その一」に出来事の紹介、「その二」に読んで考えたことを掲載しています。最後のページには、あとがきと参考にした記事を記載しています。</p><h2>出典をたどれるようにする</h2><p>本に記載された媒体名と記事名を、各本のページにも掲載します。対応するURLを確認できたものはリンクを付け、公式発表を追加するときは元の参考記事と分けて表示します。取得できていない記事本文を、確認済みとは扱いません。</p><h2>本の日付と、ページの公開日</h2><p>「本の日付」は表紙に記載された日付です。「ページ公開日」はその本の詳細ページをこのサイトで公開した日付です。どちらも、出来事が実際に起きた日と同じとは限りません。過去の本は、制作時点の内容としてお読みください。</p><h2>画像と文章について</h2><p>「文章で読む」は、掲載された本の本文を文字にしたものです。紙面上の改行や空白は読みやすく整えています。本の感想やキャラクターの発言を、元記事の引用や発表元の見解として扱わないでください。</p><h2>法律・金融などの話題について</h2><p>当サイトはニュースをもとにした制作物を読む場所です。法律上の判断、投資判断、個別の手続きの案内を提供するものではありません。必要な場合は、発表元や関係機関の案内をご確認ください。</p><h2>訂正・ご指摘の窓口</h2><p>内容の間違いや出典リンクについてお気づきの点があれば、<a href="/contact/">お問い合わせフォーム</a>から、本のタイトル、該当箇所、確認できる資料やURLをお知らせください。確認のうえ、必要な箇所を修正します。</p><h2>外部サイトとの関係</h2><p>参考記事の著作権は各権利者に帰属します。各媒体の元記事の全文は掲載していません。外部サイトの公開状況や利用条件は、それぞれのサイトでご確認ください。</p></div>''',crumb=[('ホーム','/'),('制作・掲載方針','/editorial/')])
body=intro('SOURCES','参考記事一覧','各本の最終ページに記載された参考記事と、関連する公式発表を掲載しています。')
for b in BOOKS:body+=f'<section><h2><a class="text-link" href="{b["url"]}">{H(b["title"])}</a></h2><p class="meta">本の日付：{b["date"].replace("-",".")}</p>{sources_html(b)}</section>'
shell('/sources/','参考記事一覧｜ニュース本の出典と関連発表','もちとしおの5冊のニュース本で参考にしたNHKニュース、ITmedia NEWSの記事と、関連する公式発表を掲載。本ごとの出典を確認できます。',body,kind='CollectionPage',crumb=[('ホーム','/'),('参考記事一覧','/sources/')])
# Preserve forms and legal copy, with shared navigation and new canonical paths.
for filename,title,kind in [('contact.html','お問い合わせ','ContactPage'),('privacy.html','プライバシーポリシー','WebPage'),('thanks.html','送信完了','WebPage')]:
 raw=(ROOT/'templates'/filename).read_text();match=re.search(r'<main class="page">(.*?)</main>',raw,re.S);body=match.group(1)
 body=re.sub(r'<div class="breadcrumb">.*?</div>','',body,count=1,flags=re.S)
 body=body.replace('https://mochi-shio-news.satinyvenus.chatgpt.site',BASE).replace('/contact.html','/contact/').replace('/privacy.html','/privacy/').replace('/thanks.html','/thanks/').replace('/#shelf','/books/')
 path='/'+filename.replace('.html','')+'/'
 if filename=='contact.html':body+='<script src="/contact.js" defer></script>'
 desc={'contact.html':'本の感想や掲載内容へのご連絡、制作のご相談を受け付けています。','privacy.html':'個人情報とお問い合わせフォームでお預かりする情報の取り扱いについて。','thanks.html':'お問い合わせを受け付けました。'}[filename]
 # Forms need only the small existing form styles; the shared chrome remains in site.css.
 shell(path,title,desc,'<link rel="stylesheet" href="/forms.css">'+body,kind=kind,crumb=[('ホーム','/'),(title,path)],noindex=filename=='thanks.html',main_class='page')
 # Existing external links to .html continue to work; canonical points at the new directory URL.
 legacy=OUT/filename;legacy.write_text((OUT/path.strip('/')/'index.html').read_text())
shell('/404.html','ページが見つかりません','お探しのページは見つかりませんでした。本棚から読みたい本をお探しください。',intro('PAGE NOT FOUND','この本は、見つかりませんでした。','URLが変わったか、ページが存在しないようです。公開中の本は、本棚からお探しください。')+'<div class="actions"><a class="action" href="/books/">本棚へ戻る →</a></div>',noindex=True)
# Machine-readable discovery documents contain only canonical, indexable content pages.
ns='http://www.sitemaps.org/schemas/sitemap/0.9';ET.register_namespace('',ns)
root=ET.Element('{'+ns+'}urlset')
for path in INDEXABLE:
 entry=ET.SubElement(root,'{'+ns+'}url');ET.SubElement(entry,'{'+ns+'}loc').text=url(path)
(OUT/'sitemap.xml').write_bytes(ET.tostring(root,encoding='utf-8',xml_declaration=True))
(OUT/'robots.txt').write_text('User-agent: *\nAllow: /\n\nSitemap: '+url('/sitemap.xml')+'\n')
# Atom feed: web publication date is distinct from the date printed on each book.
ns='http://www.w3.org/2005/Atom';ET.register_namespace('',ns)
feed=ET.Element('{'+ns+'}feed')
def atom(parent,k,value):ET.SubElement(parent,'{'+ns+'}'+k).text=value
atom(feed,'id',url('/'));atom(feed,'title',NAME);atom(feed,'updated','2026-10-15T00:00:00+09:00')
ET.SubElement(feed,'{'+ns+'}link',{'href':url('/feed.xml'),'rel':'self'});ET.SubElement(feed,'{'+ns+'}link',{'href':url('/')})
for b in BOOKS:
 e=ET.SubElement(feed,'{'+ns+'}entry');atom(e,'id',url(b['url']));atom(e,'title',b['title']);atom(e,'updated','2026-10-15T00:00:00+09:00');atom(e,'summary',b['summary']);a=ET.SubElement(e,'{'+ns+'}author');atom(a,'name',NAME+' 運営者');ET.SubElement(e,'{'+ns+'}link',{'href':url(b['url'])})
(OUT/'feed.xml').write_bytes(ET.tostring(feed,encoding='utf-8',xml_declaration=True))
(OUT/'books.json').write_text(json.dumps(BOOKS,ensure_ascii=False,indent=2)+'\n')
# Cloudflare Pages understands this file; the physical legacy pages also work on Sites.
(OUT/'_redirects').write_text('/contact.html /contact/ 301\n/privacy.html /privacy/ 301\n/thanks.html /thanks/ 301\n')
print(f'Built {len(INDEXABLE)} canonical indexable pages, 5 book pages, sitemap, robots and feed for {BASE}')
