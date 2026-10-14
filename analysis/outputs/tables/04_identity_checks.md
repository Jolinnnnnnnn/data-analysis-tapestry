# Customer identity diagnostics

- Lines: 3609; distinct CUST_ID: 3600; surplus lines on repeated IDs: 9
- ID space assumed uniform 6-digit [100000, 999999] (N=900,000); observed min/max 100131/999840
- Expected surplus under pure random IDs ≈ C(n,2)/N = 7.23; Monte-Carlo mean 7.26, 90% interval [3, 12]; P(sim ≥ obs) = 0.304

| attribute | repeat IDs agreeing | expected agreeing if random pair |
|---|---|---|
| CUST_AGE_GROUP | 4 / 9 | 2.7 |
| INSIDER_FLAG | 3 / 9 | 4.5 |
| GEO_REGION | 4 / 9 | 3.4 |

- Repeat IDs agreeing on ALL of age, insider, region: 0 / 9
- Repeat IDs spanning both FY25 and FY26: 6

Repeat-ID detail: outputs/tables/04_repeat_ids.csv

```
 CUST_ID     TXN_DT FISCAL_YR    GEO_REGION CUST_AGE_GROUP INSIDER_FLAG COHORT_STATUS
  271379 2026-07-04      FY26 North America         Boomer            N           New
  271379 2026-07-24      FY26 North America     Millennial            Y           New
  467752 2025-07-28      FY25        Europe     Millennial            N      Retained
  467752 2026-08-15      FY26 Greater China         Boomer            N           New
  468795 2025-08-01      FY25 North America          Gen X            N           New
  468795 2026-07-25      FY26 North America          Gen X            Y      Retained
  604081 2025-08-02      FY25 North America     Millennial            N           New
  604081 2026-07-21      FY26 Greater China     Millennial            N      Retained
  638364 2026-07-08      FY26 North America     Millennial            N   Reactivated
  638364 2026-07-18      FY26        Europe          Gen Z            Y   Reactivated
  777513 2025-08-13      FY25        Europe          Gen X            N           New
  777513 2026-07-03      FY26 North America          Gen X            Y           New
  778325 2025-08-10      FY25        Europe         Boomer            Y   Reactivated
  778325 2026-08-06      FY26 Greater China          Gen X            Y      Retained
  808307 2025-08-11      FY25 North America          Gen X            N      Retained
  808307 2026-06-30      FY26 North America          Gen X            Y      Retained
  817586 2025-07-30      FY25 North America     Millennial            Y           New
  817586 2025-08-16      FY25 North America          Gen Z            N           New
```

## COHORT_STATUS consistency
- Share of lines whose COHORT_STATUS is Retained/Reactivated although it is the ID's first in-sample purchase: 70.2% → status is sourced from history OUTSIDE this extract (as the definition says).

Insider share by cohort status (row %):
|                       |     N |     Y |
|:----------------------|------:|------:|
| ('LY', 'New')         | 0.803 | 0.197 |
| ('LY', 'Reactivated') | 0.534 | 0.466 |
| ('LY', 'Retained')    | 0.309 | 0.691 |
| ('TY', 'New')         | 0.807 | 0.193 |
| ('TY', 'Reactivated') | 0.566 | 0.434 |
| ('TY', 'Retained')    | 0.286 | 0.714 |

Cohort status mix by year (share of lines):
| COHORT_STATUS   |    LY |    TY |
|:----------------|------:|------:|
| New             | 0.271 | 0.323 |
| Reactivated     | 0.164 | 0.141 |
| Retained        | 0.565 | 0.536 |

Age-group mix by year (share of lines):
| CUST_AGE_GROUP   |    LY |    TY |
|:-----------------|------:|------:|
| Boomer           | 0.14  | 0.124 |
| Gen X            | 0.274 | 0.255 |
| Gen Z            | 0.161 | 0.218 |
| Millennial       | 0.425 | 0.404 |