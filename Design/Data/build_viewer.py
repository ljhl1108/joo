"""
Design/Data/*.csv → 그림과 함께 보는 HTML (지금은 enemies.csv → enemies.html)

  실행: 같은 폴더의 「뷰어_갱신.bat」 더블클릭 (또는 python build_viewer.py)
  - CSV가 원본. HTML은 매번 새로 만든다 (git에 올리지 않음)
  - 마지막 커밋과 비교해서 바뀐 칸을 노랗게 표시 → 누가 무엇을 고쳤는지 바로 보인다
  - 그림: '그림' 칸(유니티 Assets 기준 경로)이 있으면 그 그림, 없으면 '도형' + '색'으로 임시 그림
    직접 만든 그림(Sprite/Enemies)만 HTML 안에 넣고, 구매 에셋은 경로로만 불러온다 (라이선스 — 복사 금지)
"""
import base64, csv, html, io, json, os, subprocess, sys, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
UNITY_ASSETS = 'C:/workspace/unity/Onioncat_AG/Assets'
SHAPES = UNITY_ASSETS + '/Sprite/Enemies/Shapes'
EMBED_OK = ('Sprite/Enemies/',)   # 직접 만든 그림만 HTML에 넣는다

try:
    from PIL import Image
except ImportError:
    Image = None


def read_csv_text(text):
    rows = list(csv.DictReader(io.StringIO(text)))
    return [{k.strip(): (v or '').strip() for k, v in r.items() if k} for r in rows]


def read_csv(path):
    raw = open(path, 'rb').read()
    for enc in ('utf-8-sig', 'cp949'):   # 엑셀에서 그냥 CSV로 저장하면 cp949가 된다
        try:
            return read_csv_text(raw.decode(enc)), enc
        except UnicodeDecodeError:
            continue
    raise SystemExit(f'{path}: 글자 인코딩을 읽지 못했어요. 엑셀에서 "CSV UTF-8"로 저장해 주세요.')


def committed(name):
    """마지막 커밋의 같은 CSV (없으면 None)"""
    rel = os.path.relpath(os.path.join(HERE, name), REPO).replace('\\', '/')
    try:
        out = subprocess.run(['git', '-C', REPO, 'show', f'HEAD:{rel}'], capture_output=True, check=True).stdout
        return {r.get('ID'): r for r in read_csv_text(out.decode('utf-8-sig'))}
    except Exception:
        return None


def hex_rgb(s):
    s = (s or '#CCCCCC').lstrip('#')
    try:
        return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        return (204, 204, 204)


def png_uri(img, size=96):
    img = img.convert('RGBA')
    w, h = img.size
    k = max(1, size // max(w, h))
    img = img.resize((w * k, h * k), Image.NEAREST)
    buf = io.BytesIO()
    img.save(buf, 'PNG')
    return 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()


def picture(row):
    art = row.get('그림', '').replace('\\', '/')
    if art:
        rel = art[7:] if art.startswith('Assets/') else art
        full = f'{UNITY_ASSETS}/{rel}'
        if Image and rel.startswith(EMBED_OK) and os.path.exists(full):
            return png_uri(Image.open(full))
        return 'file:///' + full   # 구매 에셋 등은 경로로만
    if Image is None:
        return ''
    color = hex_rgb(row.get('색'))
    shape = row.get('도형', 'Square')
    path = f'{SHAPES}/Shape_{shape}.png'
    if os.path.exists(path):
        src = Image.open(path).convert('RGBA')
        px = src.load()
        for y in range(src.height):
            for x in range(src.width):
                r, g, b, a = px[x, y]
                if a:
                    px[x, y] = (r * color[0] // 255, g * color[1] // 255, b * color[2] // 255, a)
        return png_uri(src)
    img = Image.new('RGBA', (32, 32), (0, 0, 0, 0))   # 네모 (기존 슬라임류)
    for y in range(4, 28):
        for x in range(4, 28):
            edge = x in (4, 27) or y in (4, 27)
            img.putpixel((x, y), (90, 90, 100, 255) if edge else color + (255,))
    return png_uri(img)


def build(name, title):
    rows, enc = read_csv(os.path.join(HERE, name))
    before = committed(name)
    for r in rows:
        old = before.get(r.get('ID')) if before is not None else None
        r['_new'] = before is not None and old is None
        r['_changed'] = [k for k, v in r.items() if not k.startswith('_') and old is not None and (old.get(k) or '') != v]
        r['_img'] = picture(r)
    removed = [] if before is None else [i for i in before if i not in {r.get('ID') for r in rows}]
    cols = [k for k in rows[0].keys() if not k.startswith('_')] if rows else []
    data = json.dumps({'rows': rows, 'cols': cols, 'removed': removed, 'encoding': enc,
                       'built': datetime.datetime.now().strftime('%Y-%m-%d %H:%M'), 'title': title, 'csv': name},
                      ensure_ascii=False)
    out = os.path.join(HERE, name.replace('.csv', '.html'))
    open(out, 'w', encoding='utf-8').write(TEMPLATE.replace('__TITLE__', html.escape(title)).replace('__DATA__', data.replace('</', '<\\/')))
    changed = sum(1 for r in rows if r['_changed'] or r['_new'])
    print(f'{out} — {len(rows)}개, 바뀐 것 {changed}개, 지운 것 {len(removed)}개' + ('  (경고: cp949로 저장됨 — "CSV UTF-8"로 저장 권장)' if enc != 'utf-8-sig' else ''))


TEMPLATE = r'''<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITLE__</title>
<style>
:root{--bg:#f6f5f2;--card:#fff;--ink:#22212a;--sub:#6d6a75;--line:#e3e0da;--chip:#efece6;--hl:#fff1b8;--hlb:#e8b600;--req:#ffe3df;--reqb:#e0533f;--tile:#e9e6e0}
@media (prefers-color-scheme:dark){:root{--bg:#17161c;--card:#211f28;--ink:#ecebf0;--sub:#9a97a3;--line:#34313c;--chip:#2c2a34;--hl:#4a3f12;--hlb:#e8b600;--req:#4a2420;--reqb:#ff7a66;--tile:#2a2832}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.5 "Malgun Gothic","Apple SD Gothic Neo",system-ui,sans-serif}
header{position:sticky;top:0;z-index:5;background:var(--bg);border-bottom:1px solid var(--line);padding:12px 16px}
h1{margin:0 0 4px;font-size:20px}.meta{color:var(--sub);font-size:12px}
.bar{display:flex;flex-wrap:wrap;gap:6px;margin-top:10px;align-items:center}
.bar button{border:1px solid var(--line);background:var(--card);color:var(--ink);border-radius:999px;padding:4px 12px;cursor:pointer;font:inherit}
.bar button.on{background:var(--ink);color:var(--bg);border-color:var(--ink)}
.bar input{flex:1;min-width:160px;border:1px solid var(--line);background:var(--card);color:var(--ink);border-radius:8px;padding:5px 10px;font:inherit}
main{padding:16px;max-width:1500px;margin:0 auto}
h2{font-size:16px;margin:22px 0 10px;padding-left:8px;border-left:4px solid var(--ink)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:12px}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px;display:grid;grid-template-columns:88px 1fr;gap:10px}
.card.changed{border-color:var(--hlb);box-shadow:0 0 0 2px var(--hl)}
.pic{width:88px;height:88px;border-radius:10px;background:var(--tile);display:grid;place-items:center;overflow:hidden}
.pic img{max-width:80px;max-height:80px;image-rendering:pixelated}
.top{display:flex;gap:6px;align-items:baseline;flex-wrap:wrap}.id{color:var(--sub);font-size:12px}.name{font-weight:700;font-size:16px}
.chips{display:flex;gap:4px;flex-wrap:wrap;margin:4px 0}.chip{background:var(--chip);border-radius:6px;padding:0 6px;font-size:12px}
.st-구현{background:#d9f2dc;color:#1d6b2a}.st-아이디어{background:#e8e4f7;color:#4b3c8f}.st-컨펌{background:#d6ebff;color:#1b5a96}.st-보류{background:#eee;color:#777}
@media (prefers-color-scheme:dark){.st-구현{background:#1f3b24;color:#9ee0a9}.st-아이디어{background:#2e2747;color:#c5b8ff}.st-컨펌{background:#1b3149;color:#9cc9ff}.st-보류{background:#333;color:#aaa}}
dl{margin:0;display:grid;grid-template-columns:auto 1fr;gap:1px 8px;font-size:13px}dt{color:var(--sub)}dd{margin:0}
.full{grid-column:1/-1;font-size:13px}.memo{color:var(--sub)}
.hl{background:var(--hl);border-radius:4px;padding:0 3px}
.req{grid-column:1/-1;background:var(--req);border-left:3px solid var(--reqb);border-radius:6px;padding:6px 8px;font-size:13px}
.new{background:var(--hlb);color:#000;border-radius:6px;padding:0 6px;font-size:12px;font-weight:700}
.removed{background:var(--req);border-radius:8px;padding:8px 12px;margin-top:12px}
.empty{color:var(--sub);padding:30px;text-align:center}
</style></head><body>
<header><h1>__TITLE__</h1>
<div class="meta" id="meta"></div>
<div class="bar" id="groups"></div>
<div class="bar"><button id="fChanged">바뀐 것만</button><button id="fReq">요청 있는 것만</button><input id="q" placeholder="이름·공격·특성 검색"></div>
</header>
<main id="main"></main>
<script>
const D = __DATA__;
const SHOWN = ['위험도','체력','속도','움직임','공격','특성','역할'];
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const groupOf = r => r['분류'] === '보스' || r['분류'] === '엘리트' ? '보스·엘리트' : (r['스테이지'] || '기타');
const order = [...new Set(D.rows.map(groupOf))].sort((a, b) => (a === '공통' ? -1 : b === '공통' ? 1 : a === '보스·엘리트' ? 1 : b === '보스·엘리트' ? -1 : a.localeCompare(b, 'ko')));
let group = '전체', onlyChanged = false, onlyReq = false, query = '';
try { group = localStorage.getItem('viewer-group') || '전체'; } catch (e) {}
const changedCount = D.rows.filter(r => r._new || r._changed.length).length;
document.getElementById('meta').textContent = `${D.rows.length}개 · 원본 ${D.csv} · 만든 시각 ${D.built} · 마지막 커밋 이후 바뀐 것 ${changedCount}개`;
function groups() {
  const el = document.getElementById('groups'); el.innerHTML = '';
  for (const g of ['전체', ...order]) {
    const b = document.createElement('button'); b.textContent = g; b.className = g === group ? 'on' : '';
    b.onclick = () => { group = g; try { localStorage.setItem('viewer-group', g); } catch (e) {} render(); }; el.appendChild(b);
  }
}
function val(r, k) { const v = esc(r[k]); return r._changed.includes(k) ? `<span class="hl" title="바뀜">${v || '(비움)'}</span>` : v; }
function card(r) {
  const ch = r._new || r._changed.length;
  const rows = SHOWN.filter(k => r[k] || r._changed.includes(k)).map(k => `<dt>${k}</dt><dd>${k === '위험도' && !r._changed.includes(k) ? '★'.repeat(+r[k] || 0) : val(r, k)}</dd>`).join('');
  return `<article class="card${ch ? ' changed' : ''}">
    <div class="pic">${r._img ? `<img src="${r._img}" alt="">` : ''}</div>
    <div><div class="top"><span class="name">${val(r, '이름')}</span><span class="id">${esc(r.ID)} · ${esc(r['프리팹'] || '프리팹 없음')}</span>${r._new ? '<span class="new">새로 추가</span>' : ''}</div>
      <div class="chips"><span class="chip">${val(r, '분류')}</span><span class="chip st-${esc(r['상태'])}">${val(r, '상태')}</span></div>
      <dl>${rows}</dl></div>
    ${r['설명'] || r._changed.includes('설명') ? `<div class="full">${val(r, '설명')}</div>` : ''}
    ${r['메모'] || r._changed.includes('메모') ? `<div class="full memo">${val(r, '메모')}</div>` : ''}
    ${r['요청'] ? `<div class="req"><b>요청</b> ${val(r, '요청')}</div>` : ''}
  </article>`;
}
function render() {
  groups();
  const q = query.toLowerCase();
  const list = D.rows.filter(r => (group === '전체' || groupOf(r) === group)
    && (!onlyChanged || r._new || r._changed.length) && (!onlyReq || r['요청'])
    && (!q || D.cols.some(k => String(r[k]).toLowerCase().includes(q))));
  let out = '';
  for (const g of order) {
    const part = list.filter(r => groupOf(r) === g);
    if (part.length) out += `<h2>${esc(g)} (${part.length})</h2><div class="grid">${part.map(card).join('')}</div>`;
  }
  if (!out) out = '<div class="empty">조건에 맞는 항목이 없어요</div>';
  if (D.removed.length) out += `<div class="removed">마지막 커밋 이후 지운 ID: ${D.removed.map(esc).join(', ')}</div>`;
  document.getElementById('main').innerHTML = out;
}
document.getElementById('fChanged').onclick = e => { onlyChanged = !onlyChanged; e.target.classList.toggle('on', onlyChanged); render(); };
document.getElementById('fReq').onclick = e => { onlyReq = !onlyReq; e.target.classList.toggle('on', onlyReq); render(); };
document.getElementById('q').oninput = e => { query = e.target.value; render(); };
render();
</script></body></html>'''

if __name__ == '__main__':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')   # 윈도우 콘솔(cp949)에서 깨지지 않게
    except Exception:
        pass
    if Image is None:
        print('참고: Pillow가 없어 임시 그림을 못 만들어요 (pip install pillow)')
    build('enemies.csv', 'OnionCat 적 도감')
