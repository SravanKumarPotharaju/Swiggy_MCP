# Rally design system for SmartFlow

Contract for the SmartFlow web UI restyle. Two parallel agents build from this file: class names are final. Do not rename, add synonyms, or invent new `r-` classes without updating this doc.

- Tokens file: `static/css/rally-tokens.css` (already written; do not duplicate values in component CSS, reference tokens).
- Fonts: `static/fonts/`.
- Source: Rally "Track" system (`rally/track/tokens.css` v1.3, `rally/track/README.md`, `rally/app/sheets-kit.jsx`, `rally/app/rally-ai.jsx`, `rally/app/screen-states.jsx`, `rally/app/screen-support.jsx`). Rally is a 412x892 phone prototype (UPI payments app). It has no web layout, no breakpoints, no z-index scale, no safe-area handling, no QR block, no qty stepper. Where this doc fills those gaps it says **DERIVED** and shows what it was derived from. Anything not marked DERIVED is a Rally value.

---

## 0. Read first: gaps and decisions

| # | Topic | Decision |
|---|-------|----------|
| 1 | Theme | Rally is **light only**. SmartFlow is currently dark (slate/orange). Restyle flips to light. No dark mode. |
| 2 | Brand font | Track uses **UberMove** (not Neuzeit). UberMove is marked "proprietary, internal use only" in Rally source. Neuzeit-Grotesk-Bold appears only as a watermark in one promise sketch; it is shipped as `Neuzeit` 700 but **not for UI**. Confirm UberMove licensing before any public deploy. |
| 3 | Emoji and glyph icons | Rally forbids emoji and unicode glyph icons (`✓ × ▾ ➤`) in chrome. Every emoji in `index.html` and the `app.js` templates is replaced by an SVG icon or removed. See section 8 for the icon dependency. |
| 4 | Sheet radius | Track token `--sp-r-bottom-sheet` is 20px; shipped `sheets-kit.jsx` uses 24px. This doc uses the token (20px). Surface is `--sp-bg-quiet` (#F4F4F2) with white cards on it, as in shipped sheets. |
| 5 | Button radius | Track token: buttons 8px (`--sp-r-input`). Shipped checkout CTAs are full pills (999) at 54px high. Both exist: `.r-btn` is 8px, `.r-btn--cta` and `.r-btn--pill` are 999. |
| 6 | Disabled | Disabled = `--sp-bg-tertiary` fill + `--sp-content-disabled` text. Never opacity. (Rally `SheetCta` uses opacity .4; `AiCta` and the token CSS use the fill. Fill wins.) |
| 7 | Input text size | Rally composer uses 15px. Web must use 16px on every form control or iOS Safari zooms the page on focus. Already forced in the reset. |
| 8 | Product grid | The single-column-under-768 rule applies to page layout and full-width cards. Product tiles (`.r-product`) are a 2-up grid at every width (Rally `.sp-place-grid` is `1fr 1fr`, gap 10 for exactly this tile shape). |
| 9 | Circular progress | Never. No ring, dial, arc, spinner circle. Loading = linear sweep (`.r-wait`) or shimmer (`.r-skeleton`). The mic "listening" state is animated bars, not a ring. |
| 10 | Selection | Every checkbox/radio/picked row uses `.r-check` (22px circle, ink fill + white check, hairline ring when off), always on the **right** of the row. |

---

## 1. Principles

1. **Black and white, chroma only for meaning.** Ink `#101010` on white on `#E8E8E8`. Color appears only as semantic (success, warning, error, promo), the single Safety Blue accent, or brand gold.
2. **Interactive rounds, surfaces stay square.** Buttons and inputs 8px, chips/tags/CTAs pill, soft containers 18px, tiles 16px, sheets 20px top. Flush cards are 0.
3. **Flat.** No gradients, textures, or glows in chrome. Shadows are soft, low-opacity, never colored. Brand gradients are only the two Rally marks (not used in SmartFlow).
4. **Amounts have a signature.** Small baselined rupee symbol, de-emphasized paise, tabular figures, mono for lists.
5. **Calm, terse copy.** Sentence case everywhere. No exclamation marks, no emoji. Imperative, second person ("Add to cart", "Pay ₹422"). Labels/buttons have no trailing period; full-sentence help and error text does. Pending uses an ellipsis ("Connecting..."). Money uses Indian grouping (`₹1,20,500`).
6. **No bounce.** Motion uses `--sp-ease-elegant`, 100 to 500ms. No overshoot, no spring.
7. **State without opacity or glow.** Hover = inset wash, pressed = `scale(.98)` + wash, input focus = 2px ink border (no ring), disabled = grey fill, selected chip = filled ink.
8. **Mobile is the design.** Everything is specified at 360 to 412px first and then widened.

Status vocabulary for order/payment tags: **Delivered, In progress, Pending, Failed, Received**. Rally's fixed words are Settled, Pending, Failed, Received; "Delivered" and "In progress" are the food-delivery equivalents of Settled and Pending.

---

## 2. Foundations

### 2.1 HTML head

```html
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#E8E8E8">
<link rel="preload" href="/static/fonts/UberMove-Regular.ttf" as="font" type="font/ttf" crossorigin>
<link rel="preload" href="/static/fonts/UberMove-Medium.ttf" as="font" type="font/ttf" crossorigin>
<link rel="preload" href="/static/fonts/UberMove-Bold.ttf" as="font" type="font/ttf" crossorigin>
<link rel="stylesheet" href="/static/css/rally-tokens.css">
```

Remove the Google Fonts `Inter` / `Outfit` links. Rally uses no web-font service; all faces are self-hosted. `viewport-fit=cover` is required for the safe-area tokens to resolve to non-zero values.

### 2.2 Fonts

| Family | Files | Weights | Use |
|--------|-------|---------|-----|
| `UberMoveText` | UberMove-Regular/Medium/Bold.ttf | 400 500 700 | body, labels (`--sp-font-primary`) |
| `UberMove` | UberMove-Light/Regular/Medium/Bold.ttf | 300 400 500 700 | headings, display, amounts (`--sp-font-secondary`) |
| `UberMoveMono` | UberMoveMono-Regular/Medium.ttf | 400 500 | amounts in lists, UPI IDs, order refs, OTP, timers (`--sp-font-mono`) |
| `Neuzeit` | Neuzeit-Grotesk-Bold.otf | 700 | not for UI |

`font-feature-settings: 'ss01','cv11'` on `html, body` (Rally). Always add `font-variant-numeric: tabular-nums` to figures (the mono utilities and `.r-amount` already do).

### 2.3 Token table

All in `rally-tokens.css`. Names are Rally's; use `var(--sp-*)`.

**Semantic color (light theme)**

| Token | Value | Use |
|-------|-------|-----|
| `--sp-bg-primary` | #FFFFFF | cards, sheets-on-white, bubbles (agent) |
| `--sp-bg-secondary` | #F7F7F7 | secondary button, chip (rest), tag-neutral hover |
| `--sp-bg-tertiary` | #EFEFEF | disabled fill, skeleton base, neutral tag, timeline pending |
| `--sp-bg-quiet` | #F4F4F2 | sheet surface, inset boxes |
| `--sp-bg-canvas` | #E8E8E8 | page background behind white containers |
| `--sp-bg-accent` / `-subtle` | #276EF1 / #EFF4FE | accent CTA, info banner |
| `--sp-bg-success` / `-subtle` | #05944F / #E6F2ED | accept, success tag |
| `--sp-bg-warning` / `-subtle` | #B97502 / #FFF2D9 | warning banner, pending tag |
| `--sp-bg-error` / `-subtle` | #DE1135 / #FFEFEB | danger button, error tag |
| `--sp-bg-promo-subtle` | #F3ECFA | promo tag |
| `--sp-bg-gold-subtle` | #FFF6E0 | gold tag |
| `--sp-bg-takeover` | #101010 | toast, dark moments (never pure black) |
| `--sp-content-primary` | #101010 | ink, primary button fill, selected chip fill |
| `--sp-content-secondary` | #5A5A58 | sub text |
| `--sp-content-tertiary` | #9A9A98 | meta, placeholder (white surfaces only; floor #868686 on #E8E8E8) |
| `--sp-content-disabled` | #C6C6C6 | disabled text |
| `--sp-content-inverted-primary` | #FFFFFF | text on ink |
| `--sp-content-accent` | #276EF1 | links |
| `--sp-content-success` | #0F7A3A | credit, delivered, free |
| `--sp-content-warning` | #B97502 | pending |
| `--sp-content-error` | #DE1135 | failed, error text |
| `--sp-content-promo` / `--sp-content-gold` | #7356BF / #B97502 | promo, reward text |
| `--sp-border-opaque` | #DDDDDD | input border, divider |
| `--sp-border-hairline` | #CFCFCC | ring off-state |
| `--sp-border-separator` | #F2F2F0 | row separators inside cards |
| `--sp-border-selected` | #101010 | focused input |
| `--sp-border-error` | #DE1135 | invalid input |
| `--sp-state-hover` / `-pressed` | rgba(0,0,0,.04) / .08 | washes |
| `--sp-scrim` | rgba(0,0,0,.42) | sheet backdrop |
| `--sp-on-dark-primary/-secondary/-tertiary` | #FFF / .72 / .5 | text on `--sp-bg-takeover` |

**Neutral ramp**: `--sp-gray-50` #F3F3F3, `-100` #E8E8E8, `-200` #DDDDDD, `-300` #C6C6C6, `-400` #A6A6A6, `-500` #868686, `-600` #727272, `-700` #5E5E5E, `-800` #4B4B4B, `-900` #282828, `-950` #141414.

**Accent/semantic ramps**: blue 50 #EFF4FE, 100 #D6E3FB, 500 #276EF1, 600 #1E54B7, deep #0A2B69. Green 50 #E6F2ED, 500 #05944F, shipped #0F7A3A. Amber 50 #FFF2D9, 500 #B97502. Red 50 #FFEFEB, 500 #DE1135, 600 #B8092A, deep #7A0B1F. Purple 50 #F3ECFA, 500 #7356BF.

**Brand**: gold #F2A516 (hi #FFD96B, bg #FFF6E0, halo #FFE2A0, ink #5A3A01); streak warm #FF7A00, hot #E84E1B, light #FFB061. SmartFlow rule: gold only for savings/discount amounts if at all; streak colors unused.

**Avatar cycle** (hash the name, never random): a1 #FBE4E8/#A8364C, a2 #E2F3E8/#1F6B43, a3 #EFEAFB/#5B43A8, a4 #E7F0FD/#1E54B7, a5 #FCEFDC/#8A5A12 (bg/ink).

**Spacing (4px base)**: `--sp-0` 0, `-100` 2, `-200` 4, `-300` 6, `-400` 8, `-500` 12, `-550` 14, `-600` 16, `-700` 20, `-800` 24, `-900` 32, `-1000` 40, `-1100` 48, `-1200` 56, `-1400` 72, `-1600` 96. Compose from steps, never raw pixels (exceptions listed per component where Rally uses a literal).

**Radii**: `--sp-r-card` 0, `--sp-r-container` 18, `--sp-r-container-lg` 22, `--sp-r-tile` 16, `--sp-r-input` 8, `--sp-r-button-mini` 4, `--sp-r-pill` 999, `--sp-r-check` 2, `--sp-r-avatar` 50%, `--sp-r-bottom-sheet` 20.

**Shadows**: `--sp-shadow-soft` `0 1px 2px rgba(0,0,0,.04)` (containers, round buttons); `-card` `0 4px 16px rgba(0,0,0,.06)` (floating card); `-sheet` `0 -8px 32px rgba(0,0,0,.15)`; `-nav` `0 6px 24px rgba(0,0,0,.10)`; `-fab` `0 8px 24px rgba(0,0,0,.25)` (toast); numbered `-100` to `-600` for generic elevation.

**Type scale** (size/line-height; weight in class):

| Class | Spec | Font |
|-------|------|------|
| `.r-display-lg/md/sm` | 64/72, 48/56, 36/44, 700, tracking -.02/-.02/-.01em | secondary |
| `.r-heading-xl/lg/md/sm/xs` | 32/40, 28/36, 24/32, 20/24, 16/20, 700, tracking -.01 to -.015em | secondary |
| `.r-para-lg/md/sm` | 16/24, 14/20, 12/16 (sm is secondary color), 400 | primary |
| `.r-label-lg/md/sm` | 16/20, 14/16, 12/16, 500 | primary |
| `.r-label-xs` | 11/16, 500, uppercase, +.04em, tertiary | primary |
| `.r-mono-lg/md/sm` | 16/24, 14/20, 12/16, 500, tabular | mono |
| `.r-section-label` | 11/14, 500, uppercase, +.08em, tertiary, padding 20 gutter 8 | primary |

**Motion**: `--sp-ease-elegant` cubic-bezier(.16,.84,.44,1) default; `-decelerate` (0,0,.2,1) entering; `-accelerate` (.4,0,1,1) leaving; `-standard` (.83,0,.17,1); `-sheet` (.22,1,.36,1). Durations `--sp-dur-100/200/300/400/500`, `--sp-dur-sheet` 350ms, `--sp-dur-count` 900ms (money count-up), `--sp-dur-route` 400ms (tab switch), `--sp-dur-toast` 2400ms. Keyframes: `sp-fade-up`, `sp-scale-in`, `sp-fade`, `sp-sheet-up`, `sp-shimmer`, `sp-spin`, `sp-ring` (linear despite the name), `r-msg-in`, `r-typing-dot`, `r-wave-bar`. `prefers-reduced-motion` collapses all animation to 1ms.

**Layout / SmartFlow tokens (`--r-*`)**

| Token | Value | Origin |
|-------|-------|--------|
| `--r-touch-min` | 44px | Rally `--sp-nav-slot`, `.sp-topbar-icon` |
| `--r-safe-top/right/bottom/left` | `env(safe-area-inset-*, 0px)` | DERIVED |
| `--r-gutter` | 16px; 24px at 768; 32px at 1024 | 16 is Rally's side padding; others DERIVED |
| `--r-page-max` | 100%; 720px at 768; 960px at 1024 | DERIVED |
| `--r-frame-width` | 412px | Rally device frame |
| `--r-drawer-width` | 380px | rally-ai.jsx side panel |
| `--r-nav-height` | 56px | 44 button + 6+6 padding (Rally nav pill) |
| `--r-nav-bottom` | `max(32px, safe-bottom + 8px)` | Rally offset 32; max() DERIVED |
| `--r-composer-bottom` | nav-bottom + 56 + 8 (= 96 with no inset) | Rally variant C bottom: 96 |
| `--r-composer-height` | 112px | 10+34+10+50+8, Rally numbers |
| `--r-nav-clearance` | nav-bottom + 56 + 16 | bottom padding for scroll content |

**z-index scale** (every number is one Rally uses)

| Token | Value | Layer |
|-------|-------|-------|
| `--r-z-raised` | 3 | map pins, anything lifted inside a card |
| `--r-z-chrome` | 8 | top bar, tab bar, chat composer |
| `--r-z-overlay` | 40 | non-sheet overlays |
| `--r-z-sheet` | 55 | `.r-sheet-layer` (scrim + sheet + call) |
| `--r-z-takeover` | 60 | reserved |
| `--r-z-composer` | 61 | reserved (only for a composer inside a takeover; unused) |
| `--r-z-toast` | 80 | `.r-toast` (always on top) |

Leaflet creates panes up to z-index 1000. `.r-map` must set `isolation: isolate` so those stay inside the map and never cover a sheet.

### 2.4 Breakpoints

Mobile-first. Media queries cannot read custom properties, so numbers are literal.

| Name | Rule | What changes |
|------|------|--------------|
| base (mobile) | no media query, designed at 360 to 480 | single column, gutter 16, sheets full-width bottom, floating pill nav |
| 481 to 767 | no rule | same as base, fluid. Do not add a breakpoint here. |
| tablet | `@media (min-width: 768px)` | gutter 24, `.r-app__main` max-width 720 centered, `.r-grid` 2 columns, `.r-grid--tiles` 3, sheets become centered max-width 480 bottom sheets, top bar shows location inline and brand tag, `.r-hide-mobile` shows |
| desktop | `@media (min-width: 1024px)` | gutter 32, page max 960, `.r-grid--tiles` 4 columns, `.r-grid--wide` 3 columns, cart becomes a right drawer (`.r-sheet--drawer`, 380px) |

### 2.5 Mobile-first rules (binding)

1. **44px touch targets.** Every tappable element has a 44x44 minimum hit area. Where Rally's visual is smaller (chips 34px high, tag-sized buttons, 36px round buttons), keep the Rally visual and extend the hit area with `::after { content:""; position:absolute; inset:-5px 0 }` (chips) or by using `min-height: var(--r-touch-min)` (buttons). Adjacent targets must not overlap.
2. **Safe areas.** Top bar pads `padding-top: var(--r-safe-top)`; left/right of full-bleed fixed elements pad by `--r-safe-left/right`; tab bar and composer position from `--r-nav-bottom` / `--r-composer-bottom` (already include `--r-safe-bottom`); sheets pad their footer `padding-bottom: calc(18px + var(--r-safe-bottom))`.
3. **Single column under 768.** Page content is one column. Two-up allowed only for `.r-grid--tiles` (decision 8) and the 2x2 `.r-pay__apps` grid.
4. **Bottom nav on mobile.** `.r-tabbar` is a floating pill at the bottom at every size (Rally has no other nav form). Scroll content ends with `padding-bottom: var(--r-nav-clearance)`.
5. **Sheets, not centered modals,** on mobile: bottom-anchored, 20px top radius, grabber, scrim, drag-to-dismiss.
6. **Use `100dvh`**, with `100vh` as the fallback already in the reset. Never `height: 100vh` on a scroll container that has a fixed composer.
7. **No horizontal page scroll.** Only `.r-chip-rail` scrolls horizontally, with `.r-no-scrollbar`.
8. **Form controls 16px.** Set by reset.
9. **Hover only where hover exists.** Wrap hover washes in `@media (hover: hover)`. Pressed state (`:active`) always.
10. **Focus**: keyboard focus ring is `:focus-visible` 2px ink, offset 2 (DERIVED; Rally defines focus only for inputs).

---

## 3. Conventions

**BEM-ish**: block `.r-name`, element `.r-name__part`, modifier `.r-name--variant`. State is a class starting `is-` or `has-`, always on the block (or the named element), plus the matching ARIA attribute.

| State class | Meaning | ARIA |
|-------------|---------|------|
| `.is-open` | sheet layer visible | `aria-hidden` on layer toggled |
| `.is-active` | current screen / current tab | `aria-selected="true"` on tabs, `aria-current="page"` on tabbar tab |
| `.is-selected` | picked row, chip | `aria-pressed` (chip toggle) / `aria-checked` (row) |
| `.is-done` | completed timeline step | none |
| `.is-listening` | mic live | `aria-pressed="true"` on mic button |
| `.is-connected` | Swiggy account linked | none |
| `.is-visible` | toast shown | `role="status" aria-live="polite"` always present |
| `.is-busy` | button waiting | `aria-busy="true"` |
| `.has-text` | composer has typed text | none |

Disabled uses the `disabled` attribute (or `aria-disabled="true"`), never a class.

Icons: inline SVG, 24x24 viewBox, `fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"`, class `.r-icon` (20px), `.r-icon--sm` (16px), `.r-icon--lg` (24px). Always `aria-hidden="true"` with the control carrying `aria-label`.

---

## 4. Components

Format per component: **Classes** | **Anatomy** | **Spec** | **States** | **Mobile**.

### 4.1 App shell: `.r-app`, `.r-app__main`, `.r-screen`, `.r-grid`

- **Classes**: `.r-app` (root, wraps header+main+nav), `.r-app__main`, `.r-screen` (one tab pane), `.r-screen.is-active`, `.r-grid`, `.r-grid--tiles`, `.r-grid--wide`.
- **Anatomy**: `.r-app > .r-topbar + .r-app__main > .r-screen*` plus `.r-tabbar`, `.r-sheet-layer*`, `.r-toast` as siblings of `.r-app__main`.
- **Spec**: `.r-app` min-height 100dvh, background `--sp-bg-canvas`. `.r-app__main` padding-inline `--r-gutter`, padding-bottom `--r-nav-clearance`, max-width `--r-page-max`, margin-inline auto. `.r-screen` is `display:none` unless `.is-active` (use the `hidden` attribute as well so it is not in the a11y tree); when it becomes active it plays `sp-fade-up` at `--sp-dur-route`. Vertical rhythm between top-level blocks in a screen: `.r-stack` (16px). White containers on the canvas, never canvas on canvas.
- `.r-grid`: 1 column, gap `--sp-500` (12px); 2 columns at 768. `.r-grid--wide` adds 3 columns at 1024. `.r-grid--tiles`: 2 columns, gap 10px (Rally `.sp-place-grid`), 3 at 768, 4 at 1024.
- **Mobile**: one column; main never scrolls horizontally.

### 4.2 Top bar: `.r-topbar`

- **Classes**: `.r-topbar`, `__brand`, `__brand-name`, `__brand-tag`, `__location`, `__actions`. The bar is always sticky; there is no sticky modifier.
- **Anatomy**:
  ```
  header.r-topbar
    a.r-topbar__brand > span.r-topbar__brand-name + span.r-tag.r-tag--neutral.r-topbar__brand-tag.r-hide-mobile
    button.r-topbar__location (is the address pill)
    div.r-topbar__actions > [connect button] [call button] [cart button + .r-badge]
  ```
- **Spec**: Rally `TopBar`: height 52px, padding 0 8px; round controls 44. Position `sticky; top:0; z-index: var(--r-z-chrome)`; padding-top `--r-safe-top`; background `--sp-bg-canvas` (Rally top bars sit flat on the canvas). `__brand-name` 18px/700 `--sp-font-secondary`, tracking -.01em (Rally `StTop` title). No logo emoji; brand mark is text-only (no asset exists, see section 8). `__location` is a pill: `--sp-bg-primary`, `--sp-r-pill`, `--sp-shadow-soft`, min-height 44, padding 0 14px, text `.r-label-md` single line ellipsis, leading pin icon; Rally's "balance chip" is this shape. `__actions` flex, gap `--sp-300`.
- **States**: `__location` pressed = `--sp-state-pressed`. Pulse on address change (existing `pulse-update`): replace with a one-shot `sp-scale-in` re-run.
- **Mobile**: two rows. Row 1: brand left, actions right (height 52). Row 2: `__location` full width pill under the bar (it is hidden today under 768; Rally hides nothing, the address matters). `__brand-tag` hidden. Connect button shows dot + short label; call button is icon-only (`.r-hide-mobile` on its label). At 768 the location pill moves inline between brand and actions (single row, `grid-template-columns: auto 1fr auto`, location max-width 420 centered).

### 4.3 Bottom tab nav: `.r-tabbar`

- **Classes**: `.r-tabbar`, `__pill`, `__tab`, `__tab.is-active`, `__dot`.
- **Anatomy**: `nav.r-tabbar[aria-label="Main"] > div.r-tabbar__pill[role="tablist"] > button.r-tabbar__tab[role="tab"][data-target][aria-label][aria-selected] > svg.r-icon (+ span.r-tabbar__dot)`.
- **Spec** (Rally `AiNavPill`, `.sp-nav-pill`): `.r-tabbar` is `position:fixed; left:0; right:0; bottom: var(--r-nav-bottom); display:flex; justify-content:center; pointer-events:none; z-index: var(--r-z-chrome)`. `__pill`: `pointer-events:auto; display:flex; gap:4px; padding:6px; background: var(--sp-bg-primary); border-radius: var(--sp-r-pill); box-shadow: var(--sp-shadow-nav)`. `__tab`: 44x44, radius pill, transparent, icon color `--sp-content-tertiary`, transition `background-color .2s, color .2s`. `__tab.is-active`: background `--sp-content-primary`, icon `--sp-content-inverted-primary`. `__dot`: 9px circle, `--sp-nav-live` fill, 2px white border, absolute top 2 right 2 (live order in progress on the Tracking tab). Four tabs: Chat, Food, Instamart, Tracking. Icon-only (Rally); each has `aria-label` and `title`.
- **States**: rest, `:active` `scale(.98)`, `.is-active`, focus-visible ring.
- **Mobile**: this is the mobile nav. Same pill at tablet/desktop (Rally has no other form); safe-area handled by `--r-nav-bottom`. Padding-left/right `--r-safe-left/right`.

### 4.4 Chat bubbles: `.r-chat`, `.r-msg`

- **Classes**: `.r-chat`, `__thread`, `__welcome`, `__welcome-title`, `__welcome-text`, `.r-msg`, `.r-msg--user`, `.r-msg--agent`, `__bubble`, `__actions`.
- **Anatomy**: `.r-chat > .r-chat__welcome? + .r-chat__thread > .r-msg.r-msg--agent|--user > .r-msg__bubble (+ .r-msg__actions)`. No avatars next to messages (Rally ChatPhone has none; the existing `.avatar` is dropped).
- **Spec** (rally-ai.jsx ChatPhone): `__thread` flex column, gap 8px, padding 16px 12px, padding-bottom `calc(var(--r-composer-bottom) + var(--r-composer-height))` on the chat screen. `.r-msg` flex, `justify-content: flex-end` for user, `flex-start` for agent, animation `r-msg-in` 300ms `--sp-ease-elegant`. `__bubble`: max-width `min(84%, 520px)` (84% is Rally; cap DERIVED), radius 20px, padding 9px 13px, font 15px/1.4 `--sp-font-primary`, flex column gap 8px, word-wrap `anywhere`. Agent bubble: background `--sp-bg-primary`, color `--sp-content-primary`. User bubble: background `--sp-content-primary`, color `--sp-content-inverted-primary` (DERIVED from ink; Rally's own user bubble color is per-channel). `<strong>` weight 700, `<em>` normal style with weight 500 (the existing formatter emits both). Links inside agent bubble `--sp-content-accent`. `__actions`: flex wrap gap 6px, margin-top 8px, holds `.r-chip.r-chip--outline` quick links. `__welcome`: shown while the thread has no user message; centered, `__welcome-title` `.r-heading-md`, `__welcome-text` `.r-para-md` secondary, max-width 280, padding 0 40px; replaces the old hero.
- **States**: new message animates in with `r-msg-in`. Errors from the API are shown as a `.r-toast--error`, not as a bubble.
- **Mobile**: bubbles full thread width minus 16%; thread scrolls the page (not an inner scroller) so browser chrome collapses.

### 4.5 Typing indicator: `.r-typing`

- **Classes**: `.r-typing`, `__dot`.
- **Anatomy**: `.r-msg.r-msg--agent > .r-typing > span.r-typing__dot x3`. Add `role="status"` and a `.r-visually-hidden` label "SmartFlow is thinking".
- **Spec** (rally-ai.jsx): bubble look of an agent bubble with radius 20, padding 12px 14px, flex gap 4px. Dots 7px circles, `--sp-content-tertiary`, animation `r-typing-dot 1.2s infinite`, delays 0 / 160ms / 320ms. Replaces the text "SmartFlow is thinking & checking Swiggy... ⏳".
- **States**: present or removed.

### 4.6 Input bar with mic: `.r-composer`

- **Classes**: `.r-composer`, `__inner`, `__suggestions`, `__status`, `__row`, `__field`, `__input`, `__wave`, `__wave-bar`, `__action`, `__action--mic`, `__action--send`; states `.r-composer.has-text`, `.r-composer.is-listening`.
- **Anatomy**:
  ```
  div.r-composer
    div.r-composer__inner
      div.r-composer__suggestions.r-chip-rail > button.r-chip*
      p.r-composer__status
      div.r-composer__row
        div.r-composer__field > input.r-composer__input + div.r-composer__wave(.r-composer__wave-bar x5)
        button.r-composer__action.r-composer__action--mic   (#mic-btn)
        button.r-composer__action.r-composer__action--send  (#btn-send)
  ```
- **Spec** (rally-ai.jsx composer, variant C): `.r-composer` `position:fixed; left:0; right:0; bottom: var(--r-composer-bottom); z-index: var(--r-z-chrome)`; padding 10px var(--r-gutter) 8px (Rally 10px 14px 8px); background `--sp-bg-canvas`. `__inner` max-width `--r-page-max`, margin-inline auto, flex column gap 10px. `__suggestions` is a chip rail (34px chips). `__status` `.r-para-sm`, tertiary, one line, hidden when empty (replaces `#mic-status`). `__row` flex gap 8px, align center. `__field` flex 1, height 50, radius pill, background `--sp-bg-primary`, padding 0 18px, flex gap 10. `__input` flex 1, no border/outline/background, 16px (Rally 15px; web minimum), color ink, placeholder `--sp-content-tertiary`. `__action` 50x50 circle, background `--sp-content-primary`, icon white 20px stroke 2: mic icon `<rect x="9" y="3" width="6" height="11" rx="3"/><path d="M5 11a7 7 0 0 0 14 0M12 18v3"/>`, send icon `<path d="M12 19V5M5 12l7-7 7 7"/>` (both Rally inline SVG). Exactly one of the two buttons is visible: `--mic` by default, `--send` when `.has-text`.
- **States**: `.is-listening`: input hidden, `__wave` shown: 5 bars, each 3px x 18px, radius 2, `--sp-content-primary`, animation `r-wave-bar 900ms ease-in-out infinite`, delay `i*120ms`, followed by the text "Listening..." 15px `--sp-meta-alt`; mic button `aria-pressed="true"`. Mic button also keeps ink fill while listening (no color change, no ring). Disabled send = `--sp-bg-tertiary` fill, `--sp-content-disabled` icon.
- **Mobile**: this is the primary control; always visible above the tab bar on the chat screen only. The hero mic orb is removed (the mic lives here). Hide the composer when a sheet is open (`body.r-lock .r-composer { visibility:hidden }`).

### 4.7 Buttons: `.r-btn`

- **Classes**: base `.r-btn`; variants `--primary`, `--secondary`, `--ghost`, `--accent`, `--danger`, `--danger-quiet`, `--success`, `--icon`; sizes/shapes `--sm`, `--pill`, `--block`, `--cta`; parts `__label`, `__amount`, `__dot`; state `.is-busy`.
- **Spec**: base (Rally `.sp-btn`): inline-flex, center, gap 8px, font 500 16/20 `--sp-font-primary`, padding 16px 20px, radius `--sp-r-input` (8), `min-height: var(--r-touch-min)`, no border, `white-space:nowrap`, transition `transform .08s, background-color .15s` on `--sp-ease-elegant`. Pressed `scale(.98)`. Hover (only `@media (hover:hover)`): primary `box-shadow: inset 999px 999px 0 rgba(255,255,255,.12)`; secondary/ghost `inset 999px 999px 0 rgba(0,0,0,.04)`.
  - `--primary`: background `--sp-content-primary`, color `--sp-content-inverted-primary`. The dominant action. One per view region.
  - `--secondary`: background `--sp-bg-secondary`, color ink (this is Rally's `sp-btn--ghost`).
  - `--ghost`: background transparent, color ink, no fill at rest (text actions such as "Resend OTP", "Clear"). Pressed wash `--sp-state-pressed`.
  - `--accent`: background `--sp-bg-accent`, white. Rare (one accent CTA max).
  - `--danger`: background `--sp-bg-error`, white (Rally "End call", `SUP_RED`).
  - `--danger-quiet`: background `--sp-bg-error-subtle`, color `--sp-content-error` (Disconnect). DERIVED from tag pair.
  - `--success`: background `--sp-bg-success`, white (accept call). DERIVED from token.
  - `--icon`: 44x44, padding 0, radius 50%, background `--sp-bg-primary`, `--sp-shadow-soft`, color ink, icon 20px. (Rally round back/close button is 36px white; 44 here for touch.)
  - `--sm`: padding 10px 14px, font 14px, still `min-height: 44px`.
  - `--pill`: radius `--sp-r-pill`.
  - `--block`: width 100%.
  - `--cta`: the checkout/confirm button. Pill, `min-height: 54px`, padding 0 24px, font 600 16px, width 100%, flex `justify-content: space-between` when it has `__amount`, centered otherwise. `__amount`: `--sp-font-mono`, 600, tabular, on the left; label on the right. The amount is always on the CTA (Rally checkout rule): "₹422 | Pay on UPI".
  - `__dot`: 9px status dot inside a button (Connect Swiggy). `--sp-nav-live` when connected, `--sp-content-tertiary` when not.
- **States**: rest, hover, pressed, focus-visible, disabled (`disabled`: fill `--sp-bg-tertiary`, text `--sp-content-disabled`, `cursor:not-allowed`, transform none), `.is-busy` (label replaced by a 22x2 `.r-wait--inline` sweep on `--primary`/`--cta`, `pointer-events:none`).
- **Mobile**: primary actions in sheets/footers use `--cta`. Icon buttons in the top bar are 44. Never put two `--primary` side by side; the secondary partner is `--secondary`.

### 4.8 Card: `.r-card`

- **Classes**: `.r-card`, `--float`, `--flush`, `--quiet`, `--dark`; parts `__header`, `__title`, `__sub`, `__aside`, `__body`, `__footer`.
- **Spec**: base (Rally `sp-container`): background `--sp-bg-primary`, radius `--sp-r-container` (18), `--sp-shadow-soft`, padding `--sp-600` (16). `--float`: `--sp-shadow-card`, no border. `--flush`: radius 0, `border:1px solid var(--sp-border-opaque)`, no padding (lists/receipts that touch edges). `--quiet`: background `--sp-bg-quiet`, no shadow (use inside a white card or a sheet). `--dark`: background `--sp-bg-takeover`, `--sp-on-dark-*` text (use at most once per screen, e.g. an order-arriving highlight). `__header` flex space-between gap 12; `__title` `.r-heading-sm` (or `.r-heading-xs` in dense cards); `__sub` `.r-para-sm`; `__aside` right-aligned (ETA, amount). No colored left borders, no gradient borders.
- **States**: static. Interactive cards add `.r-row--interactive` behavior: pressed `scale(.985)` (Rally `.sp-place-card:active`).
- **Mobile**: full width; stacked with 12px gap.

### 4.9 Restaurant card: `.r-restaurant`

- **Classes**: `.r-restaurant`, `--hero` (menu-screen header), `--store` (Instamart header), `__media`, `__img`, `__body`, `__name`, `__meta`, `__rating`, `__eta`, `__badges`.
- **Anatomy**: `.r-restaurant.r-card > __media? + __body > __name + __meta(__rating, __eta) + __badges(.r-tag*)`.
- **Spec**: built on `.r-card`. `__name` `.r-heading-md` (24/32). `__meta` flex wrap gap 8px, `.r-para-md` secondary; separators between meta items are a 3px circle drawn with `::before` on every item after the first (no text glyph). `__rating`: `.r-tag.r-tag--neutral` with text "4.4 · 10K+ ratings" (no star glyph; star is a missing icon). `__eta`: `.r-tag.r-tag--neutral`. `__badges`: `.r-tag--accent` "Frequently ordered" (replaces `#restaurant-frequent-badge`). `__media`: 56x56 tile, radius `--sp-r-tile`, `object-fit:cover`, optional. `--hero`: card `--float`, padding 20px, name `.r-heading-md`. `--store`: same, but with `.r-tag.r-tag--neutral` carrying "10 to 15 min" in `__eta` and the `.r-search` block inside the card below `__meta`.
- **States**: static; restaurant switching is done by the chip rail (4.13), not by this card.
- **Mobile**: single column, `__meta` wraps.

### 4.10 Menu item card: `.r-dish`

- **Classes**: `.r-dish`, `__body`, `__veg`, `__veg--veg`, `__veg--nonveg`, `__name`, `__price`, `__desc`, `__media`, `__img`, `__action`.
- **Anatomy**: `article.r-dish.r-card > div.__body > (span.__veg, h3.__name, p.__price, p.__desc) + div.__media > img.__img + .__action > button.r-btn.r-btn--secondary.r-btn--sm.r-btn--pill`.
- **Spec**: flex row, gap 12px, padding 16px, align start. `__body` flex 1, min-width 0. `__veg`: 16x16 box, `border:1.5px solid`, radius `--sp-r-check` (2), center dot 8px; `--veg` color `--sp-content-success`, `--nonveg` color `--sp-content-error` (Indian veg-mark convention; semantic colors are the allowed chroma). `__name` `.r-heading-xs` (16/20), 2-line clamp. `__price` `.r-mono-md` tabular, margin-top 4. `__desc` `.r-para-sm` secondary, 2-line clamp, margin-top 4. `__media` 96x96 (`--sp-1600`), radius `--sp-r-tile`, `overflow:hidden`, background `--sp-bg-quiet` (image fallback). `__action` sits under the image, centered, margin-top 8.
- **States**: unavailable dish = `__action` button disabled with label "Unavailable"; card static. Add button pressed state per `.r-btn`.
- **Mobile**: 1 column list in `.r-grid`; image right. 768: 2 columns; 1024 with `.r-grid--wide`: 3.

### 4.11 Product card: `.r-product`

- **Classes**: `.r-product`, `__media`, `__img`, `__time`, `__discount`, `__name`, `__unit`, `__price-row`, `__price`, `__mrp`, `__footer`, `__action`.
- **Anatomy**: `article.r-product.r-card > div.__media > img.__img + span.r-tag.__time + span.r-tag.r-tag--success.__discount` then `h3.__name + p.__unit + div.__footer > div.__price-row(.__price + .__mrp) + div.__action`.
- **Spec**: `.r-card` with padding 12px. `__media` square (`aspect-ratio:1/1`), radius `--sp-r-tile`, background `--sp-bg-quiet`, `position:relative`; `__img` `object-fit:contain`, padding 8px. `__time` (delivery time tag `.r-tag--neutral`) bottom-left on the media, `__discount` top-left (`.r-tag--success`, "12% off"). `__name` `.r-label-md` 500, 2-line clamp, margin-top 8. `__unit` `.r-para-sm` secondary. `__price` `.r-mono-md` ink; `__mrp` `.r-mono-sm` tertiary with `text-decoration: line-through`. `__footer` flex space-between align end, margin-top 8. `__action` holds `.r-btn.r-btn--secondary.r-btn--sm.r-btn--pill` ("Add") which is swapped for `.r-stepper` once the item is in the cart.
- **States**: not in cart (Add), in cart (stepper), out of stock (button disabled "Out of stock"), loading (`.r-skeleton` block matching media + two lines).
- **Mobile**: `.r-grid--tiles` 2 columns (decision 8). 768: 3, 1024: 4.

### 4.12 Bottom sheet and modal: `.r-sheet`

- **Classes**: `.r-sheet-layer`, `.r-scrim`, `.r-sheet`, `--tall`, `--white`, `--drawer`, `__grabber`, `__header`, `__title`, `__subtitle`, `__close`, `__body`, `__footer`.
- **Anatomy**:
  ```
  div.r-sheet-layer [.is-open]
    div.r-scrim
    section.r-sheet[role="dialog"][aria-modal="true"][aria-labelledby]
      div.r-sheet__grabber
      header.r-sheet__header > div(.r-sheet__title + .r-sheet__subtitle) + button.r-btn.r-btn--icon.r-sheet__close[aria-label="Close"]
      div.r-sheet__body
      footer.r-sheet__footer
  ```
- **Spec** (sheets-kit `RallySheet` + token `.sp-sheet`): `.r-sheet-layer` `position:fixed; inset:0; z-index: var(--r-z-sheet)`; hidden (`visibility:hidden; pointer-events:none`) until `.is-open`. `.r-scrim` `position:absolute; inset:0; background: var(--sp-scrim)`; fade `sp-fade` `--sp-dur-300`. `.r-sheet`: `position:absolute; left:0; right:0; bottom:0; max-height: 85%` (and `85dvh`), background `--sp-bg-quiet`, radius `--sp-r-bottom-sheet --sp-r-bottom-sheet 0 0`, `--sp-shadow-sheet`, `display:flex; flex-direction:column; overflow:hidden`, entry `sp-sheet-up var(--sp-dur-sheet) var(--sp-ease-sheet) both`. `--tall`: `max-height:94%` and `height:94%` (cart). `--white`: background `--sp-bg-primary` (call sheet). `__grabber`: 40x5, radius 3, background `--sp-gray-200`, margin `8px auto 0`, flex-shrink 0. `__header`: flex, space-between, gap 12, padding 2px 22px 12px; `__title` 21px/700 `--sp-font-secondary`, tracking -.02em, ink; `__subtitle` 12.5px `--sp-meta-alt`, margin-top 3. `__close` is `.r-btn--icon` (44, white on quiet). `__body`: `flex:1; min-height:0; overflow-y:auto; overscroll-behavior:contain; padding: 0 16px 22px` hide scrollbar. `__footer`: `flex-shrink:0; padding: 8px 16px calc(18px + var(--r-safe-bottom))`; footer holds the `--cta` button; the CTA stays visible while the body scrolls.
- **Behavior**: opens by adding `.is-open` to the layer and `.r-lock` to `<body>`; focus moves into the sheet and returns to the opener on close; closes on scrim click, Escape, close button, or drag down past **120px or velocity > .5px/ms** (Rally). Stacked sheets (address inside cart etc.) are siblings in DOM order; the later one sits above (same z-index).
- **Tablet (768+)**: sheet `max-width: 480px; margin-inline:auto` (still bottom anchored, same radius).
- **Desktop (1024+)**: only the cart: `.r-sheet--drawer`: `top:0; right:0; left:auto; bottom:0; width: var(--r-drawer-width); max-height:none; height:100%; border-radius: 24px 0 0 24px` (rally-ai.jsx side panel). Everything else stays a bottom sheet.
- **States**: closed, opening, open, dragging (transform follows pointer), closing (`--sp-ease-accelerate`).
- **Mobile**: full width. Reduced motion: 1ms.

### 4.13 Chips and chip rail: `.r-chip`, `.r-chip-rail`

- **Classes**: `.r-chip`, `--selected`, `--outline`, `__icon`, `__count`; `.r-chip-rail`.
- **Spec** (Rally `.sp-chip` + composer suggestion chips): inline-flex, align center, gap 6px, height 34px, padding 0 13px, radius pill, background `--sp-bg-secondary`, color ink, font 500 13px/16px, `white-space:nowrap`, flex-shrink 0, `position:relative`, transition `all .15s` on `--sp-ease-elegant`. **Hit area**: `::after { content:""; position:absolute; inset:-5px 0 }` makes it 44px tall. `--selected`: background `--sp-content-primary`, color `--sp-content-inverted-primary` (active filter / current restaurant / current cart). `--outline`: transparent, `border:1px solid var(--sp-border-opaque)`. `__count`: 18px min-width pill, background `--sp-bg-primary`, color ink, font 500 11/14, centered; inside `--selected` the count background is `rgba(255,255,255,.18)` with white text (DERIVED). Pressed `scale(.98)`.
- `.r-chip-rail`: flex, gap 6px, `overflow-x:auto`, `scroll-snap-type:none`, margin-inline `calc(var(--r-gutter) * -1)`, padding-inline `var(--r-gutter)`, `.r-no-scrollbar`. Fades are not used (flat). Role: `role="tablist"` for tab-like rails (restaurant switcher, categories, cart service switch), `role="group"` for suggestion rails.
- **States**: rest, selected, pressed, focus-visible.
- **Mobile**: horizontally scrolling single row, never wraps.

### 4.14 Tags: `.r-tag`

- **Classes**: `.r-tag`, `--success`, `--warn`, `--error`, `--promo`, `--accent`, `--gold`, `--neutral`.
- **Spec** (Rally verbatim): inline-flex, gap 4px, padding 3px 8px, radius pill, font 500 11px/14px, tracking .02em. Pairs: success `--sp-bg-success-subtle` / `--sp-content-success`; warn `--sp-bg-warning-subtle` / `--sp-content-warning`; error `--sp-bg-error-subtle` / `--sp-content-error`; promo `--sp-bg-promo-subtle` / `--sp-content-promo`; accent `--sp-bg-accent-subtle` / `--sp-content-accent`; gold `--sp-bg-gold-subtle` / `--sp-content-gold`; neutral `--sp-bg-tertiary` / ink.
- **States**: static, non-interactive (no hit area needed).

### 4.15 Badge (count): `.r-badge`

- **Classes**: `.r-badge`, `--dot`.
- **Spec** (DERIVED from Rally nav live-dot + label-xs): min-width 18px, height 18px, padding 0 5px, radius pill, background `--sp-content-primary`, color white, font 500 11px/18px tabular, border `2px solid var(--sp-bg-canvas)`; positioned `absolute; top:2px; right:2px` when anchored to an icon button. `--dot`: 9px, no text, `--sp-nav-live`, border 2px white. Hidden (`hidden`) when count is 0.

### 4.16 List rows: `.r-list`, `.r-row`

- **Classes**: `.r-list`, `.r-row`, `--interactive`, `--selected`, `__lead`, `__main`, `__title`, `__sub`, `__trail`, `__amount`.
- **Anatomy**: `ul.r-list > li.r-row > .r-row__lead? + .r-row__main(.__title + .__sub) + .r-row__trail(.__amount | .r-check | button)`.
- **Spec** (Rally `.sp-row`): flex, align center, gap 12px, padding 14px 16px (inside a `.r-card--flush`/sheet) or 14px 0 (inside a padded `.r-card`, with `border-top: 1px solid var(--sp-border-separator)` on rows after the first). `__lead` 44px (avatar or tile icon, `--sp-bg-secondary`). `__main` flex 1, min-width 0. `__title` 500 15/20, ellipsis. `__sub` 400 13/16, secondary, margin-top 2, ellipsis. `__trail` flex-shrink 0. `__amount` `--sp-font-mono` 500 15/20 tabular. `--interactive`: cursor pointer, `:active` background `--sp-state-pressed`, `min-height:44px` (always true with this padding), `role="button"` or an `<a>/<button>` wrapper. `--selected`: the trailing `.r-check` is on; no row recolor, no left border.
- **States**: rest, pressed, selected, disabled (title/sub `--sp-content-disabled`).
- **Mobile**: full width; text truncates, never wraps the title.

### 4.17 Avatar: `.r-avatar`

- **Classes**: `.r-avatar`, `--sm` (36), `--md` (40), `--a1` to `--a5`.
- **Spec**: default 44px circle, `--sp-bg-secondary`, font 500 16/1 `--sp-font-secondary`, centered initials. `--a1..a5`: bg/ink from the avatar cycle tokens; choose by hashing the name (deterministic). Images are not used for people (Rally: initials only).

### 4.18 Form fields: `.r-field`, `.r-search`

- **Classes**: `.r-field`, `--error`, `__label`, `__control`, `__prefix`, `__input`, `__hint`; `.r-search`, `__icon`, `__input`, `__submit`.
- **Anatomy**: `div.r-field > label.r-field__label + div.r-field__control(span.r-field__prefix? + input.r-field__input) + p.r-field__hint`.
- **Spec** (Rally `.sp-input`): label 500 13/16 secondary, margin-bottom 6. Input: width 100%, padding 14px 16px, radius 8, `border:1px solid var(--sp-border-opaque)`, background white, ink, 16/20, `min-height:48px`. **Focus**: border becomes 2px ink and padding becomes 13px 15px (no glow, no ring). Placeholder `--sp-content-tertiary`. Hint 400 12/16 tertiary, margin-top 6. `__prefix` (`+91`): `--sp-font-mono` 500 16, secondary, sits inside the control with a 1px `--sp-border-separator` right divider, padding-right 12. `--error`: border `--sp-border-error`, hint color `--sp-content-error`, `aria-invalid="true"`, hint is the error sentence with a period. Disabled: background `--sp-bg-tertiary`, color `--sp-content-disabled`. Field group spacing: 16px (`.r-stack`).
- **`.r-search`** (Instamart search): pill, height 50, background white, padding-left 18px (icon 20px tertiary) with `__input` flex 1 (16px, no border) and `__submit` = `.r-btn.r-btn--primary.r-btn--sm.r-btn--pill` inside the pill's right padding (4px).
- **Mobile**: `inputmode="tel"` + `autocomplete="tel-national"` on the phone field.

### 4.19 OTP input: `.r-otp`

- **Classes**: `.r-otp`, `__input`, `__boxes`, `__box`, `.is-active` on a box, `.is-filled` on a box, `.r-otp--error`.
- **Anatomy**: `div.r-otp > input#swiggy-otp-input.r-otp__input + div.r-otp__boxes > span.r-otp__box x6`.
- **Spec** (Rally `.sp-otp`): `__boxes` flex, gap 8px. `__box` flex 1, height 54, radius 8, `border:1px solid var(--sp-border-opaque)`, mono 500 22/1, centered, transition `border-color .15s`. **Active box** (the next empty one while the input is focused): `border-width:2px; border-color: var(--sp-content-primary)`. `__input` is the real control, `maxlength=6`, `inputmode="numeric"`, `autocomplete="one-time-code"`, absolutely positioned over `__boxes` with `opacity:0` and `font-size:16px`; a few lines of JS mirror `input.value` into the boxes on `input`/`focus`/`blur`. The existing id `#swiggy-otp-input` stays on `__input`. `--error`: boxes border `--sp-border-error`.
- **Mobile**: boxes fill width; with 6 boxes at 320px each is about 44px wide, meeting touch size.

### 4.20 Selection control: `.r-check`

- **Classes**: `.r-check`, `__input`, `__box`.
- **Anatomy**: `label.r-row.r-row--interactive > .r-row__main + span.r-check > input.r-check__input[type=checkbox|radio] + span.r-check__box`.
- **Spec** (Rally `RallyCheck`): `__box` 22px circle, `box-sizing:border-box`. Off: transparent, `border:1.5px solid var(--sp-check-ring)`. On: background `--sp-content-primary`, no border, white check icon 12px stroke 2.5. Transition `background-color .2s, border-color .2s` on `--sp-ease-elegant`. `__input` is visually hidden but real (keeps `input[type=checkbox]` queries and `data-price` attributes working); `__input:checked + __box` is the on state; `__input:focus-visible + __box` shows the focus ring. Always the last child on the right of the row. The tap target is the entire row (label).

### 4.21 Quantity stepper: `.r-stepper`

- **Classes**: `.r-stepper`, `__btn`, `__qty`.
- **Spec**: **DERIVED** (Rally has no quantity stepper; composed from Rally parts). Inline-flex, align center, height 44, radius pill, background `--sp-bg-secondary`. `__btn` 44x44, radius 50%, transparent, ink icon 16px (`plus`: `M12 5v14M5 12h14`; minus: `M5 12h14`, the horizontal stroke of the plus), pressed `--sp-state-pressed`. `__qty` min-width 24, `--sp-font-mono` 500 15/20 tabular, centered, `aria-live="polite"`. Replaces both `.stepper` and `.im-qty-stepper`. Decrement from 1 removes the item.

### 4.22 Toast: `.r-toast`

- **Classes**: `.r-toast`, `--error`, `.is-visible`, `__icon`, `__body`, `__title`, `__text`, `__action`.
- **Spec** (Rally `FitToast` + `ErrorToastScreen`): `position:fixed; left: calc(var(--r-gutter) + var(--r-safe-left)); right: calc(var(--r-gutter) + var(--r-safe-right)); bottom: var(--r-nav-clearance)` (always, on every screen; on the chat screen it overlaps the composer for 2.4s, which is intended); `z-index: var(--r-z-toast)`. Background `--sp-bg-takeover`, color white, radius 12, padding 12px 16px, font 500 13px, `--sp-shadow-fab`. Appears with `sp-fade-up .2s var(--sp-ease-elegant)`; auto-dismiss after `--sp-dur-toast` (2400ms). `--error`: radius 14, padding 14px 16px, flex gap 12; `__icon` 16px color `--sp-toast-error-icon`; `__title` 600 13.5px; `__text` 11.5px `--sp-on-dark-secondary`; `__action` pill, background `--sp-on-dark-border` (rgba(255,255,255,.14)), white, 700 12.5px, padding 8px 14px, `min-height:44px` hit area via `::after`. Single element `#toast` with `role="status" aria-live="polite"` always in DOM.
- **Tablet+**: `max-width: 420px; margin-inline:auto`.
- **Copy rule**: no emoji, no exclamation. "UPI QR ready. Scan or open a UPI app."

### 4.23 Banner: `.r-banner`

- **Classes**: `.r-banner`, `--warning`, `--success`, `--info`, `--neutral`, `__icon`, `__body`, `__title`, `__text`, `__action`.
- **Spec**: DERIVED from tag pairs and toast geometry. Flex, align start, gap 12px, padding 12px 16px, radius 12, `role="status"` (use `role="alert"` for the gate-arrival alert). `--warning` background `--sp-bg-warning-subtle`, icon `--sp-content-warning`; `--success` `--sp-bg-success-subtle`/`--sp-content-success`; `--info` `--sp-bg-accent-subtle`/`--sp-content-accent`; `--neutral` `--sp-bg-primary` with `--sp-shadow-soft`. `__title` `.r-label-md`; `__text` `.r-para-sm` secondary (ink on subtle backgrounds); body text is always `--sp-content-primary`/secondary, not the semantic color, so contrast holds. `__action` is `.r-btn.r-btn--secondary.r-btn--sm.r-btn--pill`.

### 4.24 Empty state: `.r-empty`

- **Classes**: `.r-empty`, `__icon`, `__title`, `__text`, `__actions`.
- **Spec** (Rally `EmptyBody`): flex column, center, text-align center, padding 40px (Rally 0 40px) vertical 48px, min-height 50% of the screen. `__icon` 96px circle, `--sp-bg-primary`, `--sp-shadow-soft`, icon 34px color `#C6C6C4` (use `--sp-gray-300`), margin-bottom 22. `__title` 21/700 `--sp-font-secondary`, tracking -.01em, margin-bottom 8. `__text` 14px/1.5 secondary, max-width 280, margin-bottom 26. `__actions` flex column gap 8 (pill primary, then secondary). Empty cart, no active order, no addresses all use it. Copy examples: "Your cart is empty." / "No active orders." Sentence case, period for sentences.

### 4.25 Skeleton: `.r-skeleton`

- **Classes**: `.r-skeleton`, `--line`, `--line-sm`, `--block`, `--tile`, `--circle`.
- **Spec** (Rally `.sp-skeleton`): `background: linear-gradient(90deg, var(--sp-bg-tertiary) 25%, var(--sp-bg-secondary) 45%, var(--sp-bg-tertiary) 65%); background-size:200% 100%; animation: sp-shimmer 1.4s ease infinite; border-radius: var(--sp-r-input)`. `--line` height 12 radius 6; `--line-sm` height 9 radius 5; `--tile` radius 16; `--circle` radius 50%; `--block` takes explicit height. Composite skeleton row: circle 40 + two lines (50% and 30% width). Reduced motion: no animation. One shimmer for every loading surface (menu, products, past orders, address list). Container gets `aria-busy="true"`.

### 4.26 Wait / loading line: `.r-wait`

- **Classes**: `.r-wait`, `--inline`.
- **Spec** (Rally `.sp-wait-ring` and `.sp-spinner`, both linear): `.r-wait` 76x3, radius 2, background `--sp-border-opaque`, overflow hidden, `::before` width 40% ink, animation `sp-ring 1.8s var(--sp-ease-elegant) infinite`. `--inline` 22x2, background `rgba(255,255,255,.28)`, `::before` width 45% white, `sp-spin 1s var(--sp-ease-elegant) infinite` (inside `.r-btn--primary` / `--cta`). Use for: waiting on a UPI app/bank ("Waiting for payment..."), connecting to Swiggy, button busy. Never a circle.

### 4.27 Amount: `.r-amount`

- **Classes**: `.r-amount`, `__sym`, `__minor`, `--md`, `--sm`, `--credit`, `--failed`.
- **Spec**: in `rally-tokens.css`. Default 48/56 700; `--md` 36/44 (payment modal); `--sm` 20/24 (cart rows). Markup: `<span class="r-amount r-amount--md"><span class="r-amount__sym">₹</span>422<span class="r-amount__minor">.50</span></span>`; omit `__minor` for whole rupees. In lists use `.r-row__amount` (mono) instead.

### 4.28 Payment and QR block: `.r-pay`

- **Classes**: `.r-pay`, `__header`, `__ref`, `__amount`, `__method`, `__apps`, `__app`, `__divider`, `__qr`, `__qr-img`, `__vpa`, `__copy`, `__wait`, `__trust`.
- **Anatomy** (inside `.r-sheet__body`, CTA in `.r-sheet__footer`):
  ```
  div.r-pay
    p.r-pay__ref  (label + .r-code order id)
    div.r-pay__amount > .r-amount.r-amount--md
    span.r-tag.r-tag--success.r-pay__method "UPI"
    div#qr-section
      p.r-section-label "Open a UPI app"
      div.r-pay__apps > button.r-btn.r-btn--secondary.r-btn--pill.r-pay__app x4
      div.r-pay__divider (r-divider with label "or scan")
      div.r-pay__qr.r-card > img.r-pay__qr-img
      div.r-pay__vpa > span.r-code + button.r-btn.r-btn--secondary.r-btn--sm.r-pay__copy
    div.r-pay__wait > .r-wait + p.r-para-sm
    p.r-pay__trust
  ```
- **Spec**: Rally defines the payment sheet pattern (amount on the CTA, OTP inside the sheet, linear waiting) but has **no QR block**; the QR layout is DERIVED. `__ref` `.r-label-sm` tertiary with the order id in `.r-code`. `__amount` centered. `__apps` grid 2 columns, gap 10px (Rally `.sp-place-grid`), each `__app` min-height 48, text-only label (no emoji/colored dots; official UPI app logos are an asset dependency, section 8). `__qr`: white `.r-card` radius 18, padding 16, centered; `__qr-img` width `min(250px, 100%)`, `aspect-ratio:1/1`, `background:#fff` (QR must always be dark-on-white; never tint or round the modules). `__vpa` flex space-between gap 8, `.r-code` ellipsis. `__wait` shows after the user taps an app. `__trust` 12px tertiary one line ("Secure UPI payment").
- **Footer CTA**: `.r-btn.r-btn--primary.r-btn--cta` with `__amount` left and label right: "₹422 | I have paid" (the final confirm action, `#btn-final-pay`). Always enabled; the amount is always on the CTA.
- **Mobile**: order is apps, then QR (a phone cannot scan its own screen; apps are the primary path). At 768+ keep the same order; QR gets `max-width: 250px`.

### 4.29 Bill summary: `.r-bill`

- **Classes**: `.r-bill`, `__row`, `__row--total`, `__label`, `__value`, `__value--free`.
- **Spec**: DERIVED from Rally row + mono amount. Inside `.r-card`. `__row` flex space-between gap 12, padding 6px 0. `__label` `.r-para-md` secondary. `__value` `--sp-font-mono` 500 14/20 tabular. `--free` value color `--sp-content-success` ("Free"). `__row--total`: margin-top 8, padding-top 12, `border-top:1px solid var(--sp-border-opaque)`, label `.r-label-lg` ink, value `--sp-font-mono` 500 16/24 ink.

### 4.30 Tracking timeline: `.r-timeline`

- **Classes**: `.r-timeline`, `__step`, `.is-done`, `.is-active`, `__bar`, `__label`.
- **Anatomy**: `ol.r-timeline > li.r-timeline__step(.is-done|.is-active)[aria-current="step"] > span.r-timeline__bar + span.r-timeline__label`. Four steps: Confirmed, Preparing, On the way, At the gate.
- **Spec** (Rally `.sp-journey`, segmented): `.r-timeline` flex, gap 6px, margin 12px 0 4px. `__step` flex 1, min-width 0. `__bar` height 4, radius 2, background `--sp-bg-tertiary`, overflow hidden, position relative. `.is-done > __bar` filled ink (`::before` inset 0, ink). `.is-active > __bar` ink fill at 50% with a `.r-wait`-style linear sweep over the remainder (linear only). `__label` 400 11px/14 tertiary, margin-top 6, text-align left; `.is-done` label secondary; `.is-active` label ink 500. No emoji circles, no connecting line, no circular steps. The step `aria-label` carries the status for screen readers; `.r-visually-hidden` suffix "completed" / "in progress".
- **States**: upcoming, active, done. JS currently sets `step.className = 'step done'`; it must set `r-timeline__step is-done`.
- **Mobile**: 4 segments across the full card width; labels may wrap to two lines.

### 4.31 Progress bar: `.r-progress`

- **Classes**: `.r-progress`, `__fill`, `--late`.
- **Spec** (rally-ai.jsx `Bar`): height 3, radius 2, background `--sp-line`, overflow hidden; `__fill` height 100%, background ink, `width` set inline as %, `transition: width 900ms linear`. `--late` fill `--sp-content-warning`. Linear only (never a ring).

### 4.32 Map: `.r-map`

- **Classes**: `.r-map`, `__pin`, `__pin--selected`, `__pin--user`.
- **Spec** (Rally map rules: full-bleed, no radius, no border, no chrome on top): `.r-map` `position:relative; isolation:isolate; overflow:hidden; background: var(--sp-map-apron); aspect-ratio: 1 / 1; border-radius:0; border:0`. On mobile it bleeds to the screen edges (`margin-inline: calc(var(--r-gutter) * -1)`). At 768: `aspect-ratio: 4 / 3`, margin-inline 0 (DERIVED). `__pin`: 28px circle (`--sp-pin-size`), background `--sp-pin-bg`, `--sp-pin-shadow`, icon 14px; `--selected` ink background, white icon, `scale(1.14)`. `__pin--user` (the user's position) is the one blue fill: `--sp-locate`, 16px, 2.5px white border. Pins replace the emoji divIcons (`createEmojiMarker`). Leaflet controls stay default; do not restyle tiles.

### 4.33 Call sheet: `.r-call`

- **Classes**: `.r-call`, `__eyebrow`, `__clock`, `__name`, `__number`, `__status`, `__actions`.
- **Anatomy**: `.r-sheet-layer > .r-scrim + .r-sheet.r-sheet--white > .r-sheet__grabber + header(.r-call__eyebrow + .r-call__clock) + div.r-sheet__body > .r-call__name + .r-call__number + .r-call__status + footer.r-sheet__footer > .r-call__actions`.
- **Spec** (screen-support.jsx `CallSheet`: an active call is a white bottom sheet, not a full screen): `__eyebrow` 11px/700 uppercase tracking .18em color `--sp-warm` ("On call" / "Incoming call"); `__clock` `--sp-font-mono` 600 14 tabular ink; `__name` `--sp-font-secondary` 700 30/1.06 tracking -.03em, `text-wrap:balance`; `__number` `.r-code`; `__status` `.r-para-md` secondary. Incoming: `__actions` flex gap 12: `.r-btn.r-btn--danger.r-btn--cta` "Decline" + `.r-btn.r-btn--success.r-btn--cta` "Accept". Active: single `.r-btn.r-btn--danger.r-btn--block` "End call" (Rally: height 58, radius 18, red, white). Replaces `.phone-call-overlay`; no glow avatar, no emoji.

### 4.34 Section head, divider, stack, icon

- `.r-section-head` (`__title` `.r-heading-xs`, `__meta` `.r-para-sm`): flex space-between align baseline, padding 0 0 8. Replaces `#im-results-title` / `#im-results-count` pair and "Recent orders".
- `.r-section-label`: eyebrow label (tokens file).
- `.r-divider`, `.r-divider--thick`, `.r-stack`, `--sm`, `--lg`, `.r-cluster`, `.r-hide-mobile`, `.r-hide-desktop`, `.r-no-scrollbar`, `.r-visually-hidden`, `.r-lock`: in tokens file.
- `.r-icon`, `--sm`, `--lg`: `width/height` 20/16/24, `flex-shrink:0`, stroke from `currentColor`.

---

## 5. Screen compositions

| Screen | Composition (top to bottom) |
|--------|----------------------------|
| Chat | `.r-topbar`, `.r-chat__welcome` (when empty) or `.r-chat__thread`, `.r-composer`, `.r-tabbar` |
| Food menu | `.r-topbar`, `.r-restaurant--hero`, `.r-chip-rail` (restaurants), `.r-chip-rail` (categories), `.r-grid > .r-dish*`, `.r-tabbar` |
| Instamart | `.r-topbar`, `.r-restaurant--store` (with `.r-search`), `.r-chip-rail` (categories), `.r-section-head`, `.r-grid--tiles > .r-product*`, `.r-tabbar` |
| Tracking | `.r-topbar`, (`.r-empty` or [`.r-banner--warning`, `.r-card` with `.r-timeline`, `.r-map`, rider `.r-card > .r-row`]), `.r-section-label`, `.r-card--flush > .r-list`, `.r-tabbar` |
| Cart | `.r-sheet--tall` (`--drawer` at 1024) |
| Add-ons | `.r-sheet` |
| Checkout | `.r-sheet` + `.r-pay` |
| Addresses | `.r-sheet` + `.r-list` |
| Connect Swiggy | `.r-sheet` with three step blocks |

---

## 6. Mapping: current SmartFlow UI to Rally components

Selectors are those in `static/index.html` and the template strings in `static/js/app.js`. **Keep every `id`** (JS binds to them); change classes only. JS lines that assign old classes are listed in section 7.

### 6.1 Header

| Current | Replacement |
|---------|-------------|
| `header.header` | `header.r-topbar` |
| `a.logo-container`, `.logo-icon` (emoji), `.logo-text`, `.logo-badge` ("AI CONCIERGE") | `a.r-topbar__brand` > `.r-topbar__brand-name` "SmartFlow"; badge becomes `.r-tag.r-tag--neutral.r-topbar__brand-tag.r-hide-mobile`; emoji icon deleted |
| `#header-location.header-center`, `.pulse-update` | `button.r-topbar__location` (id kept); pulse = re-trigger `sp-scale-in` |
| `.header-actions` | `.r-topbar__actions` |
| `#btn-swiggy-auth.btn-swiggy-auth`, `#swiggy-auth-icon`, `#swiggy-auth-label`, `.authenticated` | `button.r-btn.r-btn--secondary.r-btn--sm.r-btn--pill` + `span.r-btn__dot` (id `swiggy-auth-icon` moves to the dot) + `span.r-btn__label` (id `swiggy-auth-label`); `.authenticated` becomes `.is-connected` |
| `#btn-call-phone.btn-call` | `button.r-btn.r-btn--icon` (phone icon) with `span.r-btn__label.r-hide-mobile`... icon-only on mobile |
| `#btn-open-cart.cart-btn`, `#cart-badge.cart-badge` | `button.r-btn.r-btn--icon` (cart icon) + `span.r-badge#cart-badge` |

### 6.2 Navigation and screens

| Current | Replacement |
|---------|-------------|
| `main.main-layout` | `main.r-app__main` |
| `nav.tabs-nav`, `.tab-btn[data-target]`, `.tab-btn.active` | `nav.r-tabbar` > `.r-tabbar__pill` > `.r-tabbar__tab[data-target]`, `.is-active`. Four tabs: `pane-chat`, `pane-menu` (Food), `pane-instamart`, `pane-tracking`. |
| `#restaurant-nav-pills` + `.tab-btn.restaurant-nav-pill` (app.js:473) | `.r-chip-rail[role=tablist]` at the top of `#pane-menu`; each restaurant is `.r-chip` (`--selected` when current). They no longer live in the nav. |
| `.tab-pane`, `.tab-pane.active`, `#pane-chat`, `#pane-menu`, `#pane-instamart`, `#pane-tracking` | `.r-screen`, `.r-screen.is-active` (+ `hidden` attr when inactive), ids kept |

### 6.3 Chat and voice

| Current | Replacement |
|---------|-------------|
| `.hero-voice`, `.hero-title`, `.hero-subtitle` | `.r-chat__welcome`, `.r-chat__welcome-title`, `.r-chat__welcome-text` (shown only while the thread is empty) |
| `.mic-wrapper`, `.mic-orb#mic-btn`, `.listening` | `button.r-composer__action.r-composer__action--mic#mic-btn`; `.listening` becomes `.is-listening` on `.r-composer` |
| `.wave-bars#wave-bars`, `.bar`, `.active` | `.r-composer__wave#wave-bars`, `.r-composer__wave-bar`; shown by `.r-composer.is-listening` |
| `#mic-status.mic-status` | `p.r-composer__status#mic-status` |
| `.quick-chips#quick-action-chips`, `.chip[data-prompt]` | `.r-composer__suggestions.r-chip-rail#quick-action-chips`, `.r-chip` (emoji removed from labels: "Food cart", "Instamart cart", "Checkout and pay", "Live tracking") |
| `#frequent-suggestions-container`, `.chip.frequent-chip` (app.js:496, 525) | same rail, `.r-chip` |
| `.chat-container` | `.r-chat` |
| `.chat-messages#chat-messages` | `.r-chat__thread#chat-messages` |
| `.msg.bot`, `.msg.user` (app.js:894) | `.r-msg.r-msg--agent`, `.r-msg.r-msg--user` |
| `.avatar`, `.msg-bubble` | avatar deleted; `.r-msg__bubble` |
| bubble quick-link `.chip` with inline style (app.js:~905) | `.r-msg__actions > .r-chip.r-chip--outline` |
| `#typing-indicator.msg.bot` (app.js:932) | `.r-msg.r-msg--agent#typing-indicator > .r-typing` |
| `.chat-input-bar`, `#chat-input.chat-input` | `.r-composer__row`, `.r-composer__field > input.r-composer__input#chat-input` |
| `#btn-send.btn-send` | `button.r-composer__action.r-composer__action--send#btn-send` |

### 6.4 Menu (Food)

| Current | Replacement |
|---------|-------------|
| `.restaurant-hero`, `.restaurant-info`, `.restaurant-meta`, `.rating-badge` | `.r-restaurant.r-restaurant--hero`, `__body`, `__meta`, `__rating` |
| `#restaurant-frequent-badge` (inline styled) | `.r-tag.r-tag--accent` inside `__badges` |
| `.category-filter#category-filters`, `.cat-pill(.active)` (app.js:958) | `.r-chip-rail#category-filters`, `.r-chip(.r-chip--selected)` |
| `.menu-grid#menu-grid` | `.r-grid#menu-grid` (add `.r-grid--wide`) |
| `.dish-card` (app.js:985) + `.dish-img-wrapper`, `.dish-img`, `.dish-details`, `.dish-veg-badge`, `.dish-name`, `.dish-price`, `.dish-desc`, `.btn-add-dish` | `.r-dish` + `__media`, `__img`, `__body`, `__veg(--veg\|--nonveg)`, `__name`, `__price`, `__desc`, `__action > .r-btn.r-btn--secondary.r-btn--sm.r-btn--pill` |

### 6.5 Instamart

| Current | Replacement |
|---------|-------------|
| `.instamart-hero`, `.im-hero-content`, `#im-hero-badge.im-hero-badge` | `.r-restaurant.r-restaurant--store`; badge = `.r-tag.r-tag--neutral#im-hero-badge` ("Instamart, 10 to 15 min") |
| `.im-search-box`, `.im-search-icon`, `#im-search-input.im-search-input`, `#btn-im-search.btn-im-search` | `.r-search`, `.r-search__icon`, `input.r-search__input#im-search-input`, `button.r-search__submit.r-btn.r-btn--primary.r-btn--sm.r-btn--pill#btn-im-search` |
| `.im-category-filter#im-category-filters`, `.im-cat-pill[data-cat]`, `.active` | `.r-chip-rail#im-category-filters`, `.r-chip[data-cat]`, `.r-chip--selected` (emoji removed) |
| `#im-results-title`, `#im-results-count` (inline styled div) | `.r-section-head > .r-section-head__title#im-results-title + .r-section-head__meta#im-results-count` |
| `.im-product-grid#im-product-grid` | `.r-grid.r-grid--tiles#im-product-grid` |
| `.im-card` (app.js:1210) + `.im-card-img-wrap`, `.im-card-img`, `.im-time-tag`, `.im-discount-tag`, `.im-card-name`, `.im-card-unit`, `.im-price-wrap`, `.im-price`, `.im-mrp`, `.im-card-bottom`, `.im-action-wrap`, `.btn-im-add`, `.im-qty-stepper`, `.im-step-dec`, `.im-step-inc` | `.r-product` + `__media`, `__img`, `__time`, `__discount`, `__name`, `__unit`, `__price-row`, `__price`, `__mrp`, `__footer`, `__action`, `.r-btn--secondary.r-btn--sm.r-btn--pill`, `.r-stepper`, `.r-stepper__btn` x2 |

### 6.6 Cart

| Current | Replacement |
|---------|-------------|
| `.cart-drawer-overlay#cart-drawer-overlay` (`.open`) | `.r-sheet-layer#cart-drawer-overlay` (`.is-open`) with `.r-scrim` |
| `aside.cart-drawer` | `section.r-sheet.r-sheet--tall.r-sheet--drawer` (drawer modifier only takes effect at 1024) |
| `.drawer-header`, `.drawer-title#drawer-main-title` | `.r-sheet__header`, `.r-sheet__title#drawer-main-title` (emoji removed: "Your cart") |
| `#btn-clear-active-cart.btn-clear-cart` | `.r-btn.r-btn--ghost.r-btn--sm` "Clear" |
| `#btn-close-cart.drawer-close` (`&times;`) | `.r-btn.r-btn--icon.r-sheet__close#btn-close-cart` (close icon) |
| `.cart-service-switch#cart-service-switch`, `.cart-switch-btn[data-cart]`, `#btn-switch-food`, `#btn-switch-im`, `.cart-pill-count` (`#cart-food-count`, `#cart-im-count`) | `.r-chip-rail[role=tablist]#cart-service-switch`, `.r-chip` (ids kept, `--selected` on current), `.r-chip__count` |
| `.drawer-body` | `.r-sheet__body` |
| `.cart-service-banner#cart-service-banner`, `#cart-banner-icon`, `#cart-banner-text` | `.r-banner.r-banner--neutral#cart-service-banner`, `.r-banner__icon#cart-banner-icon`, `.r-banner__text#cart-banner-text` |
| `#cart-items-list`, `.cart-item` (app.js:1438, 1544) | `.r-list#cart-items-list`, `.r-row` with `__main` (name, variant + price) + `__trail` (`.r-stepper` then `.r-row__amount`) |
| `.stepper`, `.btn-step[data-action]`, `.step-qty` | `.r-stepper`, `.r-stepper__btn[data-action]`, `.r-stepper__qty` |
| empty-cart inline block (app.js:1410) | `.r-empty` (icon, title "Your Instamart cart is empty.", text, `__actions`) |
| `.bill-breakdown#cart-bill-breakdown`, `.bill-row`, `.bill-row.total`, `#bill-item-total`, `#bill-delivery-fee`, `#bill-taxes`, `#bill-total-pay` | `.r-bill.r-card#cart-bill-breakdown`, `.r-bill__row`, `.r-bill__row--total`; value elements keep ids and get `.r-bill__value`; delivery fee free = `.r-bill__value--free` |
| `.drawer-footer#cart-drawer-footer`, `.btn-approve-order#btn-approve-order` | `.r-sheet__footer#cart-drawer-footer`, `.r-btn.r-btn--primary.r-btn--cta#btn-approve-order` with `__label` "Review and pay" and `__amount` = total |

### 6.7 Add-ons, payment, addresses, connect

| Current | Replacement |
|---------|-------------|
| `.modal-overlay#addons-modal` (`.open`), `.modal-content` | `.r-sheet-layer#addons-modal` (`.is-open`) > `.r-scrim` + `.r-sheet` |
| `#addon-dish-name`, `#addon-base-price`, `#btn-close-addons.drawer-close` | `.r-sheet__title#addon-dish-name`, `.r-sheet__subtitle#addon-base-price`, `.r-sheet__close#btn-close-addons` |
| addon `<label>` rows with raw `input[type=checkbox][data-price]` and amber price | `label.r-row.r-row--interactive` > `.r-row__main` (name) + `.r-row__trail` (`.r-row__amount` "+₹40" in ink, not amber, then `.r-check` containing the same `input[data-price]`) |
| `#addon-total-btn.btn-approve-order` | `.r-btn.r-btn--primary.r-btn--cta#addon-total-btn` (label "Add to cart", `__amount` total) |
| `.modal-overlay#payment-modal`, `#btn-close-payment` | `.r-sheet-layer#payment-modal`, `.r-sheet__close#btn-close-payment`, `.r-pay` |
| `#pay-order-id`, `#pay-modal-amount` (inline orange 2.2rem) | `.r-code#pay-order-id`, `.r-amount.r-amount--md#pay-modal-amount` (ink, not orange) |
| `#pay-method-input` (hidden) + `.badge` "UPI Only" | hidden input stays; `.r-tag.r-tag--success.r-pay__method` "UPI" |
| `#qr-section`, `.upi-apps-grid`, `.upi-pill-btn#btn-pay-gpay/-phonepe/-paytm/-cred` | `.r-pay__apps`, `.r-pay__app.r-btn.r-btn--secondary.r-btn--pill` (same ids; labels "Google Pay", "PhonePe", "Paytm", "CRED"; emoji dots removed) |
| `.qr-box`, `.qr-img#swiggy-qr-img` | `.r-pay__qr.r-card`, `.r-pay__qr-img#swiggy-qr-img` |
| `.copy-row`, `#upi-vpa-text`, `.copy-btn#btn-copy-upi` | `.r-pay__vpa`, `.r-code#upi-vpa-text`, `.r-btn.r-btn--secondary.r-btn--sm.r-pay__copy#btn-copy-upi` |
| `#btn-final-pay.btn-approve-order` | `.r-btn.r-btn--primary.r-btn--cta#btn-final-pay` in `.r-sheet__footer` |
| `.modal-overlay#address-modal`, `#btn-close-address`, `#address-list` | `.r-sheet-layer#address-modal`, `.r-sheet__close#btn-close-address`, `.r-list#address-list` |
| `.address-card(.active)`, `.address-card-info` (h4, p), `.address-card-badge` ("ACTIVE"/"SELECT") (app.js:379) | `li.r-row.r-row--interactive(.r-row--selected)`, `.r-row__main` (`__title` tag name, `__sub` address line), `.r-row__lead` pin icon in `.r-avatar`, trailing `.r-check` (on = active). Badge text and the green/pin emoji prefixes are deleted. |
| `.modal-overlay#swiggy-modal`, `#btn-close-swiggy` | `.r-sheet-layer#swiggy-modal`, `.r-sheet__close#btn-close-swiggy` |
| `#swiggy-step-connected`, `#btn-swiggy-disconnect`, `#btn-swiggy-relogin` | step block `.r-stack`; `.r-btn.r-btn--danger-quiet.r-btn--block#btn-swiggy-disconnect`; `.r-btn.r-btn--ghost.r-btn--sm#btn-swiggy-relogin` |
| `#swiggy-step-phone`, `#btn-swiggy-quick-connect` (green gradient) | step block `.r-stack`; `.r-btn.r-btn--primary.r-btn--cta#btn-swiggy-quick-connect` (no gradient) |
| `#swiggy-phone-input` | `.r-field` > `.r-field__control` (`__prefix` "+91" + `input.r-field__input#swiggy-phone-input`) |
| `#btn-swiggy-send-otp` (inline orange) | `.r-btn.r-btn--secondary.r-btn--cta#btn-swiggy-send-otp` if quick-connect is shown, else `--primary` (one primary per step) |
| `#swiggy-step-otp`, `#swiggy-otp-sent-msg`, `#swiggy-otp-input` | step block; `.r-banner.r-banner--success#swiggy-otp-sent-msg`; `.r-otp` with `input.r-otp__input#swiggy-otp-input` |
| `#btn-swiggy-verify-otp` (inline green) | `.r-btn.r-btn--primary.r-btn--cta#btn-swiggy-verify-otp` |
| `#btn-swiggy-resend-otp`, `#btn-swiggy-change-phone`, `#btn-swiggy-browser-flow` | `.r-btn.r-btn--ghost.r-btn--sm` (same ids) |

### 6.8 Tracking and calls

| Current | Replacement |
|---------|-------------|
| `.tracking-container` | `.r-stack` |
| `#no-active-order-box` (dashed box, inline buttons) | `.r-empty` with `__actions` (two `.r-btn.r-btn--pill`, one primary one secondary) |
| `#active-order-tracking-section` | `.r-stack#active-order-tracking-section` |
| `.arrival-alert-box#gate-arrival-alert`, `.alert-content`, `.alert-icon`, `#gate-arrival-alert-msg`, inline `.btn-call` | `.r-banner.r-banner--warning#gate-arrival-alert[role=alert]`, `__icon`, `__body`, `__text#gate-arrival-alert-msg`, `__action.r-btn.r-btn--secondary.r-btn--sm.r-btn--pill` |
| order header: `#tracking-order-id`, `#tracking-items-summary`, `#tracking-eta`, `#tracking-status-badge` | `.r-card > .r-card__header`: `.r-card__title#tracking-order-id`, `.r-card__sub#tracking-items-summary`, `.r-card__aside` with `.r-mono-lg#tracking-eta` (success color) and `.r-tag#tracking-status-badge` |
| `.timeline`, `#timeline-progress`, `.step(.active/.done)`, `#step-1..#step-4`, `.step-circle`, `.step-label` | `.r-timeline`, (`#timeline-progress` deleted; unused fill), `.r-timeline__step(.is-active/.is-done)` keeping `#step-1..4`, `.step-circle` deleted, `.r-timeline__bar`, `.r-timeline__label` |
| `#live-map`, `.map-marker-icon` | `.r-map#live-map`, `.r-map__pin` |
| `.rider-card#rider-card`, `.rider-info`, `.rider-avatar`, `.rider-name#rider-card-name`, `.rider-sub#rider-card-sub`, `#btn-call-rider.btn-call` | `.r-card > .r-row`: `.r-avatar` (initials, cycle color), `.r-row__title#rider-card-name`, `.r-row__sub#rider-card-sub`, trailing `.r-btn.r-btn--icon#btn-call-rider` (phone icon). Rating "4.9, 1.2K+ deliveries" is plain secondary text, no star glyph. |
| `.past-orders-title`, `#past-orders-list` | `.r-section-label`, `.r-card.r-card--flush > .r-list#past-orders-list` |
| `.order-history-card` (app.js:2329) | `li.r-row`: `__main` (restaurant name `__title`, items `__sub`, time + status `__sub`), `__trail` (`.r-row__amount` total, then `.r-btn.r-btn--secondary.r-btn--sm.r-btn--pill` "Track" or "Reorder") |
| "ACTIVE IN-FLIGHT" inline span, status colors | `.r-tag.r-tag--warn` "In progress"; delivered `.r-tag.r-tag--success` "Delivered" |
| `.phone-call-overlay#phone-call-overlay` (`.open`), `.phone-call-modal` | `.r-sheet-layer#phone-call-overlay` (`.is-open`) > `.r-scrim` + `.r-sheet.r-sheet--white.r-call` |
| `#call-status-label.call-status-label`, `.phone-avatar-glow`, `#call-caller-name`, `#call-number`, `#call-active-timer` | `.r-call__eyebrow#call-status-label`, avatar glow deleted, `.r-call__name#call-caller-name`, `.r-call__number#call-number`, `.r-call__clock#call-active-timer` |
| `.call-actions-row#call-incoming-actions`, `.btn-call-circle.btn-call-decline#btn-call-decline`, `.btn-call-accept#btn-call-accept` | `.r-call__actions#call-incoming-actions`, `.r-btn.r-btn--danger.r-btn--cta#btn-call-decline`, `.r-btn.r-btn--success.r-btn--cta#btn-call-accept` |
| `.call-actions-row#call-active-actions`, `#btn-call-hangup` | `.r-call__actions#call-active-actions`, `.r-btn.r-btn--danger.r-btn--block#btn-call-hangup` ("End call") |

### 6.9 Global

| Current | Replacement |
|---------|-------------|
| `.toast#toast` (`showToast`, app.js:2377) | `.r-toast#toast` (+ `.is-visible`), always in DOM with `role=status` |
| `.leaflet-*` | untouched; contained by `.r-map` isolation |
| Google Fonts Inter/Outfit | removed; UberMove via `rally-tokens.css` |
| `<link rel="icon">` data-URI with the curry emoji (index.html:8) | needs a real icon asset (section 8); remove the emoji |
| inline `style=""` colors (`#94a3b8`, `#f8fafc`, `#ff5200`, `#fc8019`, `#10b981`, `#f59e0b`) | all removed; use tokens. Orange `#ff5200`/`#fc8019` (Swiggy) is not a Rally color and does not appear. |
| any `badge`, `.chip` inline background overrides | `.r-tag` / `.r-chip` variants only |

---

## 7. JS touch points the restyle agents must coordinate on

Classes the JS writes today (so the CSS and JS agents agree):

| app.js line (approx.) | Today | Must become |
|-----------------------|-------|-------------|
| 69, 74 | `btn.classList.add/remove('authenticated')` | `is-connected` |
| 124, 141, 423, 1050, 1591, 1604, 1612, 1619, 1701, 1803, 608, 613, 1991, 2045 | `classList.add/remove('open')` and `'active'` on modal/overlay | `is-open` on `.r-sheet-layer`; also toggle `.r-lock` on `<body>` |
| 368, 370 | `pulse-update` | re-trigger `sp-scale-in` (remove class, force reflow, add `r-fade-up`/`r-scale-in`) |
| 473 | `tabBtn.className = 'tab-btn restaurant-nav-pill'` | `r-chip` (+ `r-chip--selected`) |
| 496, 525 | `'chip frequent-chip'` | `'r-chip'` |
| 569 to 578, 1826 to 1831 | `.tab-btn`, `.tab-pane` toggling `active` | `.r-tabbar__tab`, `.r-screen` toggling `is-active` (+ `hidden`, `aria-selected`) |
| 599 to 604 | `cart-switch-btn` toggling `active` | `r-chip` toggling `r-chip--selected` (+ `aria-selected`) |
| 803 to 815 | `micBtn.classList 'listening'`, `waveBars 'active'` | `is-listening` on `.r-composer` (+ `aria-pressed`) |
| 894, 932 | `msg ${role}` (`user`/`bot`) | `r-msg r-msg--user` / `r-msg r-msg--agent` |
| 958, 961 | `cat-pill`, `.active` | `r-chip`, `r-chip--selected` |
| 985 | `dish-card` | `r-dish` |
| 1084 to 1100 | `.im-cat-pill`, `.active` | `.r-chip`, `r-chip--selected` |
| 1210 | `im-card` | `r-product` |
| 1438, 1544 | `cart-item` | `r-row` |
| 1878 | `map-marker-icon` | `r-map__pin` |
| 2174 to 2261 | `step`, `step active`, `step done` | `r-timeline__step`, `... is-active`, `... is-done` |
| 2329 | `order-history-card` | `r-row` |
| 2377 | toast text/classes | `.is-visible` on `.r-toast`, dismiss after `--sp-dur-toast` (2400ms) |

New JS behavior the spec requires (small): composer `has-text` toggle; OTP box mirroring; sheet focus management and drag-to-dismiss; `r-lock` on body; `aria-selected`/`aria-pressed` upkeep. Do not change API calls or data handling.

---

## 8. Asset dependencies and open items

1. **Icons.** Rally's hand-tuned set (`rally/app/components.jsx` `ICONS`, 24x24, 2px stroke) has: back, close, search, qr, bank, contacts, upi, card, phone, check, chev, chevDown, plus, bolt, gift, bell, settings, clock, wallet, trophy, flame, trend, user, copy, more, home, chart, share, sparkle. Plus two inline SVGs in `rally-ai.jsx`: mic and arrow-up (send). **Missing for SmartFlow and not available as assets**: chat/message, food/utensils, shopping bag or cart, scooter/delivery, map pin, trash, headset. Rally fills gaps from Font Awesome Pro (kit `3b43ab4255`, `fa-regular`); that kit is not available here. These glyphs must be supplied by the design owner or drawn to the same spec (24x24, 2px stroke, round caps/joins, `currentColor`). Not created in this task.
2. **Brand mark.** No SmartFlow wordmark/logo asset exists. Top bar uses text only until one is supplied. The Rally wordmark (`rally/track/assets/rally-logo.png`) is Rally's and is not used.
3. **UPI app logos** (Google Pay, PhonePe, Paytm, CRED) and **Swiggy/Instamart marks**: not available; text labels used.
4. **Food/product photography**: comes from the API as today.
5. **UberMove licensing**: "proprietary, internal use only" in Rally source. Confirm rights before deploying SmartFlow publicly; fallback stack is `system-ui, Helvetica Neue, Helvetica, Arial`.
6. **Values Rally does not define** (all marked DERIVED above): breakpoints, z-index tokens as named, safe-area, page max width, gutter at 768/1024, user chat bubble color, quantity stepper, banner, badge, QR block, bill rows, map aspect at tablet, focus ring, hover wash guard.
7. **Rally-specific components not used** in SmartFlow: SuperCashCoin, StreakFlame, CreditCardChip, bolt pill, finder/compass, place offers, ticket.

---

## 9. Implementer checklist (runnable)

```sh
# no emoji or glyph icons left in markup or templates (perl: macOS grep has no -P)
perl -CSD -ne 'print "$ARGV:$.: $_" if /[\x{1F300}-\x{1FAFF}\x{2600}-\x{27BF}]/' static/index.html static/js/app.js    # expect no output
# no inline color overrides
grep -n 'style="[^"]*#' static/index.html                                                # expect no output
# no non-token radii or off-palette hex in component CSS
grep -nE '#(94a3b8|f8fafc|ff5200|fc8019|10b981|f59e0b)' static/css/*.css                # expect no output
# every old class gone from templates
grep -nE "class(Name)? ?= ?['\"\`][^'\"\`]*\b(dish-card|im-card|cart-item|msg-bubble|tab-btn|modal-overlay)\b" static/js/app.js   # expect no output
# tokens loaded
grep -n 'rally-tokens.css' static/index.html                                              # expect 1 line
```
