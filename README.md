# tierlist-guide

어나더에덴(Another Eden) 캐릭터 티어 빌더. 드래그 앤 드롭으로 티어 배치하고 이미지로 내보내거나 링크로 공유할 수 있는 SPA.

## Tech Stack

- 순수 HTML + inline CSS + vanilla JS (빌드 도구 없음)
- Noto Serif KR + Cinzel 웹폰트
- html2canvas (CDN) -- 티어표 이미지 내보내기
- 외부 JSON 데이터 파일 (`data/characters.json`, 184KB / 403명)
- GitHub Actions CI/CD (cloudscraper로 자동 데이터 수집)

## 구조

```
tierlist-guide/
├── index.html              # SPA 전체 (2,680줄)
├── data/
│   ├── characters.json     # 캐릭터 데이터 (184KB, 403명)
│   ├── ls_alter_cache.json # Light/Shadow + Alter 캐시
│   └── name_ko.csv         # 한국어 이름 매핑
├── images/
│   ├── banner.png          # 배너 이미지
│   ├── banner_meta.json
│   ├── Guiding_Light_Icon.png
│   ├── Luring_Shadow_Icon.png
│   ├── elements/           # 8개 원소 아이콘 (Skill_Type_8_*.png)
│   ├── icons/
│   ├── ls/
│   └── weapons/
├── tools/
│   └── build_data.py       # 데이터 빌드 스크립트
├── _tools/
│   └── update_tierlist_banner.py  # 배너 업데이트 스크립트
├── .github/workflows/
│   ├── weekly-update.yml   # 주간 자동 데이터 갱신
│   └── update-banner.yml   # 배너 자동 업데이트
└── docs/
    ├── plans/
    └── superpowers/
```

## 동작 방식

### 데이터 흐름
1. `tools/build_data.py` -- 외부 소스(altema 등)에서 캐릭터 데이터 수집/빌드
2. `data/characters.json`으로 출력 (184KB, 전체 캐릭터 정보)
3. `index.html`에서 fetch로 JSON 로드 후 UI 렌더링
4. GitHub Actions `weekly-update.yml`이 주 1회 자동 갱신 (cloudscraper로 Cloudflare 우회)

### 주요 기능
- **티어 빌더**: 캐릭터를 드래그 앤 드롭으로 티어(S/A/B/C/...) 배치
- **필터**: 원소/스타일/LS 등 다양한 조건 필터링
- **이미지 내보내기**: html2canvas로 티어표를 PNG 이미지로 저장
- **공유**: 전체 공유(세팅+배치) / 티어만 공유(배치만) 분리

### 디자인
- GitHub 스타일 다크 테마 (`--bg-primary: #0d1117`)
- 원소/스타일/LS 색상 변수 완비

## 배포

- **GitHub Pages**: 독립 repo로 배포 중
- **GitHub Actions**: 주간 자동 데이터 갱신 + 배너 업데이트
- 진입점: `index.html`

## 개발 노트

- `tools/build_data.py`와 `_tools/update_tierlist_banner.py`로 스크립트가 두 곳에 분산됨
- cloudscraper 의존성 -- Cloudflare 보호 사이트 스크래핑에 필요
- 캐릭터 데이터 갱신: `build_data.py` 실행 또는 GitHub Actions 자동 실행
- 모바일 UX 개선 진행 중 (`docs/plans/2026-03-27-mobile-ux-overhaul.md` 참조)
