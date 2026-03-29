# Tierlist Guide Design Overhaul — Spec

**Date:** 2026-03-29
**Scope:** Component Redesign — CSS + HTML 출력 변경, JS 로직 유지
**Target:** `index.html` 단일 파일 (인라인 CSS/JS)

---

## 1. Color System — Midnight Slate

기존 퍼플 계열을 뉴트럴 슬레이트로 전환. 속성/무기/스타일 뱃지 색상은 게임 원본 기반 유지.

### CSS Variable 매핑

| Variable | Before | After | Notes |
|----------|--------|-------|-------|
| `--bg-primary` | `#0e0b18` | `#0d1117` | 딥 퍼플 → 뉴트럴 슬레이트 |
| `--bg-secondary` | `#161230` | `#161b22` | Surface |
| `--bg-card` | `#1c1640` | `#1c2333` | Card 배경 |
| `--bg-pool` | `#0a0814` | `#0b1018` | Pool 영역 |
| `--bg-tier-row` | `#14102a` | `rgba(22,27,34,0.7)` | Semi-transparent |
| `--text-primary` | `#ede8f2` | `#e6edf3` | |
| `--text-secondary` | `#a8a0b8` | `#8b949e` | |
| `--text-dim` | `#5a5070` | `#484f58` | |
| `--accent` | `#c9a84c` | `#e6c77a` | 밝은 샴페인 골드 |
| `--accent-hover` | `#dfc06a` | `#f0d88a` | |
| `--accent-dim` | `rgba(201,168,76,0.15)` | `rgba(230,199,122,0.12)` | |
| `--border` | `#2e2450` | `#30363d` | |
| `--border-gold` | `rgba(201,168,76,0.25)` | `rgba(230,199,122,0.15)` | 더 은은하게 |

### 유지하는 색상 (변경 없음)
- `--el-fire`, `--el-water`, `--el-earth`, `--el-wind`, `--el-thunder`, `--el-shade`, `--el-crystal`, `--el-null`
- `.st-NS`, `.st-AS`, `.st-ES`, `.st-Alter` badge gradient
- `.sa-badge` gradient
- `.ls-light`, `.ls-shadow`

### Body gradient 변경
```css
body { background: linear-gradient(180deg, #101520 0%, var(--bg-primary) 30%, #080c12 100%); }
```

---

## 2. Character Card 리디자인

### 변경 사항

| 속성 | Before | After |
|------|--------|-------|
| 카드 폭 | `--card-w: 88px` | `--card-w: 92px` |
| 배경 | `var(--bg-card)` (단색) | `linear-gradient(180deg, #1c2333, #171e2c)` |
| border-radius | `8px` | `10px` |
| border | `2px solid transparent` | `1px solid rgba(48,54,61,0.7)` |
| 아이콘 radius | `6px` | `8px` |
| 아이콘 shadow | 없음 | `0 2px 8px rgba(0,0,0,0.4)` |
| top-edge line | 없음 | `::before` pseudo — `linear-gradient(90deg, transparent, rgba(255,255,255,0.06), transparent)` |

### 호버 효과
```css
.char-card:hover {
  border-color: rgba(230,199,122,0.5);
  transform: translateY(-3px);
  box-shadow: 0 6px 20px rgba(0,0,0,0.4), 0 0 12px rgba(230,199,122,0.08);
}
```

### 하이라이트 (선택된 카드)
```css
.char-card.highlighted {
  border-color: rgba(230,199,122,0.4);
  box-shadow: 0 2px 16px rgba(230,199,122,0.08);
}
.char-card.highlighted::after {
  content: '';
  position: absolute; inset: 0;
  border-radius: 10px;
  background: linear-gradient(180deg, rgba(230,199,122,0.04), transparent 40%);
  pointer-events: none;
}
```

### 메타 행 통합
- 기존: 속성+무기 (한 행) + 스타일 뱃지 (별도) + 레어도+L/S (별도 행) = 3행
- 변경: 속성+무기+스타일 뱃지 (한 행) + 레어도+SA (별도 행) = 2행

### 삭제 버튼
- 18px → 16px, 위치 유지 (top:3px, right:3px)

### 반응형
| Breakpoint | card-w | icon size |
|------------|--------|-----------|
| > 1024px | 92px | 64px |
| ≤ 1024px | 82px | 56px |
| ≤ 640px | 72px | 48px |

---

## 3. Tier Row 레이아웃

### 변경 사항

| 속성 | Before | After |
|------|--------|-------|
| 배경 | `var(--bg-tier-row)` (solid) | `rgba(22,27,34,0.7)` (semi-transparent) |
| border-radius | `6px` | `8px` |
| margin-bottom | `4px` | `3px` (margin으로 변경) |
| 라벨 구분선 | `border-right: 1px solid` | gradient pseudo-element (상하 fade) |
| 카드 gap | `6px` | `6px` (유지) |
| 카드 패딩 | `8px` | `8px 10px` (좌우 약간 여유) |
| 라벨 폭 | `56px` | `52px` |

### 티어 라벨 gradient divider
```css
.tier-label::after {
  content: '';
  position: absolute; right: 0; top: 12%; bottom: 12%;
  width: 1px;
  background: linear-gradient(180deg, transparent, rgba(230,199,122,0.12), transparent);
}
```

### SS/S 행 subtle glow
```css
/* SS tier label */
.tier-label[data-tier="SS"] { background: rgba(255,215,0,0.03); }
/* S tier label */
.tier-label[data-tier="S"] { background: rgba(255,107,107,0.02); }
```

> **구현 노트:** `data-tier` 속성을 `renderTierRows()`에서 `.tier-label`에 추가. 또는 JS에서 tier label의 color 기반으로 class를 동적 할당.

---

## 4. Toggle Controls — Segmented Control

기존 `.toggle-group` 3개를 iOS/macOS 스타일 Segmented Control로 교체.

### HTML 구조
```html
<div class="seg-control" data-group="mode">
  <div class="seg-indicator"></div>
  <button class="seg-btn active" data-value="builder">
    <svg><!-- pencil icon --></svg> 빌더
  </button>
  <button class="seg-btn" data-value="viewer">
    <svg><!-- eye icon --></svg> 뷰어
  </button>
</div>
```

### CSS
```css
.seg-control {
  display: flex;
  position: relative;
  background: var(--bg-primary);
  border-radius: 8px;
  padding: 3px;
  border: 1px solid var(--border);
  overflow: hidden;
}

.seg-indicator {
  position: absolute;
  top: 3px;
  height: calc(100% - 6px);
  border-radius: 6px;
  background: linear-gradient(135deg, rgba(230,199,122,0.15), rgba(230,199,122,0.08));
  border: 1px solid rgba(230,199,122,0.2);
  transition: left 0.3s cubic-bezier(0.4, 0, 0.2, 1), width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 0;
}

.seg-btn {
  position: relative;
  z-index: 1;
  padding: 5px 14px;
  font-size: 0.7rem;
  color: var(--text-secondary);
  transition: color 0.2s;
  display: flex;
  align-items: center;
  gap: 4px;
  white-space: nowrap;
}

.seg-btn.active {
  color: var(--accent);
  font-weight: 600;
}

.seg-btn svg {
  width: 13px; height: 13px;
  opacity: 0.5;
}

.seg-btn.active svg {
  opacity: 1;
}
```

### JS 로직
```javascript
function initSegControl(el) {
  const btns = el.querySelectorAll('.seg-btn');
  const indicator = el.querySelector('.seg-indicator');

  function update(activeBtn) {
    btns.forEach(b => b.classList.remove('active'));
    activeBtn.classList.add('active');
    indicator.style.left = activeBtn.offsetLeft + 'px';
    indicator.style.width = activeBtn.offsetWidth + 'px';
  }

  btns.forEach(btn => btn.addEventListener('click', () => update(btn)));
  // Initial position
  const initial = el.querySelector('.seg-btn.active');
  if (initial) {
    indicator.style.left = initial.offsetLeft + 'px';
    indicator.style.width = initial.offsetWidth + 'px';
  }
}
```

### SVG 아이콘 (인라인)
- **빌더**: pencil icon (`M12 20h9 M16.5 3.5a2.12...`)
- **뷰어**: eye icon (`M2 12s3-7 10-7...`)
- **티어**: grid icon (4 rects)
- **전체**: grid-with-lines icon
- **표**: horizontal lines icon

### html2canvas 캡처 호환
캡처 모드에서는 `.seg-indicator`의 transition을 제거하고 static 위치로 렌더링. 뷰어 모드에서는 seg-control 자체가 캡처에 포함되지 않으므로 문제 없음.

---

## 5. Header 리디자인

### 변경 사항

| 속성 | Before | After |
|------|--------|-------|
| 하단 구분선 | `::after` rainbow gradient | `border-bottom: 1px solid rgba(230,199,122,0.1)` |
| 토글 | `.toggle-group` × 3 | `.seg-control` × 3 (Section 4) |
| 버튼 radius | `4px` | `5px` |
| CTA (이미지 복사) | `linear-gradient(135deg, #b8942f, var(--accent))` | `linear-gradient(135deg, #d4a44a, #e6c77a)` + `box-shadow: 0 1px 4px rgba(230,199,122,0.2)` |

### 카테고리 탭
```css
.cat-tab.active {
  background: rgba(22,27,34,0.8);
  color: var(--accent);
  border-color: rgba(230,199,122,0.15);
}
```

---

## 6. Capture Image Output (공유용)

캡처 영역(`#capture-area`)에 상단 배너와 하단 푸터를 조건부 추가.

### 캡처 배너 (뷰어 모드 또는 캡처 시 표시)
```html
<div class="capture-banner" id="capture-banner" style="display:none">
  <h2>어나더에덴 티어표</h2>
  <div class="cap-info">
    <span class="cap-category"><!-- 활성 카테고리명 --></span>
    <span class="cap-version"><!-- 게임 버전 --></span>
    <span class="cap-date"><!-- 날짜 --></span>
  </div>
</div>
```

```css
.capture-banner {
  background: linear-gradient(135deg, #161b22, #0d1117, #161b22);
  padding: 16px 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid rgba(230,199,122,0.1);
}
.capture-banner h2 {
  font-family: var(--font-display);
  color: var(--accent);
  font-size: 0.9rem;
  letter-spacing: 1px;
}
.cap-info {
  font-size: 0.6rem;
  color: var(--text-dim);
  text-align: right;
  line-height: 1.5;
}
```

### 캡처 푸터
```html
<div class="capture-footer" id="capture-footer" style="display:none">
  <span class="cap-credit">by Team 랜선을 넘는 고양이들</span>
  <span class="cap-watermark">AE TIER LIST BUILDER</span>
</div>
```

```css
.capture-footer {
  background: #161b22;
  padding: 8px 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-top: 1px solid rgba(230,199,122,0.06);
}
.cap-watermark {
  font-family: var(--font-display);
  font-size: 0.55rem;
  color: rgba(230,199,122,0.25);
  letter-spacing: 2px;
}
```

### 캡처 시 동작
`copyAsImage()` / `saveAsImage()` 호출 시:
1. `#capture-banner`, `#capture-footer` 표시
2. 활성 카테고리명, 게임 버전, 날짜를 동적으로 채움
3. html2canvas 실행
4. 배너/푸터 다시 숨김

---

## 7. 변경하지 않는 것 (Scope Out)

- JS 로직 (드래그앤드롭, 데이터 관리, 저장/불러오기, 공유 URL)
- i18n 시스템 (I18N 객체, T() 함수) — 기존 그대로 활용
- 속성/무기/스타일 뱃지 색상 (게임 원본 기반)
- 모바일 overflow sheet 구조
- 피커 모달 구조 (색감만 변경)
- 테이블 뷰, 전체 뷰 구조 (색감만 변경)

---

## 8. html2canvas 호환성 체크리스트

- [x] `backdrop-filter` 사용 안 함
- [x] `position: fixed` 요소 캡처 영역에 없음
- [x] gradient, box-shadow만 사용 (호환됨)
- [x] SVG 인라인 (외부 참조 아님)
- [x] Segmented Control: 캡처 시 static position fallback
- [x] 캡처 배너/푸터: 캡처 전 display 전환

---

## 9. 반응형 브레이크포인트

기존 브레이크포인트 유지 (1024px, 640px). 변경사항:

| Breakpoint | 추가 변경 |
|------------|----------|
| ≤ 1024px | `--card-w: 82px`, 아이콘 56px |
| ≤ 640px | `--card-w: 72px`, 아이콘 48px, seg-control 폰트 0.6rem |

Seg-control은 640px 이하에서 아이콘만 표시 (텍스트 숨김) 고려.

---

## 10. Implementation Notes

- **단일 파일 수정**: `index.html`만 변경
- **CSS 변수 교체**: `:root` 블록의 변수값만 치환하면 80% 완료
- **카드 HTML**: `makeCard()` 함수의 HTML 출력 수정 (메타 행 통합)
- **Segmented Control**: 기존 `.toggle-group` → `.seg-control`로 HTML+CSS+JS 교체
- **캡처 배너/푸터**: `copyAsImage()`, `saveAsImage()` 앞뒤로 show/hide 로직 추가
- **테스트**: Chrome DevTools 375px/414px/768px/1024px에서 검증
