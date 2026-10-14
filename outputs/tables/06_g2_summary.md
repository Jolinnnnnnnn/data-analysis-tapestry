# G2 summary (06_g2_genz.py) — PTD like-for-like basis

## 1. New & returning customers by generation
| generation   |   new_TY |   new_LY |   new_yoy_pct |   new_count_p |   new_share_of_all_new_TY |   new_share_of_all_new_LY |   share_of_new_p |   acq_rate_TY |   acq_rate_LY |   acq_rate_p |
|:-------------|---------:|---------:|--------------:|--------------:|--------------------------:|--------------------------:|-----------------:|--------------:|--------------:|-------------:|
| Gen Z        |      240 |      108 |         1.222 |         0     |                     0.407 |                     0.238 |            0     |         0.603 |         0.399 |        0     |
| Millennial   |      175 |      170 |         0.029 |         0.788 |                     0.297 |                     0.374 |            0.008 |         0.237 |         0.235 |        0.952 |
| Gen X        |      115 |      119 |        -0.034 |         0.794 |                     0.195 |                     0.262 |            0.01  |         0.247 |         0.26  |        0.648 |
| Boomer       |       60 |       57 |         0.053 |         0.782 |                     0.102 |                     0.126 |            0.226 |         0.265 |         0.238 |        0.503 |
| All          |      590 |      454 |         0.3   |         0     |                     1     |                     1     |          nan     |         0.323 |         0.269 |      nan     |

### Returning (retention proxy, D8) by generation
| generation   |   returning_TY |   returning_LY |   returning_yoy_pct |   returning_count_p |   returning_share_TY |   returning_share_LY |   returning_share_p |   retained_TY |   retained_LY |   reactivated_TY |   reactivated_LY |
|:-------------|---------------:|---------------:|--------------------:|--------------------:|---------------------:|---------------------:|--------------------:|--------------:|--------------:|-----------------:|-----------------:|
| Gen Z        |            158 |            163 |              -0.031 |               0.78  |                0.397 |                0.601 |               0     |           125 |           131 |               33 |               32 |
| Millennial   |            564 |            552 |               0.022 |               0.719 |                0.763 |                0.765 |               0.952 |           448 |           421 |              116 |              131 |
| Gen X        |            351 |            339 |               0.035 |               0.648 |                0.753 |                0.74  |               0.648 |           281 |           267 |               70 |               72 |
| Boomer       |            166 |            182 |              -0.088 |               0.391 |                0.735 |                0.762 |               0.503 |           127 |           141 |               39 |               41 |
| All          |           1239 |           1236 |               0.002 |               0.952 |                0.677 |                0.731 |             nan     |           981 |           960 |              258 |              276 |

### Insider (loyalty) attach among NEW customers by generation
| generation   |   new_insider_rate_TY |   new_insider_rate_LY |   new_insider_p |
|:-------------|----------------------:|----------------------:|----------------:|
| Gen Z        |                 0.171 |                 0.213 |           0.348 |
| Millennial   |                 0.234 |                 0.2   |           0.44  |
| Gen X        |                 0.191 |                 0.168 |           0.643 |
| Boomer       |                 0.167 |                 0.228 |           0.404 |
| All          |                 0.193 |                 0.198 |         nan     |

- Gen Z txns TY 398.0 vs LY 271.0 (+46.9%); of the +127.0 change, new = +132.0, returning = -5
- Total new customers TY 590.0 vs LY 454.0 (+30.0%); Gen Z accounts for 97% of the increase in new customers
- Non-Gen Z new customers TY 350.0 vs LY 346.0 (+1.2%, p=0.879)

## 2. Gen Z new customers by week (W30 = Sun–Wed both years)
|   WK |   new_LY |   new_TY |   genz_new_LY |   genz_new_TY |   genz_share_of_new_LY |   genz_share_of_new_TY |   genz_new_yoy_pct |   cum_genz_new_TY |   cum_genz_new_LY | weeks_ty_share_above_ly   |
|-----:|---------:|---------:|--------------:|--------------:|-----------------------:|-----------------------:|-------------------:|------------------:|------------------:|:--------------------------|
|   23 |       52 |       66 |            15 |            22 |                  0.288 |                  0.333 |              0.467 |                22 |                15 | True                      |
|   24 |       62 |       64 |            16 |            21 |                  0.258 |                  0.328 |              0.312 |                43 |                31 | True                      |
|   25 |       50 |       70 |            12 |            29 |                  0.24  |                  0.414 |              1.417 |                72 |                43 | True                      |
|   26 |       59 |       81 |            17 |            26 |                  0.288 |                  0.321 |              0.529 |                98 |                60 | True                      |
|   27 |       69 |       82 |            12 |            34 |                  0.174 |                  0.415 |              1.833 |               132 |                72 | True                      |
|   28 |       66 |       90 |            15 |            39 |                  0.227 |                  0.433 |              1.6   |               171 |                87 | True                      |
|   29 |       58 |       87 |            16 |            41 |                  0.276 |                  0.471 |              1.562 |               212 |               103 | True                      |
|   30 |       38 |       50 |             5 |            28 |                  0.132 |                  0.56  |              4.6   |               240 |               108 | True                      |
- Weeks where TY Gen Z share of new > LY: 8 of 8

## 4. What NEW Gen Z buy on first purchase vs other new customers (TY)

### PROD_TYPE
| segment   |   genz_new_n |   other_new_n |   genz_new_share |   other_new_share |   index_vs_other_new |     p |
|:----------|-------------:|--------------:|-----------------:|------------------:|---------------------:|------:|
| Core      |           75 |           121 |            0.312 |             0.346 |               90.393 | 0.4   |
| Evergreen |           68 |           102 |            0.283 |             0.291 |               97.222 | 0.831 |
| Hero      |           58 |            50 |            0.242 |             0.143 |              169.167 | 0.002 |
| Halo      |           39 |            77 |            0.162 |             0.22  |               73.864 | 0.084 |

### PROD_CATEGORY
| segment              |   genz_new_n |   other_new_n |   genz_new_share |   other_new_share |   index_vs_other_new |     p |
|:---------------------|-------------:|--------------:|-----------------:|------------------:|---------------------:|------:|
| 1.Womens Bag         |          106 |           127 |            0.442 |             0.363 |              121.719 | 0.054 |
| 2.Womens Accessories |           53 |            71 |            0.221 |             0.203 |              108.862 | 0.599 |
| 3.Womens Footwear    |           31 |            49 |            0.129 |             0.14  |               92.262 | 0.706 |
| 6.Mens               |           22 |            37 |            0.092 |             0.106 |               86.712 | 0.576 |
| 5.Womens Other       |           15 |            37 |            0.062 |             0.106 |               59.122 | 0.069 |
| 4.Womens Apparel     |           13 |            29 |            0.054 |             0.083 |               65.374 | 0.183 |

### SALES_CHANNEL
| segment   |   genz_new_n |   other_new_n |   genz_new_share |   other_new_share |   index_vs_other_new |     p |
|:----------|-------------:|--------------:|-----------------:|------------------:|---------------------:|------:|
| RETAIL    |          178 |           242 |            0.742 |             0.691 |              107.266 | 0.186 |
| OUTLET    |           62 |           108 |            0.258 |             0.309 |               83.719 | 0.186 |

### CHANNEL_DETAIL
| segment      |   genz_new_n |   other_new_n |   genz_new_share |   other_new_share |   index_vs_other_new |     p |
|:-------------|-------------:|--------------:|-----------------:|------------------:|---------------------:|------:|
| Retail Store |          161 |           220 |            0.671 |             0.629 |              106.723 | 0.292 |
| eComm        |           79 |           130 |            0.329 |             0.371 |               88.622 | 0.292 |

### GEO_REGION
| segment       |   genz_new_n |   other_new_n |   genz_new_share |   other_new_share |   index_vs_other_new |     p |
|:--------------|-------------:|--------------:|-----------------:|------------------:|---------------------:|------:|
| North America |          119 |           203 |            0.496 |             0.58  |               85.489 | 0.044 |
| Europe        |           60 |            59 |            0.25  |             0.169 |              148.305 | 0.015 |
| Greater China |           39 |            69 |            0.162 |             0.197 |               82.428 | 0.285 |
| Japan         |           22 |            19 |            0.092 |             0.054 |              168.86  | 0.079 |

### STYLE_GROUP
| segment         |   genz_new_n |   other_new_n |   genz_new_share |   other_new_share |   index_vs_other_new |     p |
|:----------------|-------------:|--------------:|-----------------:|------------------:|---------------------:|------:|
| Tabby           |           43 |            38 |            0.179 |             0.109 |              165.022 | 0.014 |
| Willow          |           19 |            36 |            0.079 |             0.103 |               76.968 | 0.331 |
| Brooklyn        |           18 |            21 |            0.075 |             0.06  |              125     | 0.471 |
| Wallet          |           15 |            24 |            0.062 |             0.069 |               91.146 | 0.771 |
| Pillow Tabby    |           15 |            12 |            0.062 |             0.034 |              182.292 | 0.107 |
| Card Case       |           14 |            21 |            0.058 |             0.06  |               97.222 | 0.933 |
| Belt Bag        |           13 |            13 |            0.054 |             0.037 |              145.833 | 0.322 |
| Mens Bag        |           11 |            13 |            0.046 |             0.037 |              123.397 | 0.6   |
| Rogue           |           11 |            20 |            0.046 |             0.057 |               80.208 | 0.545 |
| Wristlet        |           11 |            13 |            0.046 |             0.037 |              123.397 | 0.6   |
| Loafer          |           11 |            15 |            0.046 |             0.043 |              106.944 | 0.863 |
| Lowline Sneaker |           10 |            18 |            0.042 |             0.051 |               81.019 | 0.584 |
| Sculpted Sandal |           10 |            16 |            0.042 |             0.046 |               91.146 | 0.814 |
| Tailored Jacket |            6 |            12 |            0.025 |             0.034 |               72.917 | 0.519 |
| Fragrance       |            6 |            10 |            0.025 |             0.029 |               87.5   | 0.793 |
| Mens Footwear   |            6 |            10 |            0.025 |             0.029 |               87.5   | 0.793 |
| Mens SLG        |            5 |            14 |            0.021 |             0.04  |               52.083 | 0.195 |
| Jewelry         |            5 |            12 |            0.021 |             0.034 |               60.764 | 0.337 |
| Trench          |            5 |            10 |            0.021 |             0.029 |               72.917 | 0.557 |
| Charms          |            4 |            15 |            0.017 |             0.043 |               38.889 | 0.077 |
| Knit Dress      |            2 |             7 |            0.008 |             0.02  |               41.667 | 0.256 |

### Gen Z NEW customers by first-purchase family, TY vs LY (sorted by change)
| STYLE_GROUP     |   LY |   TY |   chg |
|:----------------|-----:|-----:|------:|
| Tabby           |   19 |   43 |    24 |
| Card Case       |    2 |   14 |    12 |
| Pillow Tabby    |    3 |   15 |    12 |
| Brooklyn        |    7 |   18 |    11 |
| Wallet          |    5 |   15 |    10 |
| Mens Bag        |    1 |   11 |    10 |
| Loafer          |    3 |   11 |     8 |
| Sculpted Sandal |    3 |   10 |     7 |
| Rogue           |    5 |   11 |     6 |
| Belt Bag        |    8 |   13 |     5 |
| Willow          |   14 |   19 |     5 |
| Lowline Sneaker |    5 |   10 |     5 |
| Tailored Jacket |    2 |    6 |     4 |
| Wristlet        |    7 |   11 |     4 |
| Mens SLG        |    2 |    5 |     3 |
| Trench          |    2 |    5 |     3 |
| Mens Footwear   |    3 |    6 |     3 |
| Jewelry         |    3 |    5 |     2 |
| Fragrance       |    4 |    6 |     2 |
| Charms          |    5 |    4 |    -1 |
| Knit Dress      |    5 |    2 |    -3 |

### Gen Z NEW by PROD_TYPE TY vs LY
| PROD_TYPE   |   LY |   TY |   yoy_pct |
|:------------|-----:|-----:|----------:|
| Core        |   31 |   75 |     1.419 |
| Evergreen   |   35 |   68 |     0.943 |
| Halo        |   20 |   39 |     0.95  |
| Hero        |   22 |   58 |     1.636 |

### Gen Z NEW by region TY vs LY
| GEO_REGION    |   LY |   TY |   yoy_pct |     p |
|:--------------|-----:|-----:|----------:|------:|
| Europe        |   18 |   60 |     2.333 | 0     |
| Greater China |   23 |   39 |     0.696 | 0.042 |
| Japan         |    4 |   22 |     4.5   | 0     |
| North America |   63 |  119 |     0.889 | 0     |

### Gen Z NEW by channel TY vs LY
|                            |   LY |   TY |   yoy_pct |
|:---------------------------|-----:|-----:|----------:|
| ('OUTLET', 'Retail Store') |   21 |   41 |     0.952 |
| ('OUTLET', 'eComm')        |   10 |   21 |     1.1   |
| ('RETAIL', 'Retail Store') |   49 |  120 |     1.449 |
| ('RETAIL', 'eComm')        |   28 |   58 |     1.071 |

## 6. Value of NEW Gen Z vs other NEW customers (bootstrap 95% CI on difference)
| YEAR   | metric        |   new_genz |   other_new |   diff |   ci_lo |   ci_hi |     p |   n_genz |   n_other |
|:-------|:--------------|-----------:|------------:|-------:|--------:|--------:|------:|---------:|----------:|
| TY     | AOV $         |    332.094 |     308.234 | 23.859 | -16.921 |  63.906 | 0.236 |      240 |       350 |
| TY     | UPT           |      1.262 |       1.271 | -0.009 |  -0.101 |   0.088 | 0.836 |      240 |       350 |
| TY     | AUR $         |    261.755 |     239.74  | 22.014 |   0.883 |  42.952 | 0.041 |      240 |       350 |
| TY     | price index   |      0.937 |       0.907 |  0.031 |  -0.016 |   0.079 | 0.204 |      240 |       350 |
| TY     | outlet share  |      0.258 |       0.309 | -0.05  |  -0.12  |   0.023 | 0.192 |      240 |       350 |
| TY     | eComm share   |      0.329 |       0.371 | -0.042 |  -0.121 |   0.035 | 0.29  |      240 |       350 |
| TY     | Insider share |      0.171 |       0.209 | -0.038 |  -0.101 |   0.026 | 0.261 |      240 |       350 |
| LY     | AOV $         |    300.09  |     296.527 |  3.563 | -39.335 |  48.142 | 0.906 |      108 |       346 |
| LY     | UPT           |      1.213 |       1.249 | -0.036 |  -0.147 |   0.079 | 0.518 |      108 |       346 |
| LY     | AUR $         |    252.791 |     237.71  | 15.081 | -11.591 |  42.48  | 0.282 |      108 |       346 |
| LY     | price index   |      0.913 |       0.871 |  0.042 |  -0.013 |   0.096 | 0.139 |      108 |       346 |
| LY     | outlet share  |      0.287 |       0.295 | -0.008 |  -0.103 |   0.089 | 0.869 |      108 |       346 |
| LY     | eComm share   |      0.352 |       0.353 | -0.001 |  -0.102 |   0.103 | 0.97  |      108 |       346 |
| LY     | Insider share |      0.213 |       0.194 |  0.019 |  -0.065 |   0.109 | 0.656 |      108 |       346 |
| Both   | AOV $         |    322.161 |     302.414 | 19.747 |  -9.496 |  49.171 | 0.174 |      348 |       696 |
| Both   | UPT           |      1.247 |       1.26  | -0.013 |  -0.083 |   0.057 | 0.716 |      348 |       696 |
| Both   | AUR $         |    258.973 |     238.731 | 20.242 |   3.497 |  37.038 | 0.016 |      348 |       696 |
| Both   | price index   |      0.93  |       0.889 |  0.041 |   0.006 |   0.076 | 0.019 |      348 |       696 |
| Both   | outlet share  |      0.267 |       0.302 | -0.034 |  -0.092 |   0.023 | 0.234 |      348 |       696 |
| Both   | eComm share   |      0.336 |       0.362 | -0.026 |  -0.086 |   0.034 | 0.417 |      348 |       696 |
| Both   | Insider share |      0.184 |       0.201 | -0.017 |  -0.069 |   0.033 | 0.51  |      348 |       696 |

- TY weighted: new Gen Z AOV $332.09, AUR $263.04, UPT 1.262 | other new AOV $308.23, AUR $242.43, UPT 1.271
- TY all-cohort Gen Z AOV minus non-Gen Z AOV: $16.29 [-8.20, 41.80], p=0.191
- TY Gen Z returning AOV minus Gen Z new AOV: $-27.62 [-69.94, 15.39], p=0.206

AOV by cohort status (all generations):
| YEAR   |    New |   Reactivated |   Retained |
|:-------|-------:|--------------:|-----------:|
| LY     | 297.37 |        286.28 |     297.69 |
| TY     | 317.94 |        321    |     299.31 |

TY AOV & n by generation × cohort:
| CUST_AGE_GROUP   |   ('mean', 'New') |   ('mean', 'Reactivated') |   ('mean', 'Retained') |   ('size', 'New') |   ('size', 'Reactivated') |   ('size', 'Retained') |
|:-----------------|------------------:|--------------------------:|-----------------------:|------------------:|--------------------------:|-----------------------:|
| Boomer           |             286.9 |                     317.5 |                  302.7 |                60 |                        39 |                    127 |
| Gen X            |             301.6 |                     317.8 |                  277.7 |               115 |                        70 |                    281 |
| Gen Z            |             332.1 |                     292.4 |                  307.7 |               240 |                        33 |                    125 |
| Millennial       |             319.9 |                     332.3 |                  309.6 |               175 |                       116 |                    448 |

## 7. Insider attach of NEW customers (TY) by segment — Gen Z vs other
| dimension      | segment       |   genz_new_n |   genz_new_insider_rate |   other_new_n |   other_new_insider_rate |     p |
|:---------------|:--------------|-------------:|------------------------:|--------------:|-------------------------:|------:|
| CHANNEL_DETAIL | Retail Store  |          161 |                   0.193 |           220 |                    0.218 | 0.542 |
| CHANNEL_DETAIL | eComm         |           79 |                   0.127 |           130 |                    0.192 | 0.217 |
| SALES_CHANNEL  | OUTLET        |           62 |                   0.097 |           108 |                    0.231 | 0.029 |
| SALES_CHANNEL  | RETAIL        |          178 |                   0.197 |           242 |                    0.198 | 0.965 |
| GEO_REGION     | Europe        |           60 |                   0.2   |            59 |                    0.136 | 0.347 |
| GEO_REGION     | Greater China |           39 |                   0.051 |            69 |                    0.217 | 0.023 |
| GEO_REGION     | Japan         |           22 |                   0.182 |            19 |                    0.105 | 0.489 |
| GEO_REGION     | North America |          119 |                   0.193 |           203 |                    0.236 | 0.367 |

## 8. TY Gen Z new customers: W23–26 vs W27–30 (W30 = 4 days) by segment
| dimension      | segment       |   W23_26 |   W27_30 |   chg |
|:---------------|:--------------|---------:|---------:|------:|
| GEO_REGION     | Europe        |       23 |       37 |    14 |
| GEO_REGION     | Greater China |       20 |       19 |    -1 |
| GEO_REGION     | Japan         |        9 |       13 |     4 |
| GEO_REGION     | North America |       46 |       73 |    27 |
| CHANNEL_DETAIL | Retail Store  |       60 |      101 |    41 |
| CHANNEL_DETAIL | eComm         |       38 |       41 |     3 |
| SALES_CHANNEL  | OUTLET        |       29 |       33 |     4 |
| SALES_CHANNEL  | RETAIL        |       69 |      109 |    40 |
| PROD_TYPE      | Core          |       29 |       46 |    17 |
| PROD_TYPE      | Evergreen     |       27 |       41 |    14 |
| PROD_TYPE      | Halo          |       16 |       23 |     7 |
| PROD_TYPE      | Hero          |       26 |       32 |     6 |

Figures: outputs/figures/g2_new_customers_by_generation_ty_vs_ly.png, outputs/figures/g2_genz_share_of_new_by_week.png, outputs/figures/g2_genz_first_purchase_family_mix.png, outputs/figures/g2_new_vs_returning_yoy_by_generation.png