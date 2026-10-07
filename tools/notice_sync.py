# -*- coding: utf-8 -*-
"""
공식 인게임 공지 → 신규 캐릭터 · SA 자동 반영 (2026-10-07)

anothereden.wiki 가 Cloudflare 로 막힌 뒤 자동 갱신이 멈췄다. 인게임 공지 웹뷰
(news-ap.another-eden.games/asset/notice_v2/view/{id}?language=ko|en)는 CF 가 없고,
같은 공지 id 의 ko/en 판이 1:1 로 대응해 공식 한글명 · 영문명을 짝지을 수 있다.

⚠ 공지 서버는 해외(GitHub Actions) IP 에 403 — 2026-10-07 실측. 한국 PC 에서 돌린다
  (워크스페이스 _tools/tierlist/notice_sync_auto.bat 를 작업 스케줄러가 하루 2회 실행).

공지만으로 확정 못 하는 값은 추정해 넣고 `provisional` 목록에 적는다.
위키 동기화(_tools/tierlist/sync_tierlist_wiki.py --apply)가 이 목록을 보고 확정값으로 덮는다.
  - 무기 · 공격유형 · 입수 : 같은 캐릭터의 기본형(NS · Alter)에서 상속 (AS/ES 는 무기가 같다)
  - 명암(천명)          : 캐릭터 구간에 '천의 힘'/'명의 힘' 중 하나만 있으면 그것 (공지 11건 검증 11/11),
                          없으면 기본형 상속
  - 속성                : 기본형 상속, 기본형이 없으면 스킬 공격 속성 다수결
  - 아이콘              : 공지 입화(스탠딩 일러스트)에서 얼굴 자동 크롭, 실패하면 _pending.webp
  - 날짜                : 감지일(KST). 공지 본문엔 출시일이 글로 없다

usage:
  python tools/notice_sync.py            # data/notice_state.json 의 last_id 다음부터 스캔 → 반영
  python tools/notice_sync.py --dry-run  # 쓰지 않고 리포트만
  python tools/notice_sync.py --replay 868 855 849   # 기존 데이터와 필드별 대조(정확도 측정)
"""
import argparse
import datetime
import html
import io
import json
import re
import sys
import time
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path

if sys.platform == 'win32' and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')   # 감싸지 않는다 — import 하는 쪽 stdout 을 닫음

ROOT = Path(__file__).resolve().parent.parent
CHARS = ROOT / 'data' / 'characters.json'
NAME_CSV = ROOT / 'data' / 'name_ko.csv'
STATE = ROOT / 'data' / 'notice_state.json'
ICON_DIR = ROOT / 'images' / 'icons'
CASCADE = Path(__file__).resolve().parent / 'lbpcascade_animeface.xml'
BASE = 'https://news-ap.another-eden.games/asset/notice_v2/view/{}?language={}'
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131 Safari/537.36'}
STOP_AFTER_404 = 20          # 연속 404 이만큼이면 최신 끝으로 본다 (중간 결번 실측 최대 ~10)
PENDING_ICON = '_pending.webp'

ELEMENT = {'fire': '불', 'water': '물', 'earth': '땅', 'wind': '바람', 'thunder': '뇌',
           'shade': '그림자', 'crystal': '결정'}
EL_KO = {'불': 'fire', '물': 'water', '땅': 'earth', '바람': 'wind', '번개': 'thunder', '뇌': 'thunder',
         '그림자': 'shade', '결정': 'crystal'}
ATK = {'베기': 'slash', '찌르기': 'pierce', '타격': 'blunt', '마법': 'magic'}
# 캐릭터 소개 구간의 끝 — 다음 섹션 머리
SECTION_END = re.compile(r'\n\s*(성도 각성 캐릭터|현현|외사|본편|협주|이벤트|캠페인|만남 캐릭터)')


# ── fetch ────────────────────────────────────────────────────────────────
def fetch(nid, lang):
    """공지 HTML. 404 면 None."""
    for attempt in range(3):
        try:
            req = urllib.request.Request(BASE.format(nid, lang), headers=UA)
            return urllib.request.urlopen(req, timeout=20).read().decode('utf-8', 'replace')
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            err = e
        except Exception as e:  # noqa: BLE001 — 네트워크 일시 오류는 재시도
            err = e
        time.sleep(2 * (attempt + 1))
    raise RuntimeError(f'notice {nid}/{lang}: {err}')


def text_of(doc):
    s = re.sub(r'<script.*?</script>|<style.*?</style>', '', doc, flags=re.S)
    t = html.unescape(re.sub(r'<br\s*/?>|</p>|</div>|</h\d>|</li>|<[^>]+>', '\n', s))
    return '\n'.join(x.strip() for x in t.split('\n') if x.strip())


# ── parse ────────────────────────────────────────────────────────────────
def parse_name(raw):
    """'"월화의 영애" 히스메나 AS' → (표시명, style, 기본형 표시명, alter)."""
    raw = raw.strip().strip('・').strip()
    m = re.match(r'^"([^"]+)"\s*(.+?)(?:\s+(AS|ES))?$', raw)
    if m:                                   # Alter — 티어리스트는 이명으로 부른다
        epi, suf = m.group(1).strip(), m.group(3)
        return (f'{epi} {suf}' if suf else epi), ('Alter ' + suf if suf else 'Alter'), epi, True
    m = re.match(r'^(.+?)(?:\s*(AS|ES))?$', raw)
    name, suf = m.group(1).strip(), m.group(2)
    return (f'{name} {suf}' if suf else name), (suf or 'NS'), name, False


def encounters(t_ko, t_en):
    """(ko_raw, en_raw, ko 구간 텍스트) — '만남 캐릭터: X' 와 'Encounter Characters: X' 를 순서대로 짝짓는다."""
    ko = list(re.finditer(r'^만남 캐릭터\s*[:：]\s*(.+)$', t_ko, flags=re.M))
    en = re.findall(r'^Encounter Characters?\s*[:：]\s*(.+)$', t_en, flags=re.M)
    out, bad = [], []
    if len(ko) != len(en):
        return out, [f'만남 줄 수 불일치 ko={len(ko)} en={len(en)}']
    for mk, e in zip(ko, en):
        ks, es = re.split(r'\s*[、,]\s*', mk.group(1)), re.split(r'\s*[、,]\s*', e)
        if len(ks) != len(es):
            bad.append(f'이름 수 불일치 {mk.group(1)!r} / {e!r}')
            continue
        sec = t_ko[mk.end():]
        cut = SECTION_END.search(sec)
        sec = sec[:cut.start()] if cut else sec
        out += [(k, e2, sec) for k, e2 in zip(ks, es)]
    return out, bad


def buddies(t_ko, t_en):
    ko = list(dict.fromkeys(re.findall(r'신규 버디\s*[「<"]([^」>"]+)[」>"]', t_ko)))
    en = list(dict.fromkeys(x.strip().rstrip('.') for x in
                            re.findall(r'new Sidekick\s+"?([^"\n]+?)"?(?:\s+to\b|\.|\n|$)', t_en, flags=re.I)))
    if len(ko) != len(en):
        return [], ([f'버디 수 불일치 ko={ko} en={en}'] if ko or en else [])
    return list(zip(ko, en)), []


def sa_lines(t_ko):
    """성도 각성 캐릭터 — 인라인('성도 각성 캐릭터: X 「C」')과 머리+목록('・X 「C」') 둘 다."""
    out = re.findall(r'^성도 각성 캐릭터\s*[:：]\s*(.+?)\s*「', t_ko, flags=re.M)
    for m in re.finditer(r'^성도 각성 캐릭터\s*$', t_ko, flags=re.M):
        for line in t_ko[m.end():].split('\n')[1:6]:
            mm = re.match(r'^・\s*(.+?)\s*「', line)
            if mm:
                out.append(mm.group(1))
    return list(dict.fromkeys(out))


def majority(pattern, sec, table):
    c = Counter(table[x] for x in re.findall(pattern, sec))
    return c.most_common(1)[0][0] if c else ''


# ── icon ─────────────────────────────────────────────────────────────────
def standing_art_after(doc, anchor):
    """anchor('만남 캐릭터') 뒤 첫 입화 이미지(가로 700~900 · 세로 400~600) URL 후보들."""
    pos = doc.find(anchor)
    return re.findall(r'<img[^>]+src="([^"]+lottery_notice/img/[^"]+)"', doc[pos if pos >= 0 else 0:])


def face_icon(urls, out_name):
    """입화에서 얼굴 하나를 찾으면 64x64 webp 저장 후 파일명. 실패하면 ''."""
    try:
        import cv2
        import numpy as np
        from PIL import Image
    except ImportError:
        return ''
    casc = cv2.CascadeClassifier(str(CASCADE))
    for u in urls[:4]:
        try:
            raw = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=20).read()
        except Exception:  # noqa: BLE001
            continue
        im = Image.open(io.BytesIO(raw)).convert('RGBA')
        if not (700 <= im.width <= 900 and 400 <= im.height <= 600):
            continue                                    # 배너 · 스크린샷 제외
        bg = Image.new('RGB', im.size, (255, 255, 255))
        bg.paste(im, mask=im.split()[3])
        g = cv2.equalizeHist(cv2.cvtColor(np.array(bg), cv2.COLOR_RGB2GRAY))
        faces = casc.detectMultiScale(g, scaleFactor=1.05, minNeighbors=4, minSize=(40, 40))
        if len(faces) != 1:                             # 0 또는 다수(무기 오검출 포함) → 실패
            return ''
        x, y, w, h = faces[0]
        cx, cy, side = x + w / 2, y + h / 2 + h * 0.15, w * 1.9
        box = tuple(int(v) for v in (cx - side / 2, cy - side / 2, cx + side / 2, cy + side / 2))
        bg.crop(box).resize((64, 64), Image.LANCZOS).save(ICON_DIR / out_name, 'WEBP', quality=90)
        return out_name
    return ''


# ── build ────────────────────────────────────────────────────────────────
def norm(s):
    return re.sub(r'\s+', '', s)


def make_entry(ko_raw, en_raw, sec, local, today, acq_default='gacha'):
    name_ko, style, base_ko, alter = parse_name(ko_raw)
    name_en, _, base_en, _ = parse_name(en_raw)
    by_en = {c['nameEn']: c for c in local}
    # 기본형: AS/ES 는 같은 이름의 NS(또는 Alter), Alter NS 는 상속 대상 없음
    base = by_en.get(base_en) if style not in ('NS', 'Alter') else None
    if base and base['style'] == 'Alter' and not alter:   # 따옴표 없이 이명만 쓴 공지 (보라 의상의 창술사 AS)
        style, alter = 'Alter ' + style, True
    cid = re.sub(r'[^a-z0-9]+', '_', base_en.lower()).strip('_') + ('_alter' if alter else '')
    if style not in ('NS', 'Alter'):
        cid += '_' + style.split()[-1].lower()
    # 상속 규칙 실측(2026-10-07, 로컬 전수): AS 는 NS 와 무기 103/103 · 명암 103/103 · 속성 100/103
    # (불일치 3건은 전부 NS 가 무속성). ES 는 명암 18/18 만 같고 무기 3/18 · 속성 2/18.
    el = majority(r'(불|물|땅|바람|번개|뇌|그림자|결정) 속성 [^\n]{0,12}?(?:베기|찌르기|타격|마법)', sec, EL_KO)
    if not el and re.search(r'(?:베기|찌르기|타격|마법) 공격', sec):
        el = 'null'                                   # 공격은 있는데 속성이 없다 → 무속성
    ten, myeong = '천의 힘' in sec, '명의 힘' in sec
    ls = 'light' if ten and not myeong else 'shadow' if myeong and not ten else ''
    e = {'id': cid, 'nameKo': name_ko, 'nameEn': name_en, 'style': style, 'rarity': 5, 'sa': False,
         'element': '', 'elementKo': '', 'element2': '', 'element2Ko': '',
         'weapon': '', 'weaponKo': '', 'attackType': '', 'ls': ls, 'acq': acq_default,
         'date': today, 'icon': PENDING_ICON}
    prov = ['date']
    if base:
        e['acq'] = base['acq']
        e['ls'] = e['ls'] or base['ls']
    if base and style.endswith('AS'):
        for k in ('element', 'elementKo', 'element2', 'element2Ko', 'weapon', 'weaponKo', 'attackType'):
            e[k] = base[k]
        if base['element'] in ('', 'null') and el and el != 'null':
            e['element'], e['elementKo'] = el, ELEMENT[el]
            prov.append('element')
    else:                                             # NS · Alter · ES — 무기는 위키에서
        prov += ['element', 'weapon']
        if el:
            e['element'], e['elementKo'] = el, ELEMENT.get(el, '무')
        if not base:
            prov.append('acq')
    if not e['ls']:
        prov.append('ls')
    e['provisional'] = prov + ['icon']
    return e


def load_local():
    return json.loads(CHARS.read_text(encoding='utf-8'))


def scan(state, local_doc, dry):
    local = local_doc['characters']
    ids = {c['id'] for c in local}
    known = {norm(c['nameKo']) for c in local} | {c['nameEn'] for c in local}
    today = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    nid, miss, last_ok = state['last_id'], 0, state['last_id']
    added, sa_set, unresolved = [], [], []
    while miss < STOP_AFTER_404:
        nid += 1
        d_ko = fetch(nid, 'ko')
        if d_ko is None:
            miss += 1
            continue
        miss, last_ok = 0, nid
        d_en = fetch(nid, 'en') or ''
        t_ko, t_en = text_of(d_ko), text_of(d_en)
        encs, bad = encounters(t_ko, t_en)
        bud, bad2 = buddies(t_ko, t_en)
        unresolved += [f'#{nid} {b}' for b in bad + bad2]
        cands = [(k, en, sec, 'gacha') for k, en, sec in encs] + [(k, en, '', 'buddy') for k, en in bud]
        for k, en, sec, acq in cands:
            e = make_entry(k, en, sec, local + added, today, acq)
            if e['id'] in ids or norm(e['nameKo']) in known or e['nameEn'] in known:
                continue
            if not dry and acq == 'gacha':
                icon = face_icon(standing_art_after(d_ko, '만남 캐릭터'), f'notice_{nid}_{e["id"]}.webp')
                if icon:
                    e['icon'] = icon
            e['notice'] = nid
            added.append(e)
            ids.add(e['id'])
            known |= {norm(e['nameKo']), e['nameEn']}
        for who in sa_lines(t_ko):
            disp, _, _, _ = parse_name(who)
            pool = [c for c in local if norm(c['nameKo']) == norm(disp)
                    or norm(c['nameKo']).startswith(norm(disp)) and c['style'] != 'NS']
            todo = [c for c in pool if not c['sa']]
            if len(todo) == 1:
                todo[0]['sa'] = True
                sa_set.append(f"#{nid} {todo[0]['nameKo']}")
            elif todo:
                unresolved.append(f"#{nid} SA 대상 모호: {who} → {[c['nameKo'] for c in todo]}")
        time.sleep(0.3)
    state['last_id'] = last_ok
    return added, sa_set, unresolved


def write(local_doc, added, sa_set, state):
    if not added and not sa_set:                     # 변경 없으면 상태만 — version 날짜 갱신으로 빈 커밋 방지
        STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        return
    local_doc['characters'].extend(added)
    local_doc['meta']['total'] = len(local_doc['characters'])
    local_doc['meta']['version'] = datetime.date.today().isoformat()
    CHARS.write_text(json.dumps(local_doc, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    if added:
        raw = NAME_CSV.read_bytes()
        add = ''.join(f"{e['nameEn']},{e['nameKo']}\r\n" for e in added).encode('utf-8')
        NAME_CSV.write_bytes(raw + (b'' if raw.endswith(b'\r\n') else b'\r\n') + add)
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


PENDING_MD = ROOT.parent / '_tmp' / 'tierlist_pending.md'
FIELD_KO = {'element': '속성', 'weapon': '무기', 'ls': '천명', 'icon': '아이콘', 'date': '날짜', 'acq': '획득처'}


def write_pending(path=PENDING_MD):
    """확인 필요 목록 — characters.json 의 provisional + 상태 파일의 unresolved · wiki_notes 로 매번 재생성 (2026-10-07)."""
    chars = load_local()['characters']
    state = json.loads(STATE.read_text(encoding='utf-8')) if STATE.exists() else {}
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).strftime('%Y-%m-%d %H:%M')
    prov = [c for c in chars if c.get('provisional')]
    un = state.get('unresolved', [])
    wiki = state.get('wiki_notes', {})
    out = [f'# 티어리스트 확인 필요 목록', '', f'갱신 {now} (KST) · 위키 마지막 대조 {wiki.get("date", "없음")}', '',
           f'## 1. 위키 확인 전 임시값 — {len(prov)}명', '']
    if prov:
        out += ['| 캐릭터 | 임시 필드 | 공지 |', '|---|---|---|']
        out += [f"| {c['nameKo']} ({c['nameEn']}) | {' · '.join(FIELD_KO.get(f, f) for f in c['provisional'])} | "
                f"{('#' + str(c['notice'])) if c.get('notice') else ''} |" for c in prov]
        out += ['', '→ `tierlist_update.bat` 을 돌리면 위키에 올라온 것부터 채워진다(보통 출시 후 며칠).']
    else:
        out += ['없음']
    out += ['', f'## 2. 공지에서 판단 보류 — {len(un)}건', '']
    out += [f'- {u}' for u in un] or ['없음']
    out += ['', '→ 직접 확인 후 characters.json 을 고치고 notice_state.json 의 unresolved 에서 지운다.',
            '', f'## 3. 위키 대조 — {len(wiki.get("lines", []))}건', '']
    out += [f'- {x}' for x in wiki.get('lines', [])] or ['없음']
    path.parent.mkdir(exist_ok=True)
    path.write_text('\n'.join(out) + '\n', encoding='utf-8')
    return path


def replay(nids):
    """과거 공지로 make_entry 를 돌려 기존 데이터와 필드별 대조 — 추정 규칙 정확도 측정."""
    local = load_local()['characters']
    by_id = {c['id']: c for c in local}
    fields = ('nameKo', 'nameEn', 'style', 'element', 'element2', 'weapon', 'attackType', 'ls', 'acq')
    score = Counter()
    for nid in nids:
        d_ko, d_en = fetch(nid, 'ko'), fetch(nid, 'en')
        if not d_ko or not d_en:
            continue
        encs, bad = encounters(text_of(d_ko), text_of(d_en))
        for k, en, sec in encs:
            e = make_entry(k, en, sec, [c for c in local if c['nameEn'] != parse_name(en)[0]], 'x')
            ref = by_id.get(e['id'])
            if not ref:
                print(f'#{nid} {e["nameKo"]} ({e["id"]}) — 로컬에 없음')
                continue
            diff = [f"{f}: {e[f]!r}≠{ref[f]!r}" for f in fields if e[f] != ref[f]]
            for f in fields:
                score[f, e[f] == ref[f]] += 1
            print(f'#{nid} {e["nameKo"]:<14} {"OK" if not diff else "; ".join(diff)}')
        for b in bad:
            print(f'#{nid} ! {b}')
    print('\n필드별 일치: ' + ' · '.join(f'{f} {score[f, True]}/{score[f, True] + score[f, False]}' for f in fields))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--replay', nargs='+', type=int)
    a = ap.parse_args()
    if a.replay:
        return replay(a.replay)
    state = json.loads(STATE.read_text(encoding='utf-8')) if STATE.exists() else {'last_id': 0}
    doc = load_local()
    added, sa_set, unresolved = scan(state, doc, a.dry_run)
    print(f'스캔 끝 — last_id {state["last_id"]} · 신규 {len(added)} · SA {len(sa_set)} · 확인 필요 {len(unresolved)}')
    for e in added:
        print(f"  + {e['nameKo']} / {e['nameEn']} ({e['style']}) {e['elementKo'] or '?'} "
              f"{e['weaponKo'] or '?'} {e['ls'] or '?'} icon={e['icon']} 임시={e['provisional']}")
    for s in sa_set:
        print('  SA', s)
    for u in unresolved:
        print('  ?', u)
    state['unresolved'] = sorted(set(state.get('unresolved', [])) | set(unresolved))
    if not a.dry_run:
        write(doc, added, sa_set, state)
        print(f'확인 필요 목록: {write_pending()}')


if __name__ == '__main__':
    main()
