# tierlist-guide

어나더에덴(Another Eden) 캐릭터 티어 빌더. 드래그 앤 드롭으로 티어 배치하고 이미지로 내보내거나 링크로 공유할 수 있는 SPA.

## Tech Stack

- 순수 HTML + inline CSS + vanilla JS (빌드 도구 없음)
- Noto Serif KR + Cinzel 웹폰트
- html2canvas (CDN) -- 티어표 이미지 내보내기
- 외부 JSON 데이터 파일 (`data/characters.json`, 410명)
- 데이터 갱신: 공식 인게임 공지 자동 감지(로컬 작업 스케줄러) + 위키 원클릭 확정 — 아래 「데이터 흐름」

## 구조

```
tierlist-guide/
├── index.html              # SPA 전체 (2,680줄)
├── data/
│   ├── characters.json     # 캐릭터 데이터 (410명)
│   ├── ls_alter_cache.json # Light/Shadow + Alter 캐시
│   ├── name_ko.csv         # 한국어 이름 매핑
│   └── notice_state.json   # 공지 스캔 위치(last_id) · 확인 필요 목록
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
│   ├── notice_sync.py      # 공식 공지 → 신규 캐릭터·SA (2026-10-07)
│   ├── lbpcascade_animeface.xml  # 공지 입화 얼굴 크롭용 (MIT)
│   └── build_data.py       # 구 위키 빌드 (CF 차단으로 미사용)
├── _tools/
│   └── update_tierlist_banner.py  # 배너 업데이트 스크립트
├── .github/workflows/
│   └── update-banner.yml   # 배너 자동 업데이트
└── docs/
    ├── plans/
    └── superpowers/
```

## 동작 방식

### 데이터 흐름
2026-10-07 — 위키(anothereden.wiki)가 Cloudflare 로 막혀 2단 구조로 바꿨다.
1. **감지 (자동, 클릭 0)** — `tools/notice_sync.py` 가 인게임 공지 웹뷰
   (`news-ap.another-eden.games/asset/notice_v2/view/{id}?language=ko|en`)를 스캔해
   「만남 캐릭터」·「신규 버디」·「성도 각성 캐릭터」를 반영. 공식 한글명·영문명은 같은 공지 id 의 ko/en 판으로 짝짓는다.
   확정 못 한 값(무기·속성·명암·아이콘·날짜)은 추정해 넣고 엔트리의 `provisional` 에 적는다.
   ⚠ 공지 서버가 해외 IP(GitHub Actions)에 403 → 워크스페이스 `_tools/tierlist/notice_sync_auto.bat` 를
   작업 스케줄러 「AE tierlist notice sync」가 매일 12:30·20:30 실행, 신규가 있으면 커밋·푸시.
2. **확정 (원클릭)** — 워크스페이스 `_tools/tierlist/tierlist_update.bat` 더블클릭 → 위키 Chrome 창(CF 체크박스가 뜨면 클릭)
   → `provisional` 값을 위키 Cargo 값으로 덮고 공식 아이콘 다운로드 → Y 로 커밋·푸시.
3. `index.html` 이 `data/characters.json` 을 fetch 해 렌더링

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
- **GitHub Actions**: 배너 업데이트(`update-banner.yml`, 위키 의존이라 CF 차단 중 무력)
- 진입점: `index.html`

## 개발 노트

- `tools/build_data.py`와 `_tools/update_tierlist_banner.py`로 스크립트가 두 곳에 분산됨
- 캐릭터 데이터 갱신: 위 「데이터 흐름」. `build_data.py` 는 characters.json 을 통째로 재생성하므로 돌리지 말 것(정정분이 날아간다)
- 모바일 UX 개선 진행 중 (`docs/plans/2026-03-27-mobile-ux-overhaul.md` 참조)
