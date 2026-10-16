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
# Metrics-layer decisions (kept from the dashboard work)

D14–D15 and D17–D24 described the first web dashboard, now archived at git tag `archive/dashboard-v1`. D16 stays because those fields are still produced by `scripts/11_metrics.py`.

## D16 Metrics-layer additions and 6-decimal precision
- `11_metrics.py` adds `meta.counts`, `meta.week_dates_ty`, `meta.basis_alternatives` (+ `naive_gap_pts`, `ly_extra_days_sales`), `meta.data_quality`, `w30_daily` (M6 day segments, real values; the design mock's daily splits were placeholders), `stock_demand_shares` (M5; same definitions as script 08, asserts the 0.96 → 0.33 correlation in F11) and `growth_drill` (M3; shares of growth sum to 1, asserted).
- Fractions are now stored at 6 dp (was 4): at 4 dp, 1-dp percentages sit on rounding ties (the naive YoY rendered +7.4% vs +7.5% in FINDINGS; L1W W29 +12.6% vs +12.7%). Findings audit still 30/30; anomalies unchanged (71; 8 critical).
