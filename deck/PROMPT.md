# PROMPT D — Build the 5–8 slide findings deck

You are a senior analytics consultant working **alone** in this repository. Nobody will answer questions. The analysis lives in `analysis/`, the dashboard (if built) in `dashboard/`; you build inside `deck/`. When something is ambiguous, pick the most defensible option, record it in `deck/DECISIONS.md` (continue numbering after the last D# in `analysis/DECISIONS.md` and `dashboard/DECISIONS.md`), and keep going. A previous session finished the analysis (and possibly the dashboard). Your job is **deliverable D2: the deck**. Do not introduce new analysis unless you log it in `HISTORY.md` and produce it with a saved, numbered script.

## 0. Read first (in this order)
1. `analysis/NOTES.md`: data understanding, assumptions A1–A8, gotchas.
2. `analysis/DECISIONS.md`: D1–D13, the key definition choices (especially D3, D5, D6, D7, D8, D9, D10, D11, D13).
3. `analysis/FINDINGS.md`: findings F1–F15 with evidence paths, plus **Draft recommendations R1–R3**.
4. `analysis/data/processed/metrics_schema.md`: fields of `metrics.json` / `anomalies.json`.
5. `analysis/PROMPTS.md` (and `dashboard/PROMPTS.md` if present): AI tools, prompts and verification for the "How it was built" slide.
6. `analysis/outputs/tables/09_sensitivity.md` (robustness), `analysis/outputs/tables/10_sizing.md` (impact), `analysis/outputs/tables/14_findings_audit.md` (number audit), `analysis/outputs/tables/12_anomalies.md` (rules output).
7. If `dashboard/app.py` exists, read `dashboard/README.md`, `dashboard/summaries.json` and `dashboard/briefing.json` for the dashboard/AI-feature slide, and take screenshots of the app for the "how it was built" slide.
8. **`design/DESIGN_SIGNAL.md`: the REQUIRED visual design** (section 9 covers the deck). Open https://signal-agent-nu.vercel.app/ (briefing page and /build) for side-by-side comparison. The deck should look like the same product as the dashboard.

## 1. The exercise (source of truth, restated)
- Dataset `analysis/data/raw/TYLY_data_sample.xlsx` (read-only): transaction-line sales FY26 (TY) vs FY25 (LY), fiscal weeks W23–W30, plus weekly stock by product family.
- Goals: **G1** monitor YoY and trailing-week performance; **G2 (TOP PRIORITY)** acquire new Gen Z customers and retain customers; **G3** surface winning products to share; **G4** get stock in the right place.
- **D2 deliverable:** a **5–8 slide deck** covering key findings; **2–3 ranked recommendations, each with reason, expected impact, and data not in the file**; and **how it was built** (AI tools, prompts, verification, accuracy design). **Anything surprising in the data must be called out.**

## 2. The story (embedded so you have it before reading files; every number is in analysis/FINDINGS.md / analysis/outputs)
Basis: like-for-like period-to-date = FY26 W23–W30 (W30 = Sun–Wed, as-of 2026-08-19) vs FY25 on the same weeks and days. Sample-scale counts, so shares and ratios are the robust read.
- **Headline:** demand **+12.8%** YoY, driven by **more customers (+8.2% transactions)**, not bigger baskets (AOV +4.3% n.s., UPT flat). All 8 weeks are up (F1).
- **The Gen Z engine:** Gen Z new customers **240 vs 108 (+122%)**, ~97% of all new-customer growth. Gen Z share of new **40.7% vs 23.8%**, accelerating to 47% in W29 and 56% in W30 WTD, store-led and full-price (F4, F5). They enter through the **Tabby franchise** and aren't discount-driven (F8).
- **The leak:** returning customers are flat (**1,239 vs 1,236**) and returning Gen Z is down 3%. Only **17.1%** of new Gen Z join Insider (lowest generation), with the gaps in Outlet, Greater China and eComm (F6, F7).
- **The winner:** Tabby + Pillow Tabby = **85% of growth** (Tabby +42.9%, Pillow Tabby +83.4%). Halo apparel and Rogue are the drag (Knit Dress -50.8%, Rogue -22.6%) (F9, F10).
- **The stock problem:** Tabby has **1.9 weeks of supply** (LY 7.0) and Pillow Tabby 1.6, while apparel sits at 16–21 weeks. Replenishment covered only **0.28** of Tabby units sold vs 0.95 LY. The stock-vs-demand correlation fell 0.96 → 0.33 (F11, F12).
- **Surprises to call out:** F2 (naive YoY +7.5% vs like-for-like +12.8% because TY W30 is partial), F5 (Gen Z acceleration), F12 (replenishment broke), F13 (W30 stock snapshot post-dates the last sale), F14 (one line per transaction and a random-looking CUST_ID, so no basket or cohort analysis is possible).
- **Ranked recommendations:**
  1. **R1 Protect and chase the Tabby franchise now.** Reason: F9 + F8 + F11 + F12. Impact: 4-week demand at risk **$23.1K = 7.7%** of next-4-week demand; Tabby stocks out in ~2.6 weeks. Need ≈229 Tabby + 53 Pillow Tabby units to restore LY cover. Missing data: open POs/lead times, store-level stock, supplier constraints, margin.
  2. **R2 Rebalance open-to-buy from Halo apparel to Hero; clear the apparel overhang.** Reason: F10 + F11 + F12. Impact: **198 units / $50.5K retail** above median cover (9.0% of TY PTD demand). Missing data: cost/margin, markdown elasticity, Halo brand-role KPIs, size/colour stock.
  3. **R3 Turn the Gen Z wave into repeat customers** (Insider at first purchase + Tabby-led second-purchase journey). Reason: F4 + F6 + F7. Impact (scenario): +15 Gen Z Insiders to match Millennial attach (+37%); +10% returning Gen Z ≈ **+0.85%** of demand. Missing data: persistent customer key/history, Insider vs non-Insider repeat rate, CLV, campaign calendar.

## 3. Slides (5–8; suggested structure)
1. **Executive summary:** headline (+12.8%), the three-part story (Gen Z engine → leaky bucket → winner running out of stock), and R1–R3 in one line each.
2. **G1 performance and drivers:** `analysis/outputs/figures/g1_weekly_sales_ty_vs_ly.png` + `g1_yoy_decomposition.png` (optionally `g1_growth_contribution_by_segment.png`). L1W / L4W / WTD callouts (F1, F3).
3. **G2 Gen Z acquisition and retention (main story):** `g2_genz_share_of_new_by_week.png` and `g2_new_vs_returning_yoy_by_generation.png` (or `g2_new_customers_by_generation_ty_vs_ly.png`), first-purchase insight (`g2_genz_first_purchase_family_mix.png`), Insider gap (F4–F8). State the retention-proxy caveat (D8).
4. **G3 winners and G4 inventory alignment:** `g3_family_growth_contribution.png` or `g3_family_growth_vs_genz_index.png`, plus `g4_tabby_franchise_stock_vs_demand.png` and/or `g4_weeks_of_supply_by_family.png` (F9–F12, F15 watch list).
5. **What surprised us + caveats + key definition choices:** F2, F5, F12, F13, F14. Definitions: like-for-like days (D3), CUST_ID not a key (D5), New = brand status (D6), Gen Z = label (D7), retention proxies (D8), sample scale (D11). Robustness highlights from `09_sensitivity.md`.
6. **Recommendations (ranked):** R1–R3, each with reason (finding IDs), quantified impact with assumptions, and the data not in the file.
7. **How it was built:** tools (Claude Code + Python/pandas/matplotlib, Streamlit if built), the loop and on-disk memory files, key prompts (from `analysis/PROMPTS.md`: P4 CUST_ID collision test, P8 implied-receipts scale check, P9 adversarial challenge, P12 anomaly rules, P14 findings audit), verification (reconciliation to raw, second-method checks, `14_findings_audit.md` 30/30, `run_all.sh --clean` reproducibility), and the **AI accuracy architecture: data → metrics.json → rules (anomalies.json) → LLM (facts only) → validator → UI**. Mention that the rules flagged Tabby as critical from **W28**, two weeks before the latest week (`12_anomalies.md`).
8. *(Optional)* **Appendix:** definitions (`analysis/outputs/tables/data_dictionary.md`, `analysis/data/processed/metrics_schema.md`) and full robustness table.

## 4. Build requirements
- Pull **every number** from the outputs (`analysis/FINDINGS.md`, `analysis/data/processed/metrics.json`, `analysis/outputs/tables/*`). Write `deck/scripts/18_deck_numbers.py` that loads the numbers used on each slide from `metrics.json`/tables into `deck/deck_numbers.json`, and build slide text from that file. No hand-typed figures.
- **Cross-check:** after building, extract all numbers from the slide text and check each against `deck/deck_numbers.json` (reuse the validator from the dashboard session if present, `dashboard/scripts/17_validate_summaries.py`). Record the result in `HISTORY.md`.
- **Restyle the figures to the Signal design first.** In `analysis/scripts/_common.py`, update the palette `C` and `style()` to the DESIGN_SIGNAL.md light tokens:
  - surface `#ffffff` on bg `#f7f8fa`; text `#0f1318` / `#58616d`; grid `#e2e6eb`
  - TY / highlight `#2d54d3`; LY / neutral `#cdd3db` / `#e5e8ed`; Gen Z = accent vs neutral others (replaces orange)
  - red `#db423c`, amber `#e4a339`, green `#329d5a`, used for status only
  - fonts: Geist (text), JetBrains Mono (numbers), Instrument Serif (chart titles, or drop in-chart titles and let the slide title carry the message)

  Download the OFL font TTFs into `design/fonts/` (shared with the dashboard; log the source URLs in `deck/PROMPTS.md`) and register them with matplotlib. Then re-run `./run_all.sh --clean`, confirm `analysis/outputs/tables/14_findings_audit.md` still shows 30/30 PASS and the tables are unchanged (only PNGs should differ; diff md5s of `analysis/outputs/tables` and `data/processed`), and inspect every PNG. Log this in `analysis/HISTORY.md` (it changes analysis outputs) and `deck/HISTORY.md`. Don't otherwise redraw charts unless one is unreadable at slide size, and if you do, use a saved script and log it.
- **Design (Signal style, DESIGN_SIGNAL.md section 9):**
  - 16:9, background `#f7f8fa`, generous margins.
  - Mono uppercase eyebrow with an accent dot (e.g. "● G2 · GEN Z ACQUISITION").
  - **Instrument Serif action title** written as a full sentence with the numbers (40–48pt).
  - Geist body at 14–16pt in muted ink, ≤ 5 bullets, one message per slide.
  - Pills for finding type (Needs you / Pattern / Win / Watch, soft background + ink colours).
  - Mono evidence chips and source footnote in the footer ("F11 · F12 · analysis/scripts/08_g4_inventory.py · FY26 W23–W30 vs FY25 like-for-like, sample extract").
  - The exec summary mirrors the briefing page: pill + serif sentence + one-line body, three times.
  - The "how it was built" slide mirrors the reference /build page: a serif stat trio and the flow diagram data → metrics.json → rules → Claude → validator → UI.
  - Embed the fonts, or fall back to Georgia / Helvetica / Menlo and note it in `deck/DECISIONS.md`.
- Export to `deck/`: `deck/TYLY_findings.pptx` (python-pptx or your slides tooling) and a PDF if tooling allows. Render each slide to an image, inspect it for overflow and overlaps, compare it side by side with the reference site (type scale, colours, pill shapes, spacing), and fix the differences.

## 5. Working rules (same as before)
- Never modify `analysis/data/raw/`. Every number from a saved script. No new analysis without a numbered script + an `analysis/HISTORY.md` entry.
- Loop: ORIENT → PLAN → ACT → VERIFY → RECORD (append `deck/HISTORY.md` "## Iteration N", same format as `analysis/HISTORY.md`) → REFLECT. Keep `deck/NOTES.md` current.
- Log significant AI-assisted steps and their verification in `deck/PROMPTS.md` (continue the P# numbering after `dashboard/PROMPTS.md`, or after `analysis/PROMPTS.md` if there is no dashboard log).
- Put the build scripts in `deck/scripts/` (numbered 18+); the root `./run_all.sh` runs them after the dashboard stage (or add an executable `deck/run_all.sh`). Add `python-pptx` to the root venv install line and write `deck/README.md`. Finish when the deck has 5–8 slides, every number passes the cross-check, and `./run_all.sh --clean` rebuilds it.
