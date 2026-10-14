# Recommendation sizing (10_sizing.py)

TY PTD demand (sample) = $564,028 over 7.57 weeks → weekly run-rate $74,494

## R1 Protect Tabby franchise stock
Assumptions: demand continues at the L4W (W26–29) unit run-rate; receipts continue at the TY W24–29 average; lost units are not substituted; AUR = TY family AUR.

| family       |   eoh_W30 |   demand_units_wk |   receipts_wk_TY |   receipts_to_sales_LY |   weeks_to_stockout_at_TY_pace |   shortfall_units_4wk |   aur_TY |   demand_at_risk_4wk |   genz_new_at_risk_4wk |   units_needed_to_hold_LY_wos |
|:-------------|----------:|------------------:|-----------------:|-----------------------:|-------------------------------:|----------------------:|---------:|---------------------:|-----------------------:|------------------------------:|
| Tabby        |        82 |             44.25 |            13    |                   0.95 |                           2.62 |                 43    |   364.72 |             15682.9  |                   5.52 |                        229.2  |
| Pillow Tabby |        24 |             15    |             4.17 |                   0.85 |                           2.22 |                 19.33 |   381.49 |              7375.39 |                   2.55 |                         52.74 |

- 4-week demand at risk: $23,058 = 7.7% of the next 4 weeks' total demand (at TY run-rate)
- Units to restore LY weeks-of-supply: Tabby 229, Pillow Tabby 53
- Gen Z new customers at risk over 4 weeks: 8.1 (sample) vs TY Gen Z new run-rate 31.7/wk = 6.4% of 4-week Gen Z new

## R2 Halo apparel overstock to fund reallocation
Excess = W30 EOH − median family WOS (7.9) × L4W avg weekly units; valued at TY AUR (retail, not cost).

| STYLE_GROUP     |   eoh_W30_TY |   avg_units_wk |   wos_W30_TY_latest |   excess_units_vs_median_wos |   aur_TY |   excess_retail_value |
|:----------------|-------------:|---------------:|--------------------:|-----------------------------:|---------:|----------------------:|
| Tailored Jacket |          118 |            7.2 |                16.3 |                         60.7 |    261.4 |               15872.7 |
| Trench          |          152 |            9   |                16.9 |                         80.9 |    250.9 |               20295.3 |
| Knit Dress      |           90 |            4.2 |                21.2 |                         56.4 |    254   |               14331.5 |

- Total excess: 198 units, $50,500 retail value (vs Tabby-franchise gap to LY WOS of 282 units)
- Excess retail value = 9.0% of TY PTD demand

## R3 Convert the Gen Z acquisition wave into repeat customers (Insider at first purchase)
- TY new Gen Z: 240; Insider attach 17.1% vs new Millennial 23.4%; Insider share among Retained 71.4%
- Closing the gap to Millennial attach = +15 Gen Z Insiders in the sample period (+37% relative)
- TY returning Gen Z txns 158, AOV $304.47. Scenario (assumption: Insider enrolment + onboarding lifts returning Gen Z volume):

|   returning_genz_lift |   extra_txns_sample |   extra_demand_usd_sample |   pct_of_TY_demand |
|----------------------:|--------------------:|--------------------------:|-------------------:|
|                  0.05 |                 7.9 |                   2405.3  |             0.0043 |
|                  0.1  |                15.8 |                   4810.61 |             0.0085 |
|                  0.2  |                31.6 |                   9621.22 |             0.0171 |

- Not estimable from this file: Insider vs non-Insider repeat rate, time-to-second-purchase, CLV — data request.
