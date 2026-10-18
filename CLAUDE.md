# CLAUDE.md: project memory

Read this first in every session.
It records what the project is, how it fits together, the rules we work by, and the mistakes we have already made.
Keep it current: when something here turns out to be wrong, fix it in place.
The user's global rules in `~/.claude/CLAUDE.md` (a symlink to `~/AGENTS.md`) also apply and take precedence.

## Contents
1. [About](#about)
2. [Repo structure](#repo-structure)
3. [Terminology](#terminology)
4. [How components work](#how-components-work)
5. [Conventions](#conventions)
6. [Learnings](#learnings) (append-only log of mistakes and the rules that prevent them)

---

## About
- **What:** a Consumer Intelligence & Analytics take-home on `TYLY_data_sample.xlsx`.
  It holds transaction-line sales for FY26 (TY) vs FY25 (LY), fiscal weeks W23-W30, plus weekly stock by product family.
  The brief is `take_home_brief.pdf`.
- **Business goals:** G1 YoY and trailing-week performance; G2 (top priority) acquire new Gen Z customers and retain customers; G3 surface winning products; G4 get stock in the right place.
- **Deliverables:**
  - The analysis is done: findings F1-F15 and recommendations R1-R3 are in `FINDINGS.md`.
  - D1, the dashboard with a weekly AI feature, is done and judged on design and answer accuracy.
    It is a static React app in `web/`, live at https://data-analysis-tapestry.vercel.app/ (Vercel project, Root Directory `web`).
  - D2, the 5-8 slide deck, is still open.
    Its brief is `handoff/PROMPT_D_deck.md`, whose paths predate the web app (it mentions `app/`).
- **Headline story:**
  - Demand is +12.8% like-for-like, driven by more customers rather than bigger baskets.
  - Gen Z new customers are up +122% and their share of new customers is accelerating.
  - Tabby + Pillow Tabby (the Hero "Tabby franchise") are 85% of growth but nearly out of stock, because replenishment stopped following demand.
  - Halo apparel is overstocked, and retention can only be measured with proxies.
- **Owner:** Jolin, GitHub `Jolinnnnnnnn/data-analysis-tapestry` (public repo).
  Only `main` exists.
  Older work is kept at the tags `archive/dashboard-v1`, `archive/archive-dashboard` and `archive/restructure-dashboard-deck`.

## Repo structure
```
take_home_brief.pdf        the exercise brief
TYLY_data_sample.xlsx      copy of the raw file (the canonical copy is data/raw/, chmod 444)
run_all.sh                 one command rebuilds everything (see below)
CLAUDE.md                  this file
NOTES.md                   working memory: assumptions A1-A8, gotchas, current state
DECISIONS.md               interpretation choices D1-D13 (analysis) and D14-D24 (dashboard)
FINDINGS.md                F1-F15 with evidence paths, recommendations R1-R3
HISTORY.md                 iteration log ("## Iteration N"); latest is 16
PROMPTS.md                 AI-assisted steps and how each was verified (P1-P19)
QUESTIONS.md               hypothesis backlog (all resolved or dropped)
scripts/
  _common.py               shared loaders and KPI definitions (the one place for metric formulas)
  01-10                    analysis: profile, clean, identity checks, G1-G4, challenge, sizing
  11_metrics.py            -> data/processed/metrics.json (single source of truth for the UI)
  12_anomalies.py          -> data/processed/anomalies.json (18 deterministic rules, 71 alerts)
  13_docs.py               -> metrics_schema.md, data_dictionary.md
  14_verify_findings.py    -> outputs/tables/14_findings_audit.md (30/30 headline numbers re-derived)
  15_build_facts.py        -> data/dashboard/facts/W<wk>.json, W<wk>_cards.json, timeline.json
  16_generate_summaries.py -> data/dashboard/summaries.json, briefing.json (AI texts; live plug-in point)
  17_validate_summaries.py -> number validator, build_stats.json; exits 1 on any unverified number
  18_export_web.py         -> web/src/data/app.json (the only file the web app reads)
ai/session_texts.json      AI texts written by Claude (headline, summary, 5 cards per week), md5-stamped to their facts
data/raw/                  READ-ONLY input
data/processed/            metrics.json, anomalies.json, metrics_schema.md, tidy CSVs (generated)
data/dashboard/            facts, summaries, briefing, timeline, build_stats (generated)
outputs/tables, figures/   analysis tables (01-14) and PNG charts (generated)
handoff/                   prompts for later sessions (PROMPT_C is superseded; PROMPT_D is still open)
web/                       Vite + React + TypeScript dashboard (see web/README.md)
  src/lib/core.ts          design tokens, display formatting, data access, URL hash state, motion preference
  src/lib/validator.js     JS port of the Python validator (must stay line-for-line equivalent)
  src/lib/ask/             Ask: catalog.ts (12 templates, routing schema + prompt from app.json), engine.ts (parser, checks, answers)
  src/components/          Header, Briefing, Explore (G1-G4), Ask, HowBuilt, LikeForLike
  api/ask.ts               Vercel function: Claude routes a question to one template (needs ANTHROPIC_API_KEY)
  scripts/parity.mjs       JS validator == Python validator on every text (gates every build)
  scripts/ask-test.mjs     Ask routing, checks and every template x week x window (gates every build)
  scripts/ask-live.mjs     live router run against Claude (spends credits; not in verify)
  vercel.json              build = `npm run verify && npm run build`, output `dist`, function config for api/ask.ts
.claude/launch.json        dev server config for the Claude desktop preview (`web`, port 5199)
```

## Terminology
| Term | Meaning |
|---|---|
| TY / LY | This year FY26 / last year FY25. |
| W23-W30 | Fiscal weeks, Sun-Sat and 364-day aligned, so the same week number has the same weekday mix. |
| Partial week | TY W30 has only Sun-Wed because the data ends Wed 2026-08-19; W29 is the last full week and the default view. |
| Like-for-like (LFL) | Same weeks and same weekdays in both years (LY W30 cut to Sun-Wed); the headline is +12.8%. |
| Naive basis | All rows as-is, which gives LY 3 extra days and shows +7.5% (finding F2). |
| L1W / L4W / PTD / WTD | Selected week / that week and the 3 before (truncated before W26) / W23 through the selected week / W30 Sun-Wed. |
| Sample-scale | Counts come from a sample extract, so shares and ratios are the robust read. |
| WOS | Weeks of supply: end-of-week on hand divided by the trailing (up to) 4-full-week average units; rules use it only from W26. |
| Receipts-to-sales | Implied receipts (change in on hand + units) divided by units sold over W24-W29; Tabby is 0.28 TY vs 0.95 LY (F12). |
| Contribution pts | A family's change as points of total YoY growth (already in points in `products_by_week`; a fraction to multiply by 100 in `products_ptd`). |
| Share of growth | A family's share of total demand growth; it sums to 1 across families, negatives included. |
| Gen Z index | A family's Gen Z share vs the average, where 100 is the average. |
| New / Retained / Reactivated | `COHORT_STATUS` from the brand's full history; "returning" is Retained + Reactivated and is a mix proxy, because CUST_ID does not link customers (F14). |
| Insider attach | Share of new customers who joined the loyalty programme. |
| Hero / Halo / Core / Evergreen | Product types; Hero is Tabby + Pillow Tabby only, and Halo includes Rogue and the apparel (Knit Dress, Trench, Tailored Jacket). |
| Family / style | `STYLE_GROUP` (21 families) / `STYLE_DESC`. |
| F#, R#, D#, P# | Finding, recommendation, decision and prompt-log IDs. |
| AN### | Alert IDs in `anomalies.json`; W29's are AN048-AN058. |
| Facts | The JSON payload an AI text may cite, per week or per card. |
| Cards / severity | The 5 "flagged this week" items (stock, retention, pattern, win, overstock), labelled CRITICAL, WARNING, PATTERN, WIN or WATCH by rules. |
| Route | What Ask's picker returns: template id, parameters, premise, unmatched entities and a one-line reading. |
| Pregenerated / template / live | Who wrote a text: Claude at build time (`ai/session_texts.json`), the deterministic fallback, or the live API (`claude-opus-5-5`). |
| M1, M3, M5, M6, M8 | Motion pieces: season playhead, growth drill-down zoom, LY-to-TY morphs, naive vs LFL switch, validator replay. |

## How components work
The pipeline is data -> metrics -> rules -> facts -> AI words -> validator -> UI.
`./run_all.sh --clean` runs all of it in about 30 s and must reproduce byte-identical outputs.

1. **Analysis (01-14).**
   The scripts read `data/raw` and write tables, figures and `metrics.json`.
   Metric formulas live in `_common.py`.
   `11_metrics.py` self-asserts its reconciliations: headline = raw sums, the W30 day split = weekly totals, share correlations 0.96 -> 0.33, and family growth shares summing to 1.
   `14` re-derives every headline number in `FINDINGS.md`.
2. **Rules (12).**
   18 deterministic thresholds produce `anomalies.json`.
   `WOS_LOW` escalates to critical for G3 winners and Gen Z gateways.
   Family and stock rules fire only on full 4-week windows (W26+), and `RECEIPTS_BELOW_SALES` fires only at the latest week (W30).
   The AI never decides what is anomalous.
3. **Facts (15).**
   This step is selection only, with no arithmetic.
   Weekly facts are `weekly_facts[wk]` plus that week's alerts (with `rule_threshold`) plus `_sources`, the upstream metrics path for every number.
   Card facts hold the exact values each card may cite, with their sources and the chart series.
   It also writes the playhead timeline: one event per week chosen by rule priority, with the rule's own message as its text.
4. **Writer (16).**
   It uses live Claude if `ANTHROPIC_API_KEY` is set (marked `=== LIVE MODEL PLUG-IN POINT ===`), else a pregenerated text whose facts md5 matches, else the template.
   A stale md5 means the facts changed, so the template is used and a warning is printed.
   `--stamp` records the facts md5 for every pregenerated text.
5. **Validator (17, plus `web/src/lib/validator.js`).**
   Every printed number ($, %, K, pts, decimals, integers, signed) must match some fact within half a unit of its printed precision.
   Week labels, FY labels, L1W/L4W, ISO dates and words like "4-week" are masked.
   An explicit sign must match; unsigned numbers are compared to the absolute value; week-index fields are never citable.
   The build self-tests by changing 12.7% to 13.7% and expecting FLAGGED.
   It is an existence check, not a semantic one, so hand-review a number trace whenever wording changes.
6. **Export (18).**
   It writes `web/src/data/app.json` (about 540 KB), which is committed because Vercel does not run Python.
7. **Web app.**
   All state lives in the URL hash (`#/explore/g4?wk=30&win=PTD&ly=0`); `&demo=blocked` shows the held-back state.
   The browser re-validates every AI text before showing it, and a failing text is replaced by its facts table.
   Charts are hand-built SVG/CSS with CSS transitions and requestAnimationFrame.
   Motion follows the OS `prefers-reduced-motion` setting unless the footer "Animations" toggle (localStorage `tyly-motion`) is on.
   Ask: Claude (`api/ask.ts`, structured output) or, when it is unavailable, the keyword parser returns a route (one of 12 templates + parameters + premise + unmatched entities).
   The browser checks the route (week range, entities a template can't filter by, premises against stored YoY/WoW values) and code writes the answer; the model never sees or writes a data value.
8. **Build and deploy.**
   `run_all.sh` runs Python 01-18, then `npm --prefix web run verify` (parity) and `vite build`.
   On Vercel the Root Directory is `web`, and the build runs verify first, so an unverified number fails the deploy.
   Pushing to `main` deploys production.
   For local dev, run `npm --prefix web run dev` (port 5199).

## Conventions
**Data and accuracy**
- Never modify `data/raw/`.
- Every number comes from a saved, numbered script.
  If a view needs a new number, add it to `11_metrics.py` (documented via `13_docs.py`), not to the UI.
- The front end does no arithmetic: it only selects, filters, sorts, compares to rule thresholds and formats.
  Drawing geometry is fine.
  Animated numbers swap between stored values and never count through invented intermediate values.
- Never type figures into UI copy or prompts; read them from data (`meta.partial_week_days`, `rules[].rule`, and so on).
- Compute ratios (AOV, UPT, AUR, shares) from totals, never by averaging across weeks.
- Never sum `ON_HAND_UNITS` across weeks.
- Fractions in `metrics.json` are stored at 6 decimal places.
- Display formats are 12.7% (YoY of 100% or more as a whole percent, e.g. +156%), $71.3K, $564,028, 2.1 weeks and +5.0 pts.
- Like-for-like is the default basis.
  Label partial weeks ("so far") and truncated windows, and call counts "sample-scale".

**AI texts**
- The AI may cite only numbers that are in its facts.
- After changing text in `ai/session_texts.json`, run 17 (it must PASS), then `16 --stamp`, then 16, 17 and 18.
- Changing `15_build_facts.py` changes the facts md5s and makes every text stale.
  Re-validate the texts against the new facts before re-stamping, and never stamp blindly.
- When texts change, hand-check their meaning with a number trace (printed number -> fact -> upstream path).

**Design (single theme, from the Claude Design "TYLY Dashboard" file)**
- Palette: Sapphire `#266DD3`, Charcoal `#344055`, chrome `#232B3C`, Thistle `#DFC2F2`, page `#F6F3FA`.
- Goal hues: G1 sapphire, G2 `#8A5CC9`, G3 charcoal, G4 `#B0739F`.
  The tokens live in `core.ts` (`C`, `GOALS`).
- Fonts: Archivo (condensed headings via `font-stretch:72%`) and Space Mono for data.
- Charts have one highlighted series (TY), with LY as a muted ghost.
  Red, amber and green are for status only.
  Severity is always shown as icon + label, never colour alone.
  No dual axes, and direct labels instead of legends.
- Motion appears only where it encodes information.
  Respect reduce-motion, and keep the opt-in toggle visible.

**Writing (from the global rules)**
- Never use the em dash or en dash characters; use a plain "-".
  The data itself contains en dashes (e.g. the `partial_week_days` label); leave generated data alone, but never type them in prose or code comments.
- In long Markdown files, put each full sentence on its own line.

**Process and docs**
- Work in a loop: ORIENT (NOTES, HISTORY tail) -> PLAN -> ACT -> VERIFY (with a second method) -> RECORD -> REFLECT.
- For bugs, reproduce end to end first, as close to the user's experience as possible.
- Next numbers: D27 in DECISIONS, Iteration 19 in HISTORY, P22 in PROMPTS (D25 / Iteration 17 / P20 are reserved by `handoff/PROMPT_E_validator.md`).
  NOTES holds the current state only.
- The Python 3.9 venv is `.venv`: install with `.venv/bin/python -m pip` and run scripts with `.venv/bin/python -W ignore`.

**Git and deploy**
- Branch before non-trivial work.
- Commit and push only when asked; the user merges PRs on GitHub.
- Never add a `Co-Authored-By` (or any agent-name) trailer to commit messages.
- Before deleting a branch with unmerged commits, tag it `archive/<name>`.
- Never log in to Vercel or GitHub for the user; point them to the dashboard step instead.
- API keys live only in the Vercel project's environment variables or a git-ignored `web/.env.local`; never in chat, code or commits.

## Learnings
When a mistake is made, whether by Claude or caught by the user, add an entry here before moving on.
Each entry gives the date, what happened, and the rule that prevents it, in one or two sentences.
Update an existing entry rather than duplicating it, and promote a rule into Conventions once it is proven.

*Process*
- 2026-10-18: I followed a session-provided commit-attribution default and ignored the user's global rules in `~/.claude/CLAUDE.md`, so commits carried a Claude co-author trailer and docs used em/en dashes.
  Read `~/.claude/CLAUDE.md` at the start of every session; user rules beat tool defaults.

*Data and accuracy*
- 2026-10-13: Storing `metrics.json` at 4 decimal places put 1-dp percentages on rounding ties, so the UI showed +7.4% where FINDINGS has +7.5%.
  Store 6 decimal places, and compare UI tiles against `05_g1_kpi_windows.csv`.
- 2026-10-13: The tighter facts exposed 7 numbers in the AI texts that were off by one display unit, because they had been rounded from 4-dp values.
  Always validate against the exact stored facts, never against remembered values.
- 2026-10-13: The template fallback quoted rule thresholds ("< 20%") that were not in the facts, and the validator flagged it.
  Anything a text may cite must be in its facts (hence `rule_threshold`).
- 2026-10-13: A count ("28") matched a week index in the facts.
  Week-index keys are excluded from the validator's leaves.
- 2026-10-13: I typed example numbers into UI copy ("12.7% to 13.7%", "4 days ... 7").
  Read figures from data or reword the copy.
- 2026-10-18: Ask's keyword picker dropped words it did not know, so "Show me Tabby performance" got whole-business numbers and "Why did sales drop?" was answered without saying demand rose YoY.
  Correct numbers for the wrong question are still wrong: a picker must report entities it can't honour and premises it assumes, and code must refuse or correct before answering.
- 2026-10-14: The Claude Design prototype's numbers were placeholders, and several were wrong (alert IDs AN098+, `RECEIPTS_BELOW_SALES` firing in W29, `WOS_LOW` as a warning, TY W30 at $41.6K).
  Never trust mock data; wire everything to `app.json`.

*Tooling and environment*
- 2026-10-13: The venv's `pip` shebang pointed at an old checkout path.
  Use `.venv/bin/python -m pip`.
- 2026-10-13: In Python 3.9, nested same-quote f-strings and backslashes inside f-string expressions are syntax errors.
  Pull those expressions out into variables.
- 2026-10-13: A brief referenced files and a layout that did not exist (`design/DESIGN_SIGNAL.md`, `analysis/`).
  I restructured the repo unasked, and that whole commit was later reverted.
  Check the repo first, and keep the existing layout unless asked to change it.
- 2026-10-13: The shell is zsh, which has no `PIPESTATUS` and does not word-split a `$VAR` holding several paths; there is also no `timeout` command.
  Capture exit codes without pipes, and use a function or an array for path lists.
- 2026-10-13: (Streamlit, archived) `st.html` drops `<style>`-only content, so CSS must go through `st.markdown(unsafe_allow_html=True)`.
  `st.cache_data` ignores `_`-prefixed arguments, which silently left file mtime out of the cache key.
- 2026-10-18: `git push origin --delete a b c` is atomic, so one already-deleted ref failed the whole push.
  Run `git fetch --prune` first, then delete only refs that exist.
- 2026-10-18: The scratchpad is cleared between sessions, which lost the headless-Chrome CDP driver.
  Save reusable test tools in the repo if they will be needed again.

*Web and animation*
- 2026-10-14: The user's Mac has Reduce motion on, and the Claude browser pane and headless Chrome inherit it, so animations looked missing or without object persistence.
  Test motion with CDP `Emulation.setEmulatedMedia` (`prefers-reduced-motion: no-preference`), and keep the footer opt-in toggle discoverable.
- 2026-10-14: A hidden Claude browser pane runs 0 requestAnimationFrame frames per second.
  Verify animations in headless Chrome over CDP, not in the pane.
- 2026-10-14: The first requestAnimationFrame timestamp can precede the start time, which gave a negative playhead, index -1 and a crash.
  Clamp animation progress to 0 or more.
- 2026-10-14: Play resumed from the selected week and finished at once.
  Play replays from the start unless it is resuming a pause, and refs must stay in sync with external state changes.
- 2026-10-14: Full-page CDP screenshots restart CSS animations and show mid-animation artifacts.
  Confirm visibility from the DOM before fixing anything.

*Deploy*
- 2026-10-15: The Vercel Root Directory was left at the repo root, so the repo was served as raw static files: 404 at `/`, and `data/raw` was downloadable.
  The Root Directory must be `web`; check that the live asset hashes match the local build.
- 2026-10-15: Hashed deployment URLs sit behind Vercel Authentication, and only the production domain is public.
  Never share a deployment URL as "the link".
