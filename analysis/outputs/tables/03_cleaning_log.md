# Cleaning log

| step | table | rows_before | rows_after | note |
|---|---|---|---|---|
| read Data sheet | lines | - | 3609 | header row 1, 17 cols |
| strip text whitespace | lines | 3609 | 3609 | 0 cells changed |
| flag DEMAND_AMT<=0 (returns/zero-value) | lines | 3609 | 3609 | 0 flagged; kept=all (no returns in extract) |
| flag UNIT_QTY<=0 | lines | 3609 | 3609 | 0 flagged |
| drop exact duplicate rows | lines | 3609 | 3609 | 0 dropped |
| derive YEAR, WK, WK_START, DAY_IN_WK | lines | 3609 | 3609 | all dates within Sun–Sat fiscal week |
| flag LY lines outside TY window | lines | 3609 | 3609 | TY as-of 2026-08-19 = W30 day 3 (0=Sun); 90 LY W30 lines after that day flagged IN_TY_WINDOW=False |
| join RETAIL median unit price per STYLE_DESC → PRICE_IDX | lines | 3609 | 3609 | many_to_one validated; 0 unmatched |
| derive customer/channel boolean flags | lines | 3609 | 3609 |  |
| write data/processed/lines.csv | lines | 3609 | 3609 | 32 cols |
| read Inventory sheet | inventory | - | 336 |  |
| validate inventory key (FY, WK, STYLE_GROUP) unique & families match Data | inventory | 336 | 336 | symmetric difference of family names: none |
| join PROD_CATEGORY/PROD_TYPE to inventory | inventory | 336 | 336 | 0 unmatched |
| write data/processed/inventory.csv | inventory | 336 | 336 |  |

## Reconciliation to raw
| measure | raw | processed | match |
|---|---|---|---|
| FY26 DEMAND_AMT | 564,027.83 | 564,027.83 | True |
| FY26 UNIT_QTY | 2,270.00 | 2,270.00 | True |
| FY25 DEMAND_AMT | 524,910.67 | 524,910.67 | True |
| FY25 UNIT_QTY | 2,205.00 | 2,205.00 | True |
| inventory ON_HAND_UNITS row-sum (checksum only; never a business metric) | 36665 | 36665 | True |

TY as-of date: 2026-08-19 (W30, day 3); TY last full week: W29