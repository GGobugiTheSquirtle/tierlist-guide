"""
티어표 인트로 배너 이미지 자동 업데이트
위키 메인 페이지에서 최신 업데이트 배너를 찾아 다운로드
# 2026-03-27
"""
import requests, re, os, json
import cloudscraper

WIKI_API = "https://anothereden.wiki/api.php"
BANNER_DIR = os.path.join(os.path.dirname(__file__), "..", "images")
BANNER_FILE = "banner.png"
META_FILE = os.path.join(BANNER_DIR, "banner_meta.json")

# 배너 이미지 패턴: 버전 번호(x.xx.xx) 포함된 큰 이미지
BANNER_PATTERN = re.compile(r'\d+\.\d+\.\d+\.png$', re.IGNORECASE)


def get_main_page_images():
    """위키 메인 페이지의 이미지 목록 가져오기"""
    scraper = cloudscraper.create_scraper()
    try:
        resp = scraper.get(WIKI_API, params={
            "action": "parse",
            "page": "Another_Eden_Wiki",
            "prop": "images",
            "format": "json"
        }, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f"  [FAIL] 위키 API 접근 실패 (Cloudflare 차단 등): {e}")
        import sys
        sys.exit(0)
    data = resp.json()
    return data.get("parse", {}).get("images", [])


def find_banner_image(images):
    """버전 번호가 포함된 배너 이미지 찾기 (가장 높은 버전)"""
    candidates = []
    for img in images:
        if BANNER_PATTERN.search(img):
            # 버전 번호 추출
            ver_match = re.search(r'(\d+)\.(\d+)\.(\d+)', img)
            if ver_match:
                ver_tuple = tuple(int(x) for x in ver_match.groups())
                candidates.append((ver_tuple, img))

    if not candidates:
        return None

    # 가장 높은 버전 선택
    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1]


def get_image_url(filename):
    """MediaWiki API로 이미지 실제 URL 가져오기"""
    scraper = cloudscraper.create_scraper()
    try:
        resp = scraper.get(WIKI_API, params={
            "action": "query",
            "titles": f"File:{filename}",
            "prop": "imageinfo",
            "iiprop": "url|size",
            "format": "json"
        }, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f"  [FAIL] 위키 API(이미지 URL) 접근 실패: {e}")
        import sys
        sys.exit(0)
    pages = resp.json().get("query", {}).get("pages", {})
    for page in pages.values():
        info = page.get("imageinfo", [{}])[0]
        return info.get("url"), info.get("size", 0), info.get("width", 0), info.get("height", 0)
    return None, 0, 0, 0


def download_banner(url, dest):
    """이미지 다운로드"""
    scraper = cloudscraper.create_scraper()
    try:
        resp = scraper.get(url, timeout=30, stream=True)
        resp.raise_for_status()
    except Exception as e:
        print(f"  [FAIL] 배너 다운로드 실패: {e}")
        import sys
        sys.exit(0)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "wb") as f:
        for chunk in resp.iter_content(8192):
            f.write(chunk)
    return os.path.getsize(dest)


def main():
    print("[1/4] 위키 메인 페이지 이미지 목록 조회...")
    images = get_main_page_images()
    print(f"  → {len(images)}개 이미지 발견")

    print("[2/4] 배너 이미지 선별...")
    banner = find_banner_image(images)
    if not banner:
        print("  [FAIL] 버전 번호 포함 배너 이미지를 찾을 수 없습니다")
        return

    ver_match = re.search(r'(\d+\.\d+\.\d+)', banner)
    version = ver_match.group(1) if ver_match else "unknown"
    print(f"  → {banner} (v{version})")

    # 이미 같은 버전이면 스킵
    if os.path.exists(META_FILE):
        with open(META_FILE, "r") as f:
            meta = json.load(f)
        if meta.get("source") == banner and os.path.exists(os.path.join(BANNER_DIR, BANNER_FILE)):
            print(f"  → 이미 최신 (v{version}). 스킵.")
            return

    print("[3/4] 이미지 URL 조회...")
    url, size, w, h = get_image_url(banner)
    if not url:
        print("  [FAIL] 이미지 URL을 가져올 수 없습니다")
        return
    print(f"  → {url} ({w}x{h}, {size//1024}KB)")

    print("[4/4] 다운로드...")
    dest = os.path.join(BANNER_DIR, BANNER_FILE)
    dl_size = download_banner(url, dest)
    print(f"  → {dest} ({dl_size//1024}KB)")

    # 메타데이터 저장
    meta = {"source": banner, "url": url, "version": version, "width": w, "height": h}
    with open(META_FILE, "w") as f:
        json.dump(meta, f, indent=2)
    print(f"  [OK] 배너 업데이트 완료 (v{version})")


if __name__ == "__main__":
    main()
