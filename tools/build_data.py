#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
어나더에덴 티어리스트 데이터 빌더 (위키 직접 스크래핑)
- anothereden.wiki/w/Characters 직접 파싱
- 자체 name_ko.csv로 한글 매핑
- 위키에서 아이콘 다운로드 → 64x64 WebP
- 배너 자동 감지/다운로드

2026-03-27 — 룰렛 의존 완전 제거, 위키 독립 빌드
2026-03-28 — tierlist-guide/tools/로 이동, LS 아이콘 자동 다운로드 추가
"""

import csv
import json
import re
import sys
import io
import time
from pathlib import Path

# Windows cp949 출력 깨짐 방지
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# ─────────────────────────────────────────────
# 경로 설정 (스크립트 위치 기준 상대경로)
# ─────────────────────────────────────────────
PROJECT_DIR = Path(__file__).resolve().parent.parent  # tools/ → tierlist-guide/
NAME_KO_CSV = PROJECT_DIR / "data" / "name_ko.csv"
OUTPUT_JSON = PROJECT_DIR / "data" / "characters.json"
OUTPUT_ICON_DIR = PROJECT_DIR / "images" / "icons"
OUTPUT_LS_ICON_DIR = PROJECT_DIR / "images" / "ls"

WIKI_BASE = "https://anothereden.wiki"
WIKI_CHARACTERS_URL = f"{WIKI_BASE}/w/Characters"
WIKI_THUMB_URL = f"{WIKI_BASE}/thumb.php"

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

# ─────────────────────────────────────────────
# 디코딩 매핑 테이블
# ─────────────────────────────────────────────
ELEMENT_ICON_MAP = {
    "Skill_Type_8_0.png":  ("null",    "무"),
    "Skill_Type_8_1.png":  ("fire",    "불"),
    "Skill_Type_8_2.png":  ("earth",   "땅"),
    "Skill_Type_8_4.png":  ("wind",    "바람"),
    "Skill_Type_8_8.png":  ("water",   "물"),
    "Skill_Type_8_16.png": ("thunder", "뇌"),
    "Skill_Type_8_32.png": ("shade",   "그림자"),
    "Skill_Type_8_64.png": ("crystal", "결정"),
}

WEAPON_ICON_MAP = {
    "202000000_icon.png": ("staff",   "지팡이"),
    "202000001_icon.png": ("sword",   "검"),
    "202000002_icon.png": ("katana",  "도"),
    "202000003_icon.png": ("axe",     "도끼"),
    "202000004_icon.png": ("lance",   "창"),
    "202000005_icon.png": ("bow",     "활"),
    "202000006_icon.png": ("fist",    "권갑"),
    "202000007_icon.png": ("hammer",  "망치"),
}

WEAPON_TO_ATTACK_TYPE = {
    "sword": "slash", "katana": "slash", "axe": "slash",
    "lance": "pierce", "bow": "pierce",
    "fist": "blunt", "hammer": "blunt",
    "staff": "magic",
}

BUDDY_PATTERN = re.compile(r"Buddy[_ ]equipment", re.IGNORECASE)

# ─────────────────────────────────────────────
# 1. 한글 이름 로드 (자체 CSV)
# ─────────────────────────────────────────────
def load_name_ko():
    """name_ko.csv에서 영→한 매핑 로드"""
    mapping = {}
    with open(NAME_KO_CSV, "r", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        next(reader)  # 헤더
        for row in reader:
            if len(row) >= 2:
                eng = row[0].strip()
                kor = row[1].strip()
                if eng and kor:
                    mapping[eng.lower()] = kor
    print(f"  한글매핑 로드: {len(mapping)}개")
    return mapping


# ─────────────────────────────────────────────
# 2. 스타일 추출
# ─────────────────────────────────────────────
STYLE_PATTERNS = [
    (r"\s*\(Another Style\)\s*$", "AS"),
    (r"\s*\(Extra Style\)\s*$", "ES"),
    (r"\s+AS$", "AS"),
    (r"\s+ES$", "ES"),
    (r"\s+Alter$", "Alter"),
]

def extract_style(name_en):
    """영문 이름에서 스타일 접미사 추출 → (base_name, style)"""
    for pattern, style in STYLE_PATTERNS:
        if re.search(pattern, name_en):
            base = re.sub(pattern, "", name_en).strip()
            return base, style
    return name_en, "NS"


# ─────────────────────────────────────────────
# 3. 레어리티/SA 파싱
# ─────────────────────────────────────────────
def parse_rarity_sa(full_text):
    """'5★ SA' → (rarity, sa)"""
    sa = "SA" in full_text
    m = re.search(r"(\d)(?:~(\d))?★", full_text)
    if m:
        rarity = int(m.group(2)) if m.group(2) else int(m.group(1))
    else:
        rarity = 5
    return rarity, sa


# ─────────────────────────────────────────────
# 4. 속성/무기 디코딩
# ─────────────────────────────────────────────
def decode_icons(img_alts_str):
    """이미지 alt 문자열에서 속성/무기 추출 (다중속성 지원)"""
    elements = []
    weapon_en, weapon_ko = None, None

    if not img_alts_str:
        return [("null", "무")], weapon_en, weapon_ko

    parts = [p.strip() for p in img_alts_str.split(",")]
    for part in parts:
        if BUDDY_PATTERN.search(part):
            continue
        key = part.replace(" ", "_")
        if key in ELEMENT_ICON_MAP:
            elements.append(ELEMENT_ICON_MAP[key])
        elif key in WEAPON_ICON_MAP:
            weapon_en, weapon_ko = WEAPON_ICON_MAP[key]

    if not elements:
        elements = [("null", "무")]

    real = [e for e in elements if e[0] != "null"]
    if real:
        elements = real

    return elements, weapon_en, weapon_ko


# ─────────────────────────────────────────────
# 5. 아이콘 파일명 추출
# ─────────────────────────────────────────────
def extract_icon_filename(icon_src):
    """'/thumb.php?f=101000021_s2_rank5_command.png&width=80' → 파일명"""
    m = re.search(r"f=([^&]+)", icon_src)
    return m.group(1) if m else ""


# ─────────────────────────────────────────────
# 6. ID 생성
# ─────────────────────────────────────────────
def make_id(name_en, style, icon_filename="", seen_ids=None):
    """영문 이름 + 스타일 → 고유 ID"""
    base = re.sub(r"[^a-z0-9]+", "_", name_en.lower()).strip("_")
    if style != "NS":
        base += f"_{style.lower()}"
    if seen_ids is not None:
        candidate = base
        counter = 2
        while candidate in seen_ids:
            if icon_filename and counter == 2:
                icon_stem = re.sub(r"[^a-z0-9]+", "_", icon_filename.lower().replace(".png","").replace(".webp","")).strip("_")
                candidate = f"{base}_{icon_stem[-8:]}"
            else:
                candidate = f"{base}_{counter}"
            counter += 1
        seen_ids.add(candidate)
        return candidate
    return base


# ─────────────────────────────────────────────
# 7. 한글 이름 탐색
# ─────────────────────────────────────────────
def find_korean_name(name_en, style, name_mapping):
    """name_ko.csv에서 한글 이름 탐색"""
    key = name_en.strip().lower()

    if style == "AS":
        variants = [key, f"{key} as", f"{key} (another style)"]
    elif style == "ES":
        variants = [key, f"{key} es", f"{key} (extra style)"]
    elif style == "Alter":
        variants = [key, f"{key} alter"]
    else:
        variants = [key]

    for v in variants:
        if v in name_mapping:
            return name_mapping[v]

    # 베이스 이름만으로도 시도 (스타일 접미사 제거된 원본)
    base, _ = extract_style(name_en)
    base_key = base.strip().lower()
    if base_key != key and base_key in name_mapping:
        return name_mapping[base_key]

    return None


# ─────────────────────────────────────────────
# 8. 위키 Characters 스크래핑
# ─────────────────────────────────────────────
def scrape_characters():
    """anothereden.wiki/w/Characters 테이블에서 전체 캐릭터 파싱"""
    import requests
    from bs4 import BeautifulSoup

    print("  위키 Characters 페이지 스크래핑 중...")
    resp = requests.get(WIKI_CHARACTERS_URL, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')

    characters = []
    seen_ids = set()
    rows = soup.find_all('tr', class_='character-row-entry')
    print(f"  테이블 행 발견: {len(rows)}개")

    for row in rows:
        cells = row.find_all('td')

        # 1) 이름 — 일반(4셀): Cell 1, 간략(3셀): Cell 0
        if len(cells) >= 4:
            name_link = cells[1].find('a', href=True)
        elif len(cells) == 3:
            name_link = cells[0].find('a', href=True)
        else:
            continue
        name_en_raw = name_link.get_text(strip=True) if name_link else ''
        # 3셀 행은 링크 텍스트가 비거나 깨짐 — data-name fallback
        if not name_en_raw or name_en_raw == '80px':
            data_name = row.get('data-name', '')
            name_en_raw = data_name.split(',')[0].strip() if data_name else ''
        if not name_en_raw:
            continue

        # 2) 스타일
        base_name_en, style = extract_style(name_en_raw)

        # 3) data 속성
        data_type = row.get('data-type', '')
        data_free = row.get('data-free', '')
        data_name = row.get('data-name', '')
        is_alter = '(Alter)' in data_name
        is_buddy = row.get('data-sidekick', '0') == '1'

        # 셀 인덱스 (4셀: icon/name/attrs/date, 3셀: name/attrs/date — 아이콘 없음)
        if len(cells) >= 4:
            name_cell, attr_cell, date_cell = cells[1], cells[2], cells[3]
            icon_cell = cells[0]
        else:
            name_cell, attr_cell, date_cell = cells[0], cells[1], cells[2]
            icon_cell = None

        # 4) 레어리티/SA
        full_text = name_cell.get_text()
        rarity, sa = parse_rarity_sa(full_text)

        # 5) 속성/무기
        cell_imgs = attr_cell.find_all('img')
        img_alts = ','.join(img.get('alt', '') for img in cell_imgs)
        elements, weapon_en, weapon_ko = decode_icons(img_alts)
        element_en, element_ko = elements[0]
        element2_en = elements[1][0] if len(elements) > 1 else ""
        element2_ko = elements[1][1] if len(elements) > 1 else ""

        # 6) 아이콘
        icon_img = icon_cell.find('img') if icon_cell else None
        icon_src = icon_img.get('src', '') if icon_img else ''
        icon_filename = extract_icon_filename(icon_src)

        # 7) 릴리즈일
        release_date = date_cell.get_text(strip=True)

        # 8) 공격유형 / LS / 입수
        attack_type = WEAPON_TO_ATTACK_TYPE.get(weapon_en, '')
        ls = data_type.lower() if data_type else ''

        acq = ''
        if is_buddy:
            acq = 'buddy'
        elif data_free == 'Free':
            acq = 'free'
        elif data_free == 'Dream':
            acq = 'gacha'
        elif data_free in ('Chance', 'Side'):
            acq = 'side'
        elif data_free:
            acq = data_free.lower()

        if is_alter and style == 'NS':
            style = 'Alter'

        char_id = make_id(base_name_en, style, icon_filename, seen_ids)

        char = {
            "id": char_id,
            "nameKo": "",
            "nameEn": name_en_raw,
            "style": style,
            "rarity": rarity,
            "sa": sa,
            "element": element_en,
            "elementKo": element_ko,
            "element2": element2_en,
            "element2Ko": element2_ko,
            "weapon": weapon_en or "",
            "weaponKo": weapon_ko or "",
            "attackType": attack_type,
            "ls": ls,
            "acq": acq,
            "date": release_date,
            "icon": icon_filename,
        }
        characters.append(char)

    print(f"  스크래핑 완료: {len(characters)}명")
    return characters


# ─────────────────────────────────────────────
# 9. 한글 이름 매칭
# ─────────────────────────────────────────────
def apply_korean_names(characters, name_mapping):
    """한글 이름 매칭. 못 찾으면 영문 fallback"""
    matched = 0
    missing = []
    for char in characters:
        name_ko = find_korean_name(char['nameEn'], char['style'], name_mapping)
        if name_ko:
            char['nameKo'] = name_ko
            matched += 1
        else:
            char['nameKo'] = char['nameEn']
            missing.append(char['nameEn'])
    print(f"  한글매칭: {matched}/{len(characters)}")
    if missing:
        print(f"  누락 {len(missing)}명: {missing[:15]}...")
    return missing


# ─────────────────────────────────────────────
# 10. 아이콘 다운로드 (위키 → 로컬 WebP)
# ─────────────────────────────────────────────
def download_icons(characters):
    """위키에서 아이콘 다운로드 → 64x64 WebP 변환"""
    import requests
    from PIL import Image
    from io import BytesIO

    OUTPUT_ICON_DIR.mkdir(parents=True, exist_ok=True)
    downloaded = 0
    skipped = 0
    failed = 0

    for i, char in enumerate(characters):
        icon = char["icon"]
        if not icon:
            failed += 1
            continue

        out_name = Path(icon).stem + ".webp"
        dst = OUTPUT_ICON_DIR / out_name

        # 이미 있으면 스킵
        if dst.exists():
            char["icon"] = out_name
            skipped += 1
            continue

        url = f"{WIKI_THUMB_URL}?f={icon}&width=80"
        try:
            resp = requests.get(url, headers=HEADERS, timeout=10)
            resp.raise_for_status()
            img = Image.open(BytesIO(resp.content))
            img = img.resize((64, 64), Image.LANCZOS)
            img.save(dst, "WEBP", quality=85)
            char["icon"] = out_name
            downloaded += 1
            # 위키 서버 부담 방지
            if downloaded % 50 == 0:
                print(f"    ... {downloaded}장 다운로드됨")
                time.sleep(1)
        except Exception as e:
            print(f"    다운로드 실패: {icon} — {e}")
            failed += 1

    print(f"  아이콘: {downloaded}장 다운로드, {skipped}장 기존, {failed}장 실패")


# ─────────────────────────────────────────────
# 10-b. Light/Shadow 아이콘 다운로드
# ─────────────────────────────────────────────
LS_ICONS = {
    "light": "Guiding_Light_Icon.png",
    "shadow": "Luring_Shadow_Icon.png",
}

def download_ls_icons():
    """Guiding Light / Luring Shadow 아이콘을 위키에서 다운로드"""
    import requests

    OUTPUT_LS_ICON_DIR.mkdir(parents=True, exist_ok=True)
    for ls_type, filename in LS_ICONS.items():
        dst = OUTPUT_LS_ICON_DIR / f"{ls_type}.png"
        if dst.exists():
            continue
        url = f"{WIKI_THUMB_URL}?f={filename}&width=26"
        try:
            resp = requests.get(url, headers=HEADERS, timeout=10)
            resp.raise_for_status()
            dst.write_bytes(resp.content)
            print(f"  LS 아이콘 다운로드: {ls_type}.png")
        except Exception as e:
            print(f"  LS 아이콘 실패: {filename} — {e}")


# ─────────────────────────────────────────────
# 11. 배너 자동 감지/다운로드
# ─────────────────────────────────────────────
def fetch_banner():
    """위키 메인에서 최신 버전 배너 이미지 파일명 감지 + 다운로드"""
    import requests
    from bs4 import BeautifulSoup

    print("\n  배너 감지 중...")
    try:
        resp = requests.get(f"{WIKI_BASE}/w/Another_Eden_Wiki", headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')

        for img in soup.find_all('img'):
            src = img.get('src', '')
            alt = img.get('alt', '')
            # thumb.php 패턴
            m = re.search(r'f=([^&]*\d+\.\d+\.\d+[^&]*)', src)
            # 또는 /images/ 직접 경로
            if not m:
                m2 = re.search(r'/images/[^"]*?(\w+_\d+\.\d+\.\d+[^"/]*\.png)', src)
                if m2:
                    banner_filename = m2.group(1)
                else:
                    continue
            else:
                banner_filename = m.group(1)
            if banner_filename:
                version_m = re.search(r'(\d+\.\d+\.\d+)', banner_filename)
                version = version_m.group(1) if version_m else ''
                print(f"  배너 감지: {banner_filename} (v{version})")

                # src에서 전체 경로를 그대로 사용
                banner_url = f"{WIKI_BASE}{src}" if src.startswith('/') else src
                banner_resp = requests.get(banner_url, headers=HEADERS, timeout=15)
                banner_resp.raise_for_status()

                banner_path = PROJECT_DIR / "images" / "banner.png"
                banner_path.write_bytes(banner_resp.content)

                meta = {"filename": banner_filename, "version": version, "url": banner_url}
                meta_path = PROJECT_DIR / "images" / "banner_meta.json"
                with open(meta_path, "w", encoding="utf-8") as f:
                    json.dump(meta, f, ensure_ascii=False, indent=2)

                print(f"  배너 저장: {banner_path} ({banner_path.stat().st_size / 1024:.0f}KB)")
                return True

        print("  배너 감지 실패 — hotlink fallback 사용")
        return False

    except Exception as e:
        print(f"  배너 다운로드 실패: {e}")
        return False


# ─────────────────────────────────────────────
# 12. 나무위키 한글명 보완 (신규 캐릭터용)
# ─────────────────────────────────────────────
def fetch_namu_names():
    """나무위키 어나더에덴 캐릭터 문서에서 영→한 매핑 수집"""
    import requests
    try:
        resp = requests.get(
            "https://namu.wiki/w/어나더에덴/등장인물",
            headers={**HEADERS, 'Referer': 'https://namu.wiki'},
            timeout=15
        )
        if resp.status_code != 200:
            print("  나무위키 접근 실패 (CF 보호) — 스킵")
            return {}

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(resp.text, 'html.parser')

        # 나무위키 구조: 제목/본문에서 "영문명(한글명)" 패턴 추출
        mapping = {}
        text = soup.get_text()
        # "Aldo(알도)" 또는 "알도(Aldo)" 패턴
        for m in re.finditer(r'([A-Z][a-z]+(?:\s[A-Z][a-z]+)*)\s*\(([가-힣]+)\)', text):
            eng, kor = m.group(1).strip(), m.group(2).strip()
            mapping[eng.lower()] = kor
        for m in re.finditer(r'([가-힣]+)\s*\(([A-Z][a-z]+(?:\s[A-Z][a-z]+)*)\)', text):
            kor, eng = m.group(1).strip(), m.group(2).strip()
            mapping[eng.lower()] = kor

        print(f"  나무위키 매핑 수집: {len(mapping)}개")
        return mapping
    except Exception as e:
        print(f"  나무위키 스크래핑 실패: {e}")
        return {}


def supplement_korean_names(characters, missing_names):
    """누락된 한글명을 나무위키에서 보완"""
    if not missing_names:
        return 0
    namu_mapping = fetch_namu_names()
    if not namu_mapping:
        return 0
    supplemented = 0
    missing_set = set(n.lower() for n in missing_names)
    for char in characters:
        if char['nameEn'].lower() in missing_set and char['nameKo'] == char['nameEn']:
            key = char['nameEn'].lower()
            # 베이스 이름으로도 시도
            base, _ = extract_style(char['nameEn'])
            base_key = base.lower()
            found = namu_mapping.get(key) or namu_mapping.get(base_key)
            if found:
                char['nameKo'] = found
                supplemented += 1
    if supplemented:
        print(f"  나무위키 보완: {supplemented}명")
    return supplemented


def append_new_names_to_csv(characters, existing_mapping):
    """새로 매칭된 한글명을 name_ko.csv에 추가"""
    new_entries = []
    for char in characters:
        key = char['nameEn'].strip().lower()
        if key not in existing_mapping and char['nameKo'] != char['nameEn']:
            new_entries.append((char['nameEn'], char['nameKo']))
            existing_mapping[key] = char['nameKo']

    if new_entries:
        with open(NAME_KO_CSV, "a", encoding="utf-8", newline='') as f:
            writer = csv.writer(f)
            for eng, kor in new_entries:
                writer.writerow([eng, kor])
        print(f"  name_ko.csv에 {len(new_entries)}개 추가")


# ─────────────────────────────────────────────
# JSON 출력
# ─────────────────────────────────────────────
def save_json(characters):
    from datetime import date
    output = {
        "meta": {
            "version": date.today().isoformat(),
            "total": len(characters),
            "source": "anothereden.wiki",
            "generatedBy": "build_tierlist_data.py"
        },
        "characters": characters
    }

    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n  JSON 저장: {OUTPUT_JSON}")
    print(f"  파일 크기: {OUTPUT_JSON.stat().st_size / 1024:.1f} KB")


# ─────────────────────────────────────────────
# 실행
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("=== 어나더에덴 티어리스트 데이터 빌드 (위키 직접) ===\n")

    name_mapping = load_name_ko()
    characters = scrape_characters()
    missing = apply_korean_names(characters, name_mapping)

    if missing:
        supplemented = supplement_korean_names(characters, missing)
        append_new_names_to_csv(characters, name_mapping)

    download_icons(characters)
    download_ls_icons()
    fetch_banner()
    save_json(characters)

    if missing:
        # 최종 누락 목록 (보완 후에도 남은 것)
        still_missing = [c['nameEn'] for c in characters if c['nameKo'] == c['nameEn']]
        if still_missing:
            print(f"\n  ⚠ 최종 한글명 누락 {len(still_missing)}명 — name_ko.csv에 수동 추가 필요:")
            for name in still_missing[:20]:
                print(f"    - {name}")
            if len(still_missing) > 20:
                print(f"    ... 외 {len(still_missing)-20}명")

    print("\n=== 빌드 완료 ===")
