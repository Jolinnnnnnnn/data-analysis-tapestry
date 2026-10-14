"""02 - Profile the raw Data and Inventory sheets: types, nulls, distinct values,
ranges, week coverage, key integrity checks that inform Phase A decisions.

Output: outputs/tables/02_profile.md
"""
from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/TYLY_data_sample.xlsx"
OUT = ROOT / "outputs/tables/02_profile.md"

d = pd.read_excel(RAW, sheet_name="Data")
inv = pd.read_excel(RAW, sheet_name="Inventory")
L = []
P = L.append


def md(df):
    return df.to_markdown(index=False) if isinstance(df, pd.DataFrame) else df.to_frame().to_markdown()


P(f"# Data profile\n\nData rows: {len(d)}, cols: {d.shape[1]}; Inventory rows: {len(inv)}\n")
P("## Data dtypes / nulls / distinct")
prof = pd.DataFrame({"dtype": d.dtypes.astype(str), "nulls": d.isna().sum(),
                     "blank_str": [(d[c].astype(str).str.strip() == "").sum() for c in d.columns],
                     "n_distinct": d.nunique()}).reset_index().rename(columns={"index": "col"})
P(md(prof))

for c in ["FISCAL_YR", "GEO_REGION", "SALES_CHANNEL", "CHANNEL_DETAIL", "PROD_CATEGORY",
          "PROD_TYPE", "COHORT_STATUS", "CUST_AGE_GROUP", "INSIDER_FLAG", "UNIT_QTY"]:
    vc = d[c].value_counts(dropna=False).rename_axis(c).reset_index(name="rows")
    P(f"\n### {c}\n" + vc.to_markdown(index=False))

P("\n## Numeric ranges")
P(d[["DEMAND_AMT", "UNIT_QTY"]].describe(percentiles=[.01, .05, .5, .95, .99]).T.to_markdown())
P(f"\n- DEMAND_AMT <= 0: {(d.DEMAND_AMT <= 0).sum()}; ==0: {(d.DEMAND_AMT == 0).sum()}; <0: {(d.DEMAND_AMT < 0).sum()}")
P(f"- UNIT_QTY <= 0: {(d.UNIT_QTY <= 0).sum()}; non-integer: {(d.UNIT_QTY % 1 != 0).sum()}")
d["unit_price"] = d.DEMAND_AMT / d.UNIT_QTY.replace(0, np.nan)
P("\n### Unit price by channel")
P(d.groupby(["FISCAL_YR", "SALES_CHANNEL"]).unit_price.describe().to_markdown())

P("\n## Week coverage")
d["wk"] = d.FISCAL_WK.str.extract(r"W(\d+)").astype(int)
d["wk_fy"] = d.FISCAL_WK.str[:4]
P(f"- FISCAL_WK prefix == FISCAL_YR mismatches: {(d.wk_fy != d.FISCAL_YR).sum()}")
wk = d.groupby(["FISCAL_YR", "wk"]).agg(rows=("TXN_ID", "size"), dt_min=("TXN_DT", "min"),
                                         dt_max=("TXN_DT", "max"), dow_min=("TXN_DT", lambda s: s.dt.day_name().iloc[0])).reset_index()
wk["dt_min"] = wk.dt_min.dt.date
wk["dt_max"] = wk.dt_max.dt.date
P(wk.to_markdown(index=False))
P(f"\n- Date range FY26: {d[d.FISCAL_YR=='FY26'].TXN_DT.min().date()} – {d[d.FISCAL_YR=='FY26'].TXN_DT.max().date()}")
P(f"- Date range FY25: {d[d.FISCAL_YR=='FY25'].TXN_DT.min().date()} – {d[d.FISCAL_YR=='FY25'].TXN_DT.max().date()}")
# Year of TXN_DT matches FY?
d["dt_year"] = d.TXN_DT.dt.year
P("\n### TXN_DT calendar year vs FISCAL_YR\n" + pd.crosstab(d.FISCAL_YR, d.dt_year).to_markdown())
# Overlapping dates between weeks (same date in two different weeks?)
dd = d.groupby(["FISCAL_YR", d.TXN_DT.dt.date]).wk.nunique()
P(f"\n- Dates mapped to >1 fiscal week: {(dd > 1).sum()}")
bad = dd[dd > 1].reset_index().head(20)
if len(bad):
    P(bad.to_markdown(index=False))

P("\n## Transaction grain checks")
P(f"- Distinct TXN_ID: {d.TXN_ID.nunique()}; rows: {len(d)}; lines/txn mean {len(d)/d.TXN_ID.nunique():.3f}")
lines_per = d.groupby("TXN_ID").size().value_counts().sort_index()
P("Lines per TXN_ID:\n" + lines_per.rename_axis("lines").reset_index(name="txns").to_markdown(index=False))
g = d.groupby("TXN_ID")
attr_consistency = {c: (g[c].nunique() > 1).sum() for c in
                    ["CUST_ID", "TXN_DT", "FISCAL_WK", "GEO_REGION", "SALES_CHANNEL", "CHANNEL_DETAIL",
                     "COHORT_STATUS", "CUST_AGE_GROUP", "INSIDER_FLAG"]}
P("\nTXN_IDs with >1 distinct value of attribute (should be 0 if txn-level attr):\n" +
  pd.Series(attr_consistency).rename_axis("attr").reset_index(name="txns_inconsistent").to_markdown(index=False))
P(f"\n- TXN_ID prefix year vs FISCAL_YR mismatches: {(d.TXN_ID.str[3:5] != d.FISCAL_YR.str[2:4]).sum()}")
P(f"- Exact duplicate rows: {d.duplicated().sum()}")
P(f"- Duplicate (TXN_ID, STYLE_DESC) pairs: {d.duplicated(['TXN_ID','STYLE_DESC']).sum()}")

P("\n## Customer checks")
P(f"- Distinct CUST_ID: {d.CUST_ID.nunique()}; FY26: {d[d.FISCAL_YR=='FY26'].CUST_ID.nunique()}; FY25: {d[d.FISCAL_YR=='FY25'].CUST_ID.nunique()}")
both = set(d[d.FISCAL_YR == 'FY26'].CUST_ID) & set(d[d.FISCAL_YR == 'FY25'].CUST_ID)
P(f"- CUST_IDs in both years: {len(both)}")
gc = d.groupby("CUST_ID")
P(f"- CUST_ID with >1 CUST_AGE_GROUP: {(gc.CUST_AGE_GROUP.nunique()>1).sum()}; >1 INSIDER_FLAG: {(gc.INSIDER_FLAG.nunique()>1).sum()}; >1 GEO_REGION: {(gc.GEO_REGION.nunique()>1).sum()}")
P(f"- CUST_ID with >1 TXN_ID: {(gc.TXN_ID.nunique()>1).sum()}")
P("TXNs per customer:\n" + gc.TXN_ID.nunique().value_counts().sort_index().rename_axis("txns").reset_index(name="customers").to_markdown(index=False))
P(f"- CUST_ID range: {d.CUST_ID.min()} – {d.CUST_ID.max()}; non-positive/sentinel (<=0 or 999999-like): {(d.CUST_ID<=0).sum()}")

P("\n### COHORT_STATUS per customer: customers with 'New' on multiple TXNs")
newtx = d[d.COHORT_STATUS == "New"].groupby("CUST_ID").TXN_ID.nunique()
P(f"- customers with New on >1 distinct txn: {(newtx>1).sum()} of {len(newtx)}")
# New status after earlier purchase?
first = d.groupby("CUST_ID").TXN_DT.transform("min")
P(f"- 'New' lines not on customer's first observed date: {((d.COHORT_STATUS=='New') & (d.TXN_DT>first)).sum()}")
P(f"- 'Retained/Reactivated' lines on customer's first observed date: {((d.COHORT_STATUS!='New') & (d.TXN_DT==first)).sum()}")

P("\n## Hierarchy checks")
P(f"- STYLE_GROUP -> PROD_CATEGORY many-to-one violations: {(d.groupby('STYLE_GROUP').PROD_CATEGORY.nunique()>1).sum()}")
P(f"- STYLE_GROUP -> PROD_TYPE violations: {(d.groupby('STYLE_GROUP').PROD_TYPE.nunique()>1).sum()}")
P(f"- STYLE_DESC -> STYLE_GROUP violations: {(d.groupby('STYLE_DESC').STYLE_GROUP.nunique()>1).sum()}")
h = d.groupby(["PROD_CATEGORY", "STYLE_GROUP", "PROD_TYPE"]).agg(styles=("STYLE_DESC", "nunique"), rows=("TXN_ID", "size")).reset_index()
P(h.to_markdown(index=False))
mt = d.groupby("STYLE_GROUP").PROD_TYPE.unique()
P("\nPROD_TYPE values per STYLE_GROUP (if multiple):\n" + mt[mt.str.len() > 1].to_string())

P("\n## Inventory")
P(f"- dtypes: {dict(inv.dtypes.astype(str))}; nulls: {inv.isna().sum().sum()}")
P(f"- ON_HAND_UNITS: min {inv.ON_HAND_UNITS.min()}, max {inv.ON_HAND_UNITS.max()}, <=0: {(inv.ON_HAND_UNITS<=0).sum()}")
inv["wk"] = inv.FISCAL_WK.str.extract(r"W(\d+)").astype(int)
P(pd.crosstab(inv.FISCAL_YR, inv.wk).to_markdown())
P(f"- duplicate (FISCAL_WK, STYLE_GROUP): {inv.duplicated(['FISCAL_WK','STYLE_GROUP']).sum()}")
sg_d, sg_i = set(d.STYLE_GROUP), set(inv.STYLE_GROUP)
P(f"- STYLE_GROUP in Data not in Inventory: {sorted(sg_d - sg_i)}")
P(f"- STYLE_GROUP in Inventory not in Data: {sorted(sg_i - sg_d)}")
P(f"- whitespace/case variants: {sorted({s for s in sg_d|sg_i if s != s.strip()})}")
P(f"- Inventory weeks: {sorted(inv.FISCAL_WK.unique())}")
P(f"- Data weeks: {sorted(d.FISCAL_WK.unique())}")

OUT.write_text("\n".join(L))
print("\n".join(L))
