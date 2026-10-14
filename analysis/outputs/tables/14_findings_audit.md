# FINDINGS audit (14_verify_findings.py)

Each value is re-derived from metrics.json / output tables and must appear verbatim in FINDINGS.md.

| finding | check | expected string | result |
|---|---|---|---|
| F1 | PTD demand YoY | `+12.8%` | PASS |
| F1 | PTD txns YoY | `+8.2%` | PASS |
| F1 | TY demand $ | `$564,028` | PASS |
| F1 | LY demand $ | `$499,804` | PASS |
| F1 | L1W W29 YoY | `+12.7%` | PASS |
| F1 | L4W YoY | `+13.2%` | PASS |
| F1 | WTD W30 YoY | `+21.7%` | PASS |
| F2 | naive all-rows YoY | `+7.5%` | PASS |
| F3 | W29 WoW | `-18.8%` | PASS |
| F4 | Gen Z new TY | `240 vs 108` | PASS |
| F4 | Gen Z new YoY | `+122%` | PASS |
| F4 | Gen Z share of new TY | `40.7%` | PASS |
| F4 | Gen Z share of new LY | `23.8%` | PASS |
| F6 | returning TY vs LY | `1,239 vs 1,236` | PASS |
| F7 | new Gen Z Insider TY | `17.1%` | PASS |
| F9 | Tabby YoY | `+42.9%` | PASS |
| F9 | Pillow Tabby YoY | `+83.4%` | PASS |
| F9 | Tabby share of growth | `59%` | PASS |
| F9 | Tabby+PT share of growth | `85%` | PASS |
| F10 | Rogue YoY | `-22.6%` | PASS |
| F10 | Knit Dress YoY | `-50.8%` | PASS |
| F11 | Tabby WOS | `WOS 1.9` | PASS |
| F11 | Pillow Tabby WOS | `WOS 1.6` | PASS |
| F11 | Knit Dress WOS | `WOS 21.2` | PASS |
| F11 | median WOS | `7.9` | PASS |
| F12 | Tabby receipts/sales | `0.28 vs 0.95` | PASS |
| R1 | 4wk demand at risk % | `7.7%` | PASS |
| R1 | 4wk demand at risk $ | `$23.1K` | PASS |
| R2 | apparel excess units | `198 units` | PASS |
| R2 | apparel excess $ | `$50.5K` | PASS |

- 30/30 PASS
- First critical Tabby anomaly fires in W28 (rules engine early-warning lead time)