"""04 - Customer-identity & cohort-field diagnostics (Phase A: QA5, QA6, QA8).

Tests whether repeated CUST_IDs are genuine repeat customers or random-ID collisions:
  * expected # colliding IDs if IDs are drawn uniformly from the observed ID range
  * Monte-Carlo distribution of collisions
  * attribute agreement (age group / insider / region) among repeat IDs vs chance
Also checks COHORT_STATUS internal consistency.

Output: outputs/tables/04_identity_checks.md, outputs/tables/04_repeat_ids.csv
"""
from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
d = pd.read_csv(ROOT / "data/processed/lines.csv", parse_dates=["TXN_DT"])
OUT = ROOT / "outputs/tables/04_identity_checks.md"
L = ["# Customer identity diagnostics", ""]

n = len(d)
n_ids = d.CUST_ID.nunique()
lo, hi = 100_000, 999_999  # observed IDs are 6-digit (min 100131, max 999840)
N = hi - lo + 1
extra_obs = n - n_ids  # lines beyond first per ID
rng = np.random.default_rng(42)
sims = np.array([n - len(np.unique(rng.integers(lo, hi + 1, n))) for _ in range(5000)])
L += [f"- Lines: {n}; distinct CUST_ID: {n_ids}; surplus lines on repeated IDs: {extra_obs}",
      f"- ID space assumed uniform 6-digit [{lo}, {hi}] (N={N:,}); observed min/max {d.CUST_ID.min()}/{d.CUST_ID.max()}",
      f"- Expected surplus under pure random IDs ≈ C(n,2)/N = {n*(n-1)/2/N:.2f}; Monte-Carlo mean {sims.mean():.2f}, "
      f"90% interval [{np.percentile(sims,5):.0f}, {np.percentile(sims,95):.0f}]; P(sim ≥ obs) = {(sims>=extra_obs).mean():.3f}",
      ""]

rep = d[d.CUST_ID.duplicated(keep=False)].sort_values(["CUST_ID", "TXN_DT"])
rep[["CUST_ID", "TXN_DT", "FISCAL_YR", "GEO_REGION", "CUST_AGE_GROUP", "INSIDER_FLAG", "COHORT_STATUS", "STYLE_DESC"]] \
    .to_csv(ROOT / "outputs/tables/04_repeat_ids.csv", index=False)
g = rep.groupby("CUST_ID")
agree = pd.DataFrame({a: (g[a].nunique() == 1) for a in ["CUST_AGE_GROUP", "INSIDER_FLAG", "GEO_REGION"]})
p_chance = {a: float((d[a].value_counts(normalize=True) ** 2).sum()) for a in agree.columns}
L.append("| attribute | repeat IDs agreeing | expected agreeing if random pair |")
L.append("|---|---|---|")
for a in agree.columns:
    L.append(f"| {a} | {int(agree[a].sum())} / {len(agree)} | {p_chance[a]*len(agree):.1f} |")
L.append(f"\n- Repeat IDs agreeing on ALL of age, insider, region: {int(agree.all(axis=1).sum())} / {len(agree)}")
L.append(f"- Repeat IDs spanning both FY25 and FY26: {int((g.FISCAL_YR.nunique()>1).sum())}")
L.append("\nRepeat-ID detail: outputs/tables/04_repeat_ids.csv\n")
L.append("```\n" + rep[["CUST_ID", "TXN_DT", "FISCAL_YR", "GEO_REGION", "CUST_AGE_GROUP", "INSIDER_FLAG", "COHORT_STATUS"]]
         .assign(TXN_DT=lambda x: x.TXN_DT.dt.date).to_string(index=False) + "\n```")

# COHORT_STATUS consistency
L += ["", "## COHORT_STATUS consistency",
      f"- Share of lines whose COHORT_STATUS is Retained/Reactivated although it is the ID's first in-sample purchase: "
      f"{((d.COHORT_STATUS!='New') & (d.TXN_DT==d.groupby('CUST_ID').TXN_DT.transform('min'))).mean():.1%} "
      "→ status is sourced from history OUTSIDE this extract (as the definition says).",
      ""]
ct = pd.crosstab([d.YEAR, d.COHORT_STATUS], d.INSIDER_FLAG, normalize="index").round(3)
L.append("Insider share by cohort status (row %):\n" + ct.to_markdown())
L.append("\nCohort status mix by year (share of lines):\n" +
         pd.crosstab(d.COHORT_STATUS, d.YEAR, normalize="columns").round(3).to_markdown())
L.append("\nAge-group mix by year (share of lines):\n" +
         pd.crosstab(d.CUST_AGE_GROUP, d.YEAR, normalize="columns").round(3).to_markdown())

OUT.write_text("\n".join(L))
print("\n".join(L))
