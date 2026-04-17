# Tierlist Guide Mobile UX Overhaul — Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 모바일 환경에서 티어표 빌더가 실사용 가능하도록 P0~P2 문제를 체계적으로 해결한다.

**Architecture:** 단일 `index.html` SPA 유지. CSS/JS 인라인. 변경은 3개 Phase(P0 모바일 핵심 → P1 UX → P2 성능)로 나누되, 각 Task가 독립적으로 동작 가능하도록 설계.

**Tech Stack:** Vanilla HTML5 + CSS3 + JavaScript (ES2020). No frameworks, no build tools. GitHub Pages 배포.

**Testing:** 빌드 도구/테스트 프레임워크 없음. 각 Task 완료 시 브라우저 수동 검증 (Chrome DevTools 모바일 에뮬레이션 375px, 414px, 768px).

---

## ERRATA — Post-Review Corrections (2026-03-27)

리뷰에서 발견된 문제를 반영한 정오표. **구현 시 이 섹션을 우선 참조.**

### E1. 라인 번호 무효 — 함수명 앵커로 탐색

계획서의 모든 `line NNN` 참조는 ~140줄 오프셋 오류. **라인 번호 대신 함수명/주석 앵커로 코드 위치를 찾을 것.**

| 계획서 참조 | 실제 위치 (함수/앵커) |
|---|---|
| line ~399 JS 시작 | `let DB = { meta:...` (line 396) |
| line ~659 renderAll | `function renderAll()` (line 797) |
| line ~923 makeCard | `function makeCard(c)` (line 1061) |
| line ~1064 openCharPicker input | `function openCharPicker(tierDef, catId)` (line 1163) |
| line ~1185 renderFilterBar | `function renderFilterBar()` (line 1324) |
| line ~1242 renderPool | `function renderPool()` (line 1383) |
| line ~1510 dragMove | `function dragMove(e)` (line 1646) |
| line ~1537 dragEnd | `function dragEnd(e)` (line 1670) |
| line ~1611 UTILS esc | `function esc(s)` (line 1751) |
| line ~1832 DOMContentLoaded | `document.addEventListener('DOMContentLoaded'` (line 1972) |

### E2. i18n 시스템 (I18N + T() 함수) 존재 — 반드시 사용

파일에 `I18N` 객체 (line 408~503)와 `T(key)` 함수 (line 504), `updateStaticUI()` (line 751)가 존재한다. 모든 사용자 노출 문자열은 `T()` 사용 필수.

**Task 1 수정:** 헤더 버튼에 반드시 기존 `id` 속성 유지 (`btn-add-char`, `btn-template`, `btn-share`, `btn-export`, `btn-copy-img`, `btn-save-jpg`, `btn-import`). `updateStaticUI()`가 이 ID로 텍스트를 i18n 업데이트한다. Overflow sheet 버튼에도 `T()` 사용:

```javascript
// overflow panel 내 버튼 텍스트는 동적으로:
function renderOverflowPanel() {
  const panel = document.querySelector('.overflow-panel');
  if (!panel) return;
  panel.innerHTML = `<div class="overflow-handle"></div>
    <button class="btn btn-outline btn-add-char" onclick="toggleOverflow();showAddCharModal()">${T('addChar')}</button>
    <button class="btn btn-outline" onclick="toggleOverflow();showPresetModal()">${T('template')}</button>
    <button class="btn btn-outline" onclick="toggleOverflow();shareURL()">${T('share')}</button>
    <button class="btn btn-outline" onclick="toggleOverflow();exportJSON()">${T('export')}</button>
    <button class="btn btn-primary" onclick="toggleOverflow();copyAsImage()">${T('copyImage')}</button>
    <button class="btn btn-outline" onclick="toggleOverflow();saveAsImage()">${T('saveJpg')}</button>
    <label class="btn btn-outline" style="cursor:pointer">${T('import')}<input type="file" accept=".json" style="display:none" onchange="importJSON(this.files[0]);toggleOverflow()"></label>`;
}
// renderAll() 또는 setLang()에서 호출
```

**Task 2 수정:** `renderFilterBar()` 내 라벨에 `T()` 사용:

```javascript
// "Filter" → T('searchLabel'), "Element" → T('elementLabel') 등
// summary 생성 시 T() 불필요 (내부 요약용)
// ACQ_I18N 맵 유지: const ACQ_I18N = {free:T('acqFree'),gacha:T('acqGacha'),buddy:T('acqBuddy'),custom:T('acqCustom')};
```

**Task 5 수정:** Pool 헤더에 `T('unrankedFmt')` 사용:

```javascript
header.textContent = T('unrankedFmt')(_poolChars.length, total, DB.characters.length);
```

**Task 9 수정:** 인라인 입력 placeholder에 `T()` 사용:

```javascript
// addCategory: placeholder = T('catNamePrompt')
// addTierRow: placeholder = T('tierPrompt')
```

**Task 11 수정:** `renderAll(trigger)` 시작에 `updateStaticUI()` 유지:

```javascript
function renderAll(trigger) {
  updateStaticUI();  // ← 반드시 유지
  // ... 나머지
}
```

### E3. Task 5 — Pool sentinel flex 레이아웃 수정

`.pool-grid`가 `display:flex;flex-wrap:wrap`이므로 sentinel과 load-more가 한 줄을 차지하도록:

```css
.pool-sentinel{height:1px;width:100%;flex-basis:100%}
.pool-load-more{text-align:center;padding:8px;font-size:0.75rem;color:var(--text-dim);flex-basis:100%}
```

### E4. Task 9 — addTierRow() 인덱스 계산 수정

DOM 구조: `[topAdd] + [tier-row × N] + [botAdd]`. tier-actions는 상하단에만 있으므로:

```javascript
// 기존 (잘못된): area.children[idx * 2]
// 수정: area.children[idx + 1]  // +1 for topAdd element
```

### E5. iOS Safe Area 대응

overflow sheet, info toast, tap-hint에 safe-area 패딩 추가:

```css
.overflow-panel{padding-bottom:calc(24px + env(safe-area-inset-bottom, 0px))}
.info-toast{bottom:calc(16px + env(safe-area-inset-bottom, 0px))}
.tap-hint{bottom:calc(20px + env(safe-area-inset-bottom, 0px))}
```

### E6. Pool batch 크기 통일

계획서 본문은 `POOL_BATCH = 60` (모든 배치 동일)이 맞다. 커밋 메시지의 "60 initial + 40 batch"는 오기 — `"60 per batch"` 로 수정.

---

## File Structure

이 프로젝트는 단일 파일 배포 원칙을 따르므로, 모든 변경은 하나의 파일에서 이루어진다:

- **Modify:** `index.html` — CSS (line 8~247), HTML (line 248~391), JS (line 392~1982, includes i18n block at 408~504)
  - CSS 변경: 새 컴포넌트 스타일 추가, 반응형 규칙 보강
  - HTML 변경: 헤더 구조 개편, 필터 바텀시트 마크업
  - JS 변경: 가상 스크롤, debounce, long-press, 바텀시트 로직

파일 분할하지 않음 (프로젝트 컨벤션 준수).

---

## Chunk 1: Phase 1 — P0 모바일 핵심 수정

> 이 Phase를 완료하면 모바일에서 기본적인 사용이 가능해진다.

### Task 1: 헤더 모바일 축소 — 더보기 메뉴 (overflow menu)

**문제:** 640px 이하에서 9개 버튼이 2~3줄로 넘침, 화면 20%+ 차지.
**해결:** 모바일에서 Mode/View/Lang 토글만 상시 노출, 나머지 7개(+Char, Template, Share, Export, Copy Image, Save JPG, Import)를 `⋮` 버튼 → 바텀시트로 이동.

**Files:**
- Modify: `index.html` CSS (새 스타일 추가), HTML (헤더 구조 변경), JS (메뉴 토글 함수)

**CSS 추가 (line ~36 부근, `.btn-danger` 뒤):**

```css
/* ─── Overflow Menu (mobile) ─── */
.overflow-toggle{display:none;width:36px;height:36px;border-radius:var(--radius);border:1px solid var(--border);font-size:1.2rem;color:var(--text-secondary);align-items:center;justify-content:center}
.overflow-toggle:hover{border-color:var(--accent);color:var(--accent)}

.overflow-sheet{position:fixed;inset:0;z-index:2500;display:none;flex-direction:column;justify-content:flex-end}
.overflow-sheet.open{display:flex}
.overflow-backdrop{flex:1;background:rgba(0,0,0,.5)}
.overflow-panel{background:var(--bg-secondary);border-top:1px solid var(--border);border-radius:12px 12px 0 0;padding:12px 16px 24px;display:flex;flex-direction:column;gap:6px;max-height:60vh;overflow-y:auto}
.overflow-panel .btn{text-align:left;padding:12px 16px;font-size:0.9rem;border:1px solid var(--border);border-radius:var(--radius)}
.overflow-panel .btn:active{background:rgba(212,164,74,0.15)}
.overflow-handle{width:40px;height:4px;background:var(--text-dim);border-radius:2px;margin:0 auto 10px;opacity:.5}

@media(max-width:640px){
  .overflow-toggle{display:flex}
  .header-actions .desktop-only{display:none}
}
```

**HTML 변경 — 헤더 (line 262~286):**

현재 `<div class="header-actions">` 내부의 버튼들을 두 그룹으로 분리:

```html
<header class="header">
  <h1>AE Tier List Builder</h1>
  <div class="header-actions">
    <!-- 항상 노출 -->
    <div class="toggle-group">
      <button id="btn-viewer" onclick="setMode('viewer')">Viewer</button>
      <button id="btn-builder" class="active" onclick="setMode('builder')">Builder</button>
    </div>
    <div class="toggle-group">
      <button id="btn-tier" class="active" onclick="setView('tier')">Tier</button>
      <button id="btn-all" onclick="setView('all')">All</button>
      <button id="btn-table" onclick="setView('table')">Table</button>
    </div>
    <div class="toggle-group">
      <button id="btn-ko" class="active" onclick="setLang('ko')">KO</button>
      <button id="btn-en" onclick="setLang('en')">EN</button>
    </div>
    <!-- 데스크톱에서만 직접 노출 -->
    <button class="btn btn-outline btn-sm btn-add-char desktop-only" onclick="showAddCharModal()">+ Char</button>
    <button class="btn btn-outline btn-sm desktop-only" onclick="showPresetModal()">Template</button>
    <button class="btn btn-outline btn-sm desktop-only" onclick="shareURL()">Share</button>
    <button class="btn btn-outline btn-sm desktop-only" onclick="exportJSON()">Export</button>
    <button class="btn btn-primary btn-sm desktop-only" onclick="copyAsImage()">Copy Image</button>
    <button class="btn btn-outline btn-sm desktop-only" onclick="saveAsImage()">Save JPG</button>
    <label class="btn btn-outline btn-sm desktop-only" style="cursor:pointer">Import<input type="file" accept=".json" style="display:none" onchange="importJSON(this.files[0])"></label>
    <!-- 모바일 더보기 -->
    <button class="overflow-toggle" onclick="toggleOverflow()" aria-label="More actions">&#8942;</button>
  </div>
</header>

<!-- Overflow Bottom Sheet (헤더 밖, body 직속) -->
<div class="overflow-sheet" id="overflow-sheet">
  <div class="overflow-backdrop" onclick="toggleOverflow()"></div>
  <div class="overflow-panel">
    <div class="overflow-handle"></div>
    <button class="btn btn-outline btn-add-char" onclick="toggleOverflow();showAddCharModal()">+ Add Character</button>
    <button class="btn btn-outline" onclick="toggleOverflow();showPresetModal()">Template</button>
    <button class="btn btn-outline" onclick="toggleOverflow();shareURL()">Share URL</button>
    <button class="btn btn-outline" onclick="toggleOverflow();exportJSON()">Export JSON</button>
    <button class="btn btn-primary" onclick="toggleOverflow();copyAsImage()">Copy as Image</button>
    <button class="btn btn-outline" onclick="toggleOverflow();saveAsImage()">Save JPG</button>
    <label class="btn btn-outline" style="cursor:pointer" onclick="toggleOverflow()">Import JSON<input type="file" accept=".json" style="display:none" onchange="importJSON(this.files[0])"></label>
  </div>
</div>
```

**JS 추가 (UTILS 섹션, line ~1611 부근):**

```javascript
/* ─── Overflow Menu ─── */
function toggleOverflow() {
  document.getElementById('overflow-sheet').classList.toggle('open');
}
```

- [ ] **Step 1:** CSS에 `.overflow-*` 스타일 블록 추가
- [ ] **Step 2:** HTML 헤더를 desktop-only / overflow 구조로 재구성
- [ ] **Step 3:** HTML에 overflow-sheet 마크업 추가 (body 직속, intro-screen 뒤)
- [ ] **Step 4:** JS에 `toggleOverflow()` 함수 추가
- [ ] **Step 5:** 검증 — DevTools 375px: 토글 3개 + ⋮만 보이는지, ⋮ 클릭 시 바텀시트 올라오는지, 백드롭 탭 시 닫히는지
- [ ] **Step 6:** 검증 — 1024px: desktop-only 버튼들 정상 노출, ⋮ 숨겨짐
- [ ] **Step 7:** Commit: `feat: mobile overflow menu for header actions`

---

### Task 2: 필터바 접이식 + 수평 스크롤 칩

**문제:** 30+ 필터 태그가 flex-wrap으로 5줄 이상 → Pool이 fold 아래로 밀림.
**해결:** 필터바를 접이식(collapse)으로 변경. 기본 접힌 상태에서 검색 + 1줄 요약만 노출. 펼치면 전체 필터 표시. 속성/무기 행은 수평 스크롤.

**Files:**
- Modify: `index.html` CSS, JS (`renderFilterBar` 함수)

**CSS 추가:**

```css
/* ─── Collapsible Filter ─── */
.filter-toggle{display:flex;align-items:center;gap:8px;padding:10px 16px;background:var(--bg-pool);border-top:2px solid var(--border);cursor:pointer;user-select:none}
.filter-toggle .ft-arrow{transition:transform .2s;font-size:0.7rem;color:var(--text-dim)}
.filter-toggle.open .ft-arrow{transform:rotate(90deg)}
.filter-toggle .ft-summary{font-size:0.75rem;color:var(--text-dim);flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.filter-body{max-height:0;overflow:hidden;transition:max-height .25s ease-out}
.filter-body.open{max-height:500px;overflow:visible}

@media(max-width:640px){
  .filter-row{flex-wrap:nowrap;overflow-x:auto;-webkit-overflow-scrolling:touch;scrollbar-width:none;padding-bottom:4px}
  .filter-row::-webkit-scrollbar{display:none}
  .filter-row label{position:sticky;left:0;background:var(--bg-pool);z-index:1;padding-right:4px}
}
```

**JS 변경 — `renderFilterBar()` (line 1185~1227):**

현재 `filter-bar` div의 innerHTML을 교체하는 로직을 다음으로 변경:

```javascript
function renderFilterBar() {
  const bar = document.getElementById('filter-bar');
  const f = S.ui.filters;
  const isOpen = bar.dataset.open === '1';

  // Active filter summary
  const parts = [];
  if (S.ui.query) parts.push(`"${S.ui.query}"`);
  if (f.elements.length) parts.push(f.elements.map(e => ELEMENT_KO[e]).join(','));
  if (f.weapons.length) parts.push(f.weapons.map(w => WEAPON_KO[w]).join(','));
  if (f.styles.length) parts.push(f.styles.join(','));
  if (f.rarities.length) parts.push(f.rarities.map(r => r+'★').join(','));
  if (f.sa) parts.push('SA');
  if (f.ls) parts.push(f.ls);
  if (f.acq.length) parts.push(f.acq.join(','));
  const summary = parts.length ? parts.join(' | ') : 'No filters';

  bar.innerHTML = `
    <div class="filter-toggle ${isOpen?'open':''}" onclick="toggleFilterBar()">
      <span class="ft-arrow">&#9654;</span>
      <label style="min-width:auto;cursor:pointer">Filter</label>
      <span class="ft-summary">${esc(summary)}</span>
      <input class="search-input" type="text" placeholder="Search..." value="${esc(S.ui.query)}"
        onclick="event.stopPropagation()" oninput="debounceSearch(this.value)" style="width:140px;font-size:0.8rem">
      ${parts.length ? '<span class="filter-reset" onclick="event.stopPropagation();resetFilters()">Reset</span>' : ''}
    </div>
    <div class="filter-body ${isOpen?'open':''}" id="filter-body">
      <div style="padding:8px 16px">
        <div class="filter-row">
          <label>Element</label>
          ${['fire','water','earth','wind','thunder','shade','crystal','null'].map(el =>
            `<button class="ftag ${f.elements.includes(el)?'on':''}" onclick="toggleFilter('elements','${el}')"><img src="images/elements/${EL_ICON[el]}" width="18" height="18"> ${ELEMENT_KO[el]}</button>`
          ).join('')}
        </div>
        <div class="filter-row">
          <label>Weapon</label>
          ${['sword','katana','axe','lance','bow','fist','hammer','staff'].map(w =>
            `<button class="ftag ${f.weapons.includes(w)?'on':''}" onclick="toggleFilter('weapons','${w}')"><img src="images/weapons/${WP_ICON[w]}" width="18" height="18"> ${WEAPON_KO[w]}</button>`
          ).join('')}
        </div>
        <div class="filter-row">
          <label>Style</label>
          ${['NS','AS','ES','Alter'].map(s =>
            `<button class="ftag ${f.styles.includes(s)?'on':''}" onclick="toggleFilter('styles','${s}')">${s}</button>`
          ).join('')}
          <span style="margin-left:8px"></span>
          ${[4,5].map(r =>
            `<button class="ftag ${f.rarities.includes(r)?'on':''}" onclick="toggleFilter('rarities',${r})">${r}★</button>`
          ).join('')}
          <button class="ftag ${f.sa===true?'on':''}" onclick="S.ui.filters.sa=S.ui.filters.sa?null:true;renderAll()">SA</button>
          <span style="margin-left:8px"></span>
          <button class="ftag ${f.ls==='light'?'on':''}" onclick="S.ui.filters.ls=S.ui.filters.ls==='light'?null:'light';renderAll()" style="color:var(--ls-light)">Light</button>
          <button class="ftag ${f.ls==='shadow'?'on':''}" onclick="S.ui.filters.ls=S.ui.filters.ls==='shadow'?null:'shadow';renderAll()" style="color:var(--ls-shadow)">Shadow</button>
        </div>
        <div class="filter-row">
          <label>Acquire</label>
          ${['free','gacha','buddy','custom'].map(a =>
            `<button class="ftag ${f.acq.includes(a)?'on':''}" onclick="toggleFilter('acq','${a}')">${{free:'Free',gacha:'Gacha',buddy:'Buddy',custom:'Custom'}[a]}</button>`
          ).join('')}
          <button class="ftag ${f.excludeBuddy?'on':''}" onclick="S.ui.filters.excludeBuddy=!S.ui.filters.excludeBuddy;renderAll()" style="${f.excludeBuddy?'border-color:#e74c3c;color:#e74c3c':''}">Buddy &#10005;</button>
        </div>
      </div>
    </div>`;
}

function toggleFilterBar() {
  const bar = document.getElementById('filter-bar');
  bar.dataset.open = bar.dataset.open === '1' ? '0' : '1';
  renderFilterBar();
}
```

- [ ] **Step 1:** CSS에 `.filter-toggle`, `.filter-body`, 모바일 `.filter-row` 수평 스크롤 추가
- [ ] **Step 2:** `renderFilterBar()` 함수를 접이식 구조로 교체
- [ ] **Step 3:** `toggleFilterBar()` 함수 추가
- [ ] **Step 4:** 검증 — 375px: 필터바 접힌 상태에서 검색+요약만 보임, 탭하면 펼침, 속성/무기 행 수평 스크롤
- [ ] **Step 5:** 검증 — 1024px: 동일하게 작동 (데스크톱에서도 접이식이 공간 효율적)
- [ ] **Step 6:** Commit: `feat: collapsible filter bar with horizontal scroll on mobile`

---

### Task 3: 검색 debounce + 한글 IME 대응

**문제:** 매 keydown마다 `renderAll()` → 한글 조합 중 깜빡임 + 성능 저하.
**해결:** 150ms debounce + composing 플래그로 IME 조합 완료 후에만 반영.

**Files:**
- Modify: `index.html` JS

**JS 추가 (UTILS 섹션):**

```javascript
/* ─── Debounced Search ─── */
let _searchTimer = null;
let _isComposing = false;

function debounceSearch(val) {
  if (_isComposing) return;
  clearTimeout(_searchTimer);
  _searchTimer = setTimeout(() => {
    S.ui.query = val;
    renderAll();
  }, 150);
}

// IME composition events — attach once after DOM ready
function setupSearchIME() {
  document.addEventListener('compositionstart', () => { _isComposing = true; });
  document.addEventListener('compositionend', (e) => {
    _isComposing = false;
    // compositionend 후 input 이벤트가 한 번 더 오므로 직접 트리거
    if (e.target.classList.contains('search-input')) {
      debounceSearch(e.target.value);
    }
  });
}
```

**JS 변경 — DOMContentLoaded (line 1832)에 `setupSearchIME()` 호출 추가:**

```javascript
document.addEventListener('DOMContentLoaded', () => {
  setupSearchIME();  // ← 추가
  loadIntroBanner();
  if (sessionStorage.getItem('ae_intro_dismissed')) {
    document.getElementById('intro-screen').style.display = 'none';
  }
  init();
});
```

**JS 변경 — Picker 검색도 동일 적용:**

`openCharPicker()` 내 (line 1064) input 이벤트 핸들러:

```javascript
// 기존:
input.addEventListener('input', () => {
  _picker.query = input.value;
  renderPickerGrid();
});

// 변경:
let _pickerTimer = null;
input.addEventListener('input', () => {
  if (_isComposing) return;
  clearTimeout(_pickerTimer);
  _pickerTimer = setTimeout(() => {
    _picker.query = input.value;
    renderPickerGrid();
  }, 150);
});
input.addEventListener('compositionend', () => {
  _picker.query = input.value;
  renderPickerGrid();
});
```

- [ ] **Step 1:** `debounceSearch()`, `_isComposing`, `setupSearchIME()` 함수 추가
- [ ] **Step 2:** `DOMContentLoaded`에 `setupSearchIME()` 추가
- [ ] **Step 3:** `renderFilterBar()` 내 검색 input의 `oninput`을 `debounceSearch(this.value)`로 변경 (Task 2에서 이미 반영)
- [ ] **Step 4:** Picker 검색 input에도 debounce + compositionend 적용
- [ ] **Step 5:** 검증 — 한글 "마이" 입력 시 ㅁ→마→마이 중간에 리렌더 안 됨, 완성 후 150ms 뒤 필터 적용
- [ ] **Step 6:** Commit: `feat: debounced search with Korean IME support`

---

### Task 4: touch-action 조건부 적용 — Pool 스크롤 복원

**문제:** 모든 카드에 `touch-action: none` → Pool 영역 스크롤 불가.
**해결:** 카드 기본은 `touch-action: pan-y` (세로 스크롤 허용), 드래그 시작 판정(8px 이동) 후에만 `none`으로 전환.

**Files:**
- Modify: `index.html` JS (`makeCard`, `dragStart`, `dragEnd`)

**JS 변경 — `makeCard()` (line 927):**

```javascript
// 기존:
card.style.touchAction = 'none';

// 변경:
card.style.touchAction = 'pan-y';
```

**JS 변경 — `dragMove()` (line 1510~1511):**

```javascript
// 기존:
if (!_drag.moved && Math.abs(dx) < 8 && Math.abs(dy) < 8) return;
_drag.moved = true;

// 변경:
if (!_drag.moved && Math.abs(dx) < 8 && Math.abs(dy) < 8) return;
_drag.moved = true;
_drag.origCard.style.touchAction = 'none'; // 드래그 확정 후 스크롤 차단
```

**JS 변경 — `dragEnd()` (line 1537):**

```javascript
// 기존:
if (_drag.origCard) _drag.origCard.style.opacity = '1';

// 변경:
if (_drag.origCard) {
  _drag.origCard.style.opacity = '1';
  _drag.origCard.style.touchAction = 'pan-y'; // 복원
}
```

- [ ] **Step 1:** `makeCard()`의 `touchAction`을 `pan-y`로 변경
- [ ] **Step 2:** `dragMove()`에서 moved 확정 시 `touchAction = 'none'` 설정
- [ ] **Step 3:** `dragEnd()`에서 `touchAction = 'pan-y'` 복원
- [ ] **Step 4:** 검증 — 모바일에서 Pool 영역 세로 스크롤 정상 작동
- [ ] **Step 5:** 검증 — 카드 드래그는 여전히 정상 (8px 이동 후 스크롤 차단)
- [ ] **Step 6:** Commit: `fix: restore scroll in pool area on mobile (conditional touch-action)`

---

### Task 5: Pool 가상 스크롤 (Lazy Render)

**문제:** 366개 카드를 전부 DOM에 렌더 → 저사양 모바일 버벅임.
**해결:** IntersectionObserver 기반 lazy render. 초기 60개만 렌더, 하단 센티넬 도달 시 40개씩 추가.

**Files:**
- Modify: `index.html` JS (`renderPool`), CSS

**CSS 추가:**

```css
.pool-sentinel{height:1px;width:100%}
.pool-load-more{text-align:center;padding:8px;font-size:0.75rem;color:var(--text-dim)}
```

**JS 변경 — Pool 관련 상태 + `renderPool()` (line 1242~1260):**

```javascript
/* ─── Pool Lazy Render ─── */
const POOL_BATCH = 60;
let _poolChars = []; // 필터 적용된 미배치 캐릭터 전체
let _poolRendered = 0;
let _poolObserver = null;

function renderPool() {
  const grid = document.getElementById('pool-grid');
  const header = document.getElementById('pool-header');
  grid.innerHTML = '';

  const catId = S.workspace.activeCategory;
  const placed = catId ? getPlacedIds(catId) : new Set();

  _poolChars = [];
  DB.characters.forEach(c => {
    if (placed.has(c.id)) return;
    if (!charMatchesFilter(c)) return;
    _poolChars.push(c);
  });

  const total = DB.characters.length - placed.size;
  header.textContent = `Unranked: ${_poolChars.length}/${total} shown (${DB.characters.length} total)`;

  _poolRendered = 0;
  renderPoolBatch(grid);
  setupPoolObserver(grid);
}

function renderPoolBatch(grid) {
  const end = Math.min(_poolRendered + POOL_BATCH, _poolChars.length);
  for (let i = _poolRendered; i < end; i++) {
    grid.appendChild(makeCard(_poolChars[i]));
  }
  _poolRendered = end;

  // Remove old sentinel, add new one if more chars remain
  const oldSentinel = grid.querySelector('.pool-sentinel');
  if (oldSentinel) oldSentinel.remove();

  if (_poolRendered < _poolChars.length) {
    const sentinel = document.createElement('div');
    sentinel.className = 'pool-sentinel';
    grid.appendChild(sentinel);

    const info = document.createElement('div');
    info.className = 'pool-load-more';
    info.textContent = `${_poolRendered} / ${_poolChars.length} loaded`;
    grid.appendChild(info);
  }
}

function setupPoolObserver(grid) {
  if (_poolObserver) _poolObserver.disconnect();
  _poolObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting && _poolRendered < _poolChars.length) {
        // Remove info text
        const info = grid.querySelector('.pool-load-more');
        if (info) info.remove();
        renderPoolBatch(grid);
        // Re-observe new sentinel
        const newSentinel = grid.querySelector('.pool-sentinel');
        if (newSentinel) _poolObserver.observe(newSentinel);
      }
    });
  }, { root: null, rootMargin: '200px' });

  const sentinel = grid.querySelector('.pool-sentinel');
  if (sentinel) _poolObserver.observe(sentinel);
}
```

- [ ] **Step 1:** CSS에 `.pool-sentinel`, `.pool-load-more` 추가
- [ ] **Step 2:** Pool 관련 상태 변수(`_poolChars`, `_poolRendered`, `_poolObserver`, `POOL_BATCH`) 추가
- [ ] **Step 3:** `renderPool()` 함수를 lazy render 버전으로 교체
- [ ] **Step 4:** `renderPoolBatch()`, `setupPoolObserver()` 함수 추가
- [ ] **Step 5:** 검증 — Pool에 초기 60개만 렌더됨, 스크롤 시 40개씩 추가 로드
- [ ] **Step 6:** 검증 — 필터 변경 시 Pool 리셋 + 재로드 정상
- [ ] **Step 7:** 검증 — 카드 드래그/탭 여전히 정상
- [ ] **Step 8:** Commit: `perf: lazy-render pool with IntersectionObserver (60 initial + 40 batch)`

---

## Chunk 2: Phase 2 — P1 UX 개선

> Pool이 사용 가능해진 상태에서, 세부 인터랙션을 모바일 친화적으로 개선.

### Task 6: Long-press → Context Menu (모바일 이동 메뉴)

**문제:** 우클릭 context menu가 모바일에서 접근 어려움.
**해결:** 500ms long-press 시 이동 메뉴 표시. 기존 `contextmenu` 이벤트와 공존.

**Files:**
- Modify: `index.html` JS (`makeCard` 내 이벤트 바인딩)

**JS 변경 — `makeCard()` Builder 모드 이벤트 (line 948~954):**

```javascript
if (S.mode === 'builder') {
  let _lpTimer = null;
  card.addEventListener('pointerdown', e => {
    if (e.button !== 0) return;
    // Long-press timer
    _lpTimer = setTimeout(() => {
      _lpTimer = null;
      showMoveMenu(c, e);
    }, 500);
    dragStart(c.id, card, e);
  });
  card.addEventListener('pointerup', () => { if (_lpTimer) { clearTimeout(_lpTimer); _lpTimer = null; } });
  card.addEventListener('pointermove', (e) => {
    // 이동하면 long-press 취소
    if (_lpTimer && _drag && _drag.moved) { clearTimeout(_lpTimer); _lpTimer = null; }
  });
  card.addEventListener('contextmenu', e => { e.preventDefault(); showMoveMenu(c, e); });
}
```

**주의:** `dragStart`에서 `_drag.moved`가 true가 되면(8px 이동) long-press 타이머를 취소해야 한다. 드래그와 long-press가 충돌하지 않도록:
- 500ms 안에 8px 이동 → 드래그 (long-press 취소)
- 500ms 동안 정지 → context menu (드래그 취소)

**JS 변경 — `dragStart()` 앞부분에 long-press 드래그 취소 로직:**

long-press에서 context menu가 뜨면 드래그를 중단해야 하므로, `showMoveMenu` 호출 시 기존 _drag 정리:

```javascript
function showMoveMenu(c, e) {
  // 진행 중인 드래그 취소
  if (_drag) {
    if (_drag.origCard) _drag.origCard.style.opacity = '1';
    if (_drag.ghost) _drag.ghost.remove();
    document.removeEventListener('pointermove', dragMove);
    document.removeEventListener('pointerup', dragEnd);
    document.removeEventListener('pointercancel', dragEnd);
    _drag = null;
  }
  closeAllPopups();
  // ... 기존 코드 계속
```

- [ ] **Step 1:** `makeCard()` 내 pointerdown에 long-press 타이머 추가
- [ ] **Step 2:** pointermove/pointerup에서 타이머 취소 로직 추가
- [ ] **Step 3:** `showMoveMenu()` 시작부에 _drag 정리 코드 추가
- [ ] **Step 4:** 검증 — 모바일에서 카드 500ms 홀드 → 이동 메뉴 표시
- [ ] **Step 5:** 검증 — 빠른 탭 → tap-select, 드래그 이동 → 드래그, 긴 홀드 → 메뉴 (3가지 분기 테스트)
- [ ] **Step 6:** Commit: `feat: long-press context menu for mobile character placement`

---

### Task 7: Picker 스크롤 위치 보존

**문제:** 캐릭터 추가 시 `renderPickerGrid()` → innerHTML 교체 → 스크롤 위치 리셋.
**해결:** 렌더 전 scrollTop 저장, 렌더 후 복원.

**Files:**
- Modify: `index.html` JS (`renderPickerGrid`)

**JS 변경 — `renderPickerGrid()` (line 1135):**

```javascript
function renderPickerGrid() {
  if (!_picker) return;
  const grid = document.getElementById('picker-grid');
  const countEl = document.getElementById('picker-count');
  const body = grid.parentElement; // .picker-body
  const scrollY = body ? body.scrollTop : 0; // ← 저장

  grid.innerHTML = '';
  // ... 기존 로직 동일 ...

  // 렌더 후 스크롤 복원
  if (body) requestAnimationFrame(() => { body.scrollTop = scrollY; });
}
```

- [ ] **Step 1:** `renderPickerGrid()` 시작에 `body.scrollTop` 저장
- [ ] **Step 2:** 함수 끝에 `requestAnimationFrame`으로 복원
- [ ] **Step 3:** 검증 — Picker에서 캐릭터 추가 시 스크롤 위치 유지
- [ ] **Step 4:** Commit: `fix: preserve picker scroll position on character add`

---

### Task 8: All View 모바일 세로 스택

**문제:** 카테고리 4개면 수평 스크롤만 가능, 세로 스택 없음.
**해결:** 640px 이하에서 `flex-direction: column`.

**Files:**
- Modify: `index.html` CSS

**CSS 변경 — 기존 `@media(max-width:640px)` 블록에 추가:**

```css
@media(max-width:640px){
  /* ... 기존 규칙들 ... */
  .mcat-grid{flex-direction:column}
  .mcat-col{min-width:unset}
}
```

- [ ] **Step 1:** 640px 미디어쿼리에 `.mcat-grid` 세로 스택 규칙 추가
- [ ] **Step 2:** 검증 — 375px에서 All View 카테고리가 세로로 쌓임
- [ ] **Step 3:** 검증 — 1024px에서 기존 수평 레이아웃 유지
- [ ] **Step 4:** Commit: `fix: stack All View columns vertically on mobile`

---

### Task 9: prompt() → 인라인 입력 교체

**문제:** 카테고리/티어 추가/수정에 `prompt()` 사용 → 모바일 UX 파괴.
**해결:** 인라인 input 또는 작은 모달로 교체.

**Files:**
- Modify: `index.html` CSS, JS (`addCategory`, `editCategoryName`, `addTierRow`, `resetAll`)

**CSS 추가:**

```css
/* ─── Inline Input ─── */
.inline-input{display:inline-flex;align-items:center;gap:4px}
.inline-input input{width:120px;padding:4px 8px;font-size:0.8rem}
.inline-input button{padding:4px 8px;font-size:0.75rem}
```

**JS 변경 — `addCategory()` (line 754):**

```javascript
function addCategory() {
  const bar = document.getElementById('cat-bar');
  // 이미 인라인 입력 중이면 무시
  if (bar.querySelector('.inline-input')) return;

  const wrap = document.createElement('span');
  wrap.className = 'inline-input';
  wrap.innerHTML = `<input type="text" placeholder="Category name" autofocus>
    <button class="btn btn-sm btn-primary" data-action="ok">OK</button>
    <button class="btn btn-sm btn-outline" data-action="cancel">X</button>`;
  bar.insertBefore(wrap, bar.querySelector('.cat-add'));

  const input = wrap.querySelector('input');
  input.focus();

  const confirm = () => {
    const name = input.value.trim();
    if (name) {
      const id = 'cat_' + Date.now();
      S.workspace.categories.push({ id, name });
      S.workspace.activeCategory = id;
      autoSave();
    }
    wrap.remove();
    renderAll();
  };

  wrap.querySelector('[data-action="ok"]').onclick = confirm;
  wrap.querySelector('[data-action="cancel"]').onclick = () => { wrap.remove(); };
  input.addEventListener('keydown', e => {
    if (e.key === 'Enter') confirm();
    if (e.key === 'Escape') wrap.remove();
  });
}
```

**JS 변경 — `editCategoryName()` (line 773):**

```javascript
function editCategoryName(cat) {
  const tab = [...document.querySelectorAll('.cat-tab')].find(t =>
    t.querySelector('.cat-name')?.textContent === cat.name
  );
  if (!tab) return;

  const nameSpan = tab.querySelector('.cat-name');
  const origText = nameSpan.textContent;
  const input = document.createElement('input');
  input.type = 'text';
  input.value = origText;
  input.style.cssText = 'width:80px;padding:2px 4px;font-size:0.8rem';
  nameSpan.replaceWith(input);
  input.focus();
  input.select();

  const finish = () => {
    const val = input.value.trim();
    if (val && val !== origText) { cat.name = val; autoSave(); }
    renderAll();
  };

  input.addEventListener('blur', finish);
  input.addEventListener('keydown', e => {
    if (e.key === 'Enter') { e.preventDefault(); input.blur(); }
    if (e.key === 'Escape') { input.value = origText; input.blur(); }
  });
}
```

**JS 변경 — `addTierRow()` (line 841):**

```javascript
function addTierRow(idx) {
  const area = document.getElementById('tier-area');
  // 이미 인라인 입력 중이면 무시
  if (area.querySelector('.inline-input')) return;

  const target = idx === 0 ? area.firstElementChild : area.children[idx * 2]; // accounts for tier-actions
  const wrap = document.createElement('div');
  wrap.className = 'inline-input';
  wrap.style.cssText = 'justify-content:center;padding:6px';
  wrap.innerHTML = `<input type="text" placeholder="Tier label (e.g. S)" autofocus style="width:80px">
    <button class="btn btn-sm btn-primary" data-action="ok">Add</button>
    <button class="btn btn-sm btn-outline" data-action="cancel">Cancel</button>`;

  if (target) area.insertBefore(wrap, target);
  else area.appendChild(wrap);

  const input = wrap.querySelector('input');
  input.focus();

  const confirm = () => {
    const label = input.value.trim();
    if (label) {
      const color = TIER_COLORS[S.workspace.tierDefs.length % TIER_COLORS.length];
      S.workspace.tierDefs.splice(idx, 0, { id:'t_'+Date.now(), label, color });
      autoSave();
    }
    wrap.remove();
    renderAll();
  };

  wrap.querySelector('[data-action="ok"]').onclick = confirm;
  wrap.querySelector('[data-action="cancel"]').onclick = () => { wrap.remove(); };
  input.addEventListener('keydown', e => {
    if (e.key === 'Enter') confirm();
    if (e.key === 'Escape') wrap.remove();
  });
}
```

**JS 변경 — `resetAll()` (line 511):**

`prompt()` 대신 작은 confirm 모달:

```javascript
function resetAll() {
  // 기존 모달 재사용 스타일
  const overlay = document.createElement('div');
  overlay.className = 'modal-overlay';
  overlay.innerHTML = `<div class="modal">
    <h2>Reset</h2>
    <p>What would you like to reset?</p>
    <div class="preset-list">
      <button class="preset-btn" data-choice="1"><strong>Placements only</strong><small>Keep categories and tiers, clear all placements</small></button>
      <button class="preset-btn" data-choice="2"><strong>Everything</strong><small>Reset to Prydwen preset</small></button>
      <button class="preset-btn" style="border-color:var(--text-dim)"><strong>Cancel</strong><small>Go back</small></button>
    </div>
  </div>`;

  document.body.appendChild(overlay);

  overlay.querySelectorAll('.preset-btn').forEach(btn => {
    btn.onclick = () => {
      const choice = btn.dataset.choice;
      if (choice === '1') { S.workspace.placements = {}; autoSave(); renderAll(); }
      else if (choice === '2') { S.workspace.placements = {}; applyPreset('prydwen'); }
      overlay.remove();
    };
  });
}
```

- [ ] **Step 1:** CSS에 `.inline-input` 스타일 추가
- [ ] **Step 2:** `addCategory()` → 인라인 input으로 교체
- [ ] **Step 3:** `editCategoryName()` → 탭 내 인라인 편집으로 교체
- [ ] **Step 4:** `addTierRow()` → 인라인 input으로 교체
- [ ] **Step 5:** `resetAll()` → 모달 선택으로 교체
- [ ] **Step 6:** 검증 — 모바일에서 카테고리 추가/수정/리셋이 시스템 prompt 없이 작동
- [ ] **Step 7:** 검증 — Enter/Escape 키보드 동작, 바깥 클릭 시 취소 동작
- [ ] **Step 8:** Commit: `feat: replace prompt() dialogs with inline inputs and modals`

---

### Task 10: 모바일 캐릭터 정보 토스트 (Tooltip 대체)

**문제:** mouseenter Tooltip이 터치에서 안 뜸.
**해결:** Viewer 모드 또는 tap-select 미활성 상태에서 카드 탭 → 하단 토스트로 정보 표시.

**Files:**
- Modify: `index.html` CSS, JS

**CSS 추가:**

```css
/* ─── Info Toast ─── */
.info-toast{position:fixed;bottom:16px;left:50%;transform:translateX(-50%);z-index:1800;background:var(--bg-secondary);border:1px solid var(--border);border-radius:8px;padding:10px 16px;font-size:0.8rem;color:var(--text-primary);box-shadow:0 4px 16px rgba(0,0,0,.5);display:flex;align-items:center;gap:10px;max-width:90vw;animation:tapHintIn .2s ease-out}
.info-toast img{width:40px;height:40px;border-radius:6px;flex-shrink:0}
.info-toast .it-details{line-height:1.5}
.info-toast .it-name{font-weight:700;color:var(--accent)}
.info-toast .it-sub{color:var(--text-secondary);font-size:0.72rem}
```

**JS 추가:**

```javascript
/* ─── Info Toast (mobile tooltip replacement) ─── */
let _toastEl = null;
let _toastTimer = null;

function showInfoToast(c) {
  hideInfoToast();
  const el = document.createElement('div');
  el.className = 'info-toast';
  el.innerHTML = `
    <img src="${c.customImg || ('images/icons/' + c.icon)}" alt="${esc(charName(c))}">
    <div class="it-details">
      <div class="it-name">${esc(c.nameKo)}</div>
      <div class="it-sub">${esc(c.nameEn)}</div>
      <div class="it-sub">${c.style} ${c.rarity}★${c.sa?' SA':''} | ${c.elementKo||''} ${c.weaponKo||''} ${c.attackType||''}</div>
      ${c.ls ? `<div class="it-sub">${c.ls==='light'?'Light':'Shadow'}</div>` : ''}
    </div>`;
  document.body.appendChild(el);
  _toastEl = el;
  _toastTimer = setTimeout(hideInfoToast, 3000);

  // Tap anywhere to dismiss
  el.addEventListener('pointerdown', hideInfoToast);
}

function hideInfoToast() {
  clearTimeout(_toastTimer);
  if (_toastEl) { _toastEl.remove(); _toastEl = null; }
}
```

**JS 변경 — `makeCard()` (line 957~959)에 터치 토스트 트리거 추가:**

```javascript
// 기존 tooltip (마우스)
card.addEventListener('mouseenter', e => showTooltip(c, e));
card.addEventListener('mouseleave', hideTooltip);
card.addEventListener('mousemove', moveTooltip);

// 터치 토스트 (Viewer 모드 또는 Builder에서 간단한 탭)
card.addEventListener('click', () => {
  if (S.mode === 'viewer' || !('ontouchstart' in window)) return; // 마우스는 tooltip 사용
  // Builder + 터치: tap-select가 처리하므로 여기선 skip
});
// Viewer 모드 전용
if (S.mode !== 'builder') {
  card.addEventListener('pointerup', (e) => {
    if (e.pointerType === 'touch') showInfoToast(c);
  });
}
```

- [ ] **Step 1:** CSS에 `.info-toast` 스타일 추가
- [ ] **Step 2:** `showInfoToast()`, `hideInfoToast()` 함수 추가
- [ ] **Step 3:** `makeCard()` Viewer 모드에서 터치 시 토스트 연결
- [ ] **Step 4:** 검증 — Viewer 모드 모바일: 카드 탭 → 하단 토스트 3초 표시
- [ ] **Step 5:** 검증 — Builder 모드에서는 기존 tap-select 우선, 토스트 미간섭
- [ ] **Step 6:** 검증 — 데스크톱에서는 기존 mouseenter 툴팁 유지
- [ ] **Step 7:** Commit: `feat: info toast for mobile card details (tooltip replacement)`

---

## Chunk 3: Phase 3 — P2 성능/품질

> 체감 성능 개선 및 코드 품질 향상.

### Task 11: renderAll() 부분 렌더 최적화

**문제:** 필터 토글, 검색 시 전체 DOM 재생성 → 불필요한 이미지 재로드.
**해결:** 변경 원인(trigger)에 따라 필요한 영역만 렌더.

**Files:**
- Modify: `index.html` JS

**JS 변경 — `renderAll()` (line 659)에 optional trigger 파라미터:**

```javascript
function renderAll(trigger) {
  // Credits
  const dv = document.getElementById('data-version');
  const dt = document.getElementById('data-total');
  if (dv) dv.textContent = DB.meta.version || '-';
  if (dt) dt.textContent = DB.meta.total || DB.characters.length;

  const elTier = document.getElementById('tier-area');
  const elCat = document.getElementById('cat-bar');
  const elPool = document.getElementById('pool-area');
  const elTable = document.getElementById('table-view');
  const elAll = document.getElementById('all-view');

  // Hide all first
  [elTier,elCat,elPool,elTable,elAll].forEach(e => e.style.display = 'none');

  if (currentView === 'table') {
    elTable.style.display = '';
    if (trigger !== 'placement') renderFilterBar();
    renderTableView();
    renderStats();
  } else if (currentView === 'all') {
    elAll.style.display = '';
    if (trigger !== 'placement') renderFilterBar();
    renderAllView();
    renderStats();
  } else {
    [elTier,elCat,elPool].forEach(e => e.style.display = '');
    if (trigger !== 'filter') renderCategoryTabs();
    renderTierRows();
    if (trigger !== 'placement') renderFilterBar();
    if (trigger !== 'category') renderPool();
    renderStats();
  }
}
```

그리고 호출처에 trigger 전달:

```javascript
// toggleFilter / resetFilters 내:
renderAll('filter');

// addPlacement / removePlacement 후:
renderAll('placement');

// tab 클릭 (category switch):
renderAll('category');
```

- [ ] **Step 1:** `renderAll(trigger)` 시그니처 추가, 조건부 렌더 분기
- [ ] **Step 2:** `toggleFilter`, `resetFilters`에서 `renderAll('filter')` 호출
- [ ] **Step 3:** 배치 변경 코드에서 `renderAll('placement')` 호출
- [ ] **Step 4:** 카테고리 탭 전환에서 `renderAll('category')` 호출
- [ ] **Step 5:** 검증 — 필터 토글 시 카테고리 탭 불필요하게 재렌더 안 됨
- [ ] **Step 6:** 검증 — 전체 기능 정상 동작 (regression 없음)
- [ ] **Step 7:** Commit: `perf: partial render based on change trigger`

---

### Task 12: 이미지 export Retina 대응

**문제:** `scale:1`로 캡처 → Retina에서 흐릿.
**해결:** `devicePixelRatio` 적용.

**Files:**
- Modify: `index.html` JS (`captureArea`)

**JS 변경 — `captureArea()` (line 1634):**

```javascript
// 기존:
const canvas = await html2canvas(area, {
  backgroundColor: '#1a1a2e',
  scale: 1,
  useCORS: true,
  logging: false
});

// 변경:
const canvas = await html2canvas(area, {
  backgroundColor: '#1a1a2e',
  scale: Math.min(window.devicePixelRatio || 1, 2),
  useCORS: true,
  logging: false
});
```

- [ ] **Step 1:** `captureArea()` 내 scale 값을 `Math.min(devicePixelRatio, 2)`로 변경
- [ ] **Step 2:** 검증 — Retina 디스플레이에서 캡처 이미지 선명도 확인
- [ ] **Step 3:** Commit: `fix: retina-quality image export (scale up to 2x)`

---

### Task 13: makeCard() 코드 중복 제거

**문제:** 일반 카드(line 923~962)와 Picker 카드(line 1151~1176)에서 동일 HTML 생성 코드 중복.
**해결:** 공통 HTML 생성을 `renderCardHTML(c)` 유틸로 추출.

**Files:**
- Modify: `index.html` JS

**JS 추가 (UTILS 섹션):**

```javascript
function renderCardHTML(c, opts = {}) {
  const stClass = 'st-' + c.style;
  const elSrc = c.element && EL_ICON[c.element] ? `images/elements/${EL_ICON[c.element]}` : '';
  const wpSrc = c.weapon && WP_ICON[c.weapon] ? `images/weapons/${WP_ICON[c.weapon]}` : '';

  let html =
    `<img class="card-icon" src="${c.customImg || ('images/icons/' + c.icon)}" alt="${esc(charName(c))}" loading="lazy">` +
    `<span class="card-name">${esc(charName(c))}</span>` +
    `<span class="card-meta">` +
      (elSrc ? `<img src="${elSrc}" alt="${c.elementKo}">` : '') +
      (wpSrc ? `<img src="${wpSrc}" alt="${c.weaponKo}">` : '') +
      `<span class="st-badge ${stClass}">${c.style}</span>` +
    `</span>`;

  if (!opts.compact) {
    html +=
      `<span class="card-sub">` +
        (c.ls ? `<span class="ls-badge ls-${c.ls}">${c.ls==='light'?'L':'S'}</span>` : '') +
        `<span class="rarity-badge r${c.rarity}">${c.rarity}★</span>` +
        (c.sa ? `<span class="sa-badge">SA</span>` : '') +
      `</span>`;
  }

  return html;
}
```

**JS 변경 — `makeCard()` (line 933~945):**

```javascript
card.innerHTML = renderCardHTML(c);
```

**JS 변경 — `renderPickerGrid()` 내 카드 생성 (line 1159~1166):**

```javascript
card.innerHTML = renderCardHTML(c, { compact: true });
```

- [ ] **Step 1:** `renderCardHTML(c, opts)` 유틸 함수 추가
- [ ] **Step 2:** `makeCard()` 내 HTML 생성을 `renderCardHTML(c)` 호출로 교체
- [ ] **Step 3:** `renderPickerGrid()` 내 HTML 생성을 `renderCardHTML(c, {compact:true})` 호출로 교체
- [ ] **Step 4:** 검증 — 카드 렌더링 동일, Picker 카드도 동일
- [ ] **Step 5:** Commit: `refactor: extract renderCardHTML() to deduplicate card rendering`

---

## Execution Checklist

| Phase | Task | 설명 | 의존성 |
|-------|------|------|--------|
| P0 | 1 | 헤더 overflow 메뉴 | 없음 |
| P0 | 2 | 필터바 접이식 | 없음 |
| P0 | 3 | 검색 debounce + IME | Task 2 (debounceSearch 참조) |
| P0 | 4 | touch-action 조건부 | 없음 |
| P0 | 5 | Pool 가상 스크롤 | 없음 |
| P1 | 6 | Long-press context menu | 없음 |
| P1 | 7 | Picker 스크롤 보존 | 없음 |
| P1 | 8 | All View 세로 스택 | 없음 |
| P1 | 9 | prompt() 교체 | 없음 |
| P1 | 10 | 모바일 토스트 | 없음 |
| P2 | 11 | 부분 렌더 최적화 | 전 Task 완료 후 |
| P2 | 12 | Retina export | 없음 |
| P2 | 13 | makeCard 중복 제거 | 없음 |

**병렬 가능 그룹:**
- Phase 1: Task 1, 2, 4, 5 병렬 가능 (Task 3은 Task 2 의존)
- Phase 2: Task 6~10 모두 독립, 병렬 가능
- Phase 3: Task 11은 마지막, Task 12, 13 독립

**각 Task 완료 후:** Chrome DevTools 375px (iPhone SE), 414px (iPhone 14), 768px (iPad) 에뮬레이션으로 수동 검증.
