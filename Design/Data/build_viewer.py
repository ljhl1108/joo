"""
Design/Data/*.csv → 그림과 함께 보는 도감 한 장 (도감.html — 탭: 적 / 아이템)

  실행: 같은 폴더의 「뷰어_갱신.bat」 더블클릭 (또는 python build_viewer.py)
  - CSV가 원본. HTML은 매번 새로 만든다 (git에 올리지 않음)
  - 마지막 커밋과 비교해서 바뀐 칸을 노랗게 표시 → 누가 무엇을 고쳤는지 바로 보인다
  - 그림: 그림·아이콘 칸(유니티 Assets 기준 경로)이 있으면 그 그림, 적은 없으면 '도형' + '색'으로 임시 그림
    직접 만든 그림만 HTML 안에 넣고, 구매 에셋은 경로로만 불러온다 (라이선스 — 복사 금지)
"""
import base64, csv, html, io, json, os, subprocess, sys, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
UNITY_ASSETS = 'C:/workspace/unity/Onioncat_AG/Assets'
SHAPES = UNITY_ASSETS + '/Sprite/Enemies/Shapes'
EMBED_OK = ('Sprite/Enemies/', 'Sprite/UI/GearIcons/')   # 직접 만든 그림만 HTML에 넣는다
OUT = os.path.join(HERE, '도감.html')

try:
    from PIL import Image
except ImportError:
    Image = None

warnings = []


# ── 읽기 ──────────────────────────────────────────────────────────────────

def read_csv_text(text):
    rows = list(csv.DictReader(io.StringIO(text)))
    return [{k.strip(): (v or '').strip() for k, v in r.items() if k} for r in rows]


def read_csv(name):
    raw = open(os.path.join(HERE, name), 'rb').read()
    for enc in ('utf-8-sig', 'cp949'):   # 엑셀에서 그냥 CSV로 저장하면 cp949가 된다
        try:
            rows = read_csv_text(raw.decode(enc))
            if enc != 'utf-8-sig':
                warnings.append(f'{name}: "CSV UTF-8"이 아닌 형식으로 저장됨 — 다음엔 CSV UTF-8로 저장해 주세요')
            return rows
        except UnicodeDecodeError:
            continue
    raise SystemExit(f'{name}: 글자 인코딩을 읽지 못했어요. 엑셀에서 "CSV UTF-8"로 저장해 주세요.')


def committed(name):
    """마지막 커밋의 같은 CSV (ID → 줄). 커밋된 적이 없으면 None"""
    rel = os.path.relpath(os.path.join(HERE, name), REPO).replace('\\', '/')
    try:
        out = subprocess.run(['git', '-C', REPO, 'show', f'HEAD:{rel}'], capture_output=True, check=True).stdout
        return {r.get('ID'): r for r in read_csv_text(out.decode('utf-8-sig'))}
    except Exception:
        return None


def same(a, b):
    """엑셀이 2.0 → 2 처럼 숫자 모양만 바꾼 건 같은 값으로 본다"""
    a, b = (a or '').strip(), (b or '').strip()
    if a == b:
        return True
    try:
        return float(a) == float(b)
    except ValueError:
        return False


def mark_changes(name, rows):
    """각 줄에 _new · _changed(바뀐 열) 표시. 반환: 지운 ID 목록"""
    before = committed(name)
    for r in rows:
        old = before.get(r.get('ID')) if before is not None else None
        r['_new'] = before is not None and old is None
        r['_changed'] = [k for k, v in r.items() if not k.startswith('_') and old is not None and not same(old.get(k), v)]
    if before is None:
        return []
    ids = {r.get('ID') for r in rows}
    return [i for i in before if i not in ids]


# ── 그림 ──────────────────────────────────────────────────────────────────

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


_cache = {}


def asset_image(path):
    """유니티 Assets 기준 경로 → 이미지 주소 (직접 만든 그림은 HTML에 넣고, 나머지는 경로로)"""
    path = path.replace('\\', '/')
    rel = path[7:] if path.startswith('Assets/') else path
    full = f'{UNITY_ASSETS}/{rel}'
    if rel in _cache:
        return _cache[rel]
    if Image and rel.startswith(EMBED_OK) and os.path.exists(full):
        uri = png_uri(Image.open(full))
    else:
        uri = 'file:///' + full
    _cache[rel] = uri
    return uri


def shape_image(shape, color_hex):
    if Image is None:
        return ''
    color = hex_rgb(color_hex)
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


# ── 표마다 ─────────────────────────────────────────────────────────────────

def styles():
    """style.csv: 그림 종류별 공통 프롬프트 (적·보스·아이콘·타일·소품)"""
    if not os.path.exists(os.path.join(HERE, 'style.csv')):
        return {}
    return {r['ID']: r.get('공통 프롬프트', '') for r in read_csv('style.csv')}


def prompt(style, subject):
    return f'{style}, {subject}' if style and subject else subject


RARITY_COLOR = {'일반': '#9a9a9a', '희귀': '#4f9dff', '에픽': '#b06cff', '전설': '#ff9a26'}


def enemies():
    rows = read_csv('enemies.csv')
    removed = mark_changes('enemies.csv', rows)
    st = styles()
    for r in rows:
        boss = r.get('분류') in ('보스', '엘리트')
        r['_prompts'] = [['그림', prompt(st.get('boss' if boss else 'enemy'), r.get('그림 프롬프트'))]] if r.get('그림 프롬프트') else []
        r['_img'] = asset_image(r['그림']) if r.get('그림') else shape_image(r.get('도형', 'Square'), r.get('색'))
        r['_group'] = '보스·엘리트' if r.get('분류') in ('보스', '엘리트') else (r.get('스테이지') or '기타')
        r['_sub'] = f"{r.get('ID')} · {r.get('프리팹') or '프리팹 없음'}"
        r['_chips'] = [[r.get('분류', ''), '', '분류'], [r.get('상태', ''), 'st', '상태']]
        r['_stars'] = '위험도'
    groups = sorted({r['_group'] for r in rows}, key=lambda g: (g != '공통', g == '보스·엘리트', g))
    return {'key': 'enemies', 'title': '적', 'csv': 'enemies.csv', 'rows': rows, 'removed': removed, 'groups': groups,
            'fields': ['위험도', '체력', '속도', '움직임', '공격', '특성', '역할'], 'notes': ['설명', '메모'], 'groupInfo': {}}


def items():
    rows = read_csv('items.csv')
    removed = mark_changes('items.csv', rows)
    sets = read_csv('sets.csv')
    set_removed = mark_changes('sets.csv', sets)
    set_color = {s['세트']: s.get('색', '#888') for s in sets}
    set_order = list(dict.fromkeys(s['세트'] for s in sets))
    st = styles()
    for r in rows:
        r['_prompts'] = [['아이콘', prompt(st.get('icon'), r.get('그림 프롬프트'))]] if r.get('그림 프롬프트') else []
        r['_img'] = asset_image(r['아이콘']) if r.get('아이콘') else ''
        st = r.get('세트', '없음')
        if r.get('상태') == '보류':
            r['_group'] = '보류 (아직 못 만듦)'
        elif st and st != '없음':
            r['_group'] = f'{st} 세트'
        elif r.get('부위') == '패시브':
            r['_group'] = '패시브 (세트 없음)'
        elif r.get('부위') == '마법서':
            r['_group'] = '마법서 (세트 없음)'
        else:
            r['_group'] = '기본 장비'
        r['_sub'] = r.get('ID', '')
        r['_rarity'] = RARITY_COLOR.get(r.get('등급', ''), '')
        r['_chips'] = [[r.get('주인', ''), 'own', '주인'], [r.get('부위', ''), '', '부위'],
                       [r.get('등급', ''), 'rar', '등급'], [r.get('상태', ''), 'st', '상태']]
        if st and st != '없음':
            r['_chips'].insert(3, [st, 'set:' + set_color.get(st, '#888'), '세트'])
    fixed = ['기본 장비', '마법서 (세트 없음)', '패시브 (세트 없음)', '보류 (아직 못 만듦)']
    groups = [f'{s} 세트' for s in set_order] + fixed
    groups = [g for g in groups if any(r['_group'] == g for r in rows)] + sorted({r['_group'] for r in rows} - set(groups))
    info = {}
    for s in sets:   # 세트 묶음 위에 단계별 보너스 (sets.csv — 같이 고칠 수 있음)
        info.setdefault(f"{s['세트']} 세트", {'color': s.get('색', '#888'), 'rows': []})['rows'].append(s)
    return {'key': 'items', 'title': '아이템', 'csv': 'items.csv + sets.csv', 'rows': rows, 'removed': removed + set_removed,
            'groups': groups, 'fields': ['효과 이름', '효과', '능력치(Lv1)', '스킬', '스킬 설명', '할퀴기', '최대 레벨'],
            'notes': ['설명', '메모'], 'groupInfo': info}


def stages():
    rows = read_csv('stages.csv')
    removed = mark_changes('stages.csv', rows)
    st = styles()
    for r in rows:
        r['_img'] = ''
        r['_swatch'] = [r.get('주색') or '#888', r.get('보조색') or '#ccc']
        order = r.get('순서', '')
        r['_group'] = '처음 (고정)' if order.startswith('1') else '가운데 (무작위)' if '가운데' in order else '마지막'
        r['_sub'] = r.get('ID', '')
        r['_chips'] = [[r.get('순서', ''), '', '순서'], [r.get('상태', ''), 'st', '상태']]
        r['_prompts'] = [p for p in (['타일', prompt(st.get('tile'), r.get('타일 프롬프트'))], ['소품', prompt(st.get('prop'), r.get('소품 프롬프트'))]) if p[1]]
    groups = [g for g in ('처음 (고정)', '가운데 (무작위)', '마지막') if any(r['_group'] == g for r in rows)]
    return {'key': 'stages', 'title': '스테이지', 'csv': 'stages.csv (+ style.csv)', 'rows': rows, 'removed': removed, 'groups': groups,
            'fields': ['해금', '보스', '분위기', '바닥', '벽', '장애물·소품', '특수 지형'], 'notes': ['메모'], 'groupInfo': {}}


def build():
    tables = []
    for make, name in ((stages, 'stages.csv'), (enemies, 'enemies.csv'), (items, 'items.csv')):
        if os.path.exists(os.path.join(HERE, name)):
            tables.append(make())
    for t in tables:
        for r in t['rows']:
            r['_isChanged'] = bool(r['_new'] or r['_changed'])
    data = json.dumps({'tables': tables, 'built': datetime.datetime.now().strftime('%Y-%m-%d %H:%M'), 'warnings': warnings},
                      ensure_ascii=False)
    open(OUT, 'w', encoding='utf-8').write(TEMPLATE.replace('__DATA__', data.replace('</', '<\\/')))
    for t in tables:
        changed = sum(1 for r in t['rows'] if r['_isChanged']) + sum(
            1 for g in t['groupInfo'].values() for s in g['rows'] if s['_new'] or s['_changed'])
        print(f"{t['title']}: {len(t['rows'])}개, 바뀐 것 {changed}개, 지운 것 {len(t['removed'])}개")
    for w in warnings:
        print('경고:', w)
    print(OUT)


TEMPLATE = r'''<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>OnionCat 도감</title>
<style>
:root{--bg:#f6f5f2;--card:#fff;--ink:#22212a;--sub:#6d6a75;--line:#e3e0da;--chip:#efece6;--hl:#fff1b8;--hlb:#e8b600;--req:#ffe3df;--reqb:#e0533f;--tile:#e9e6e0}
@media (prefers-color-scheme:dark){:root{--bg:#17161c;--card:#211f28;--ink:#ecebf0;--sub:#9a97a3;--line:#34313c;--chip:#2c2a34;--hl:#4a3f12;--hlb:#e8b600;--req:#4a2420;--reqb:#ff7a66;--tile:#2a2832}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.5 "Malgun Gothic","Apple SD Gothic Neo",system-ui,sans-serif}
header{position:sticky;top:0;z-index:5;background:var(--bg);border-bottom:1px solid var(--line);padding:12px 16px}
.head{display:flex;gap:14px;align-items:baseline;flex-wrap:wrap}h1{margin:0;font-size:20px}
.tabs{display:flex;gap:4px}.tabs button{border:0;background:none;color:var(--sub);font:inherit;font-size:17px;font-weight:700;padding:2px 10px;cursor:pointer;border-bottom:3px solid transparent}
.tabs button.on{color:var(--ink);border-bottom-color:var(--ink)}
.meta{color:var(--sub);font-size:12px;margin-top:4px}.warn{color:var(--reqb);font-size:12px}
.bar{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px;align-items:center}
.bar button{border:1px solid var(--line);background:var(--card);color:var(--ink);border-radius:999px;padding:3px 11px;cursor:pointer;font:inherit;font-size:13px}
.bar button.on{background:var(--ink);color:var(--bg);border-color:var(--ink)}
.bar input{flex:1;min-width:160px;border:1px solid var(--line);background:var(--card);color:var(--ink);border-radius:8px;padding:5px 10px;font:inherit}
main{padding:16px;max-width:1500px;margin:0 auto}
h2{font-size:16px;margin:22px 0 10px;padding-left:8px;border-left:4px solid var(--gc,var(--ink))}
.bonus{background:var(--card);border:1px solid var(--line);border-left:4px solid var(--gc);border-radius:10px;padding:8px 12px;margin-bottom:10px;font-size:13px;display:grid;grid-template-columns:auto 1fr;gap:2px 10px}
.bonus b{color:var(--gc)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:12px}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px;display:grid;grid-template-columns:72px 1fr;gap:10px;border-top:3px solid var(--rc,var(--line))}
.card.changed{border-color:var(--hlb);box-shadow:0 0 0 2px var(--hl)}
.pic{width:72px;height:72px;border-radius:10px;background:var(--tile);display:grid;place-items:center;overflow:hidden}
.pic img{max-width:64px;max-height:64px;image-rendering:pixelated}.pic .none{color:var(--sub);font-size:11px}
.top{display:flex;gap:6px;align-items:baseline;flex-wrap:wrap}.id{color:var(--sub);font-size:12px}.name{font-weight:700;font-size:16px}
.chips{display:flex;gap:4px;flex-wrap:wrap;margin:4px 0}.chip{background:var(--chip);border-radius:6px;padding:0 6px;font-size:12px}
.st-구현{background:#d9f2dc;color:#1d6b2a}.st-아이디어{background:#e8e4f7;color:#4b3c8f}.st-컨펌{background:#d6ebff;color:#1b5a96}.st-보류{background:#eee;color:#777}
.own-고양이{background:#ffe6cc;color:#94500a}.own-양파{background:#ddf3d6;color:#2f6b1f}
@media (prefers-color-scheme:dark){.st-구현{background:#1f3b24;color:#9ee0a9}.st-아이디어{background:#2e2747;color:#c5b8ff}.st-컨펌{background:#1b3149;color:#9cc9ff}.st-보류{background:#333;color:#aaa}.own-고양이{background:#46301a;color:#ffc78a}.own-양파{background:#22391c;color:#a7e391}}
dl{margin:0;display:grid;grid-template-columns:auto 1fr;gap:1px 8px;font-size:13px}dt{color:var(--sub);white-space:nowrap}dd{margin:0}
.full{grid-column:1/-1;font-size:13px}.memo{color:var(--sub)}
.hl{background:var(--hl);border-radius:4px;padding:0 3px}
.req{grid-column:1/-1;background:var(--req);border-left:3px solid var(--reqb);border-radius:6px;padding:6px 8px;font-size:13px}
.new{background:var(--hlb);color:#000;border-radius:6px;padding:0 6px;font-size:12px;font-weight:700}
.removed{background:var(--req);border-radius:8px;padding:8px 12px;margin-top:12px}
.empty{color:var(--sub);padding:30px;text-align:center}
.prompt{display:flex;gap:8px;align-items:flex-start;flex-wrap:wrap;font-size:12px;color:var(--sub)}
.prompt details{flex:1;min-width:120px}.prompt summary{cursor:pointer}
.copy{border:1px solid var(--line);background:var(--chip);color:var(--ink);border-radius:6px;padding:2px 8px;cursor:pointer;font:inherit;font-size:12px}
.copy.done{background:var(--hl)}
</style></head><body>
<header>
<div class="head"><h1>OnionCat 도감</h1><div class="tabs" id="tabs"></div></div>
<div class="meta" id="meta"></div><div class="warn" id="warn"></div>
<div class="bar" id="groups"></div>
<div class="bar"><button id="fChanged">바뀐 것만</button><button id="fReq">요청 있는 것만</button><input id="q" placeholder="이름·효과·특성 검색"></div>
</header>
<main id="main"></main>
<script>
const D = __DATA__;
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const store = (k, v) => { try { if (v === undefined) return localStorage.getItem(k); localStorage.setItem(k, v); } catch (e) {} };
let tab = store('dogam-tab') || D.tables[0].key;
if (!D.tables.some(t => t.key === tab)) tab = D.tables[0].key;
let group = '전체', onlyChanged = false, onlyReq = false, query = '';
const T = () => D.tables.find(t => t.key === tab);
document.getElementById('warn').textContent = D.warnings.join(' · ');

function val(r, k) { const v = esc(r[k]); return r._changed.includes(k) ? `<span class="hl" title="바뀜">${v || '(비움)'}</span>` : v; }
function chip([text, kind, col], r) {
  if (!text) return '';
  let cls = 'chip', style = '';
  if (kind === 'st') cls += ' st-' + esc(text);
  if (kind === 'own') cls += ' own-' + esc(text);
  if (kind === 'rar' && r._rarity) style = `color:${r._rarity};font-weight:700`;
  if (kind.startsWith('set:')) style = `background:${kind.slice(4)};color:#1b1a20;font-weight:700`;
  return `<span class="${cls}" style="${style}">${val(r, col)}</span>`;
}
function card(t, r) {
  const fields = t.fields.filter(k => r[k] || r._changed.includes(k)).map(k =>
    `<dt>${k}</dt><dd>${r._stars === k && !r._changed.includes(k) ? '★'.repeat(+r[k] || 0) : val(r, k)}</dd>`).join('');
  const notes = t.notes.filter(k => r[k] || r._changed.includes(k)).map(k => `<div class="full${k === '메모' ? ' memo' : ''}">${val(r, k)}</div>`).join('');
  return `<article class="card${r._isChanged ? ' changed' : ''}" style="${r._rarity ? '--rc:' + r._rarity : ''}">
    <div class="pic" style="${r._swatch ? `background:linear-gradient(135deg,${r._swatch[0]} 55%,${r._swatch[1]} 55%)` : ''}">${r._img ? `<img src="${r._img}" alt="" loading="lazy">` : r._swatch ? '' : '<span class="none">그림 없음</span>'}</div>
    <div><div class="top"><span class="name">${val(r, '이름')}</span><span class="id">${esc(r._sub)}</span>${r._new ? '<span class="new">새로 추가</span>' : ''}</div>
      <div class="chips">${r._chips.map(c => chip(c, r)).join('')}</div>
      <dl>${fields}</dl></div>
    ${notes}${(r._prompts || []).map(([label, text]) => `<div class="full prompt"><button class="copy" data-p="${esc(text)}">${esc(label)} 프롬프트 복사</button><details><summary>보기</summary>${esc(text)}</details></div>`).join('')}
    ${r['요청'] ? `<div class="req"><b>요청</b> ${val(r, '요청')}</div>` : ''}
  </article>`;
}
function bonus(info) {
  return `<div class="bonus" style="--gc:${esc(info.color)}">${info.rows.map(s => {
    const mark = s._new || s._changed.length;
    return `<b>${val(s, '조각')}세트</b><span${mark ? ' class="hl"' : ''}>${esc(s['보너스'])}${s['요청'] ? ` — <span style="color:var(--reqb)">요청: ${esc(s['요청'])}</span>` : ''}</span>`;
  }).join('')}</div>`;
}
function render() {
  const t = T();
  document.getElementById('tabs').innerHTML = D.tables.map(x => `<button class="${x.key === tab ? 'on' : ''}" data-k="${x.key}">${esc(x.title)}</button>`).join('');
  document.querySelectorAll('#tabs button').forEach(b => b.onclick = () => { tab = b.dataset.k; store('dogam-tab', tab); group = '전체'; render(); });
  const changed = t.rows.filter(r => r._isChanged).length;
  document.getElementById('meta').textContent = `${t.title} ${t.rows.length}개 · 원본 ${t.csv} · 만든 시각 ${D.built} · 마지막 커밋 이후 바뀐 것 ${changed}개`;
  const gEl = document.getElementById('groups');
  gEl.innerHTML = ['전체', ...t.groups].map(g => `<button class="${g === group ? 'on' : ''}">${esc(g)}</button>`).join('');
  gEl.querySelectorAll('button').forEach(b => b.onclick = () => { group = b.textContent; render(); });
  const q = query.toLowerCase();
  const list = t.rows.filter(r => (group === '전체' || r._group === group)
    && (!onlyChanged || r._isChanged) && (!onlyReq || r['요청'])
    && (!q || Object.keys(r).some(k => !k.startsWith('_') && String(r[k]).toLowerCase().includes(q))));
  let out = '';
  for (const g of t.groups) {
    const part = list.filter(r => r._group === g);
    if (!part.length) continue;
    const info = t.groupInfo[g];
    out += `<h2 style="${info ? '--gc:' + esc(info.color) : ''}">${esc(g)} (${part.length})</h2>${info ? bonus(info) : ''}<div class="grid">${part.map(r => card(t, r)).join('')}</div>`;
  }
  if (!out) out = '<div class="empty">조건에 맞는 항목이 없어요</div>';
  if (t.removed.length) out += `<div class="removed">마지막 커밋 이후 지운 ID: ${t.removed.map(esc).join(', ')}</div>`;
  document.getElementById('main').innerHTML = out;
}
document.getElementById('main').addEventListener('click', e => {
  const b = e.target.closest('.copy'); if (!b) return;
  const text = b.dataset.p;
  const done = () => { const t = b.textContent; b.textContent = '복사됨!'; b.classList.add('done'); setTimeout(() => { b.textContent = t; b.classList.remove('done'); }, 1200); };
  if (navigator.clipboard && window.isSecureContext) navigator.clipboard.writeText(text).then(done, () => fallback());
  else fallback();
  function fallback() { const ta = document.createElement('textarea'); ta.value = text; document.body.appendChild(ta); ta.select(); document.execCommand('copy'); ta.remove(); done(); }
});
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
    build()
