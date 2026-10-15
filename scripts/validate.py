#!/usr/bin/env python3
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
import json,re,xml.etree.ElementTree as ET,os
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'dist'
BASE=os.environ.get('SITE_URL',json.loads((ROOT/'site.config.json').read_text())['url']).rstrip('/')
class Doc(HTMLParser):
 def __init__(self,text):
  super().__init__(convert_charrefs=True);self.tags=[];self.data=[];self.jsons=[];self.current_json=None;self.title='';self.intitle=False;self.h1=0;self.feed(text)
 def handle_starttag(self,t,a):
  a=dict(a);self.tags.append((t,a))
  if t=='script' and a.get('type')=='application/ld+json':self.current_json=''
  if t=='title':self.intitle=True
  if t=='h1':self.h1+=1
 def handle_endtag(self,t):
  if t=='script' and self.current_json is not None:self.jsons.append(json.loads(self.current_json));self.current_json=None
  if t=='title':self.intitle=False
 def handle_data(self,d):
  if self.current_json is not None:self.current_json+=d
  else:self.data.append(d)
  if self.intitle:self.title+=d
 def find(self,tag,key,value):return [a for t,a in self.tags if t==tag and a.get(key)==value]
def file_for(path):return OUT/('index.html' if path in ('','/') else path.lstrip('/')+'index.html' if path.endswith('/') else path.lstrip('/'))
def normalize(s):return re.sub(r'\s+','',s)
ns={'s':'http://www.sitemaps.org/schemas/sitemap/0.9'}
sitemap=ET.parse(OUT/'sitemap.xml');urls=[x.text for x in sitemap.findall('.//s:loc',ns)]
expected_books=json.loads((ROOT/'content/books.json').read_text())
expected_topics=json.loads((ROOT/'content/topics.json').read_text())
expected_months=len({b['date'][:7] for b in expected_books})
assert len(urls)==len(set(urls))==len(expected_books)+11+len(expected_topics)+expected_months
seen_titles=set();docs={}
for f in OUT.rglob('*.html'):docs[f]=Doc(f.read_text())
for f,d in docs.items():
 assert d.h1==1,(f,'h1',d.h1)
 canon=d.find('link','rel','canonical');assert len(canon)==1
 assert canon[0]['href'].startswith(BASE+'/')
 assert len(d.find('meta','name','description'))==1
 assert len(d.find('meta','property','og:url'))==1
 assert d.find('meta','property','og:url')[0]['content']==canon[0]['href']
 graph=d.jsons[0]['@graph'];assert len(d.jsons)==1
 types=[x['@type'] for x in graph];assert 'WebSite' in types and 'Organization' in types
 ids=[x['@id'] for x in graph];assert len(ids)==len(set(ids))
 for entity in graph:
  if entity['@type']=='BreadcrumbList':
   assert [x['position'] for x in entity['itemListElement']]==list(range(1,len(entity['itemListElement'])+1))
  if entity['@type']=='BlogPosting':
   visible=normalize(' '.join(d.data))
   for para in entity['articleBody'].split('\n'):assert normalize(para) in visible,(f,'article text missing')
   assert entity['headline'] in ' '.join(d.data)
   links=[a['href'] for t,a in d.tags if t=='a' and 'href' in a]
   for citation in entity['citation']:assert citation in links
   assert re.fullmatch(r'\d{4}-\d{2}-\d{2}',entity['datePublished'])
 for t,a in d.tags:
  if t not in ('a','link','img','script'):continue
  ref=a.get('href') if t in ('a','link') else a.get('src')
  if not ref or ref.startswith(('mailto:','tel:','data:')):continue
  parsed=urlsplit(ref)
  if parsed.netloc and parsed.netloc!=urlsplit(BASE).netloc:continue
  target=file_for(parsed.path) if parsed.path else f
  assert target.exists(),(f,ref,'missing local file')
  if parsed.fragment and t=='a':
   dd=docs.get(target)
   if dd:assert parsed.fragment in [v.get('id') for _,v in dd.tags],(f,ref,'missing anchor')
for u in urls:
 assert u.startswith(BASE+'/');d=docs[file_for(urlsplit(u).path)]
 assert d.find('link','rel','canonical')[0]['href']==u
 assert 'noindex' not in d.find('meta','name','robots')[0]['content']
 assert d.title not in seen_titles;seen_titles.add(d.title)
assert BASE+'/thanks/' not in urls
assert BASE+'/404.html' not in urls
assert 'noindex' in docs[OUT/'thanks/index.html'].find('meta','name','robots')[0]['content']
robots=(OUT/'robots.txt').read_text();assert 'Disallow: /' not in robots and BASE+'/sitemap.xml' in robots
c=docs[OUT/'contact/index.html'];form=next(a for t,a in c.tags if t=='form')
assert form['action']=='https://formsubmit.co/ryotarouchid4@gmail.com' and form['method']=='POST'
fields={a.get('name'):a.get('value') for t,a in c.tags if t=='input'}
assert fields['_next']==BASE+'/thanks/'
assert fields['_url']==BASE+'/contact/'
assert '_captcha' not in fields
assert fields['_autoresponse'] and 'ryotarouchid4@gmail.com' in fields['_autoresponse']
books=json.loads((ROOT/'content/books.json').read_text())
for b in books:
 d=docs[file_for(b['url'])]
 assert any(x['@type']=='BlogPosting' for x in d.jsons[0]['@graph'])
 for p in b['pages']:assert (OUT/p).exists()
# All books must be discoverable from the static home and static archive HTML.
links=[a['href'] for t,a in docs[OUT/'books/index.html'].tags if t=='a' and 'href' in a]
assert all(b['url'] in links for b in books)
# トップページには、いちばん新しい本が必ずのっている
home=[a['href'] for t,a in docs[OUT/'index.html'].tags if t=='a' and 'href' in a]
assert books[0]['url'] in home
ET.parse(OUT/'feed.xml')
print(f'PASS: {len(docs)} HTML files, {len(urls)} canonical sitemap URLs, {len(books)} text articles, {sum(len(b['pages']) for b in books)} images, links/anchors, JSON-LD, metadata, form configuration and XML feeds')
