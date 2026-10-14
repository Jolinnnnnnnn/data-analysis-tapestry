# PROMPTS — AI-assisted steps and how each was verified

Tooling: Claude Code (Claude Opus 5.5) acting as an autonomous analyst in this directory. Python 3.9 + pandas/openpyxl/matplotlib in `.venv`. The master prompt is the take-home brief ("autonomous senior analytics consultant… data structure + analysis ONLY"), saved as the session's initial instruction.

| # | Step | Prompt / instruction given to the AI (summary) | Output | Verification |
|---|---|---|---|---|
| P1 | Workbook inventory | "Inventory every sheet: hidden sheets, header offsets, merged cells, notes; read Column Definitions in full" | scripts/01_inventory_workbook.py → outputs/tables/01_workbook_inventory.md | openpyxl max_row (3,610 incl. header) = pandas rows (3,609) + 1; 336 inventory rows = 21 families × 8 wks × 2 yrs |
| P2 | Data profile | "Profile types, nulls, distincts, ranges, week coverage, grain, customer and hierarchy integrity" | scripts/02_profile.py → outputs/tables/02_profile.md | Hand-inspected first 12 raw rows vs parsed; week date ranges checked to be Sun–Sat |
| P3 | Cleaning with logged row counts | "Write a cleaning script that logs every transformation with before/after row counts" | scripts/03_clean.py → data/processed/lines.csv, inventory.csv, outputs/tables/03_cleaning_log.md | Asserts: no row loss, many_to_one joins validated; DEMAND_AMT & UNIT_QTY by FY reconcile to raw exactly |
| P4 | CUST_ID collision hypothesis | AI noticed 3,600 IDs on 3,609 lines and proposed testing "are repeats just random-ID collisions?" | scripts/04_identity_checks.py → outputs/tables/04_identity_checks.md | Closed-form expectation (C(n,2)/N = 7.23) cross-checked by 5,000-run Monte Carlo (mean 7.26); attribute-agreement test |
| P5 | G1 KPI windows + decomposition | "TY vs LY and trailing 1/4 weeks; decompose YoY into customers × frequency × AOV; segment contribution" | scripts/_common.py (single KPI definition), scripts/05_g1_performance.py | Log-decomposition terms assert-sum to total; segment contributions sum to total per dimension; PTD LY rows = 1,780 − 90 |
| P6 | G2 Gen Z deep dive | "New customers by generation, Gen Z share over time, first-purchase mix, retention proxies, value vs other new; significance on every comparison" | scripts/06_g2_genz.py | Generation rows sum to All (240+175+115+60=590); weekly cumsum = PTD totals; z-tests + bootstrap CIs |
| P7 | G3 product scorecard | "YoY ranking with min-volume, contribution, Gen Z over-index, winner rule" | scripts/07_g3_products.py | share_of_growth sums to 1.0 across families; threshold documented (D12) |
| P8 | G4 inventory | "WOS, sell-through, over/understock; never sum snapshots across weeks" | scripts/08_g4_inventory.py | one_to_one join validated (336 rows); AI-proposed scale check (implied receipts never negative) used to validate D9 |
| P9 | Adversarial challenge | "For each major finding test alternative definition, single-outlier, mix effect; downgrade fragile ones" | scripts/09_challenge.py → 09_sensitivity.md | Two independent tests per key claim (z-test + bootstrap/permutation); F8 AUR premium downgraded as a result |
| P10 | Impact sizing | "Quantify expected impact of each draft recommendation with explicit assumptions" | scripts/10_sizing.py | Inputs read from 08 outputs, not retyped; hand-derived ratios moved into script after a ground-rule check |
| P11 | Metrics layer | "metrics.json: every dashboard metric, indexed by fiscal week, app does no math" | scripts/11_metrics.py | In-script asserts: headline = raw sums; weekly sums = PTD; L4W W29 = script 05 value; weekly_facts = trailing values |
| P12 | Anomaly rules | "Deterministic rules: YoY/WoW thresholds, WOS out of band, Gen Z new drops" | scripts/12_anomalies.py | Reviewed all 91 initial alerts by hand → found truncated-window false positives → added full-window guard (D13) |
| P13 | Docs | "Data dictionary + metrics schema generated from data" | scripts/13_docs.py | Caught & fixed FISCAL_WK definition collision between sheets |
| P14 | Findings audit (accuracy design) | "Re-derive every headline number in FINDINGS.md from metrics.json and require it verbatim" | scripts/14_verify_findings.py → 14_findings_audit.md | 30/30 PASS after it caught one missing figure (Tabby 59% share of growth) |
| P15 | Chart QA | AI rendered every PNG and inspected it visually (label collisions, legend errors, grid over bars, hard-coded numbers in titles) | outputs/figures/*.png | Fixed: W30 label overlap, WOS legend colour bug, hard-coded "+12.8%" and "72%" titles → now computed |

## Prompting approach (for the deck)
- One master instruction, then an explicit loop: ORIENT (read NOTES/HISTORY/QUESTIONS) → PLAN → ACT (numbered script) → VERIFY (reconcile, second method) → RECORD → REFLECT.
- Memory lives on disk (NOTES.md, HISTORY.md, FINDINGS.md, DECISIONS.md), so the work survives context loss.
- Guardrails: raw file read-only (chmod 444); every number from a saved script; run_all.sh rebuilds from scratch; a findings audit re-derives quoted numbers.
- Where the AI added judgment beyond the brief: CUST_ID collision test (P4), implied-receipts scale check (P8), mix-standardised Gen Z share (P9), full-window anomaly guard (P12).
