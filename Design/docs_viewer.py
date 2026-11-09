"""문서 보기 화면 — 저장소의 .md 파일을 도감처럼 보여 주는 작은 로컬 서버.  실행: 문서_보기.bat (또는 python Design/docs_viewer.py)

- 왼쪽: 문서 목록 (시작 · 설계 · 데이터 · 가이드 · 아이디어 · 레퍼런스) / 가운데: 문서 (장마다 카드) / 오른쪽: 목차
- 파일을 저장하면 열려 있는 문서가 1~2초 안에 저절로 다시 그려진다 (스크롤 위치 유지)
- 위쪽 검색: 모든 .md에서 찾기 (IdeaPool·레퍼런스 포함)
- 이 PC(127.0.0.1)에서만 열린다. 표시는 브라우저가 marked.js(cdnjs)로 그리므로 인터넷이 필요하다
"""
import json
import os
import socket
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

ROOT = Path(__file__).resolve().parent.parent
PORT = 8765
SKIP_DIRS = {".git", ".claude", "Art", "Tools", "node_modules"}

# 왼쪽 목록 — (묶음 이름, [(경로, 보이는 이름)]) . 목록에 없는 문서도 링크·검색으로 열 수 있다
NAV = [
    ("시작", [("README.md", "문서 지도"), ("GameConcept.md", "게임 컨셉"), ("TODO.md", "할 일"), ("TODO_Art.md", "그림 할 일")]),
    ("설계", [
        ("Design/00_Implemented.md", "00 구현된 것 · 진행 기록"),
        ("Design/01_Characters.md", "01 캐릭터"),
        ("Design/02_Enemies.md", "02 적 — 규칙"),
        ("Design/02_Enemies_Content.md", "02 적 — 목록"),
        ("Design/03_Maps.md", "03 방"),
        ("Design/04_Combat.md", "04 전투 · 협동"),
        ("Design/05_Items.md", "05 아이템 — 규칙"),
        ("Design/05_Items_Content.md", "05 아이템 — 목록"),
        ("Design/06_FeelParameters.md", "06 조절 수치"),
        ("Design/07_StoryMeta.md", "07 이야기 · 메타"),
        ("Design/08_RunFlow.md", "08 한 판의 흐름"),
        ("Design/README.md", "설계 문서 쓰는 법"),
    ]),
    ("데이터", [("Design/Data/README.md", "데이터 표 안내")]),
    ("가이드", "Guides"),
    ("아이디어", [("Design/IdeaPool/README.md", "날짜별"), ("Design/IdeaPool/BY_TOPIC.md", "주제별")]),
    ("레퍼런스", [("Design/References/README.md", "게임 · 기술 · 아트")]),
]


def all_md():
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        for f in filenames:
            if f.endswith(".md"):
                yield Path(dirpath, f)


def rel(p: Path) -> str:
    return p.relative_to(ROOT).as_posix()


def title_of(p: Path) -> str:
    try:
        with open(p, encoding="utf-8") as fh:
            for line in fh:
                if line.startswith("# "):
                    return line[2:].strip()
    except OSError:
        pass
    return p.stem


def nav_json():
    groups = []
    for name, items in NAV:
        if isinstance(items, str):  # 폴더 통째로 (끝난 가이드는 맨 아래)
            folder = ROOT / items
            files = sorted(folder.glob("*.md")) + sorted((folder / "Done").glob("*.md"))
            items = [(rel(f), ("✔ " if f.parent.name == "Done" else "") + title_of(f)) for f in files]
        groups.append({"name": name, "items": [{"path": p, "title": t} for p, t in items if (ROOT / p).exists()]})
    return groups


def safe_path(path: str):
    p = (ROOT / unquote(path).lstrip("/")).resolve()
    if ROOT not in p.parents or p.suffix.lower() != ".md" or not p.is_file():
        return None
    return p


def search(q: str, limit=200):
    q = q.strip().lower()
    if len(q) < 2:
        return []
    hits = []
    for p in all_md():
        try:
            lines = p.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError):
            continue
        heading = ""
        for i, line in enumerate(lines):
            if line.startswith(("## ", "### ", "#### ")):
                heading = line.lstrip("#").strip()
            if q in line.lower():
                text = line.strip().replace("**", "").replace("`", "").lstrip("-|# ").strip()
                hits.append({"path": rel(p), "title": title_of(p), "line": i + 1, "heading": heading, "text": text[:200]})
                if len(hits) >= limit:
                    return hits
    # 설계·할 일 문서가 먼저, IdeaPool·레퍼런스는 뒤로
    hits.sort(key=lambda h: (("IdeaPool" in h["path"]) or ("References" in h["path"]), h["path"]))
    return hits


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def send(self, body, ctype="application/json; charset=utf-8", code=200):
        data = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        url = urlparse(self.path)
        qs = parse_qs(url.query)
        if url.path == "/":
            return self.send(PAGE, "text/html; charset=utf-8")
        if url.path == "/api/nav":
            return self.send(json.dumps(nav_json(), ensure_ascii=False))
        if url.path == "/api/doc":
            p = safe_path(qs.get("path", [""])[0])
            if not p:
                return self.send(json.dumps({"error": "없는 문서"}, ensure_ascii=False), code=404)
            return self.send(json.dumps({"path": rel(p), "mtime": p.stat().st_mtime, "text": p.read_text(encoding="utf-8")}, ensure_ascii=False))
        if url.path == "/api/stamp":
            p = safe_path(qs.get("path", [""])[0])
            return self.send(json.dumps({"mtime": p.stat().st_mtime if p else 0}))
        if url.path == "/api/search":
            return self.send(json.dumps(search(qs.get("q", [""])[0]), ensure_ascii=False))
        # 문서 안의 그림 (상대 경로) — 저장소 안의 이미지만
        p = (ROOT / unquote(url.path).lstrip("/")).resolve()
        if ROOT in p.parents and p.is_file() and p.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp"}:
            ctype = {".svg": "image/svg+xml", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}.get(p.suffix.lower(), "image/" + p.suffix.lower()[1:])
            return self.send(p.read_bytes(), ctype)
        self.send("not found", "text/plain; charset=utf-8", 404)


PAGE = r"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>OnionCat 문서</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/marked/12.0.2/marked.min.js"></script>
<style>
:root{--bg:#f6f5f2;--card:#fff;--ink:#22212a;--sub:#6d6a75;--line:#e3e0da;--chip:#efece6;--hl:#fff1b8;--acc:#d9822b;--ok:#d9f2dc;--okc:#1d6b2a;--wip:#fff0d6;--wipc:#8a5a00;--plan:#e8e4f7;--planc:#4b3c8f;--ask:#ffe3df;--askc:#b03a2a;--off:#eee;--offc:#777}
@media (prefers-color-scheme:dark){:root{--bg:#17161c;--card:#211f28;--ink:#ecebf0;--sub:#9a97a3;--line:#34313c;--chip:#2c2a34;--hl:#4a3f12;--acc:#f0a050;--ok:#1f3a24;--okc:#8fd99b;--wip:#3d3016;--wipc:#f0c070;--plan:#2e2846;--planc:#b9aaf0;--ask:#4a2420;--askc:#ff9a88;--off:#2c2a34;--offc:#9a97a3}}
*{box-sizing:border-box}html{scroll-padding-top:70px}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.65 "Malgun Gothic","Apple SD Gothic Neo",system-ui,sans-serif}
header{position:sticky;top:0;z-index:10;background:var(--bg);border-bottom:1px solid var(--line);padding:10px 16px;display:flex;gap:12px;align-items:center}
header h1{font-size:18px;margin:0;white-space:nowrap;cursor:pointer}header h1 span{color:var(--acc)}
#q{flex:1;max-width:520px;border:1px solid var(--line);background:var(--card);color:var(--ink);border-radius:999px;padding:6px 14px;font:inherit}
#live{font-size:12px;color:var(--sub);white-space:nowrap}#live.flash{color:var(--acc);font-weight:700}
#menu{display:none;border:1px solid var(--line);background:var(--card);color:var(--ink);border-radius:8px;padding:4px 10px;font:inherit}
.wrap{display:grid;grid-template-columns:250px minmax(0,1fr) 220px;gap:20px;padding:16px;max-width:1500px;margin:0 auto}
nav,aside{position:sticky;top:66px;align-self:start;max-height:calc(100vh - 80px);overflow:auto;font-size:14px}
nav .g{font-size:12px;font-weight:700;color:var(--sub);margin:14px 0 4px;letter-spacing:.05em}
nav a{display:block;padding:3px 10px;border-radius:8px;color:var(--ink);text-decoration:none}
nav a:hover{background:var(--chip)}nav a.on{background:var(--ink);color:var(--bg)}
aside .t{font-size:12px;font-weight:700;color:var(--sub);margin-bottom:6px}
aside a{display:block;color:var(--sub);text-decoration:none;padding:2px 0;border-left:2px solid var(--line);padding-left:10px;font-size:13px}
aside a.h3{padding-left:22px;font-size:12px}aside a.on{color:var(--ink);border-color:var(--acc)}
main{min-width:0}
.crumb{color:var(--sub);font-size:12px;margin-bottom:4px}
.doc>h1{font-size:28px;margin:0 0 10px;line-height:1.3}
.doc>blockquote,.intro blockquote{margin:0 0 10px;padding:10px 14px;background:var(--chip);border-radius:10px;border:0;color:var(--ink);font-size:14px}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:4px 20px 14px;margin:16px 0;border-top:4px solid var(--acc)}
.card>h2{font-size:21px;margin:14px 0 8px}
h3{font-size:17px;margin:20px 0 6px;padding-bottom:3px;border-bottom:1px dashed var(--line)}h4{font-size:15px;margin:16px 0 4px}
a{color:var(--acc)}code{background:var(--chip);border-radius:5px;padding:1px 5px;font-size:.88em;font-family:Consolas,"D2Coding",monospace}
pre{background:var(--chip);border-radius:10px;padding:12px;overflow:auto;line-height:1.4}pre code{background:none;padding:0}
.tw{overflow-x:auto;margin:10px 0}
table{border-collapse:collapse;width:100%;font-size:14px}
th{background:var(--chip);text-align:left;font-weight:700;white-space:nowrap}
th,td{border:1px solid var(--line);padding:5px 9px;vertical-align:top}
tr:hover td{background:color-mix(in srgb,var(--hl) 35%,transparent)}
td.s-ok{background:var(--ok)}td.s-wip{background:var(--wip)}td.s-plan{background:var(--plan)}td.s-ask{background:var(--ask)}td.s-off{background:var(--off)}
.b{display:inline-block;border-radius:6px;padding:0 6px;font-size:12px;font-weight:700;line-height:1.6}
.b.ok{background:var(--ok);color:var(--okc)}.b.wip{background:var(--wip);color:var(--wipc)}.b.plan{background:var(--plan);color:var(--planc)}.b.ask{background:var(--ask);color:var(--askc)}.b.off{background:var(--off);color:var(--offc)}
ul,ol{padding-left:22px}li{margin:2px 0}li.task{list-style:none;margin-left:-20px}li.task.done{color:var(--sub)}
input[type=checkbox]{accent-color:var(--acc);margin-right:6px}
details{background:var(--chip);border-radius:10px;padding:6px 12px;margin:10px 0}summary{cursor:pointer;color:var(--sub);font-weight:700}
hr{display:none}
.hit{display:block;background:var(--card);border:1px solid var(--line);border-radius:10px;padding:8px 12px;margin:6px 0;color:var(--ink);text-decoration:none}
.hit small{color:var(--sub)}.hit mark{background:var(--hl);color:inherit}
.flash-el{animation:fl 1.5s}@keyframes fl{from{background:var(--hl)}to{background:transparent}}
@media (max-width:1100px){.wrap{grid-template-columns:220px minmax(0,1fr)}aside{display:none}}
@media (max-width:720px){.wrap{grid-template-columns:1fr;padding:12px}nav{display:none;position:static;max-height:none}nav.open{display:block}#menu{display:block}header{flex-wrap:wrap}#q{max-width:none;order:3;flex-basis:100%}}
</style></head><body>
<header><button id="menu">☰</button><h1 onclick="go('README.md')">🧅🐱 OnionCat <span>문서</span></h1>
<input id="q" placeholder="모든 문서에서 찾기 (두 글자 이상) — Enter" autocomplete="off"><span id="live">● 실시간</span></header>
<div class="wrap"><nav id="nav"></nav><main id="main"></main><aside id="toc"></aside></div>
<script>
const $=s=>document.querySelector(s);
let cur=null, curMtime=0;
const STATUS=[["✅","ok","s-ok"],["🔶","wip","s-wip"],["📝","plan","s-plan"],["❓","ask","s-ask"],["⏸","off","s-off"]];
const LABEL={ok:"완료",wip:"잠정",plan:"계획",ask:"결정 대기",off:"꺼 둠"};
function slug(t,used){let s=t.trim().toLowerCase().replace(/[^\p{L}\p{N}_\- ]/gu,'').replace(/ /g,'-');let b=s,i=1;while(used.has(s))s=b+'-'+(i++);used.add(s);return s}
function esc(s){return s.replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]))}
function dir(p){return p.includes('/')?p.slice(0,p.lastIndexOf('/')+1):''}
function resolve(base,href){const parts=(dir(base)+href).split('/');const out=[];for(const x of parts){if(x==='..')out.pop();else if(x!=='.')out.push(x)}return out.join('/')}

async function loadNav(){
  const g=await (await fetch('/api/nav')).json();
  $('#nav').innerHTML=g.map(x=>`<div class="g">${esc(x.name)}</div>`+x.items.map(i=>`<a href="#${encodeURIComponent(i.path)}" data-p="${esc(i.path)}">${esc(i.title)}</a>`).join('')).join('');
  markNav();
}
function markNav(){document.querySelectorAll('nav a').forEach(a=>a.classList.toggle('on',a.dataset.p===cur))}

// 한글 조사가 붙은 굵은 글씨(**"…"**으로)는 마크다운 규칙상 안 굵어진다 → 코드 밖의 **…**를 미리 <strong>으로
function koBold(text){let fence=false;return text.split('\n').map(l=>{if(/^\s*```/.test(l)){fence=!fence;return l}if(fence)return l;
  return l.split(/(`[^`]*`)/).map((seg,i)=>i%2?seg:seg.replace(/\*\*([^*\n]+?)\*\*/g,'<strong>$1</strong>')).join('')}).join('\n')}
function render(path,text){
  const used=new Set();
  const r=new marked.Renderer();
  r.heading=(t,l,raw)=>`<h${l} id="${slug(raw.replace(/<[^>]+>/g,''),used)}">${t}</h${l}>`;
  r.table=(h,b)=>`<div class="tw"><table><thead>${h}</thead><tbody>${b}</tbody></table></div>`;
  r.listitem=(t,task,checked)=>task?`<li class="task${checked?' done':''}">${t}</li>`:`<li>${t}</li>`;
  const html=marked.parse(koBold(text),{renderer:r,gfm:true});
  const tmp=document.createElement('div');tmp.innerHTML=html;
  // 장(h2)마다 카드로 묶기
  const doc=document.createElement('div');doc.className='doc';let box=doc;
  for(const n of [...tmp.childNodes]){
    if(n.tagName==='H2'){box=document.createElement('section');box.className='card';doc.appendChild(box)}
    box.appendChild(n);
  }
  // 상태 표시: 표 칸 색칠 + 글 속 표시를 작은 딱지로
  doc.querySelectorAll('td').forEach(td=>{const t=td.textContent.trim();for(const [e,,c] of STATUS)if(t.startsWith(e)||t.endsWith(e)){td.classList.add(c);break}});
  const walker=document.createTreeWalker(doc,NodeFilter.SHOW_TEXT);const nodes=[];while(walker.nextNode())nodes.push(walker.currentNode);
  for(const n of nodes){
    if(n.parentElement.closest('code,pre,td,th,h1,h2,h3,h4,a'))continue;
    let s=n.nodeValue,hit=false;
    for(const [e,k] of STATUS)if(s.includes(e)){hit=true;s=esc(s).split(e).join(`<span class="b ${k}" title="${LABEL[k]}">${e}</span>`)}
    if(hit){const sp=document.createElement('span');sp.innerHTML=s;n.replaceWith(sp)}
  }
  // 링크: 다른 .md는 이 화면 안에서 열기
  doc.querySelectorAll('a[href]').forEach(a=>{
    const h=a.getAttribute('href');if(/^(https?:|mailto:)/.test(h)){a.target='_blank';return}
    if(h.startsWith('#'))return;
    const [p,anc]=h.split('#');const target=resolve(path,decodeURIComponent(p));
    if(target.endsWith('.md'))a.href='#'+encodeURIComponent(target)+(anc?'::'+anc:'');
    else if(target.endsWith('/'))a.href='#'+encodeURIComponent(target+'README.md');
  });
  doc.querySelectorAll('img[src]').forEach(i=>{const s=i.getAttribute('src');if(!/^https?:/.test(s))i.src='/'+resolve(path,s)});
  const main=$('#main');main.innerHTML=`<div class="crumb">${esc(path)}</div>`;main.appendChild(doc);
  // 목차
  const hs=[...doc.querySelectorAll('h2,h3')];
  $('#toc').innerHTML=hs.length?'<div class="t">목차</div>'+hs.map(h=>`<a class="${h.tagName.toLowerCase()}" href="#${encodeURIComponent(path)}::${h.id}">${esc(h.textContent)}</a>`).join(''):'';
}

async function open_(path,anchor,keepScroll){
  const y=window.scrollY;
  const res=await fetch('/api/doc?path='+encodeURIComponent(path));
  if(!res.ok){$('#main').innerHTML=`<p>문서를 찾을 수 없어요: ${esc(path)}</p>`;return}
  const d=await res.json();cur=d.path;curMtime=d.mtime;document.title=(d.text.match(/^# (.+)$/m)||[,d.path])[1]+' — OnionCat 문서';
  if(window.marked)render(cur,d.text);else $('#main').innerHTML=`<p>표시 도구(marked.js)를 못 불러왔어요 — 인터넷 연결을 확인하세요.</p><pre>${esc(d.text)}</pre>`;
  markNav();$('#nav').classList.remove('open');
  if(keepScroll)window.scrollTo(0,y);
  else if(anchor){const el=document.getElementById(anchor);if(el){el.scrollIntoView();el.classList.add('flash-el')}}
  else window.scrollTo(0,0);
}
function go(path){location.hash=encodeURIComponent(path)}
function route(){
  const h=decodeURIComponent(location.hash.slice(1)||'README.md');
  if(h.startsWith('?')){doSearch(h.slice(1));return}
  const [p,a]=h.split('::');
  if(p===cur&&a){const el=document.getElementById(a);if(el){el.scrollIntoView();el.classList.add('flash-el')}return}
  open_(p,a,false);
}
window.addEventListener('hashchange',route);

// 실시간 — 열린 문서가 저장되면 다시 그림
setInterval(async()=>{
  if(!cur)return;
  try{const d=await (await fetch('/api/stamp?path='+encodeURIComponent(cur))).json();
    $('#live').textContent='● 실시간';
    if(d.mtime&&d.mtime!==curMtime){await open_(cur,null,true);const l=$('#live');l.textContent='● 방금 바뀜';l.classList.add('flash');setTimeout(()=>{l.classList.remove('flash');l.textContent='● 실시간'},2000)}
  }catch(e){$('#live').textContent='○ 서버 꺼짐'}
},1500);

// 검색
async function doSearch(q){
  const hits=await (await fetch('/api/search?q='+encodeURIComponent(q))).json();
  cur=null;markNav();$('#toc').innerHTML='';$('#q').value=q;
  const re=new RegExp(q.replace(/[.*+?^${}()|[\]\\]/g,'\\$&'),'gi');
  $('#main').innerHTML=`<div class="doc"><h1>“${esc(q)}” 찾기</h1><p>${hits.length}곳${hits.length>=200?' (앞 200곳만)':''}</p>`+
    hits.map(h=>`<a class="hit" href="#${encodeURIComponent(h.path)}${h.heading?'::'+slug(h.heading.replace(/\*\*|`/g,''),new Set()):''}"><small>${esc(h.title)}${h.heading?' › '+esc(h.heading):''} · ${esc(h.path)}:${h.line}</small><br>${esc(h.text).replace(re,m=>`<mark>${m}</mark>`)}</a>`).join('')+'</div>';
  window.scrollTo(0,0);
}
$('#q').addEventListener('keydown',e=>{if(e.key==='Enter'&&e.target.value.trim().length>=2)location.hash='?'+e.target.value.trim()});
$('#menu').onclick=()=>$('#nav').classList.toggle('open');

// 스크롤에 따라 목차 강조
window.addEventListener('scroll',()=>{let on=null;document.querySelectorAll('.doc h2,.doc h3').forEach(h=>{if(h.getBoundingClientRect().top<90)on=h.id});
  document.querySelectorAll('aside a').forEach(a=>a.classList.toggle('on',a.getAttribute('href').endsWith('::'+on)))},{passive:true});

loadNav().then(route);
</script></body></html>"""


def port_in_use(port):
    with socket.socket() as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    url = f"http://127.0.0.1:{PORT}/"
    if port_in_use(PORT):  # 이미 켜져 있으면 브라우저만 연다
        if "--no-browser" not in sys.argv:
            webbrowser.open(url)
        sys.exit(0)
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"OnionCat 문서 보기 — {url}")
    print("이 창을 닫으면 꺼집니다.")
    if "--no-browser" not in sys.argv:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
