# HISTORY (append-only)

## Iteration 1
- Goal (Phase A): set up, copy raw, inventory workbook, read Column Definitions.
- Actions / scripts: created dir layout + .venv; copied xlsx → data/raw (chmod 444); scripts/01_inventory_workbook.py; scripts/02_profile.py.
- Result: outputs/tables/01_workbook_inventory.md, outputs/tables/02_profile.md. 3,609 lines (TY 1,829 / LY 1,780), 16 fiscal weeks, 336 inventory rows.
- Verification: row counts from openpyxl max_row (3,610 incl header) match pandas (3,609). Inventory 336 = 21×8×2.
- Surprises / errors: (1) TY W30 partial (4 days); (2) every TXN_ID is a single line; (3) CUST_ID ~unique — behavioural retention not measurable; (4) COHORT_STATUS relies on history outside the extract.
- Next: cleaning script with logged row counts; quantify CUST_ID collision hypothesis; draft DECISIONS.

## Iteration 2
- Goal (Phase A): cleaning + customer identity.
- Actions / scripts: scripts/03_clean.py, scripts/04_identity_checks.py; wrote DECISIONS.md D1–D12, PROMPTS.md.
- Result: data/processed/lines.csv (3,609 × 32), inventory.csv (336). TY as-of 2026-08-19 (W30 day 3). 90 LY W30 lines outside the TY window. CUST_ID repeats = 9 vs 7.23 expected under random IDs (MC p=0.30); 0/9 repeats agree on all attributes. Status mix: New 27.1%→32.3% of lines; Gen Z 16.1%→21.8% of lines.
- Verification: DEMAND_AMT TY 564,027.83 / LY 524,910.67 and units 2,270 / 2,205 reconcile to raw; closed-form vs Monte Carlo agree.
- Surprises / errors: CUST_ID non-durable → behavioural retention impossible; TY W30 inventory snapshot future-dated vs sales.
- Next: G1 performance script (05) with PTD / L1W / L4W / WTD and decomposition.

## Iteration 3
- Goal (G1): KPI windows, weekly trend, decomposition, segment contribution.
- Actions / scripts: scripts/_common.py (shared KPI defs, stats, chart style); scripts/05_g1_performance.py.
- Result: PTD like-for-like demand TY $564,028 vs LY $499,804 (+12.8%); txns +8.2% (z=2.34, p=0.019); AOV +4.3% (bootstrap p=0.085, n.s.); AUR +4.2%, UPT flat, freq 1.00. Decomposition: customers 65% / AUR 34% of log growth. L1W (W29) +12.7%; L4W +13.2%; WTD +21.7%. W29 WoW -18.8% (W28 AOV spike $343). Top contributors: Womens Bag +12.7pts, Hero +50.5% YoY, New cohort +38.9%, Gen Z +47.2%; Halo -21.2%, Womens Apparel -35.7%. Naive alt-a (LY full W30) gives only +7.5%.
- Verification: decomposition log terms sum to total (assert); segment contributions sum to total per dimension (visual + table); PTD LY row count 1,690 = 1,780 - 90.
- Surprises / errors: method-sensitivity of headline (+12.8% vs +7.5%); Halo/Apparel decline.
- Next: G2 Gen Z acquisition + retention proxies (06).

## Iteration 4
- Goal (G2): Gen Z acquisition, first purchase, retention proxies, value.
- Actions / scripts: scripts/06_g2_genz.py → outputs/tables/06_g2_*.csv, 06_g2_summary.md; 4 figures g2_*.png.
- Result: Gen Z new 240 vs 108 (+122%, p<0.001); Gen Z = 97% of the +136 increase in new customers; non-Gen Z new +1.2% (p=0.88). Gen Z share of new 23.8%→40.7% (p<0.001), TY > LY in 8/8 weeks, TY trend rising W23 33% → W29 47% → W30 WTD 56%. Returning txns flat overall (+0.2%), Gen Z returning -3% (158 vs 163). New Gen Z Insider attach 17.1% (LY 21.3%, n.s.). New Gen Z over-index Hero (169, p=0.002), Tabby (165, p=0.014), Europe (148, p=0.015); AUR +$22 vs other new (p=0.04), outlet share lower (n.s.).
- Verification: generation rows sum to All (new 240+175+115+60=590 ✓; LY 108+170+119+57=454 ✓); weekly Gen Z new cumsum = 240/108 matches totals.
- Surprises / errors: Gen Z acquisition accelerating within TY; Gen Z returning base NOT growing despite LY acquisition (weak retention signal).
- Next: G3 products (07), G4 inventory (08), then challenge (09).

## Iteration 5
- Goal (G3): winning products.
- Actions / scripts: scripts/07_g3_products.py → 07_g3_family_scorecard.csv, 07_g3_style_scorecard.csv, 07_g3_summary.md; figures g3_family_growth_vs_genz_index.png, g3_family_growth_contribution.png.
- Result: Tabby +42.9% (p=0.006) = 59% of total growth; Pillow Tabby +83.4% (p=0.011) = 27%; together 85%. Hero +50.5% PTD, Halo -21.2%. Decliners: Rogue -22.6% (p=0.021), Knit Dress -50.8% (p=0.029), Tailored Jacket -33.3% (p=0.081). Winners: Tabby, Pillow Tabby, Mens SLG, Wallet. Gen Z over-index: Mens Bag 151, Pillow Tabby 144, Loafer 130, Tabby 122. Top style contributors: Tabby 20 (+57%), Willow Bucket Bag (+65%), Tabby Messenger (+42%).
- Verification: family contributions sum to total growth (share_of_growth sums to 1.0); all 21 families pass min-volume ≥30.
- Surprises / errors: growth extremely concentrated in one franchise (Tabby).
- Next: G4.

## Iteration 6
- Goal (G4): inventory alignment.
- Actions / scripts: scripts/08_g4_inventory.py → 08_g4_weekly_family.csv, 08_g4_position.csv, 08_g4_summary.md; figures g4_weeks_of_supply_by_family.png, g4_stock_vs_demand_share.png.
- Result: Tabby WOS 1.9 (LY 7.0), EOH -66% YoY, EOH -72% W23→W30; Pillow Tabby WOS 1.6 (LY 5.1). Apparel WOS 16–21 (median 7.9): Knit Dress 21.2, Trench 16.9 (EOH +83% YoY), Tailored Jacket 16.3. Stock-demand correlation 0.96 LY → 0.33 TY. Implied receipts: Tabby received 28% of units sold (LY 95%), Pillow Tabby 29% (LY 85%); apparel 1.30–1.38×. Receipts-demand correlation 0.99 → 0.53.
- Verification: inventory join validated one_to_one (336 rows in/out); implied receipts never negative over 273 family-weeks (scale consistency, D9); snapshots summed only across families within a week.
- Surprises / errors: replenishment is not following demand this year; the winner/Gen Z gateway is about to stock out.
- Next: challenge script (09) — robustness of F1–F8 + G3/G4; then lost-sales sizing for recommendations.

## Iteration 7
- Goal (Challenge, all G): robustness of F1–F11.
- Actions / scripts: scripts/09_challenge.py → outputs/tables/09_sensitivity.md, 09_robustness.csv.
- Result: F1 holds (8/8 weeks; LOO +11.1…+14.3%), but ex-Tabby growth is +6.4% and ex-both-Tabby +2.4%. F4 robust to every alternative (New+Reactivated +95%; ex-Tabby +121%; mix-standardized 39.3% vs 23.8%; CI [+11.2, +22.5] pts). F5 significant (p=0.006; permutation p=0.002; LY flat). F6 holds. F8 AUR premium downgraded (within-family +$8.4 vs raw +$22). Hero ≡ Tabby + Pillow Tabby. F11 WOS holds under 3 alternative denominators.
- Verification: two independent tests each for F4 (z-test + bootstrap) and F5 (half-split z + permutation).
- Surprises / errors: F8 partly a mix effect, downgraded.
- Next: size recommendations.

## Iteration 8
- Goal (Recommendations): quantify R1–R3.
- Actions / scripts: scripts/10_sizing.py → outputs/tables/10_sizing.md, 10_sizing.json; FINDINGS F13, F14, Draft recommendations R1–R3; run_all.sh written; CHECKPOINT: `./run_all.sh --clean` OK (10 scripts, 30 tables, 11 figures); NOTES condensed; QUESTIONS statuses updated.
- Result: R1 4-week demand at risk $23.1K (7.7% of next-4-week demand), Tabby OOS in ~2.6 wks, Pillow Tabby ~2.2. R2 apparel excess 198 units / $50.5K retail (9.0% of TY PTD demand). R3 +15 Gen Z Insiders to reach Millennial attach (+37%); +10% returning Gen Z = +0.85% of TY demand.
- Verification: sizing inputs re-read from 08 outputs (not retyped); hand-derived ratios moved into script.
- Surprises / errors: none.
- Next: QN7 (Insider by segment) then Phase M.

## Iteration 9
- Goal (G2): QN7 Insider gap by segment; source of the F5 acceleration.
- Actions / scripts: extended scripts/06_g2_genz.py → 06_g2_new_insider_by_segment.csv, 06_g2_genz_new_acceleration_split.csv.
- Result: new Gen Z Insider attach gap is in Outlet (9.7% vs 23.1%, p=0.029), Greater China (5.1% vs 21.7%, p=0.023), eComm (12.7% vs 19.2%, n.s.); retail parity. Acceleration W27–30 is store-led (+41 of +44) and full-price (+40), North America/Europe; broad across product types.
- Verification: segment counts sum to totals (161+79 = 240 Gen Z new; 98+142 = 240).
- Surprises / errors: acceleration is not Tabby-driven.
- Next: decision-relevant additions are now marginal (iterations 7–9 refined rather than changed the story). Move to Phase M.

## Iteration 10
- Goal (G3/G2): emerging Gen Z products from existing outputs.
- Actions / scripts: no new computation; read 07/06/08 outputs → FINDINGS F15 (tentative).
- Result: Mens Bag Gen Z index 151 (League Backpack 181), Gen Z new 11 vs 1, family demand +5.5%, WOS 5.8.
- Verification: values read directly from 07_g3_family_scorecard.csv / 06_g2_genz_new_by_family_yoy.csv / 08_g4_position.csv.
- Surprises / errors: none.
- Next: STOP analysis. Iterations 9–10 refined targeting but did not change the ranked recommendations; with the half-day budget, diminishing returns → Phase M.

## Iteration 11 (Phase M)
- Goal: dashboard-ready metrics + anomaly rules + docs.
- Actions / scripts: 11_metrics.py → data/processed/metrics.json (+ metrics_*.csv); 12_anomalies.py → anomalies.json, outputs/tables/12_anomalies.md; 13_docs.py → outputs/tables/data_dictionary.md, data/processed/metrics_schema.md; new figure g4_tabby_franchise_stock_vs_demand.png (08).
- Result: metrics.json 19 sections indexed W23–W30; weekly_facts per week for the LLM. 71 anomalies (8 critical, 58 warning, 5 info). First critical Tabby WOS alert in W28.
- Verification: metrics self-asserts (headline = raw; weekly sums = PTD; L4W = script 05); anomaly alerts reviewed by hand → truncated-window guard added (D13).
- Surprises / errors: hard-coded numbers found in 3 chart titles → replaced with computed values (ground rule 2).
- Next: findings audit, handoffs.

## Iteration 12 (verification)
- Goal: accuracy audit of FINDINGS.md.
- Actions / scripts: 14_verify_findings.py → outputs/tables/14_findings_audit.md; DECISIONS sensitivities filled; D13 added; PROMPTS P5–P15.
- Result: 30/30 PASS after adding the missing "Tabby alone = 59%" figure to F9.
- Verification: audit reads metrics.json/tables (second path), not the producing scripts' stdout.
- Next: Phase H handoff prompts; final clean rebuild + reproducibility diff.

## Iteration 13 — FINAL (analysis session)
- Goal: Phase H handoffs + final checks.
- Actions / scripts: handoff/PROMPT_C_dashboard.md, handoff/PROMPT_D_deck.md; README.md; `./run_all.sh --clean` ×2.
- Result: 14 numbered scripts; 36 tables, 12 figures; metrics.json + anomalies.json (71 alerts, 8 critical). Two clean runs → 46 output files byte-identical. Raw xlsx md5 unchanged (1e0cdc15…).
- Verification: findings audit 30/30; metrics self-asserts pass inside run_all.
- **What was done:** Phase A structure (D1–D13), G1–G4 analysis (F1–F15), challenge (09), sizing (10), metrics layer + rules (11–13), audit (14), handoffs.
- **Dead ends / dropped:** behavioural retention, repeat rate by first-purchase product, and basket analysis are impossible (CUST_ID non-durable, 1 line per txn → Q2.3, Q3.3 dropped). Discount depth not observable (no list price; PRICE_IDX too noisy to lean on).
- **Open questions:** QN5 (what triggered the W27+ Gen Z store surge: needs campaign/store-event calendar). Cause of the Tabby replenishment cut (needs PO/supplier data). Whether the TY W30 stock snapshot is mid-week or projected.
- **Confidence by finding:**
  - High: F1 (+12.8%, robust except to the naive window), F2, F4 (Gen Z new +122%, survives every alternative), F5 (p=0.006 / permutation p=0.002), F9 (Tabby concentration), F11 (WOS under every denominator), F14.
  - Medium-high: F6 (flat returning; proxy, not cohort), F12 (receipts inferred, not observed), F10 (Rogue/Knit Dress significant; Trench/Tailored Jacket not).
  - Medium: F3, F7 (segment gaps n=22–79), F8 (Tabby gateway solid; AUR premium downgraded to mix), F13.
  - Low / tentative: F15 (Mens Bag watch list, n=11). R3 impact (scenario-based).

## Iteration 14 (dashboard: data layer)
- Goal: give the new web dashboard (Claude Design "TYLY Dashboard") real data for every view and animation.
- Actions: restored the 6-dp precision + meta fields in `11_metrics.py`; added `w30_daily`, `stock_demand_shares`, `growth_drill`, basis gap fields; documented in `13_docs.py`.
- Verification: in-script asserts (W30 day sums = weekly totals; correlations = 0.96 / 0.33 as in F11; family shares of growth sum to 1); findings audit 30/30; anomalies unchanged.

## Iteration 15 (dashboard: AI pipeline)
- Actions: `15_build_facts.py` (week facts + upstream source path for every number; card facts; rule-picked playhead timeline), `16_generate_summaries.py` (headline + summary + cards; pregenerated / template / live plug-in), `17_validate_summaries.py`, `18_export_web.py` → `web/src/data/app.json`.
- Result: 56/56 texts PASS (8 headlines, 8 summaries, 40 cards; 513 numbers). Injected error (12.7% → 13.7%) FLAGGED; with that edit in `ai/session_texts.json` the build exits non-zero.

## Iteration 16 (dashboard: web app)
- Actions: `web/` Vite + React app porting the Claude Design file: Briefing (M8 validator replay, held-back state, facts table with source paths, hover connector, 5 cards with micro-charts, rules + alerts rail), Explore G1 (M1 playhead) / G2 (M5 share morph) / G3 (M3 drill-down) / G4 (M5 scatter + WOS morph), Ask (8 templates), How it was built (M6 basis switch, system prompts, definitions); JS validator + parity check.
- Bugs found and fixed while testing: playhead crash (first rAF timestamp precedes start → index −1); playhead resumed from the selected week instead of replaying; stale week ref after external week change; rule cells guessed WOS_LOW severity instead of reading the alerts; Tabby scatter label overflow; doubled parentheses in partial-week copy.
- Finding: this Mac reports `prefers-reduced-motion: reduce`, so animations were (correctly) off; added an opt-in footer toggle and verified motion in headless Chrome with emulated `no-preference`.
- Verification: headless Chrome (DevTools protocol) samples: playhead W23→W30 at 0.9 s/week with the global week following; M8 holds back at the injected number (6/27 ok); M6 +12.8% ↔ +7.5% with "≈5.4 pts lost to 3 extra days ($25.1K)"; M3 Demand → Drivers → Families → Tabby styles (Tabby 20 = 25% of growth); production build renders all pages for W23/W29/W30; no horizontal overflow at 900 px; two `./run_all.sh --clean` runs → 79 outputs byte-identical; raw md5 unchanged.

## Iteration 17 (validator: meaning, not just existence)
- Goal: make the AI-text validator check that each printed number is the fact it cites and that the words around it agree (handoff/PROMPT_E_validator.md, DECISIONS D25).
- Reproduction first: with the real W29 facts, "W29 transactions -1.8% YoY", "W29 demand fell 12.7% YoY" and "Gen Z demand was $71.3K in W29" all PASSED in both the Python and the JS validator, matched to `l1w_aov_yoy_pct`, `l1w_sales_yoy_pct` and `l1w_sales_ty`.
- Actions:
  - Texts became placeholder sources (`{fact key|format}`); 17 gained `render()`, citations and six checks (citation, metric, subject, period, direction, comparison) driven by one vocabulary, `web/src/lib/vocabulary.json`; `web/src/lib/validator.js` was ported line for line.
  - Shared corpus `web/scripts/validator_cases.json` (51 cases, including the four reproduction sentences); 17 and `parity.mjs` both run it and exit 1 on any change in verdict.
  - 16: placeholder system prompts and template, render and store source + text + citations, demos per week (edited number, wrong metric, wrong direction, wrong subject). 18 exports them. 15: the win card carries `l4w_top_families_by_contrib` so rank words can be checked.
  - All 56 texts rewritten in placeholder form, validated, then stamped; 17 now writes `outputs/tables/17_number_trace.md` (printed number → cited key → value → upstream path).
  - UI: tooltips show the cited key, its source path and the checks that ran; the held-back panel names the failed check, the cited key and why (no more nearest-fact guessing); four demo links; How page lists the six checks with run counts and the unchecked claim types.
  - Rounding: `render()` and 12's rule messages now round like the UI's `toFixed` (`_common.fixed`); one alert message changed (W28 Knit Dress 21.2 → 21.3, value 21.25), matching the chart.
- Honest sentences that had to be reworded, and why:
  - "Three retention warnings", "Two critical stock alerts" (W23, W28, W29): spelled-out counts are uncited numbers and the facts hold no alert count.
  - "less than half of last year's" (W24 and W26 stock cards, W26 summary): no cited fraction backs it, and the validator does no arithmetic between two numbers.
  - "These are the period's growth leaders" (W29): a rank claim must name the families; now "Tabby and Pillow Tabby are L4W growth leaders".
  - "The gap is widest in Outlet" (W29 retention) and "the main growth family/engine" (W26 stock, W28 summary): the facts hold no ranking for them, so the rank words were dropped.
  - "add +5.0 and +5.5 pts", "with 27 and 92 units", "2.5 and 2.8 weeks ... 6.7 and 7.8 last year": the nearest-word rule cannot read "respectively", so each number got its own clause with its family.
  - "(+70.8% YoY)" after "contribution", "and holds 22.4 weeks" after "demand", "+18.9% WoW" in a YoY clause, "17.8 weeks ... of sales", "+21.7% YoY on the same 4 days": the nearest word named another metric or basis, so the clauses were reordered or split.
  - "traffic-led rebound": "led" is a rank word; now "a rebound driven by traffic".
  - "four weeks" and "first four days" became "4-week" and "so far", and the en dashes the old texts had typed in week and day ranges became plain hyphens.
- Result: 56/56 texts PASS all checks (514 numbers; checks run: citation 514, metric 374, subject 314, period 238, direction 32, comparison 14); corpus 51/51 in Python and JS; 32 demos each FLAGGED by exactly their check; the edited-number self-test is FLAGGED.
- Verification:
  - Printed numbers of every old vs new text compared as multisets: only the two rounding ties above and the window/days counts that are now cited changed.
  - Number trace hand-checked for W28, W29 and W30 (headline, summary, 5 cards each): every figure lands on the metric, family, window and year its sentence names.
  - Negative tests: re-pointing one W29 citation to `l1w_aov_yoy_pct` makes 17 exit 1 (metric); flipping one corpus expectation makes 17 and `npm run verify` exit 1.
  - Browser (port 5201): W23, W29, W30 and all four demos for W23/W29/W30 hold back with the right check, key and source; tooltips and facts table checked; no console errors.
  - Two `./run_all.sh --clean` runs → 80 outputs byte-identical (79 before plus the number trace); raw md5 unchanged (1e0cdc15…).
- Surprises / errors: the old validator had passed W30 "29%" (Pillow Tabby receipts) as Tabby's +28.9% demand growth, and W28 "85" (returning Gen Z LY) as a stock count; Python's `format()` and the UI's `toFixed` disagreed on exact ties; `.gitignore` `.venv/` did not match a symlinked venv in a worktree.
- Next: the deck (handoff/PROMPT_D_deck.md) can quote the validator story; a live Ask answer would need placeholders to get the semantic checks.
