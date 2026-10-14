# QUESTIONS — prioritized hypothesis backlog
Status: [ ] open · [x] resolved (→ where) · [~] dropped (reason)

## Phase A — structure (all must resolve in DECISIONS.md)
- [x] QA1 Sheet inventory: hidden sheets, header offsets, merged cells, notes → D1
- [x] QA2 Column Definitions: ambiguous / mismatching definitions → D2
- [x] QA3 TY/LY representation & YoY basis (TY partial?) → D3
- [x] QA4 Line → transaction → customer rollup; returns, negatives, discounts, zero lines → D4
- [x] QA5 Customer identity: ID present? anonymous/null share? → D5, F14
- [x] QA6 "New customer" definition & left-censoring → D6
- [x] QA7 Gen Z definition: field, cutoff, missing values → D7
- [x] QA8 Retention definition → D8
- [x] QA9 Inventory: snapshot handling, join key, family name match → D9
- [x] QA10 Trailing-week window definition → D10

## Phase B — analysis
### G1 Performance
- [x] Q1.1 Sales, units, txns, customers, AOV, UPT: TY vs LY, trailing 1w & 4w vs LY → F1 (05)
- [x] Q1.2 Weekly TY/LY trend → F1, F3 (05)
- [x] Q1.3 Decompose YoY into customers × frequency × AOV → F1 (05)
- [x] Q1.4 Mix: channel / region / category drivers of YoY → F1, F9, F10 (05, 07)
### G2 Gen Z acquisition & retention (deepest)
- [x] Q2.1 New customer count & share by generation, TY vs LY; Gen Z share of new over time → F4, F5 (06)
- [x] Q2.2 Gen Z first purchase: products, families, channel, region → F8 (06)
- [~] Q2.3 Repeat/retention rates by generation & by first-purchase product — DROPPED as behavioural metric (CUST_ID non-durable, D5/F14); replaced by COHORT_STATUS proxies → F6
- [x] Q2.4 Value of new Gen Z vs other new: AOV, units, discount dependence (outlet, price index), Insider → F7, F8 (06, 09)
- [x] Q2.5 Is Gen Z growth statistically distinguishable from noise at this sample size? → F4, F5 (09)
### G3 Winning products
- [x] Q3.1 YoY growth ranking with min-volume threshold; contribution to growth → F9, F10 (07)
- [x] Q3.2 Gen Z over-index by product → F8, F9 (07)
- [~] Q3.3 Products that acquire new customers who come back — not measurable behaviourally (D5). Proxy: genz_new_mix_index AND genz_ret_mix_index ≥120 (07_g3_family_scorecard.csv): Tabby (165/122), Pillow Tabby (182/159), Mens Bag (123/211) — tentative
### G4 Inventory
- [x] Q4.1 Weeks of supply & sell-through by family, TY vs LY → F11 (08)
- [x] Q4.2 Overstock (high WOS, declining sales) / understock (low WOS, rising sales), esp. G3 winners & Gen Z-heavy → F11, F12 (08)
### Surprises / challenge
- [x] QS1 Data errors, impossible values, structural breaks, mix shifts → F2, F5, F12, F13, F14
- [x] QS2 Robustness of each major finding (alt definition, outliers, mix) → 09_sensitivity.md

## New hypotheses (from REFLECT steps)
- [x] QN1 Is the Tabby stock decline a replenishment cut or a demand surge? → implied receipts (08): receipts cut -62% YoY → F12
- [x] QN2 Are inventory and sample sales on the same scale? → implied receipts never negative (08) → D9
- [x] QN3 Is Gen Z growth a product-mix or region-mix artifact? → no (09) → F4
- [x] QN4 Is the AUR premium of new Gen Z a within-product effect? → mostly mix (09) → F8 downgraded
- [ ] QN5 What triggered the W27+ Gen Z acceleration? — needs marketing calendar / social data (not in file) → data request
- [x] QN6 Is W29's -18.8% WoW a traffic problem? → no, AOV normalization after W28 spike → F3
- [ ] QN7 Does Gen Z under-enrolment in Insider persist by channel (store vs eComm)? → check in next iteration
