# DECISIONS — interpretation choices
Each entry: question · options · choice · rationale · sensitivity (how much results move under the alternative).
Evidence scripts in brackets. Sensitivity numbers are filled from `scripts/09_challenge.py` → `outputs/tables/09_sensitivity.md` once run.

---
## D1 (QA1) Workbook structure
- **Question:** hidden sheets, header offsets, merged cells, notes?
- **Finding:** 3 visible sheets, no hidden sheets/defined names/formulas/comments/hidden rows. `Data` and `Inventory` headers on row 1 with autofilter. `Column Definitions` has a title in row 1, a merged A2:D2 explanatory note (contains the YoY & trailing-week guidance), Data definitions in rows 5–22 and Inventory definitions in rows 25–29. [01_inventory_workbook.py → outputs/tables/01_workbook_inventory.md]
- **Choice:** read Data/Inventory with `header=0`; treat the merged note as part of the spec.
- **Sensitivity:** none.

## D2 (QA2) Column Definitions — ambiguities & mismatches
| Column | Issue | Resolution |
|---|---|---|
| (sheet note) "one row per transaction line" | True, but every TXN_ID has exactly ONE line (3,609 rows = 3,609 TXN_IDs) | Line = transaction. UPT = units per line. Multi-item baskets cannot be observed. [02] |
| CUST_ID "Identifier for the purchasing customer" | Does not behave as a durable key: 3,600 IDs on 3,609 lines; repeat count consistent with random 6-digit IDs (9 vs 7.3 expected, p=0.30); 0/9 repeat IDs agree on age+insider+region; one ID is "New" twice | See D5. [04] |
| COHORT_STATUS "based on full purchase history"; "Reactivated = after a long gap" | Gap length undefined; status uses history outside the extract (70.2% of lines are Retained/Reactivated on the ID's first in-sample purchase) | Use status as-is; it is the only retention signal. Gap length listed as missing data. [04] |
| CUST_AGE_GROUP "Customer generation" | No birth year or cutoffs given; cannot apply a 1997–2012 rule | Use label as-is (D7). |
| DEMAND_AMT "after discounts" | No list price / discount amount → discount depth not observable | Proxies: OUTLET channel share (definition says outlet = discount) and PRICE_IDX (D4). |
| PROD_TYPE | Defined at product-family level; verified 1 type per STYLE_GROUP | Use as family attribute. [02] |
| ON_HAND_UNITS "end of the week" | FY26 W30 snapshot exists although TY sales stop Wed 2026-08-19 (day 4 of 7) | Treat FY26 W30 stock as the latest available position (D9). Flag as surprising. |
| (note) "trailing week = the FY26 week sequence" | Silent on the partial final week | D10. |
| FISCAL_WK labels | W23–W30 = late Jun–Aug. Calendar/FY boundary not documented | Take labels as given; verified 364-day alignment (FY26 W23 starts Sun 2026-06-28, FY25 W23 starts Sun 2025-06-29). |
| "Every column is populated" | Verified: 0 nulls, 0 blanks | — |

## D3 (QA3) TY/LY representation and YoY basis
- **Representation:** long format: one row per line with a `FISCAL_YR` flag (FY26=TY, FY25=LY) and `FISCAL_WK` = "FYxx Wnn". Not wide TY/LY columns. Inventory is the same.
- **Problem:** TY is partial. FY26 W30 has only Sun–Wed (2026-08-16..19, 147 lines), while FY25 W30 is a full week (222 lines). [02]
- **Options:** (a) all weeks W23–W30, both years as-is (LY gets 3 extra days); (b) full weeks only, W23–W29; (c) **same-days-to-date**: W23–W29 plus W30 Sun–Wed in both years.
- **Choice:** (c) as the headline YTD-in-window ("period-to-date", PTD) basis. Each LY line carries `IN_TY_WINDOW`; 90 LY W30 lines (Thu–Sat) are excluded. Weekly charts show W23–W29 as full weeks and W30 labelled "WTD (Sun–Wed)" against LY Sun–Wed.
- **Rationale:** like-for-like days; fiscal weeks align exactly (364-day shift), so same-week-number = same weekday mix.
- **Sensitivity (09_sensitivity.md):** (c) +12.8% · (b) full weeks W23–W29 +12.1% · (a) naive all rows +7.5%. Option (a) materially understates growth (F2), and (b) vs (c) differ by <1 pt. Gen Z new: +122% under (c), +106% excluding W30.

## D4 (QA4) Line → transaction → customer rollup; returns, discounts, zero lines
- **Rollup:** line = transaction (1:1). Transactions = distinct TXN_ID. Customers = distinct CUST_ID within the period (≈ transactions; see D5). AOV = DEMAND_AMT ÷ transactions. UPT = UNIT_QTY ÷ transactions. AUR = DEMAND_AMT ÷ UNIT_QTY.
- **Returns / negatives / zero-value lines:** none present (min DEMAND_AMT 27.86, UNIT_QTY ∈ {1,2,3}). Cleaning logs the check, and the rule if any appeared would be: keep returns as negative demand in net sales, exclude them from transaction counts. Demand here is gross = net.
- **Discounts:** already netted in DEMAND_AMT. Discount-dependence proxies: (1) `IS_OUTLET` share (primary, defined by the business as discount stores); (2) `PRICE_IDX` = unit price ÷ median RETAIL unit price of the same STYLE_DESC (pooled TY+LY). Secondary only: retail unit prices for one style vary ±40%, so the index is noisy.
- **Sensitivity:** n/a (no returns). Outlier sensitivity of AOV is tested in 09 (trimmed top 1%).

## D5 (QA5) Customer identity
- **Finding:** CUST_ID exists for 100% of lines, so there are no anonymous or null customers (0% of sales). But it is not a durable link across purchases (D2 evidence). Only 6 IDs span both years, and that matches random collisions.
- **Options:** (a) treat CUST_ID as a true key and compute repeat/retention behaviourally; (b) treat CUST_ID as non-linking, count customers = distinct IDs per period, and measure retention through COHORT_STATUS.
- **Choice:** (b).
- **Rationale:** with (a), behavioural LY→TY retention = 6/1,779 = 0.3%, an artifact. Frequency (txns/customer) = 1.00 in both years, so it adds nothing.
- **Sensitivity:** customer counts differ from transaction counts by ≤ 3 per year, which is immaterial.

## D6 (QA6) "New customer"
- **Options:** (a) `COHORT_STATUS == 'New'` (brand's full-history definition); (b) first appearance in this extract (left-censored: no data before FY25 W23, so 99.7% of IDs would be "new"); (c) New + Reactivated ("new-to-file-or-lapsed" acquisition).
- **Choice:** (a) primary, (c) as a sensitivity.
- **Rationale:** (b) is meaningless here because of censoring and the ID issue. (a) is computed by the source system with full history, so it is not left-censored by our extract. We cannot validate it, though (LY "New" could only be checked against pre-FY25 data we don't have). The 1 ID that is "New" on two TY lines is treated as a collision, and each line is counted.
- **Unit:** new customers = lines (= transactions) with status New. That is ≈ distinct new CUST_IDs (1,072 lines vs 1,069 IDs).
- **Sensitivity (09):** under (c) New+Reactivated, Gen Z = 273 vs 140 (+95%), share 32.2% vs 19.2% (p<0.001). Same conclusion.

## D7 (QA7) Gen Z definition
- **Field:** `CUST_AGE_GROUP == 'Gen Z'`. No birth-date field exists, so the 1997–2012 cutoff can't be applied or checked. We assume the source uses a standard band.
- **Missing values:** none (0 nulls, 4 labels). If an "Unknown" appeared it would be excluded from share denominators and reported separately.
- **Sensitivity:** n/a. Note that age group is recorded per line, and colliding IDs disagree (D2), which supports D5.

## D8 (QA8) Retention
- **Not measurable behaviourally:** LY→TY repurchase, repeat within N weeks and second-purchase rate all need a durable customer key (D5).
- **Choice (proxies):**
  1. **Returning-customer share** = share of transactions (and demand) from customers whose status is Retained or Reactivated, TY vs LY, by generation. This measures how much of the business existing customers carry.
  2. **Retained vs Reactivated split** within returning customers.
  3. **Gen Z returning-customer volume** TY vs LY: Gen Z customers acquired in earlier periods who are buying again.
  4. **Insider (loyalty) attach among new customers** as a leading indicator of future retention (Insider share is 19% for New vs 70% for Retained [04]).
- **Rationale:** these use the brand's full-history status field and are comparable TY vs LY.
- **Caveat:** these are mix measures, not cohort rates. They can't give "x% of Gen Z new customers came back" or repeat rate by first-purchase product (data request R1).

## D9 (QA9) Inventory
- **Snapshot rule:** ON_HAND_UNITS is end-of-week stock, so it is never summed across weeks. Multi-week views use the latest week (or the average of weekly snapshots, labelled as such).
- **Join:** inventory ↔ sales on (FISCAL_YR, WK, STYLE_GROUP). 21/21 family names match exactly. Key unique, 336 = 21 × 8 × 2. [03]
- **Weeks of supply (WOS):** end-of-week ON_HAND ÷ trailing-4-full-week average weekly units for that family (same year). For TY W30 (partial sales) the denominator is W26–W29. For weeks < W26 the trailing window is truncated to the available weeks (W23 → 1 week), flagged `wos_window_weeks`.
- **Sell-through (weekly):** units sold in week ÷ (units sold + end-of-week on hand), which approximates units ÷ beginning-of-week stock without needing the W22 snapshot. The window version is total units W23–W29 ÷ (units + W29 EOH).
- **Scale assumption — TESTED:** sales come from a sample extract (~225 lines/week). If stock and sample sales are on the same scale, implied receipts (ΔEOH + units) can't be negative. Result (08_g4_summary.md): 0 of 273 family-weeks negative, minimum +3. Absolute WOS is therefore treated as meaningful.
- **Sensitivity (09):** Tabby WOS 1.8–2.2 and Pillow Tabby 1.3–1.8 under 3 alternative denominators. Knit Dress 17.5–21.2, Trench 16.2–19.0. Conclusions unchanged.
- **TY W30 stock snapshot:** labelled end of week but sales stop Wednesday. It's used as "latest position" for WOS. Flagged surprising.

## D10 (QA10) Trailing-week window
- **Choice:** as-of = last complete TY week **W29** (week ending Sat 2026-08-15).
  - **L1W** = W29 vs LY W29 (YoY) and vs TY W28 (WoW).
  - **L4W** = W26–W29 vs LY W26–W29 (YoY) and vs TY W23–W25, the prior period, which is only 3 weeks; compared on a weekly-average basis and labelled as such.
  - **WTD** = TY W30 Sun–Wed vs LY W30 Sun–Wed (flash only).
- **Dashboard:** any selected week w gives L1W = w and L4W = w-3..w when w ≥ 26 (truncated before that, flagged).
- **Rationale:** partial weeks distort WoW. Like-for-like days are kept for WTD.

## D11 Sample scaling (cross-cutting)
- **Question:** the workbook is a "sample extract" (~225 lines/week). Are TY and LY sampled at the same rate?
- **Choice:** assume an equal sampling rate, so count growth (transactions, customers, demand) represents real YoY. Ratios (AOV, shares, mix) don't depend on this assumption, so they are the most robust findings.
- **Sensitivity:** if TY were oversampled, every count-based growth claim would shift by the same factor. Share/mix claims would not.

## D12 Statistical noise (cross-cutting)
- Weekly cells are small (Gen Z new customers per week range 21–41 TY, 5–17 LY incl. partial W30; 06_g2_genz_new_by_week.csv). Every key TY-vs-LY share comparison gets a two-proportion z-test or bootstrap 95% CI. Product rankings use a minimum-volume threshold (≥ 30 TY+LY lines per family). Findings with p > 0.05 or CIs spanning 0 are labelled **tentative**.

## D13 Anomaly rules (Phase M)
- **Question:** which deterministic rules flag an unusual week, and how do we avoid noise from truncated windows?
- **Choice:** 18 rules in scripts/12_anomalies.py (thresholds in data/processed/metrics_schema.md). WOS and family-decline rules fire only on full 4-week windows (W26+). Earlier weeks produced spurious alerts, e.g. a Pillow Tabby WOS of 17.8 in W23 from a single 5-unit week. WOS_LOW escalates to critical for G3 winners and Gen Z gateways.
- **Sensitivity:** with no window guard there were 91 anomalies (8 critical). With the guard, 71 (8 critical). The critical set is unchanged.

---
# Dashboard (web app) decisions

## D14 Front end: static React app on Vercel, not Streamlit
- **Question:** the brief lets us choose the tools; the design calls for purposeful animation (playhead, morphs, drill-down zoom) and a shareable link.
- **Choice:** Vite + React + TypeScript in `web/`, reading one precomputed JSON (`web/src/data/app.json`); deployed as a static site on Vercel. Charts are hand-built SVG/CSS (no chart library) so every transition is controllable.
- **Rationale:** Streamlit reruns the whole page on every interaction, which fights animation; a static bundle needs no server or API key, so a reviewer just opens a link.

## D15 Precompute everything; the browser does no arithmetic
- **Choice:** all metrics come from `scripts/01–14` (metrics.json, anomalies.json); `scripts/15–18` select facts, word them, validate them and export `app.json`. The UI only selects, filters, sorts, compares to rule thresholds, and formats (0.128 → +12.8%, 71,311 → $71.3K); the only other arithmetic is drawing geometry (bar widths, chart coordinates).
- **Consequence:** animated numbers never count through intermediate values; they swap between two stored values (e.g. +12.8% ↔ +7.5%). The playhead label shows the nearest week's stored value, not an interpolation.

## D16 New precomputed fields and 6-decimal precision
- `11_metrics.py` adds `meta.counts`, `meta.week_dates_ty`, `meta.basis_alternatives` (+ `naive_gap_pts`, `ly_extra_days_sales`), `meta.data_quality`, `w30_daily` (M6 day segments, real values; the design mock's daily splits were placeholders), `stock_demand_shares` (M5; same definitions as script 08, asserts the 0.96 → 0.33 correlation in F11) and `growth_drill` (M3; shares of growth sum to 1, asserted).
- Fractions are now stored at 6 dp (was 4): at 4 dp, 1-dp percentages sit on rounding ties (the naive YoY rendered +7.4% vs +7.5% in FINDINGS; L1W W29 +12.6% vs +12.7%). Findings audit still 30/30; anomalies unchanged (71; 8 critical).

## D17 Briefing cards and severity are decided by rules, not the AI
- Five card types per week (stock, retention, pattern, win, overstock). Severity pill from that week's anomaly hits: critical → CRITICAL, warning → WARNING, else WATCH; pattern = PATTERN, win = WIN; overstock is always WATCH (a planning action). Ranked by that severity.
- Time travel: each week's card uses only data as of that week; latest-position facts (receipts W24–29, R1/R2/R3 sizing, TY Insider segment gaps) only from W29.

## D18 Number validator, implemented twice
- Every printed number ($, %, K, pts, decimals, integers, signed) must equal some value in the facts the text was written from, within half a unit of the printed precision; explicit signs must match; week labels/FY/L1W/dates/"4-week" are masked; week-index fields are not citable; rule thresholds are.
- Python (`scripts/17_validate_summaries.py`) gates the build; a JavaScript port (`web/src/lib/validator.js`) re-checks every text in the browser before showing it; `web/scripts/parity.mjs` asserts both reach identical verdicts and fact matches on all texts (56 texts, 513 numbers).
- Limitation: an existence check, not a semantic one (a value several facts round to can match the "wrong" fact); mitigated by narrow per-card facts and a hand review of W28–W30.
- Superseded by D25 for AI texts: texts now cite fact keys and six checks run. This existence check stays as the second layer, and is what `validateText(text, facts)` runs for a caller without citations.

## D19 Who writes the text
- Default: texts written by Claude (this build session, acting as the model) from each week's facts only, stored in `ai/session_texts.json` with the md5 of those facts; stale md5 → deterministic template + warning. With `ANTHROPIC_API_KEY`, `16_generate_summaries.py` calls `claude-opus-5-5` (plug-in point marked) through the same validator, one retry with the unmatched numbers, else template. Per week: masthead headline, ~150-word summary, 5 cards.

## D20 Visual design: Claude Design "Briefing directions" → final TYLY Dashboard (single theme)
- Palette Sapphire / Charcoal Blue / Lavender / Thistle, Archivo + Space Mono, flat colour blocks; single theme (no dark mode) by the user's choice.
- Mock content replaced by data: alert IDs (mock AN098–AN108 → real AN048–AN058), rule states (mock showed RECEIPTS_BELOW_SALES firing in W29 and WOS_LOW as a warning; real: receipts fires only in W30, WOS_LOW escalates to critical for Tabby/Pillow Tabby, FAMILY_L4W_DECLINE fires twice), finding IDs (F5 pattern, F4/F9 win), weekly demand series, W30 TY ($44.9K, mock $41.6K), daily splits, family tables.

## D21 Motion only where it carries information; reduced motion respected
- M1 playhead (time), M3 drill-down zoom (part → whole), M5 LY → TY morphs (change), M6 naive vs like-for-like (basis), M8 validator replay (trust). No loops; UI transitions ≤ ~450 ms.
- `prefers-reduced-motion: reduce` → final states immediately. A footer toggle ("Animations: … play them anyway") lets a viewer opt in; saved in localStorage only.

## D22 Playhead events are chosen by rules
- One event per week by priority: first-ever critical rule → first stock-rule hit → week-on-week swing → YoY spike → transactions below LY → partial week. Event text is the rule's deterministic message from anomalies.json (not AI).

## D23 Ask = fixed query templates (superseded by D26)
- Eight templates over app.json; offline a keyword/regex picker chooses template + parameters; a model may replace only the picker (returns template + params, never numbers). Answers list the template, parameters and data read. Unmatched questions get "no template matches" instead of a guess.

## D24 Defaults and state
- Default week W29 (last full week), window L4W, LY shown. All state lives in the URL hash (`#/explore/g4?wk=30&win=PTD&ly=0`), so any view is linkable; `&demo=blocked` (edited number), `&demo=metric`, `&demo=direction` and `&demo=subject` show the validator holding a text back (D25).

## D25 AI texts cite fact keys; the validator checks meaning, not just existence
- Question: D18 asked only whether some fact matched each printed number, so it passed misstatements.
  "W29 transactions -1.8% YoY" (the AOV change), "W29 demand fell 12.7%" (it rose) and "Gen Z demand was $71.3K" (total demand) all passed.
  It also passed two live texts for the wrong reason: W30 "29%" (Pillow Tabby receipts) matched Tabby's L4W demand growth, and W28 "85" (returning Gen Z LY) matched a stock count.
- Options: (a) keep the existence check and narrow the facts further; (b) parse free text and guess which fact each number means; (c) have the writer cite the fact key and check the words against it.
- Choice: (c).
  - Texts are placeholder sources, `{fact key|format}`, with no typed figures.
    Formats: money_k ($71.3K), money ($564,028), money2 ($285.25), pct (12.7%), pct+ (+12.7%), pct0 (28%), pct2 (0.85%), pct_abs (a change without its sign, only after an up or down word), pts+ (+5.0 pts), int (1,142), wos (2.1), ratio2 (0.33).
  - `render()` in 17 turns a source into the shown text plus one citation per number (span, key, format, value); 16 stores source, text and citations, 18 exports all three, and the UI never formats AI numbers.
  - Six checks run in Python (17) and JavaScript (`web/src/lib/validator.js`), from one vocabulary (`web/src/lib/vocabulary.json`): citation (key exists, format fits the kind of value, the shown figure re-reads to the cited value; uncited and spelled-out numbers fail), metric, subject, period (window, YoY/WoW, last-year label), direction, and comparison (half, majority, doubled, rank words against the ranked lists in the facts).
  - Attribution is deterministic: clauses split at sentence ends, `;` `:`, top-level commas and spaced dashes; each number takes the word attached right after it ("2.1 weeks of supply", "+12.7% YoY"), else the nearest word before it in its clause, else the nearest word after it (a last-year label works the other way round: it labels the number right after it, else the nearest number before it).
  - Comparison and rank words use the clause first and then the sentence; a claim with nothing in the facts to check it against fails.
  - The shared corpus `web/scripts/validator_cases.json` (51 cases) runs in 17 and in `parity.mjs`; both exit 1 if a case changes verdict or Python and JS disagree, so the Vercel build fails.
  - Demos (`&demo=blocked|metric|direction|subject`) are built by 16 from the week's facts and asserted by 17 to fail exactly their check.
  - The win card's facts now include `l4w_top_families_by_contrib` (copied, no arithmetic) so "Tabby and Pillow Tabby lead L4W growth" can be checked.
  - `render()` and the rule messages in 12 (`_common.fixed`) round like the UI's `Number.toFixed` (exact binary value, ties away from zero); Python's `format()` rounds exact ties to even, which had put "21.2" in an alert next to "21.3" in the chart (W28 Knit Dress, 21.25).
- Rationale: a misattribution is now visible as a key name, and every claim type that the facts can settle is checked deterministically.
  When a rule is too strict for an honest sentence, the sentence is reworded and the rule stays (HISTORY Iteration 17 lists the rewordings).
- Sensitivity: claim types that remain unchecked are listed in `vocabulary.json` (`unchecked`) and on the How page.
  The nearest-word rule cannot read "X and Y respectively", so writers give each number its own clause.
  `validateText(text, facts)` without citations still runs the D18 existence check, so callers that cannot cite (for example a future live Ask answer) keep working but get the weaker guarantee.

## D26 Ask: Claude picks the template, code checks the choice and answers
- A Vercel function (`web/api/ask.ts`) sends the question to Claude (`claude-opus-5-5`, effort low, server-side refusal fallback) with structured output against a fixed schema: one of 12 templates plus parameters, any premise the question takes for granted, any entity the template cannot filter by, and a one-line reading.
- Claude never sees or writes a data value; the schema enums (families, weeks, windows) are read from app.json, and the reading is shown only if it has no numbers beyond week labels.
- The browser runs the route through the same checks as the offline keyword parser (`web/src/lib/ask/engine.ts`): week in range, unmatched products or regions refuse instead of answering for the whole business, family templates need a family, and a premise is checked against the stored YoY and WoW values and stated before the answer.
- Any failure (no key, timeout, rate limit, refusal) falls back to the keyword parser and the answer says which picker ran, so the public page never depends on the function.
- Abuse guard: 300-character questions, a per-IP limit per warm instance, a small in-memory cache, same-origin check, and the Anthropic console spend limit as the hard cap.
- Premise scope (Iteration 21): every premise gets a verdict, whatever the template, checked over the period the answer covers (the template's week and window, the full period for PTD-only templates, else the single week) and for the route's subject (a family's demand, Gen Z transactions or new customers, or the whole business); what nothing stored can settle gets an explicit "isn't checked" sentence instead of silence.
- Why not let Claude answer directly: an answer written by a model would need the number validator plus a semantic check; routing keeps every number in code and makes wrong-entity answers impossible by construction.
