# DESIGN_SIGNAL: the visual design for the TYLY dashboard

Source: measured from the reference build https://signal-agent-nu.vercel.app/ (briefing, Classic dashboard toggle, /ask, /build) on 2026-10-13. The CSS custom properties and computed styles were read from the live page, so they are not approximations. (The file was missing from the repo, so it was reconstructed here: see dashboard/DECISIONS.md D15.)

## 1. Principles
- **An agent briefing, not a wall of charts.** The landing page is a short stream of sentences that each contain a number, are ranked by urgency, and come with evidence and a next action. The classic dashboard is one toggle away.
- **One highlight per view.** A single accent series, with everything else neutral. Red, amber and green carry status only.
- **Editorial type.** A serif for headlines (Instrument Serif), a quiet sans for UI (Geist), and a mono for data labels and IDs (JetBrains Mono).
- **Calm surfaces.** Off-white page, white cards, 1px hairline borders, no shadows, 8px radius.

## 2. Tokens
Applied as CSS custom properties on `:root`. The theme toggle swaps the whole set.

| token | light | dark | use |
|---|---|---|---|
| `--bg` | `#f7f8fa` | `#0c0e11` | page and sidebar background |
| `--surface` | `#ffffff` | `#13161a` | cards, tiles, inputs |
| `--surface2` | `#f1f3f6` | `#1a1e23` | active nav item, hover |
| `--surface3` | `#e5e8ed` | `#252a31` | bar tracks, neutral bars ("others") |
| `--border` | `#e2e6eb` | `#242a31` | hairlines, card borders, chips |
| `--border2` | `#cdd3db` | `#363d47` | outline buttons; **LY series** |
| `--text` | `#0f1318` | `#e6e9ed` | ink; primary button background |
| `--muted` | `#58616d` | `#9aa3ae` | body copy, labels |
| `--faint` | `#868e9b` | `#6d7682` | placeholders, captions |
| `--accent` | `#2d54d3` | `#7099ff` | **TY series / Gen Z highlight**, accent buttons, badges |
| `--accent-soft` | `#e9f0ff` | `#18274b` | info banner, "Claude" node, Ask-agent button |
| `--accent-ink` | `#2346bc` | `#a7c3ff` | text on accent-soft |
| `--on-accent` | `#ffffff` | `#0c0e11` | text on accent |
| `--green` / `-soft` / `-ink` | `#329d5a` / `#e0f7e5` / `#126635` | `#4fb772` / `#16321f` / `#89dea1` | Win pill, "checked" badge, good |
| `--amber` / `-soft` / `-ink` | `#e4a339` / `#fff0d1` / `#8d5406` | `#e9b452` / `#3f2c10` / `#f5cf7d` | Pattern pill, warning, latest-week column |
| `--red` / `-soft` / `-ink` | `#db423c` / `#ffebe9` / `#b02b27` | `#ef6661` / `#451e1c` / `#ffaaa2` | Needs-you pills, critical, blocked |

Radii: pill 999px · button / card / input 8px · segmented outer 9px, inner 6px · chip 4px · badge 9px.
Spacing: content gutter 32px (≥900px) / 16px; card stack gap 28px; card internal gap 16px; card bottom padding 32px with a 1px `--border` bottom rule.

## 3. Typography
| role | font | size / line-height | weight | other |
|---|---|---|---|---|
| Page h1 | Instrument Serif | 60px / 1.0 (40px <900px) | 400 | letter-spacing -0.02em; optional italic tail in `--muted` |
| Card headline | Instrument Serif | 42px / 1.08 at ≥1280px, 30px below | 400 | -0.01em; text-wrap: balance |
| Section h2 (build page) | Instrument Serif | 32px / 1.1 | 400 | |
| Stat number (build page) | Instrument Serif | 44px | 400 | caption 12px muted |
| Logo wordmark | Instrument Serif | 28px | 400 | |
| Eyebrow | JetBrains Mono | 11.5px | 400 | uppercase, letter-spacing 0.08em, `--muted`, leading accent dot |
| Lead | Geist | 15px / 1.5 | 400 | `--muted`, max-width 600px |
| Card body | Geist | 14px / 1.625 | 400 | `--muted`, max-width 640px |
| UI / nav / buttons | Geist | 13px | 400 (nav) / 500 (active nav, buttons) / 600 (primary button) | |
| Meta line, pill | Geist | 12px | 400 / 500 | |
| KPI tile value | Geist | 26px | 600 | label 12px muted |
| Data labels, chips, numbers in bars | JetBrains Mono | 11.5–12px | 400 | `--muted` |

## 4. Layout
- **Sidebar** 232px, `--bg`, padding 20px 12px 16px, sticky full height. Logo (accent square mark + serif wordmark), nav list (icon + label + right-aligned count/badge), then the controls block, and the "● Agent watching" status block pinned at the bottom (12.5px, the dot in `--accent`).
- **Top bar**: a search input (surface, 1px border, radius 8, 34px tall, leading ○ glyph, "/" key hint) and a theme toggle button at the right ("◐ Light" / "◑ Dark").
- **Info banner** under the top bar: `--accent-soft`, radius 8, padding 10px 12px 10px 14px, a leading accent dot, 13px text, and a × to dismiss.
- **Briefing grid**: cards column `minmax(0,1fr)` plus a 320px right rail at ≥1280px. Below 1280px the rail stacks under the cards.
- **Header row**: eyebrow, h1, lead on the left, with the segmented toggle bottom-right (it wraps under on narrow screens).

## 5. Components
- **Briefing card** (no box): pill + meta line → serif headline → muted body → micro-chart → action row (buttons left, evidence chips right) → 1px bottom rule.
- **Pill**: radius 999, padding 2px 9px, 12px/500. Variants: *Needs you today* / *Needs you* = red-soft bg + red-ink; *Pattern* = amber-soft + amber-ink; *Win* = green-soft + green-ink; *Watch* = surface2 + muted.
- **Buttons** (32px tall, radius 8, 13px): *primary* = `--text` bg + `--bg` text, 600; *accent* = `--accent` bg + `--on-accent` text, 500, leading "●"; *ask-soft* = `--accent-soft` bg + `--accent-ink` text; *outline* = transparent, 1px `--border2`, `--text`.
- **Segmented control**: outer surface, 1px border, radius 9, padding 3px; inner buttons 30px, radius 6, 13px/500; the active one is ink bg + bg text with a small accent dot.
- **Evidence chip**: mono 11.5px, 1px `--border`, radius 4, padding 1px 7px, muted.
- **Comparison bars** (micro-chart): rows of label (12.5px muted, 170px) | track (8px, `--surface3`, radius 4) with fill | value (mono 12px muted, right-aligned, 56px).
- **Column sparkline**: equal-width columns with a mono value above and a mono label below. Past columns `--surface3`, the latest column `--amber`.
- **Watch rail**: 1px `--text` top rule, title 13px/600 + muted count on the right, rows of a coloured dot (status colour), the rule label and a mono count, then the alert list. Severity is always shown as icon + label (▲ Critical, ◆ Warning, ● Info), never colour alone.
- **KPI tile**: surface card, 1px border, radius 8, padding 14px 16px; label 12px muted; value 26px/600; sub-line mono 11.5px with LY and a YoY delta coloured by sign (up green-ink, down red-ink, with an arrow glyph).
- **Chart card**: surface, 1px border, radius 8, padding 14px 16px; title 12.5px/500; optional muted note on the right.
- **Filter select**: outline style (surface bg, 1px border, radius 8, 30px, 12px).
- **Trust badge**: 12px, with a ✓ in green-ink: "Worded by Claude; every number checked". Blocked variant: ✕ in red-ink, "Blocked: unverified number".
- **Floating Ask pill**: fixed bottom-right 20px, 44px tall, radius 22, accent bg, "● Ask" plus a count bubble.

## 6. Charts
- Plotly, transparent background, Geist 12px ticks in `--muted`, no top/right spines, faint horizontal gridlines (`--border`), no vertical grid.
- **TY = `--accent`, LY = `--border2`**. Gen Z = `--accent` vs other generations `--surface3`. Red/amber/green only for status.
- No dual axes. No rainbow palettes. Direct labels at the line ends instead of legends. Mono value labels on bars.
- Hover tooltips in the surface colour with a 1px border.
- Partial week W30 is marked (dotted segment and a "partial" annotation); LY full W30 is shown as a hollow reference point.

## 7. Voice
- First person, agent-like: "I checked…", "I'm watching…".
- The headline is one sentence that states what happened, with the number in it. It doesn't use hype words, and the reader should be able to act on it without reading the body.
- The body is 2–3 short sentences: why it matters → the evidence → what to do next. Name the finding/rule. Say "sample-scale" when quoting counts.
- Numbers are printed exactly as they appear in the facts, rounded for display only: percentages to 1 dp (YoY > 100% to whole %), money as $71.3K or $564,028, WOS to 1 dp.
- Never invent a number: no derived ratios ("2.9 times"), no sums, no differences that aren't in the facts.

## 8. Content mapping (TYLY)
| card | pill (by week) | finding / rec | rules | micro-chart |
|---|---|---|---|---|
| Tabby franchise stock-out | critical → *Needs you today*; warning → *Needs you*; else *Watch* | F11, F12, R1 | WOS_LOW, WOS_COLLAPSE_VS_LY, RECEIPTS_BELOW_SALES | comparison bars: TY WOS vs LY WOS for Tabby and Pillow Tabby |
| Retention leak & Insider gap | warning → *Needs you*; else *Watch* | F6, F7, R3 | RETURNING_YOY_FLAT, GENZ_RETURNING_YOY_NEG, GENZ_NEW_INSIDER_LOW | comparison bars: Insider attach of new customers (Gen Z vs all) TY vs LY; segment gaps from W29 |
| Gen Z share of new accelerating | *Pattern* | F5 | GENZ_SHARE_BELOW_LY (inverse) | column sparkline of TY share by week, latest amber |
| Gen Z acquisition / Tabby growth | *Win* | F4, F9 | SALES_YOY_SPIKE | before/after bars: Gen Z new LY → TY |
| Apparel overstock | *Watch* | F10, F11, R2 | WOS_HIGH, FAMILY_L4W_DECLINE | comparison bars: WOS TY vs LY for over-stocked families |
