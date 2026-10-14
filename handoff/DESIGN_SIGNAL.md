# Design spec — "Signal" style (reference: https://signal-agent-nu.vercel.app/)

Both the dashboard (PROMPT_C) and the deck (PROMPT_D) must follow this style. It was extracted from the reference site's computed CSS on 2026-10-13. Open the reference in a browser before building, and compare your result against it side by side at the end.

## 1. The idea
An **agent briefing**, not a wall of charts. The landing view tells the reader *what changed and what to do*, with each finding written as a full sentence that carries its numbers. A big editorial serif headline sits over calm UI text. There is one accent colour, and status colours are used only when they carry meaning. The reference even ships a "Classic dashboard" toggle as a deliberate foil: "Everything is here. You find the story." Our app should do the same. The briefing is the default; the classic G1–G4 charts sit one click away.

## 2. Design tokens (copy exactly)
```css
[data-theme="light"] {
  --bg:#f7f8fa; --surface:#ffffff; --surface2:#f1f3f6; --surface3:#e5e8ed;
  --border:#e2e6eb; --border2:#cdd3db;
  --text:#0f1318; --muted:#58616d; --faint:#868e9b;
  --accent:#2d54d3; --accent-soft:#e9f0ff; --accent-ink:#2346bc; --on-accent:#ffffff;
  --green:#329d5a; --green-soft:#e0f7e5; --green-ink:#126635;
  --amber:#e4a339; --amber-soft:#fff0d1; --amber-ink:#8d5406;
  --red:#db423c;   --red-soft:#ffebe9;   --red-ink:#b02b27;
}
[data-theme="dark"] {
  --bg:#0c0e11; --surface:#13161a; --surface2:#1a1e23; --surface3:#252a31;
  --border:#242a31; --border2:#363d47;
  --text:#e6e9ed; --muted:#9aa3ae; --faint:#6d7682;
  --accent:#7099ff; --accent-soft:#18274b; --accent-ink:#a7c3ff; --on-accent:#0c0e11;
  --green:#4fb772; --green-soft:#16321f; --green-ink:#89dea1;
  --amber:#e9b452; --amber-soft:#3f2c10; --amber-ink:#f5cf7d;
  --red:#ef6661;   --red-soft:#451e1c;   --red-ink:#ffaaa2;
}
```
The page background is `--bg`. Cards and controls sit on `--surface` with a 1px `--border`. Hover and active nav use `--surface2`. Chart tracks and neutral bars use `--surface3`. Provide a **Light/Dark toggle** (top-right, outline button with a half-moon icon) that swaps the full token set. Never auto-invert colours.

## 3. Typography (Google Fonts, OFL-licensed)
| Role | Font | Size / weight / tracking | Colour |
|---|---|---|---|
| Page title (h1) | **Instrument Serif** 400 | 60px, line-height 1.0, letter-spacing −0.02em (−1.2px). Optional second line in *italic* `--muted` (e.g. "Everything is here. / *You find the story.*") | `--text` |
| Finding / card headline | Instrument Serif 400 | 30px (42px ≥1280px wide), line-height 1.08, −0.01em, `text-wrap: balance` | `--text` |
| Big stat numbers ("How it was built" trio) | Instrument Serif 400 | ~40px | `--text` |
| Lead paragraph under h1 | **Geist** 400 | 15px / 1.5, max-width 600px | `--muted` |
| Card body | Geist 400 | 14px / 1.625, max-width 640px | `--muted` |
| UI text, nav, buttons | Geist 400 / 500 (nav) / 600 (primary button) | 13px / 1.45 | `--text` |
| Meta line next to pill ("Risk · Northwind Media") | Geist 400 | 12px | `--muted` |
| Eyebrow (above h1, section labels) | **JetBrains Mono** 400, UPPERCASE | 11.5px, letter-spacing 0.08em, preceded by a 7px round `--accent` dot | `--muted` |
| Numbers in charts, IDs, chips, section numbers ("01") | JetBrains Mono 400 | 11.5–12px | `--muted` |

Base body font size is **13px**. The UI is compact and the serif headlines carry the hierarchy.

## 4. Layout
- **Left sidebar**, ~200px, background `--bg`, no border:
  - Logo: an 18px `--accent` rounded square with a white inner square, plus the wordmark in Instrument Serif ~24px. Use our product name (e.g. "Signal · TYLY" or "Pulse").
  - Nav items: icon + label, 13px weight 500, 6px radius. Active item gets a `--surface2` background. A count badge on the right is either an `--accent` filled 18px pill with a white 11px/600 number (items needing attention) or a faint mono number (totals).
  - Bottom block: "● Agent watching" (accent dot) with 2–3 muted lines (e.g. "1,829 TY transactions · 336 stock snapshots / Data as of {meta.as_of_date} · {n} insights"), then a faint footer "Sample data · Built with Claude Code".
- **Top bar:** search-style input on the left ("Jump to a family, week or finding", with a `/` key hint chip) and the Light/Dark toggle on the right.
- **Dismissible info banner** under the top bar: `--accent-soft` background, `--text`, 13px, with a leading accent dot and an × on the right. Example: "Sample extract of FY26 vs FY25, like-for-like days. Try: open the Tabby stock alert, switch week, or ask the data a question."
- **Main column** about 720–760px wide for the briefing stream, plus an optional **right rail** of 320px at ≥1280px (the "What I'm watching" panel). Generous vertical rhythm: 28px between cards.
- **Floating action button**, bottom-right: an `--accent` pill "● Ask {name}" with a white count badge. It opens the Ask view.

## 5. Components
- **Pill / tag:** fully rounded, padding 2px 9px, 12px Geist 500, soft background + ink colour:
  - "Needs you today": red-soft / red-ink (critical anomaly, e.g. a stock-out)
  - "Needs you": red-soft / red-ink
  - "Pattern": amber-soft / amber-ink (trend or acceleration)
  - "Win": green-soft / green-ink
  - "Watch" or "Definition": accent-soft / accent-ink
- **Briefing card** (no box; a hairline `--border` bottom divider, padding 8px top / 32px bottom), in this order:
  1. Pill + meta line ("Inventory · Tabby franchise").
  2. Serif headline: one full sentence containing the key numbers.
  3. Muted body paragraph (2–4 sentences): the comparison, why it matters, what to look at first.
  4. Micro-chart (see section 6).
  5. Action row: **primary** button (`--text` background, `--bg` text, 600, 32px high, 8px radius); **accent** button "● Ask why" (`--accent` background, white); **secondary** buttons (`--surface` background, 1px `--border`, `--muted` text, 8px radius). Right-aligned **mono chips** for evidence IDs (1px `--border`, 4px radius, 11.5px JetBrains Mono, `--muted`), e.g. `F11` `F12` `AN062`.
  6. A small trust badge where text is AI-worded: green check + "Worded by Claude; every number checked" (green-ink, 12px). Show "Blocked: unverified number" in red-ink if the validator fails.
- **"What I'm watching · N rules"** panel: a `--surface` card, 1px border, 12px radius, 16px padding. Title 13px/600 with a faint rule count. Each row is a rule's plain-language name and its count of hits for the selected week, right-aligned. Footer link: "+ Add a watch rule in plain language" (`--accent`, can be inert).
- **KPI tiles** (classic view only): `--surface`, 1px border, 10–12px radius, a 12px muted label and a 28px Geist 600 number. YoY goes underneath as a mono delta in green-ink or red-ink.
- **Segmented toggle** ("Agent briefing | Classic dashboard"): an outline container with the active segment `--text`-filled (white label) and the inactive one plain. The briefing segment has a leading accent dot.
- **Filters** (classic view): small outline selects, 8px radius, 13px.
- **Diagrams** ("How it was built"): rounded boxes with a 1px border; the active path in `--accent` with a solid 1.5px stroke; mono uppercase lane labels ("SIGNAL · EVERY REFRESH"); the Claude node highlighted `--accent-soft` with a ✦ icon.

## 6. Charts (match the reference's micro-charts)
- **Comparison bars** (e.g. "Tabby WOS TY vs LY"): two rows, each with a 12.5px muted label (170px), an 8px-high track in `--surface3` with 4px radius, a filled bar (`--red` for the problem value, `--surface3`/`--border2` for the baseline, `--green` for an improvement), and a right-aligned mono value (`1.9w`, `7.0w`).
- **Column sparkline** (e.g. weekly Gen Z share of new): 6–8 columns in `--surface3` with a 3px top radius, mono value labels above (11.5px muted), mono week labels below, and **only the latest or notable column highlighted** (`--amber` for a pattern, `--accent` for neutral emphasis, `--red`/`--green` for status).
- **Full charts** (classic view, deck): white or `--surface` panels with no top or right spines, faint `--border` gridlines, Geist tick labels at 11–12px in `--muted`, and mono numbers. **Colour rule: one highlighted series, everything else neutral.** TY = `--accent`, LY = `--border2` gray. Gen Z vs other generations = `--accent` vs `--surface3`. Status (stock-out, decline) = `--red`, win = `--green`, pattern/acceleration = `--amber`. **Never use rainbow categorical palettes.** The reference's "Classic dashboard" uses multi-colour bars on purpose as the anti-example, so our classic view should still use the one-highlight rule. No dual axes. Direct labels instead of legends wherever possible.

## 7. Voice (copy style for headlines and cards)
- Headlines are complete sentences with the numbers in them. Examples of the pattern: "Northwind Media cache purge task sits 4.7 days with Network Eng, 2.9 times median", "Security Review rework rose from 9% to 21% since July, with 15 bounces."
- Page headline in first person from the agent, counting what needs attention: "Three things need you this week." Lead: "I checked {n} transactions and {m} stock snapshots for FY26 W23–W{w}. {k} need a decision from you, {j} are worth knowing about."
- Body copy states the comparison, the baseline, and the first place to look. No hype words.
- Every number in AI-worded text must come from metrics.json/anomalies.json and pass the validator. The trust badge says so.

## 8. Mapping our content into this design
| Signal element | Our content (source) |
|---|---|
| Eyebrow "AGENT BRIEFING · WED OCT 7" | "AGENT BRIEFING · {weekday} {meta.as_of_date}" (or the selected week) |
| h1 "Two things need you today." | count of critical + needs-you cards for the selected week (from anomalies.json + findings) |
| Card "Needs you today" (red) | R1 / F11–F12: Tabby + Pillow Tabby weeks of supply vs LY, comparison bars, chips F11 F12 + anomaly IDs |
| Card "Needs you" (red) | F6–F7: retention leak. Returning flat, Gen Z Insider attach lowest, gaps by segment as comparison bars |
| Card "Pattern" (amber) | F5: Gen Z share of new by week, column sparkline with the latest week highlighted amber |
| Card "Win" (green) | F4 / F9: Gen Z new +122% / Tabby franchise growth, before/after bars |
| "What I'm watching · N rules" | anomalies.json `rules` (18), with hit counts for the selected week from `by_week` |
| "Classic dashboard" toggle | the G1–G4 tabs (KPI tiles, filters, full charts) under the one-highlight colour rule |
| Ask page (suggested question chips + input) | the fixed-template Q&A (stretch goal): 6 suggested questions as outline chips in a 2-column grid |
| "How I built Signal" page | "How it was built": stat trio (e.g. scripts, findings audit "30/30 checks passed", validator status), numbered sections "01 / 02 / 03", the flow diagram data → metrics.json → rules → Claude → validator → UI, and the "Use only the facts provided…" prompt card |
| Floating "Ask Signal 4" | "Ask {name}" with the count of critical alerts |

## 9. Deck adaptation (PROMPT_D)
Use the same tokens and fonts on 16:9 slides. Background `--bg` (#f7f8fa). Action titles in Instrument Serif (40–48pt) written as full sentences with numbers. A mono uppercase eyebrow with an accent dot top-left ("G2 · GEN Z ACQUISITION"). Body in Geist 14–16pt `--muted`. Pills for finding type. Mono evidence chips (F#, script paths) in the footer. Charts restyled to the one-highlight rule. The exec-summary slide should look like the briefing (pill + serif sentence + one-line body, ×3). The "how it was built" slide should mirror the reference's /build page (stat trio + flow diagram).

## 10. Implementation notes
- Load fonts via Google Fonts CSS (`Geist`, `Instrument Serif` incl. italic, `JetBrains Mono`) in the app. For matplotlib/PowerPoint, download the OFL TTFs into `assets/fonts/` (log the source URLs in PROMPTS.md), register them (`matplotlib.font_manager.fontManager.addfont`), and embed or ship them with the deck. If a font can't be embedded in PPTX, fall back to Georgia (serif) / Inter or Helvetica (sans) / Menlo (mono) and note it.
- Before finishing, take screenshots of the built app and deck in **light and dark** and compare them with the reference: spacing, type scale, colours, and pill/button shapes. Fix differences. Log the comparison in HISTORY.md.
