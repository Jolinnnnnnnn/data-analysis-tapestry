# KPI tile spot-check (rendered app vs analysis outputs)

| week | window | tile | field | rendered | expected (05_g1_kpi_windows.csv) | in 14_findings_audit.md | result |
|---|---|---|---|---|---|---|---|
| W29 | L1W | Demand | yoy | `+12.7%` | `+12.7%` (05 L1W (W29) sales yoy_pct) | `+12.7%` PASS | PASS |
| W29 | L4W | Demand | yoy | `+13.2%` | `+13.2%` (05 L4W (W26–W29) sales yoy_pct) | `+13.2%` PASS | PASS |
| W29 | L4W | Demand | ty | `$310.9K` | `$310.9K` (05 L4W (W26–W29) sales TY) | — | PASS |
| W30 | L1W | Demand | yoy | `+21.7%` | `+21.7%` (05 WTD (W30 Sun–Wed) sales yoy_pct) | `+21.7%` PASS | PASS |
| W30 | PTD | Demand | yoy | `+12.8%` | `+12.8%` (05 PTD sales yoy_pct) | `+12.8%` PASS | PASS |
| W30 | PTD | Transactions | yoy | `+8.2%` | `+8.2%` (05 PTD txns yoy_pct) | `+8.2%` PASS | PASS |
| W30 | PTD | AOV | ty | `$308.38` | `$308.38` (05 PTD aov TY) | — | PASS |
| W30 | PTD | AOV | yoy | `+4.3%` | `+4.3%` (05 PTD aov yoy_pct) | — | PASS |
| W29 | L1W | UPT | ty | `1.22` | `1.22` (05 L1W units/txns (test-side ratio)) | — | PASS |
| W29 | L4W | Customers | ty | `1,019` | `1,019` (05 L4W customers TY) | — | PASS |

10/10 tiles match.