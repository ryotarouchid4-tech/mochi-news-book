// サイト内検索：search-index.json（全部の本）をよみこんで、タイトル・説明・話題・出典でさがす
(()=>{const input=document.getElementById('site-search-q'),status=document.getElementById('search-status'),list=document.getElementById('search-results');if(!input)return;
const norm=s=>String(s).normalize('NFKC').toLowerCase();let books=[];
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const render=()=>{const words=norm(input.value).trim().split(/\s+/).filter(Boolean);
 if(!words.length){status.textContent='';list.replaceChildren();return}
 const hits=books.filter(b=>{const text=norm([b.t,b.s,b.c,b.n,b.d,b.d.replaceAll('-','.'),b.r==='world'?'海外':'日本',...b.g].join(' '));return words.every(w=>text.includes(w))});
 status.textContent=hits.length?`${hits.length}冊`:'ありませんでした';
 list.innerHTML=hits.slice(0,100).map(b=>`<a class="search-hit" href="${esc(b.u)}"><img src="${esc(b.i)}" alt="" loading="lazy" width="480" height="640"><span><small>${esc(b.d.replaceAll('-','.'))} ・ ${esc(b.c)}${b.r==='world'?' ・ 海外':''}</small><strong>${esc(b.t)}</strong><span>${esc(b.s)}</span></span></a>`).join('');
 const u=new URL(location.href);if(input.value)u.searchParams.set('q',input.value);else u.searchParams.delete('q');history.replaceState(null,'',u)};
input.value=new URLSearchParams(location.search).get('q')||'';status.textContent='';
fetch('/search-index.json').then(r=>r.json()).then(d=>{books=d;render()}).catch(()=>{status.textContent='よみこめませんでした'});
input.addEventListener('input',render);input.form.addEventListener('submit',e=>{e.preventDefault();render()})})();
