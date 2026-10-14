# Data profile

Data rows: 3609, cols: 17; Inventory rows: 336

## Data dtypes / nulls / distinct
| col            | dtype          |   nulls |   blank_str |   n_distinct |
|:---------------|:---------------|--------:|------------:|-------------:|
| TXN_DT         | datetime64[ns] |       0 |           0 |          109 |
| FISCAL_YR      | object         |       0 |           0 |            2 |
| FISCAL_WK      | object         |       0 |           0 |           16 |
| GEO_REGION     | object         |       0 |           0 |            4 |
| SALES_CHANNEL  | object         |       0 |           0 |            2 |
| CHANNEL_DETAIL | object         |       0 |           0 |            2 |
| PROD_CATEGORY  | object         |       0 |           0 |            6 |
| STYLE_GROUP    | object         |       0 |           0 |           21 |
| STYLE_DESC     | object         |       0 |           0 |           36 |
| PROD_TYPE      | object         |       0 |           0 |            4 |
| CUST_ID        | int64          |       0 |           0 |         3600 |
| COHORT_STATUS  | object         |       0 |           0 |            3 |
| CUST_AGE_GROUP | object         |       0 |           0 |            4 |
| INSIDER_FLAG   | object         |       0 |           0 |            2 |
| DEMAND_AMT     | float64        |       0 |           0 |         3478 |
| UNIT_QTY       | int64          |       0 |           0 |            3 |
| TXN_ID         | object         |       0 |           0 |         3609 |

### FISCAL_YR
| FISCAL_YR   |   rows |
|:------------|-------:|
| FY26        |   1829 |
| FY25        |   1780 |

### GEO_REGION
| GEO_REGION    |   rows |
|:--------------|-------:|
| North America |   1966 |
| Europe        |    739 |
| Greater China |    667 |
| Japan         |    237 |

### SALES_CHANNEL
| SALES_CHANNEL   |   rows |
|:----------------|-------:|
| RETAIL          |   2525 |
| OUTLET          |   1084 |

### CHANNEL_DETAIL
| CHANNEL_DETAIL   |   rows |
|:-----------------|-------:|
| Retail Store     |   2320 |
| eComm            |   1289 |

### PROD_CATEGORY
| PROD_CATEGORY        |   rows |
|:---------------------|-------:|
| 1.Womens Bag         |   1444 |
| 2.Womens Accessories |    723 |
| 3.Womens Footwear    |    450 |
| 6.Mens               |    347 |
| 5.Womens Other       |    335 |
| 4.Womens Apparel     |    310 |

### PROD_TYPE
| PROD_TYPE   |   rows |
|:------------|-------:|
| Core        |   1108 |
| Evergreen   |   1079 |
| Halo        |    791 |
| Hero        |    631 |

### COHORT_STATUS
| COHORT_STATUS   |   rows |
|:----------------|-------:|
| Retained        |   1987 |
| New             |   1072 |
| Reactivated     |    550 |

### CUST_AGE_GROUP
| CUST_AGE_GROUP   |   rows |
|:-----------------|-------:|
| Millennial       |   1496 |
| Gen X            |    953 |
| Gen Z            |    685 |
| Boomer           |    475 |

### INSIDER_FLAG
| INSIDER_FLAG   |   rows |
|:---------------|-------:|
| Y              |   1852 |
| N              |   1757 |

### UNIT_QTY
|   UNIT_QTY |   rows |
|-----------:|-------:|
|          1 |   2918 |
|          2 |    516 |
|          3 |    175 |

## Numeric ranges
|            |   count |      mean |        std |   min |      1% |     5% |    50% |     95% |    99% |     max |
|:-----------|--------:|----------:|-----------:|------:|--------:|-------:|-------:|--------:|-------:|--------:|
| DEMAND_AMT |    3609 | 301.729   | 217.144    | 27.86 | 49.8716 | 79.888 | 249.84 | 701.576 | 1142.6 | 1723.21 |
| UNIT_QTY   |    3609 |   1.23996 |   0.528615 |  1    |  1      |  1     |   1    |   2     |    3   |    3    |

- DEMAND_AMT <= 0: 0; ==0: 0; <0: 0
- UNIT_QTY <= 0: 0; non-integer: 0

### Unit price by channel
|                    |   count |    mean |      std |   min |     25% |     50% |     75% |     max |
|:-------------------|--------:|--------:|---------:|------:|--------:|--------:|--------:|--------:|
| ('FY25', 'OUTLET') |     550 | 165.655 |  77.8866 | 27.86 | 102.7   | 154.79  | 224.412 | 329.84  |
| ('FY25', 'RETAIL') |    1230 | 271.511 | 124.854  | 45.4  | 169.778 | 263.445 | 366.474 | 532.89  |
| ('FY26', 'OUTLET') |     534 | 176.798 |  84.3746 | 32.85 | 107.619 | 167.33  | 239.998 | 357.71  |
| ('FY26', 'RETAIL') |    1295 | 278.013 | 137.799  | 45.21 | 161.575 | 256.13  | 382.22  | 574.403 |

## Week coverage
- FISCAL_WK prefix == FISCAL_YR mismatches: 0
| FISCAL_YR   |   wk |   rows | dt_min     | dt_max     | dow_min   |
|:------------|-----:|-------:|:-----------|:-----------|:----------|
| FY25        |   23 |    211 | 2025-06-29 | 2025-07-05 | Tuesday   |
| FY25        |   24 |    241 | 2025-07-06 | 2025-07-12 | Monday    |
| FY25        |   25 |    200 | 2025-07-13 | 2025-07-19 | Monday    |
| FY25        |   26 |    229 | 2025-07-20 | 2025-07-26 | Saturday  |
| FY25        |   27 |    224 | 2025-07-27 | 2025-08-02 | Wednesday |
| FY25        |   28 |    235 | 2025-08-03 | 2025-08-09 | Friday    |
| FY25        |   29 |    218 | 2025-08-10 | 2025-08-16 | Tuesday   |
| FY25        |   30 |    222 | 2025-08-17 | 2025-08-23 | Monday    |
| FY26        |   23 |    225 | 2026-06-28 | 2026-07-04 | Sunday    |
| FY26        |   24 |    234 | 2026-07-05 | 2026-07-11 | Monday    |
| FY26        |   25 |    204 | 2026-07-12 | 2026-07-18 | Saturday  |
| FY26        |   26 |    264 | 2026-07-19 | 2026-07-25 | Thursday  |
| FY26        |   27 |    249 | 2026-07-26 | 2026-08-01 | Wednesday |
| FY26        |   28 |    256 | 2026-08-02 | 2026-08-08 | Friday    |
| FY26        |   29 |    250 | 2026-08-09 | 2026-08-15 | Friday    |
| FY26        |   30 |    147 | 2026-08-16 | 2026-08-19 | Wednesday |

- Date range FY26: 2026-06-28 – 2026-08-19
- Date range FY25: 2025-06-29 – 2025-08-23

### TXN_DT calendar year vs FISCAL_YR
| FISCAL_YR   |   2025 |   2026 |
|:------------|-------:|-------:|
| FY25        |   1780 |      0 |
| FY26        |      0 |   1829 |

- Dates mapped to >1 fiscal week: 0

## Transaction grain checks
- Distinct TXN_ID: 3609; rows: 3609; lines/txn mean 1.000
Lines per TXN_ID:
|   lines |   txns |
|--------:|-------:|
|       1 |   3609 |

TXN_IDs with >1 distinct value of attribute (should be 0 if txn-level attr):
| attr           |   txns_inconsistent |
|:---------------|--------------------:|
| CUST_ID        |                   0 |
| TXN_DT         |                   0 |
| FISCAL_WK      |                   0 |
| GEO_REGION     |                   0 |
| SALES_CHANNEL  |                   0 |
| CHANNEL_DETAIL |                   0 |
| COHORT_STATUS  |                   0 |
| CUST_AGE_GROUP |                   0 |
| INSIDER_FLAG   |                   0 |

- TXN_ID prefix year vs FISCAL_YR mismatches: 0
- Exact duplicate rows: 0
- Duplicate (TXN_ID, STYLE_DESC) pairs: 0

## Customer checks
- Distinct CUST_ID: 3600; FY26: 1827; FY25: 1779
- CUST_IDs in both years: 6
- CUST_ID with >1 CUST_AGE_GROUP: 5; >1 INSIDER_FLAG: 6; >1 GEO_REGION: 5
- CUST_ID with >1 TXN_ID: 9
TXNs per customer:
|   txns |   customers |
|-------:|------------:|
|      1 |        3591 |
|      2 |           9 |
- CUST_ID range: 100131 – 999840; non-positive/sentinel (<=0 or 999999-like): 0

### COHORT_STATUS per customer: customers with 'New' on multiple TXNs
- customers with New on >1 distinct txn: 3 of 1069
- 'New' lines not on customer's first observed date: 4
- 'Retained/Reactivated' lines on customer's first observed date: 2532

## Hierarchy checks
- STYLE_GROUP -> PROD_CATEGORY many-to-one violations: 0
- STYLE_GROUP -> PROD_TYPE violations: 0
- STYLE_DESC -> STYLE_GROUP violations: 0
| PROD_CATEGORY        | STYLE_GROUP     | PROD_TYPE   |   styles |   rows |
|:---------------------|:----------------|:------------|---------:|-------:|
| 1.Womens Bag         | Brooklyn        | Evergreen   |        2 |    251 |
| 1.Womens Bag         | Pillow Tabby    | Hero        |        2 |    135 |
| 1.Womens Bag         | Rogue           | Halo        |        2 |    237 |
| 1.Womens Bag         | Tabby           | Hero        |        3 |    496 |
| 1.Womens Bag         | Willow          | Core        |        3 |    325 |
| 2.Womens Accessories | Belt Bag        | Evergreen   |        2 |    173 |
| 2.Womens Accessories | Card Case       | Core        |        2 |    176 |
| 2.Womens Accessories | Wallet          | Core        |        2 |    184 |
| 2.Womens Accessories | Wristlet        | Core        |        2 |    190 |
| 3.Womens Footwear    | Loafer          | Evergreen   |        1 |    146 |
| 3.Womens Footwear    | Lowline Sneaker | Evergreen   |        1 |    162 |
| 3.Womens Footwear    | Sculpted Sandal | Halo        |        2 |    142 |
| 4.Womens Apparel     | Knit Dress      | Halo        |        1 |     98 |
| 4.Womens Apparel     | Tailored Jacket | Halo        |        1 |     99 |
| 4.Womens Apparel     | Trench          | Halo        |        1 |    113 |
| 5.Womens Other       | Charms          | Evergreen   |        2 |    130 |
| 5.Womens Other       | Fragrance       | Evergreen   |        1 |    103 |
| 5.Womens Other       | Jewelry         | Halo        |        2 |    102 |
| 6.Mens               | Mens Bag        | Core        |        2 |    126 |
| 6.Mens               | Mens Footwear   | Evergreen   |        1 |    114 |
| 6.Mens               | Mens SLG        | Core        |        1 |    107 |

PROD_TYPE values per STYLE_GROUP (if multiple):
Series([], )

## Inventory
- dtypes: {'FISCAL_YR': 'object', 'FISCAL_WK': 'object', 'STYLE_GROUP': 'object', 'ON_HAND_UNITS': 'int64'}; nulls: 0
- ON_HAND_UNITS: min 24, max 290, <=0: 0
| FISCAL_YR   |   23 |   24 |   25 |   26 |   27 |   28 |   29 |   30 |
|:------------|-----:|-----:|-----:|-----:|-----:|-----:|-----:|-----:|
| FY25        |   21 |   21 |   21 |   21 |   21 |   21 |   21 |   21 |
| FY26        |   21 |   21 |   21 |   21 |   21 |   21 |   21 |   21 |
- duplicate (FISCAL_WK, STYLE_GROUP): 0
- STYLE_GROUP in Data not in Inventory: []
- STYLE_GROUP in Inventory not in Data: []
- whitespace/case variants: []
- Inventory weeks: ['FY25 W23', 'FY25 W24', 'FY25 W25', 'FY25 W26', 'FY25 W27', 'FY25 W28', 'FY25 W29', 'FY25 W30', 'FY26 W23', 'FY26 W24', 'FY26 W25', 'FY26 W26', 'FY26 W27', 'FY26 W28', 'FY26 W29', 'FY26 W30']
- Data weeks: ['FY25 W23', 'FY25 W24', 'FY25 W25', 'FY25 W26', 'FY25 W27', 'FY25 W28', 'FY25 W29', 'FY25 W30', 'FY26 W23', 'FY26 W24', 'FY26 W25', 'FY26 W26', 'FY26 W27', 'FY26 W28', 'FY26 W29', 'FY26 W30']