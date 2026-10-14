# PROMPT C — Build the TYLY weekly dashboard (Streamlit + accuracy-guarded AI summary)

You are a senior analytics engineer working **alone** in this directory. Nobody will answer questions. When something is ambiguous, pick the most defensible option, record it in `DECISIONS.md` (new entry D14+), and keep going. A previous session finished the data analysis. Your job is to build **deliverable D1: the dashboard**. Do **not** redo the analysis.

## 0. Read first (in this order) before writing any code
1. `NOTES.md`: data understanding, assumptions A1–A8, gotchas.
2. `DECISIONS.md`: D1–D13 (especially D3 like-for-like basis, D5 CUST_ID not a key, D8 retention proxies, D9 WOS, D10 trailing windows, D13 anomaly rules).
3. `FINDINGS.md`: findings F1–F15 and draft recommendations R1–R3.
4. `data/processed/metrics_schema.md`: every section and field of `metrics.json` and `anomalies.json`.
5. **`handoff/DESIGN_SIGNAL.md`: the REQUIRED visual design** (tokens, fonts, layout, components, chart rules, voice, content mapping). Also open the reference https://signal-agent-nu.vercel.app/ in a browser (briefing, "Classic dashboard" toggle, /ask, /build) and keep it open for side-by-side comparison.
6. Skim `HISTORY.md` (last 3 entries) and `PROMPTS.md`.

## 1. The exercise (source of truth, restated)
- Dataset `data/raw/TYLY_data_sample.xlsx` (read-only): transaction-line sales for FY26 (TY) and FY25 (LY), fiscal weeks W23–W30, plus weekly stock by product family (STYLE_GROUP).
- Business goals: **G1** monitor YoY and trailing-week performance; **G2 (TOP PRIORITY)** acquire new Gen Z customers and retain customers; **G3** surface winning products to share across the business; **G4** get stock in the right place.
- **D1 deliverable:** a dashboard with **at least one weekly-use AI feature**, judged on **design** and **answer accuracy**. Anything surprising in the data must be called out.

## 2. The story so far (context; verify against metrics.json and don't re-type)
Basis: PTD like-for-like = FY26 W23–W30 (W30 is only Sun–Wed, as-of 2026-08-19) vs FY25 on the same weeks and days. Counts are sample-scale, so shares and ratios are the robust read.
- **F1** Demand +12.8% YoY ($564,028 vs $499,804). Transactions +8.2% (p=0.019). AOV +4.3% (n.s.). Growth comes from more customers, not bigger baskets. L1W (W29) +12.7%, L4W +13.2%, WTD (W30 Sun–Wed) +21.7%.
- **F2 (surprising)** A naive comparison that includes LY's full W30 shows only +7.5%. The dashboard must default to like-for-like days.
- **F3** W29 -18.8% WoW is a basket (AOV) normalisation after a W28 spike, not a traffic drop.
- **F4** Gen Z new customers 240 vs 108 (+122%). Gen Z = ~97% of the growth in new customers. Gen Z share of new 40.7% vs 23.8%. Robust to every alternative definition.
- **F5 (surprising)** Gen Z acquisition is accelerating within TY: share of new 33% (W23) → 47% (W29) → 56% (W30 WTD). The rise is store-led and full-price.
- **F6** Retention proxy is weak: returning customers flat (1,239 vs 1,236) and returning Gen Z -3%.
- **F7** New Gen Z Insider (loyalty) attach is 17.1%, the lowest of any generation. The gap is in Outlet, Greater China and eComm.
- **F8** New Gen Z buy the Tabby franchise first (Hero = Tabby + Pillow Tabby), and they are not discount-driven.
- **F9** Tabby + Pillow Tabby = 85% of total demand growth (Tabby +42.9%, Pillow Tabby +83.4%).
- **F10** Halo apparel and Rogue are the drag (Knit Dress -50.8%, Rogue -22.6%).
- **F11** Winners are nearly out of stock: Tabby WOS 1.9 (LY 7.0), Pillow Tabby 1.6 (LY 5.1). Apparel holds 16–21 weeks (median 7.9).
- **F12 (surprising)** Replenishment stopped following demand: Tabby receipts covered 0.28 of units sold vs 0.95 LY.
- **F13/F14 (surprising, artifacts)** TY W30 stock snapshot is dated after the last sale. CUST_ID behaves like a random number, so there is no cohort retention.
- **Ranked recommendations:** **R1** re-open Tabby/Pillow Tabby replenishment now (4-week demand at risk $23.1K = 7.7% of next-4-week demand). **R2** move open-to-buy from Halo apparel to Hero and clear the apparel overhang (198 units / $50.5K retail). **R3** Insider enrolment at the first Gen Z purchase plus a Tabby-led second-purchase journey (+10% returning Gen Z ≈ +0.85% of demand).

## 3. What to build
A **single-file Streamlit app** at `app/dashboard.py` that reads **only** `data/processed/metrics.json` and `data/processed/anomalies.json` (plus the pregenerated `app/summaries.json` you create, which is itself derived only from those two files). **The app does no ad-hoc math**: no sums, ratios, or YoY. It selects and formats precomputed fields. Formatting (e.g. 0.128 → "+12.8%") is allowed. Computing new numbers is not. If a view needs a number that isn't in metrics.json, add it to `scripts/11_metrics.py` (and to `metrics_schema.md` via `scripts/13_docs.py`), re-run `./run_all.sh`, and log it in `HISTORY.md`.

### Layout (Signal style; see `handoff/DESIGN_SIGNAL.md` for exact tokens and components)
Streamlit stays (the brief asks for it), but the default Streamlit look must not show through. Inject one global CSS block that:
- imports Geist, Instrument Serif (incl. italic) and JetBrains Mono from Google Fonts;
- defines the light and dark token sets from DESIGN_SIGNAL.md section 2 and applies them;
- hides Streamlit's header/toolbar/footer and restyles the sidebar, buttons, radios, selects and tabs to the spec.

Render briefing cards, pills, chips, micro-charts, the watch panel and the banner as HTML strings built from metrics.json values (`st.markdown(..., unsafe_allow_html=True)`; escape all text). Keep a small `theme` section at the top of the file holding the tokens, so charts (Plotly) use the same values. Implement the Light/Dark toggle by swapping token sets.

- **Sidebar (left nav, Signal style):**
  - Logo + wordmark.
  - Nav: **Briefing** (badge = critical alerts for the selected week), **Explore** (the classic G1–G4 view; can also be reached via the segmented toggle), **Ask** (template Q&A, stretch), **How it was built**.
  - Controls block: fiscal-week selector over `meta.weeks` (default `meta.last_full_week` = 29; W30 labelled "W30 · partial (Sun–Wed)"); window segmented control L1W / L4W / PTD (reads `trailing[<wk>][<window>]`); **TY-vs-LY toggle** (show or hide LY comparison series/columns).
  - "● Agent watching" status block at the bottom, using `meta` values.
- **Top bar:** jump/search input (can filter families and findings), Light/Dark toggle. Under it, a dismissible accent-soft info banner stating the like-for-like basis and sample scale.
- **Briefing (default landing page; this is where the AI feature lives):**
  - Mono eyebrow "AGENT BRIEFING · {weekday, as-of date or selected week}". Serif h1 counting what needs attention (e.g. "{k} things need you this week."). Muted lead sentence of the form "I checked {txns} transactions and {snapshots} stock snapshots…", with the counts read from metrics.json.
  - Segmented toggle **Agent briefing | Classic dashboard**.
  - A stream of **briefing cards** (DESIGN_SIGNAL.md sections 5 and 8). Each has a pill, meta line, serif sentence headline with numbers, muted body, micro-chart, action buttons ("Open in Explore" jumps to the relevant tab; "● Ask why" pre-fills Ask), and evidence chips (finding IDs + anomaly IDs). Minimum set, ordered by severity for the selected week:
    1. Needs you today: Tabby franchise stock-out (F11/F12, R1), with comparison bars TY WOS vs LY WOS.
    2. Needs you: retention leak and Insider gap (F6/F7, R3), with comparison bars by segment.
    3. Pattern: Gen Z share of new accelerating (F5), a column sparkline with the latest week amber.
    4. Win: Gen Z acquisition / Tabby growth (F4/F9), before/after bars.
    5. Watch (optional): apparel overstock (F10/F11, R2).
    Card headline and body text are **AI-worded and validated** (section 4). Show the trust badge "Worded by Claude; every number checked".
  - The weekly AI summary (section 4) as the first block under the h1, or as a "This week in one paragraph" card.
  - **Right rail "What I'm watching · 18 rules"** (≥1280px; below the cards on narrow screens): each rule from `anomalies.json → rules` with its hit count for the selected week, and the alert list (critical → warning → info) with icon + label, never colour alone.
- **Classic dashboard / Explore** (tabs mirroring the goals; one-highlight colour rule, KPI tiles, outline filter selects):
  1. **G1 Performance:** KPI tiles (sales, txns, AOV, UPT, AUR, customers) for the selected window, each with TY, LY and yoy from `trailing`. Weekly TY vs LY line from `weekly[*].sales` (mark W30 partial; `meta.ly_w30_full_week_sales` as a hollow reference point). Decomposition bars from `decomposition_ptd`. Content reference: `outputs/figures/g1_weekly_sales_ty_vs_ly.png`, `g1_yoy_decomposition.png`.
  2. **G2 Gen Z:** Gen Z new TY/LY and `genz_share_of_new` for the window (`trailing`). Weekly Gen Z share-of-new (`genz_weekly`). New vs returning by generation (`generation_ptd`). First-purchase family mix (`first_purchase_mix`, dimension = STYLE_GROUP, YEAR = TY). Insider attach (`new_insider_by_segment`). Retention-proxy caveat from D8. Content reference: `g2_genz_share_of_new_by_week.png`, `g2_new_customers_by_generation_ty_vs_ly.png`, `g2_new_vs_returning_yoy_by_generation.png`, `g2_genz_first_purchase_family_mix.png`.
  3. **G3 Products:** family table for the selected week and window from `products_by_week` (filter `wk`, `window` ∈ {L1W, L4W}), sortable by `contrib_pts` (percentage points), `sales_yoy_pct`, `genz_index_ty`. PTD scorecard with Winner/Decliner pills from `products_ptd`. Style drill-down from `styles_ptd`. Content reference: `g3_family_growth_contribution.png`, `g3_family_growth_vs_genz_index.png`.
  4. **G4 Inventory:** WOS by family for the selected week (`inventory_by_week`, year TY, with `wos_ly_same_week`). Risk table from `inventory_position` (risk, receipts_to_sales_TY/LY, stock_minus_demand_share_pts). Tabby franchise stock vs demand (`inventory_by_week` filtered to Tabby & Pillow Tabby). Content reference: `g4_weeks_of_supply_by_family.png`, `g4_stock_vs_demand_share.png`, `g4_tabby_franchise_stock_vs_demand.png`.
  (The PNGs are content references only; the app redraws with Plotly in the Signal palette and doesn't embed them.)
- **How it was built** (mirror the reference's /build page): serif title, a stat trio of serif numbers with muted captions (from `outputs/tables/14_findings_audit.md`, validator results and script count, all read by code, not typed), numbered sections "01 / 02 / 03" in mono, and a flow diagram **data → metrics.json → rules (anomalies.json) → Claude (facts only) → validator → UI** with the Claude node accent-soft. Include the system-prompt card ("Use ONLY numbers that appear in the JSON facts…"), `meta.definitions`, D3/D5/D8/D9/D10 in plain words, and the surprises F2/F5/F12/F13/F14.
- **Floating "● Ask" pill** (bottom-right) with the critical-alert count, linking to Ask.
- **Charts:** Plotly, styled with the tokens: no top/right spines, faint gridlines, Geist ticks, mono value labels, hover tooltips. One highlighted series, everything else neutral (TY = `--accent`, LY = `--border2`; Gen Z = `--accent` vs others `--surface3`; red/amber/green only for status). No dual axes. No rainbow palettes. Direct labels over legends. Check both themes at laptop width (1280–1440px) and at ~900px.

## 4. AI feature: auto-written weekly summary + anomaly alerts (accuracy-guarded)
Pipeline: **metrics.json → rules (anomalies.json) → compact facts JSON → LLM writes prose → validator → UI**.
1. **Rules first:** anomalies already exist in `data/processed/anomalies.json` (18 rules, `rules[]`; 71 alerts; `by_week`). Do not let the LLM decide what's anomalous.
2. **Facts payload:** write `scripts/15_build_facts.py`. For each week, take `metrics.json → weekly_facts[<wk>]` and replace the `"anomalies"` placeholder with the list of `{id, severity, rule_id, entity, message, values}` from `anomalies.json` for that week. Save `app/facts/W<wk>.json`. No new arithmetic, only selection.
3. **Writer:** write `scripts/16_generate_summaries.py` with a function `generate_summary(facts: dict) -> str`.
   - **Default (no API key):** you (this session) act as the model. Write the ~120–180-word summary for each week yourself, using **only** the numbers in that week's facts file, and store them. Optionally add a deterministic template fallback.
   - **Plug-in point (clearly marked `# === LIVE MODEL PLUG-IN POINT ===`):** if `ANTHROPIC_API_KEY` is set, call the Anthropic Messages API (model `claude-opus-5-5`) with a system prompt like: *"You write a weekly retail performance summary. Use ONLY numbers that appear in the JSON facts. Do not compute, round differently, or infer new numbers. Percent fields are fractions; render 0.1265 as 12.7%. Lead with the most severe anomaly. Max 180 words."* and the facts JSON as the user message.
   - Store results in `app/summaries.json` as `{"<wk>": {"text": ..., "facts_file": ..., "generated_by": "pregenerated|template|live:<model>", "validation": {...}}}`.
4. **Validator:** write `scripts/17_validate_summaries.py` (and import the same function in the app). Extract every number from the text: `$`, `%`, `K`, decimals, integers, signed values. Normalise: "12.7%" → 0.127, "$71.3K" → 71300, "W29" week labels excluded. Each number must match some value in that week's facts JSON within display-rounding tolerance (half a unit of the printed precision). Output per week: `{n_numbers, n_matched, unmatched: [...], status: "PASS"|"FLAGGED"}`. A FLAGGED summary is **blocked** in the UI (show the facts table instead, with a warning). It must fail the build in `run_all.sh`.
5. **UI:** on the Briefing page, show the summary and the briefing-card text with the trust badge **"Worded by Claude; every number checked"** (green-ink check) or **"Blocked: unverified number"** (red-ink, falling back to a facts table). Add a **"Facts used"** expander showing the exact facts JSON. Alerts come from anomalies.json.
6. **Briefing cards use the same pipeline:** `scripts/15_build_facts.py` also emits per-week card facts (`app/facts/W<wk>_cards.json`: card type, finding IDs, and the exact metric values each card may cite). `scripts/16_generate_summaries.py` writes card headlines and bodies in the Signal voice (DESIGN_SIGNAL.md section 7) into `app/briefing.json`. `scripts/17_validate_summaries.py` validates them exactly like the summaries.
7. **Optional stretch (the Ask page):** "Ask the data" Q&A restricted to fixed query templates over metric tables, for example "Which families have WOS below {x} in week {w}?", "Gen Z new customers in {window} ending week {w}?", "Top {n} families by contribution in {window} for week {w}". The LLM may only pick a template and parameters. The answer is rendered from metrics.json by code. Style it like the reference's /ask page: centred title, 6 suggested questions as outline chips in a 2-column grid, an input bar with an accent Send button.

## 5. Verification (required)
- **Hand-check every number** in the summaries for 3 sample weeks: **W29** (last full week), **W28** (W28 AOV spike, first critical Tabby WOS alert), and **W30** (partial week). Trace each number to its metrics.json path. Record the checks in `HISTORY.md` and `PROMPTS.md`.
- Validator self-test: deliberately inject a wrong number (e.g. change 12.7% to 13.7%) and confirm it is FLAGGED and blocked.
- Spot-check 5 dashboard tiles against `outputs/tables/05_g1_kpi_windows.csv` and `14_findings_audit.md`.
- Launch the app (`streamlit run app/dashboard.py`). Click through Briefing, every Explore tab, Ask and How it was built for weeks 23, 29 and 30, with the TY/LY toggle on and off, **in light and dark**. Take screenshots.
- **Design check:** compare the screenshots side by side with https://signal-agent-nu.vercel.app/ (type scale, fonts, colours, spacing, pill/button/chip shapes, card rhythm). List the differences in HISTORY.md and fix them until the app reads as the same design system. Fix layout issues (label collisions, overflow).

## 6. Working rules (same as the analysis session)
- Never modify `data/raw/`. Every number comes from `metrics.json`/`anomalies.json` (produced by saved scripts). No hand-typed figures in code or UI text.
- Loop: ORIENT (read NOTES/HISTORY tail) → PLAN → ACT → VERIFY → RECORD (append `HISTORY.md` "## Iteration N" entries in the existing format) → REFLECT.
- Log every significant AI-assisted step and its verification in `PROMPTS.md` (continue numbering from P16).
- Add the new scripts to `run_all.sh` (it already runs `scripts/[0-9][0-9]_*.py` in order; make sure 15–17 run after 14) and add a `README.md` with setup and run instructions (`./run_all.sh --clean`, then `.venv/bin/streamlit run app/dashboard.py`; add `streamlit` and `plotly` or `altair` to the venv install line).
- Keep `NOTES.md` current. Stop when all tabs work, the 3-week hand check passes, the validator self-test blocks the injected error, and `./run_all.sh --clean` reproduces everything.
