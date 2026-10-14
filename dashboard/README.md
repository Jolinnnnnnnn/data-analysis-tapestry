# TYLY weekly dashboard (deliverable D1)

A Streamlit app in the **Signal** design (`../design/DESIGN_SIGNAL.md`), with an accuracy-guarded weekly AI feature: an agent briefing that Claude words and that a number validator checks against `metrics.json` before anything reaches the screen.

## Setup and run
From the repo root:
```bash
./run_all.sh --clean
```
```bash
.venv/bin/streamlit run dashboard/app.py
```
`run_all.sh` creates `.venv` if needed (pandas, openpyxl, matplotlib, numpy, tabulate, streamlit, plotly), rebuilds the analysis (`analysis/run_all.sh`), then runs `dashboard/run_all.sh`: facts → AI texts → validator → headless smoke test. **The build fails if any AI-written number can't be found in its facts.**

Optional live model: `pip install anthropic` and set `ANTHROPIC_API_KEY`. Then `scripts/16_generate_summaries.py` has Claude (`claude-opus-5-5`) write every summary and card from the facts JSON, and the Ask page lets Claude pick the query template. Without a key, the texts written at build time by Claude Code are used (`pregenerated/session_texts.json`), with a deterministic template as the fallback. The validator applies to all three.

## What's on screen
| Page | What it does |
|---|---|
| **Briefing** (default) | "{n} things need you this week." A Claude-worded weekly paragraph (every number hoverable to its metrics.json source, plus a "Facts used" expander), then five rule-ranked cards: Tabby stock-out, retention / Insider gap, Gen Z share pattern, Gen Z + Tabby win, apparel overstock. Each card has a pill, headline, body, micro-chart, "Open in Explore", "Ask why" and evidence chips. Right rail: the 18 rules with this week's hit counts, and the alert list (critical → warning → info, icon + label). |
| **Explore** (= Classic dashboard) | G1 Performance (KPI tiles, weekly TY vs LY, growth decomposition) · G2 Gen Z (share of new, generation mix, first purchase, Insider attach, retention-proxy caveat) · G3 Products (sortable family table, growth-vs-Gen Z map, PTD scorecard, style drill-down) · G4 Inventory (WOS by family vs LY and the rule lines, Tabby franchise stock vs demand, stock-risk table). |
| **Ask** | Template Q&A over metrics.json: 8 fixed query templates; the model may only pick the template and parameters, and code renders the answer and shows the steps. |
| **How it was built** | Stats read from the audit and validator outputs, the pipeline diagram, how Claude is used (facts → prompt → text → number check), definitions, decisions in plain words, and the surprises. |

Controls (sidebar): fiscal week (default W29; W30 is labelled partial), window L1W / L4W / PTD, show/hide LY. Top bar: search (families, findings, rules) and Light/Dark. The URL keeps the state, e.g. `?page=explore&wk=30&win=PTD&tab=G4&theme=dark`. `?inject_error=1` demonstrates the validator blocking a wrong number.

## How accuracy is enforced
1. **Rules first:** what is anomalous comes from `anomalies.json` (18 deterministic rules), never from the model.
2. **Facts only:** `scripts/15_build_facts.py` copies the week's metrics and rule hits into a small JSON (no arithmetic).
3. **Writer:** Claude words the facts (`scripts/16_generate_summaries.py`).
4. **Validator:** `scripts/17_validate_summaries.py` checks every printed number against the facts (half-unit tolerance) and fails the build on a miss. The app re-runs the same check when it renders and blocks any text that fails.
5. **Audit:** `tests/trace_numbers.py` re-reads every cited number from its upstream metrics.json path (`verification/number_trace.md`).

## Files
| Path | What |
|---|---|
| `app.py` | the app (theme tokens at the top) |
| `scripts/15–17` | facts → writer → validator |
| `pregenerated/session_texts.json` | Claude-written texts, md5-stamped to their facts |
| `facts/`, `summaries.json`, `briefing.json`, `build_stats.json` | build outputs (regenerated) |
| `tests/` | smoke test, number trace, tile spot-check |
| `verification/`, `screenshots/` | evidence |
| `DECISIONS.md` (D14+), `HISTORY.md`, `PROMPTS.md` (P17+), `NOTES.md` | session records |
