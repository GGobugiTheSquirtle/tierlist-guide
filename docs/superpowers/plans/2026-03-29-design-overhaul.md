# Tierlist Guide Design Overhaul — Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 티어리스트 빌더의 색감 + 카드/티어행/헤더/토글/캡처 디자인을 Midnight Slate 팔레트 + Component Redesign으로 업그레이드한다.

**Architecture:** 단일 `index.html` SPA 유지. CSS 변수 교체 → 컴포넌트 CSS 리디자인 → HTML 출력 수정 → Segmented Control 교체 → 캡처 출력 강화. JS 비즈니스 로직(드래그, 저장, 공유) 변경 없음.

**Tech Stack:** Vanilla HTML5 + CSS3 + JavaScript (ES2020). No frameworks, no build tools. GitHub Pages 배포.

**Testing:** 빌드 도구/테스트 프레임워크 없음. 각 Task 완료 시 브라우저 수동 검증 (Chrome DevTools 375px/768px/1024px).

**Spec:** `docs/superpowers/specs/2026-03-29-design-overhaul-design.md`

---

## File Structure

모든 변경은 `index.html` 단일 파일 내:

| 영역 | 라인 범위 | 내용 |
|------|----------|------|
| CSS `:root` | 14-28 | 변수 선언 |
| CSS 컴포넌트 | 29-308 | 카드, 티어행, 헤더, 필터, 모달 등 |
| HTML Header | 322-348 | 헤더 토글 + 버튼 |
| HTML capture-area | 357-380 | 캡처 영역 (배너/푸터 추가 지점) |
| JS `renderCardHTML()` | 2110-2138 | 카드 HTML 출력 |
| JS `renderTierRows()` | 1119-1180 | 티어 행 렌더링 |
| JS `updateStaticUI()` | 908-949 | i18n 텍스트 업데이트 |
| JS `setMode/setView/setLang` | 682-1001 | 토글 상태 관리 |
| JS `captureArea()` | 2208-2236 | 이미지 캡처 |

---

## Task 1: CSS Variable System — Midnight Slate 팔레트 교체

**Files:**
- Modify: `index.html:14-28` (`:root` 블록)
- Modify: `index.html:30` (body gradient)
- Modify: `index.html:2228` (captureArea backgroundColor)

- [ ] **Step 1: `:root` CSS 변수 교체**

`index.html` 라인 14-28의 `:root` 블록을 아래로 교체:

```css
:root{
  --bg-primary:#0d1117;--bg-secondary:#161b22;--bg-card:#1c2333;
  --bg-pool:#0b1018;--bg-tier-row:rgba(22,27,34,0.7);
  --text-primary:#e6edf3;--text-secondary:#8b949e;--text-dim:#484f58;
  --accent:#e6c77a;--accent-hover:#f0d88a;--accent-dim:rgba(230,199,122,0.12);
  --border:#30363d;--border-gold:rgba(230,199,122,0.15);
  --el-fire:#e74c3c;--el-water:#3498db;--el-earth:#8B6914;
  --el-wind:#2ecc71;--el-thunder:#f1c40f;--el-shade:#9b59b6;
  --el-crystal:#00bcd4;--el-null:#95a5a6;
  --style-as:#c0c0c0;--style-es:#50c878;--style-alter:#ff6b6b;
  --ls-light:#ffeaa7;--ls-shadow:#636e72;
  --radius:6px;--card-w:92px;
  --font-display:'Cinzel','Noto Serif KR',Georgia,serif;
  --font-body:'Noto Serif KR','Segoe UI',system-ui,sans-serif;
}
```

- [ ] **Step 2: body gradient 변경**

라인 30:
```css
/* Before */
body{...background:linear-gradient(180deg,#100c20 0%,var(--bg-primary) 30%,#08060e 100%)}
/* After */
body{...background:linear-gradient(180deg,#101520 0%,var(--bg-primary) 30%,#080c12 100%)}
```

- [ ] **Step 3: captureArea backgroundColor 변경**

`captureArea()` 함수 내 (라인 2228):
```javascript
// Before
backgroundColor: '#0e0b18',
// After
backgroundColor: '#0d1117',
```

- [ ] **Step 4: 브라우저 검증**

Chrome에서 `index.html` 열기. 확인:
- 배경이 뉴트럴 슬레이트(파란기 없는 다크 그레이)인지
- 골드 악센트가 더 밝은 샴페인 톤인지
- 속성/스타일 뱃지 색상이 기존과 동일한지

- [ ] **Step 5: Commit**
```bash
git add index.html
git commit -m "design: Midnight Slate 팔레트 적용 — CSS 변수 교체"
```

---

## Task 2: Character Card 리디자인

**Files:**
- Modify: `index.html:82-107` (카드 CSS)
- Modify: `index.html:2110-2138` (`renderCardHTML()`)
- Modify: `index.html:256-280` (반응형 카드)

- [ ] **Step 1: 카드 CSS 교체**

`.char-card` (라인 82) 교체:
```css
.char-card{width:var(--card-w);background:linear-gradient(180deg,#1c2333 0%,#171e2c 100%);border-radius:10px;padding:5px 4px 4px;text-align:center;cursor:grab;user-select:none;border:1px solid rgba(48,54,61,0.7);transition:border-color .2s,transform .15s,box-shadow .2s;position:relative;overflow:hidden}
```

`.char-card::before` 추가 (라인 82 뒤):
```css
.char-card::before{content:'';position:absolute;top:0;left:0;right:0;height:1px;background:linear-gradient(90deg,transparent,rgba(255,255,255,0.06),transparent)}
```

- [ ] **Step 2: 카드 hover 효과 교체**

`.char-card:hover` (라인 83):
```css
.char-card:hover{border-color:rgba(230,199,122,0.5);transform:translateY(-3px);box-shadow:0 6px 20px rgba(0,0,0,0.4),0 0 12px rgba(230,199,122,0.08)}
```

- [ ] **Step 3: 카드 아이콘 CSS 교체**

`.char-card .card-icon` (라인 91):
```css
.char-card .card-icon{width:64px;height:64px;border-radius:8px;display:block;background:var(--bg-secondary);box-shadow:0 2px 8px rgba(0,0,0,0.4)}
```

- [ ] **Step 4: 삭제 버튼 사이즈 조정**

`.card-remove` (라인 85) — width/height 18→16:
```css
.card-remove{position:absolute;top:3px;right:3px;width:16px;height:16px;border-radius:50%;background:rgba(231,76,60,0.85);color:#fff;font-size:0.55rem;display:flex;align-items:center;justify-content:center;cursor:pointer;z-index:10;opacity:0;transition:opacity .15s;line-height:1}
```

모바일 (라인 87):
```css
@media(max-width:640px){.card-remove{opacity:1;width:14px;height:14px;font-size:0.5rem}}
```

- [ ] **Step 5: renderCardHTML() 메타 행 통합**

`renderCardHTML()` (라인 2110-2138) 교체:
```javascript
function renderCardHTML(c, opts = {}) {
  const stClass = 'st-' + c.style;
  const el1Src = c.element && EL_ICON[c.element] ? `images/elements/${EL_ICON[c.element]}` : '';
  const el2Src = c.element2 && EL_ICON[c.element2] ? `images/elements/${EL_ICON[c.element2]}` : '';
  const wpSrc = c.weapon && WP_ICON[c.weapon] ? `images/weapons/${WP_ICON[c.weapon]}` : '';
  const lsIcon = c.ls === 'light' ? 'images/ls/light.png' : c.ls === 'shadow' ? 'images/ls/shadow.png' : '';

  let html =
    `<div class="card-icon-wrap">` +
    `<img class="card-icon" src="${c.customImg || ('images/icons/' + c.icon)}" alt="${esc(charName(c))}" loading="lazy">` +
    (lsIcon ? `<img class="card-ls" src="${lsIcon}" alt="${c.ls}">` : '') +
    `</div>` +
    `<span class="card-name">${esc(charName(c))}</span>` +
    `<span class="card-meta">` +
      (el1Src ? `<img src="${el1Src}" alt="${c.elementKo}">` : '') +
      (el2Src ? `<img src="${el2Src}" alt="${c.element2Ko || ''}">` : '') +
      (wpSrc ? `<img src="${wpSrc}" alt="${c.weaponKo}">` : '') +
      `<span class="st-badge ${stClass}">${c.style}</span>` +
    `</span>`;
  if (!opts.compact) {
    html +=
      `<span class="card-sub">` +
        `<span class="rarity-badge r${c.rarity}">${c.rarity}★</span>` +
        (c.sa ? `<span class="sa-badge">SA</span>` : '') +
      `</span>`;
  }
  return html;
}
```

핵심 변경: 스타일 뱃지(NS/AS/ES/Alter)를 `.card-sub`에서 `.card-meta`로 이동 — 속성+무기+스타일이 한 행.

- [ ] **Step 6: 반응형 카드 사이즈 업데이트**

라인 255-258 (1024px breakpoint):
```css
@media(max-width:1024px){
  :root{--card-w:82px}
  .char-card .card-icon{width:56px;height:56px}
}
```

라인 259-266 (640px breakpoint) — card-w 70→72:
```css
@media(max-width:640px){
  :root{--card-w:72px}
  .char-card .card-icon{width:48px;height:48px}
  ...
}
```

- [ ] **Step 7: 브라우저 검증**

확인:
- 카드 배경이 subtle gradient인지
- 카드 상단에 미세한 하이라이트 라인이 보이는지
- 호버 시 glow + translateY(-3px) 동작
- 메타 행에 속성+무기+스타일 뱃지가 한 행에 표시
- 모바일(375px)에서 72px 카드 정상 렌더링

- [ ] **Step 8: Commit**
```bash
git add index.html
git commit -m "design: 캐릭터 카드 리디자인 — gradient, shadow, 메타행 통합"
```

---

## Task 3: Tier Row 레이아웃 리디자인

**Files:**
- Modify: `index.html:72-79` (티어 행 CSS)
- Modify: `index.html:1119-1168` (`renderTierRows()` — 라벨 속성 추가)

- [ ] **Step 1: 티어 행 CSS 교체**

`.tier-row` (라인 74):
```css
.tier-row{display:flex;align-items:stretch;margin:3px 0;border-radius:8px;background:var(--bg-tier-row);border:1px solid rgba(48,54,61,0.4);overflow:hidden}
```

`.tier-label` (라인 75):
```css
.tier-label{width:52px;min-width:52px;display:flex;flex-direction:column;align-items:center;justify-content:center;font-family:var(--font-display);font-weight:700;font-size:1rem;cursor:pointer;user-select:none;padding:4px;text-align:center;position:relative}
```

- [ ] **Step 2: 라벨 gradient divider 추가**

`.tier-label` 뒤에 추가:
```css
.tier-label::after{content:'';position:absolute;right:0;top:12%;bottom:12%;width:1px;background:linear-gradient(180deg,transparent,rgba(230,199,122,0.12),transparent)}
```

기존 `.tier-label small` 유지 (라인 76).

- [ ] **Step 3: 드롭 영역 패딩 조정**

`.tier-drop` (라인 77):
```css
.tier-drop{flex:1;display:flex;flex-wrap:wrap;align-content:flex-start;gap:6px;padding:8px 10px;min-height:52px;transition:background .15s}
```

- [ ] **Step 4: renderTierRows() — 라벨에 glow 적용**

`renderTierRows()` 내 라벨 스타일 설정 (라인 1139) 변경:
```javascript
// Before
label.style.background = td.color + '22';
label.style.color = td.color;

// After
label.style.color = td.color;
// SS/S 라벨에 subtle glow 배경
const labelUpper = td.label.toUpperCase();
if (labelUpper === 'SS' || labelUpper === 'TOP') {
  label.style.background = 'rgba(255,215,0,0.03)';
} else if (labelUpper === 'S') {
  label.style.background = 'rgba(255,107,107,0.02)';
} else {
  label.style.background = 'transparent';
}
```

- [ ] **Step 5: 반응형 티어 라벨**

640px breakpoint 내 (라인 267):
```css
.tier-label{width:44px;min-width:44px;font-size:0.85rem}
```

기존 `border-right:1px solid var(--border)` 참조 — 이제 `::after` pseudo로 대체했으므로 `border-right` 속성이 있다면 제거.

- [ ] **Step 6: 브라우저 검증**

확인:
- 티어 행 배경이 semi-transparent인지
- 라벨과 카드 영역 사이에 gradient divider가 보이는지
- SS/TOP 행 라벨에 미세한 금색 glow
- 행 간 3px 갭이 적절한지

- [ ] **Step 7: Commit**
```bash
git add index.html
git commit -m "design: 티어 행 리디자인 — gradient divider, glow, spacing"
```

---

## Task 4: Segmented Control — 토글 교체

**Files:**
- Modify: `index.html:61-63` (CSS `.toggle-group` → `.seg-control` 교체)
- Modify: `index.html:322-338` (HTML 헤더 토글)
- Modify: `index.html:682-688,989-995,997-1001` (JS setMode/setView/setLang)
- Modify: `index.html:908-930` (JS updateStaticUI)

이 Task가 가장 크므로 주의.

- [ ] **Step 1: Segmented Control CSS 추가**

기존 `.toggle-group` CSS (라인 61-63) 뒤에 추가 (기존은 유지 — 점진적 교체):
```css
/* ─── Segmented Control ─── */
.seg-control{display:flex;position:relative;background:var(--bg-primary);border-radius:8px;padding:3px;border:1px solid var(--border);overflow:hidden}
.seg-indicator{position:absolute;top:3px;height:calc(100% - 6px);border-radius:6px;background:linear-gradient(135deg,rgba(230,199,122,0.15),rgba(230,199,122,0.08));border:1px solid rgba(230,199,122,0.2);transition:left .3s cubic-bezier(.4,0,.2,1),width .3s cubic-bezier(.4,0,.2,1);z-index:0;pointer-events:none}
.seg-btn{position:relative;z-index:1;padding:5px 14px;font-size:0.7rem;color:var(--text-secondary);transition:color .2s;display:flex;align-items:center;gap:4px;white-space:nowrap;cursor:pointer;background:none;border:none;font-family:var(--font-body)}
.seg-btn.active{color:var(--accent);font-weight:600}
.seg-btn svg{width:13px;height:13px;fill:none;stroke:currentColor;stroke-width:2;stroke-linecap:round;stroke-linejoin:round;opacity:.5;flex-shrink:0}
.seg-btn.active svg{opacity:1}
```

- [ ] **Step 2: 헤더 HTML — 토글 교체**

라인 326-338 교체:
```html
    <div class="seg-control" id="seg-mode">
      <div class="seg-indicator"></div>
      <button class="seg-btn active" id="btn-builder" onclick="setMode('builder')">
        <svg viewBox="0 0 24 24"><path d="M12 20h9"/><path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z"/></svg>
        <span class="seg-label">빌더</span>
      </button>
      <button class="seg-btn" id="btn-viewer" onclick="setMode('viewer')">
        <svg viewBox="0 0 24 24"><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/></svg>
        <span class="seg-label">뷰어</span>
      </button>
    </div>
    <div class="seg-control" id="seg-view">
      <div class="seg-indicator"></div>
      <button class="seg-btn active" id="btn-tier" onclick="setView('tier')">
        <svg viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>
        <span class="seg-label">티어</span>
      </button>
      <button class="seg-btn" id="btn-all" onclick="setView('all')">
        <svg viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M3 15h18M9 3v18"/></svg>
        <span class="seg-label">전체</span>
      </button>
      <button class="seg-btn" id="btn-table" onclick="setView('table')">
        <svg viewBox="0 0 24 24"><path d="M3 6h18M3 12h18M3 18h18"/></svg>
        <span class="seg-label">표</span>
      </button>
    </div>
    <div class="seg-control" id="seg-lang">
      <div class="seg-indicator"></div>
      <button class="seg-btn active" id="btn-ko" onclick="setLang('ko')">KO</button>
      <button class="seg-btn" id="btn-en" onclick="setLang('en')">EN</button>
    </div>
```

- [ ] **Step 3: JS — initSegControl() 함수 추가**

JS 영역 (`/* ─── App State ─── */` 부근, 라인 640 전) 에 추가:

```javascript
/* ─── Segmented Control ─── */
function initSegControl(el) {
  const indicator = el.querySelector('.seg-indicator');
  if (!indicator) return;
  const activeBtn = el.querySelector('.seg-btn.active');
  if (activeBtn) {
    indicator.style.left = activeBtn.offsetLeft + 'px';
    indicator.style.width = activeBtn.offsetWidth + 'px';
  }
}

function updateSegControl(el, activeBtn) {
  const indicator = el.querySelector('.seg-indicator');
  const btns = el.querySelectorAll('.seg-btn');
  btns.forEach(b => b.classList.remove('active'));
  activeBtn.classList.add('active');
  if (indicator) {
    indicator.style.left = activeBtn.offsetLeft + 'px';
    indicator.style.width = activeBtn.offsetWidth + 'px';
  }
}

function initAllSegControls() {
  document.querySelectorAll('.seg-control').forEach(initSegControl);
}
```

- [ ] **Step 4: JS — setMode/setView/setLang 수정**

`setMode()` (라인 682):
```javascript
function setMode(m) {
  S.mode = m;
  document.body.className = 'mode-' + m;
  const seg = document.getElementById('seg-mode');
  const btn = document.getElementById(m === 'builder' ? 'btn-builder' : 'btn-viewer');
  if (seg && btn) updateSegControl(seg, btn);
  renderAll();
}
```

`setView()` (라인 989):
```javascript
function setView(v) {
  currentView = v;
  const seg = document.getElementById('seg-view');
  const btnId = v === 'tier' ? 'btn-tier' : v === 'all' ? 'btn-all' : 'btn-table';
  const btn = document.getElementById(btnId);
  if (seg && btn) updateSegControl(seg, btn);
  renderAll();
}
```

`setLang()` (라인 997):
```javascript
function setLang(l) {
  lang = l;
  document.documentElement.lang = l;
  const seg = document.getElementById('seg-lang');
  const btn = document.getElementById(l === 'ko' ? 'btn-ko' : 'btn-en');
  if (seg && btn) updateSegControl(seg, btn);
  renderAll();
}
```

- [ ] **Step 5: JS — updateStaticUI() i18n 수정**

`updateStaticUI()` 내 (라인 915-930):

토글 텍스트 업데이트 — 기존 `_s('btn-viewer','viewer')` 등은 `.seg-label` 대신 button 전체 텍스트를 덮어씀. seg-btn 내부에 `<span class="seg-label">`을 사용하므로 해당 span만 업데이트:

```javascript
// 기존 toggle text update 교체
const _sl = (id,k) => { const e = document.getElementById(id); if(e) { const sl = e.querySelector('.seg-label'); if(sl) sl.textContent = T(k); else e.textContent = T(k); } };
_sl('btn-viewer','viewer'); _sl('btn-builder','builder');
_sl('btn-tier','tier'); _sl('btn-all','all'); _sl('btn-table','table');
```

active 상태 복원 (라인 923-930) — 기존 className 할당 제거, seg-control 기반으로 교체:

```javascript
// Restore seg-control active states
const segPairs = [
  ['seg-mode', S.mode === 'builder' ? 'btn-builder' : 'btn-viewer'],
  ['seg-view', currentView === 'tier' ? 'btn-tier' : currentView === 'all' ? 'btn-all' : 'btn-table'],
  ['seg-lang', lang === 'ko' ? 'btn-ko' : 'btn-en']
];
segPairs.forEach(([segId, btnId]) => {
  const seg = document.getElementById(segId);
  const btn = document.getElementById(btnId);
  if (seg && btn) updateSegControl(seg, btn);
});
```

- [ ] **Step 6: DOMContentLoaded — initAllSegControls() 호출**

`document.addEventListener('DOMContentLoaded', ...)` 내 (라인 2445-2453)에서 `init()` 호출 전에:
```javascript
initAllSegControls();
```

- [ ] **Step 7: 반응형 — 640px 이하 seg-label 숨김**

640px media query 내에 추가:
```css
.seg-btn{padding:4px 10px;font-size:0.65rem}
.seg-control .seg-label{display:none}
```

모바일에서는 아이콘만 표시, 언어 토글(KO/EN)은 텍스트만이므로 그대로.

- [ ] **Step 8: 기존 `.toggle-group` CSS 삭제**

라인 61-63의 `.toggle-group` CSS를 삭제 (더 이상 사용하지 않음).

- [ ] **Step 9: 브라우저 검증**

확인:
- 세그먼트 컨트롤 3개 (모드/뷰/언어) 정상 렌더링
- 클릭 시 인디케이터 슬라이딩 애니메이션
- 모바일(375px)에서 아이콘만 표시, KO/EN은 텍스트
- i18n 전환(KO↔EN) 시 seg-label 텍스트 정상 업데이트
- 공유 URL 로드 시 올바른 초기 상태

- [ ] **Step 10: Commit**
```bash
git add index.html
git commit -m "design: Segmented Control 도입 — 슬라이딩 인디케이터 토글"
```

---

## Task 5: Header + Category Tab + 기타 CSS 정리

**Files:**
- Modify: `index.html:37-48` (헤더 CSS)
- Modify: `index.html:65-70` (카테고리 탭 CSS)
- Modify: `index.html:44-46` (버튼 CSS)

- [ ] **Step 1: 헤더 하단 라인 정리**

`.header::after` (라인 39) 삭제 — rainbow gradient 제거.
`.header` border-bottom 유지:
```css
.header{display:flex;align-items:center;justify-content:space-between;padding:10px 16px;background:var(--bg-secondary);border-bottom:1px solid var(--border-gold);flex-wrap:wrap;gap:10px}
```

- [ ] **Step 2: CTA 버튼 gradient 업데이트**

`.btn-primary` (라인 44):
```css
.btn-primary{background:linear-gradient(135deg,#d4a44a,var(--accent));color:#0d1117;font-weight:600;border:1px solid rgba(255,255,255,0.1);box-shadow:0 1px 4px rgba(230,199,122,0.2)}
.btn-primary:hover{background:linear-gradient(135deg,var(--accent),var(--accent-hover));box-shadow:0 3px 10px rgba(230,199,122,0.3)}
```

- [ ] **Step 3: 카테고리 탭 active 스타일**

`.cat-tab.active` (라인 68):
```css
.cat-tab.active{background:rgba(22,27,34,0.8);color:var(--accent);border-color:var(--border-gold)}
```

- [ ] **Step 4: 브라우저 검증**

확인:
- 헤더 하단에 rainbow gradient 없고 깔끔한 border만
- 이미지 복사 버튼 gradient 업데이트
- 카테고리 탭 active 상태 정상

- [ ] **Step 5: Commit**
```bash
git add index.html
git commit -m "design: 헤더/카테고리탭/버튼 CSS 정리"
```

---

## Task 6: Capture Image Output — 배너 + 푸터

**Files:**
- Modify: `index.html:357` (HTML — 캡처 배너 추가)
- Modify: `index.html:380` (HTML — 캡처 푸터 추가)
- Modify: `index.html:246-251` (CSS — 캡처 배너/푸터 스타일)
- Modify: `index.html:2208-2236` (`captureArea()`)

- [ ] **Step 1: 캡처 배너/푸터 CSS 추가**

`#capture-area` CSS (라인 247) 뒤에 추가:
```css
.capture-banner{background:linear-gradient(135deg,#161b22,#0d1117,#161b22);padding:16px 20px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid rgba(230,199,122,0.1);display:none}
.capture-banner h2{font-family:var(--font-display);color:var(--accent);font-size:0.9rem;letter-spacing:1px}
.cap-info{font-size:0.6rem;color:var(--text-dim);text-align:right;line-height:1.5}
.capture-footer{background:#161b22;padding:8px 20px;display:flex;align-items:center;justify-content:space-between;border-top:1px solid rgba(230,199,122,0.06);display:none}
.cap-credit{font-size:0.55rem;color:var(--text-dim)}
.cap-credit a{color:var(--accent);text-decoration:none}
.cap-watermark{font-family:var(--font-display);font-size:0.55rem;color:rgba(230,199,122,0.25);letter-spacing:2px}
```

- [ ] **Step 2: 캡처 배너/푸터 HTML 추가**

`<div id="capture-area">` 직후 (라인 358):
```html
<div class="capture-banner" id="capture-banner">
  <h2 id="cap-title">어나더에덴 티어표</h2>
  <div class="cap-info">
    <div id="cap-category"></div>
    <div id="cap-version"></div>
  </div>
</div>
```

`</div><!-- /capture-area -->` 직전 (라인 380):
```html
<div class="capture-footer" id="capture-footer">
  <span class="cap-credit">by <a href="#">Team 랜선을 넘는 고양이들</a></span>
  <span class="cap-watermark">AE TIER LIST BUILDER</span>
</div>
```

- [ ] **Step 3: captureArea() 함수 수정**

기존 워터마크 로직 (라인 2221-2224)을 배너/푸터 show/hide로 교체:

```javascript
async function captureArea() {
  if (typeof html2canvas === 'undefined') {
    alert(T('html2canvasWait'));
    return null;
  }
  if (S.mode === 'builder') {
    if (confirm(T('captureWarning'))) {
      setMode('viewer');
      await new Promise(r => setTimeout(r, 100));
    }
  }
  const area = document.getElementById('capture-area');

  // Show capture banner/footer
  const banner = document.getElementById('capture-banner');
  const footer = document.getElementById('capture-footer');
  const capTitle = document.getElementById('cap-title');
  const capCat = document.getElementById('cap-category');
  const capVer = document.getElementById('cap-version');
  if (banner) {
    capTitle.textContent = T('title').replace(' 빌더', '').replace(' Builder', '');
    const activeCat = S.workspace.categories.find(c => c.id === S.workspace.activeCategory);
    capCat.textContent = (activeCat ? activeCat.name + ' · ' : '') + new Date().toISOString().slice(0,10);
    capVer.textContent = gameVersion ? T('gameVerPrefix') + gameVersion : '';
    banner.style.display = 'flex';
  }
  if (footer) footer.style.display = 'flex';

  const canvas = await html2canvas(area, {
    backgroundColor: '#0d1117',
    scale: Math.max(window.devicePixelRatio || 2, 3),
    useCORS: true,
    logging: false
  });

  // Hide banner/footer
  if (banner) banner.style.display = 'none';
  if (footer) footer.style.display = 'none';

  return canvas;
}
```

- [ ] **Step 4: 브라우저 검증**

1. 빌더 모드에서 "이미지 복사" 클릭
2. 뷰어 전환 확인 → 클립보드에 이미지 복사됨
3. 복사된 이미지에 상단 배너(제목+카테고리+버전) + 하단 푸터(크레딧+워터마크) 확인
4. 일반 사용 시 배너/푸터가 보이지 않는지 확인

- [ ] **Step 5: Commit**
```bash
git add index.html
git commit -m "design: 캡처 이미지 배너+푸터 추가 — 공유 품질 강화"
```

---

## Task 7: 모달/필터/기타 색감 정리 + 최종 검증

**Files:**
- Modify: `index.html` — 모달, 피커, 필터, 인트로 등 잔여 색상 참조

- [ ] **Step 1: 인트로 화면 배경 업데이트**

`.intro` (라인 283):
```css
.intro{...background:radial-gradient(ellipse at 50% 30%,#1a2030 0%,#0a0e14 70%,#050810 100%)...}
```

`.intro .intro-start` (라인 290):
```css
.intro .intro-start{...background:linear-gradient(135deg,#c9a84c,#e6c77a,#c9a84c)...}
```

- [ ] **Step 2: 모달 배경 업데이트**

`.modal` (라인 194):
```css
.modal{background:linear-gradient(180deg,var(--bg-secondary) 0%,#0d1020 100%);...}
```

`.picker-modal` (라인 167):
```css
.picker-modal{...background:linear-gradient(180deg,var(--bg-secondary) 0%,#0c0e1c 100%);...}
```

`.edit-pop` (라인 204):
```css
.edit-pop{...background:linear-gradient(180deg,var(--bg-secondary),#0d1020);...}
```

- [ ] **Step 3: 하드코딩된 색상 참조 검색 및 교체**

`#0e0b18`, `#161230`, `#1c1640`, `#14102a`, `#0a0814` 등 기존 퍼플 색상이 CSS 변수 외에 하드코딩된 곳을 검색:
- `.header::after`의 `#c9a84c` → `var(--accent)` (이미 삭제됨)
- `.btn-primary` gradient 내 `#b8942f` → `#d4a44a` (Task 5에서 완료)
- `body` gradient (Task 1에서 완료)

JS 내 하드코딩:
- `captureArea()` backgroundColor (Task 1에서 완료)

- [ ] **Step 4: 전체 브라우저 검증 (모든 뷰)**

전체 플로우 테스트:
1. 인트로 화면 표시 → 색감 확인
2. "시작하기" → 빌더 모드 진입
3. Segmented Control 전환 (빌더↔뷰어, 티어/전체/표, KO↔EN)
4. 카드 호버, 드래그, 배치
5. 필터 열기/닫기
6. 피커 모달 열기 → 캐릭터 선택
7. 이미지 복사 → 결과 확인
8. 공유 URL 생성 → 새 탭에서 열기 → 뷰어 모드 정상
9. 모바일 뷰(375px) 전체 확인
10. 태블릿 뷰(768px) 확인

- [ ] **Step 5: Commit**
```bash
git add index.html
git commit -m "design: 모달/인트로/잔여 색상 정리 + 최종 검증"
```

- [ ] **Step 6: Push**
```bash
git push origin main
```

---

## Summary

| Task | 내용 | 예상 |
|------|------|------|
| 1 | CSS Variable 교체 | 5분 |
| 2 | Card 리디자인 | 15분 |
| 3 | Tier Row 리디자인 | 10분 |
| 4 | Segmented Control | 20분 |
| 5 | Header/Tab/Button 정리 | 5분 |
| 6 | Capture 배너/푸터 | 10분 |
| 7 | 모달/잔여 + 최종검증 | 10분 |
| **Total** | | **~75분** |
