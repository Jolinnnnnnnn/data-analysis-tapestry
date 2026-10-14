"""03 - Clean & enrich. Logs every transformation with before/after row counts.

Inputs : data/raw/TYLY_data_sample.xlsx (read-only)
Outputs: data/processed/lines.csv        (one row per transaction line, enriched)
         data/processed/inventory.csv    (one row per FY x week x STYLE_GROUP snapshot)
         outputs/tables/03_cleaning_log.md

Key derived fields (see DECISIONS.md):
  YEAR       TY/LY from FISCAL_YR (FY26=TY, FY25=LY)              [D3]
  WK         integer fiscal week number (23..30)                   [D3]
  WK_START   Sunday that starts the fiscal week (min date of week, snapped to Sunday)
  DAY_IN_WK  0=Sun..6=Sat
  IN_TY_WINDOW  False for LY lines in the last fiscal week that fall after the
             TY as-of day-of-week (like-for-like days for partial week)  [D3/D10]
  IS_FULL_WK  week is complete in TY (W23..W29)                    [D3]
  UNIT_PRICE DEMAND_AMT / UNIT_QTY
  PRICE_IDX  UNIT_PRICE / median RETAIL unit price of the same STYLE_DESC (pooled TY+LY);
             a noisy discount proxy                                 [D4]
  IS_GENZ, IS_NEW, IS_RETURNING (Retained or Reactivated)          [D6, D7, D8]
"""
from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/TYLY_data_sample.xlsx"
PROC = ROOT / "data/processed"
LOG = ROOT / "outputs/tables/03_cleaning_log.md"
PROC.mkdir(parents=True, exist_ok=True)

log = ["# Cleaning log", "", "| step | table | rows_before | rows_after | note |", "|---|---|---|---|---|"]


def step(name, table, before, after, note=""):
    log.append(f"| {name} | {table} | {before} | {after} | {note} |")


# ---------- Data ----------
d = pd.read_excel(RAW, sheet_name="Data")
n0 = len(d)
step("read Data sheet", "lines", "-", n0, "header row 1, 17 cols")

# 1. strip whitespace on text columns (defensive; profile found none)
obj = d.select_dtypes("object").columns
changed = sum((d[c] != d[c].str.strip()).sum() for c in obj)
for c in obj:
    d[c] = d[c].str.strip()
step("strip text whitespace", "lines", n0, len(d), f"{changed} cells changed")

# 2. validity filters (none expected to drop; logged for audit)
before = len(d)
bad_amt = (d.DEMAND_AMT <= 0) | d.DEMAND_AMT.isna()
bad_qty = (d.UNIT_QTY <= 0) | d.UNIT_QTY.isna()
step("flag DEMAND_AMT<=0 (returns/zero-value)", "lines", before, before, f"{int(bad_amt.sum())} flagged; kept=all (no returns in extract)")
step("flag UNIT_QTY<=0", "lines", before, before, f"{int(bad_qty.sum())} flagged")
dups = d.duplicated().sum()
d = d.drop_duplicates()
step("drop exact duplicate rows", "lines", before, len(d), f"{dups} dropped")
assert len(d) == n0, "Unexpected row drop"

# 3. year/week fields
d["YEAR"] = d.FISCAL_YR.map({"FY26": "TY", "FY25": "LY"})
assert d.YEAR.notna().all()
d["WK"] = d.FISCAL_WK.str.extract(r"W(\d+)$")[0].astype(int)
assert (d.FISCAL_WK.str[:4] == d.FISCAL_YR).all()
d["TXN_DT"] = pd.to_datetime(d.TXN_DT)
# week start = Sunday on/before the earliest date of that week
wk_min = d.groupby(["FISCAL_YR", "WK"]).TXN_DT.transform("min")
d["WK_START"] = wk_min - pd.to_timedelta((wk_min.dt.dayofweek + 1) % 7, unit="D")
d["DAY_IN_WK"] = (d.TXN_DT - d.WK_START).dt.days
assert d.DAY_IN_WK.between(0, 6).all(), "date outside its fiscal week"
step("derive YEAR, WK, WK_START, DAY_IN_WK", "lines", len(d), len(d), "all dates within Sun–Sat fiscal week")

# 4. TY as-of & like-for-like window
ty = d[d.YEAR == "TY"]
asof = ty.TXN_DT.max()
last_wk = int(ty.WK.max())
asof_day = int(ty.loc[ty.TXN_DT == asof, "DAY_IN_WK"].iloc[0])
d["IS_FULL_WK"] = d.WK < last_wk if asof_day < 6 else True
d["IN_TY_WINDOW"] = ~((d.YEAR == "LY") & (d.WK == last_wk) & (d.DAY_IN_WK > asof_day))
n_excl = int((~d.IN_TY_WINDOW).sum())
step("flag LY lines outside TY window", "lines", len(d), len(d),
     f"TY as-of {asof.date()} = W{last_wk} day {asof_day} (0=Sun); {n_excl} LY W{last_wk} lines after that day flagged IN_TY_WINDOW=False")

# 5. price fields
d["UNIT_PRICE"] = d.DEMAND_AMT / d.UNIT_QTY
ref = d[d.SALES_CHANNEL == "RETAIL"].groupby("STYLE_DESC").UNIT_PRICE.median().rename("REF_PRICE")
d = d.merge(ref, on="STYLE_DESC", how="left", validate="many_to_one")
assert d.REF_PRICE.notna().all() and len(d) == n0
d["PRICE_IDX"] = d.UNIT_PRICE / d.REF_PRICE
step("join RETAIL median unit price per STYLE_DESC → PRICE_IDX", "lines", n0, len(d), "many_to_one validated; 0 unmatched")

# 6. customer flags
d["IS_GENZ"] = d.CUST_AGE_GROUP.eq("Gen Z")
d["IS_NEW"] = d.COHORT_STATUS.eq("New")
d["IS_RETURNING"] = d.COHORT_STATUS.isin(["Retained", "Reactivated"])
d["IS_INSIDER"] = d.INSIDER_FLAG.eq("Y")
d["IS_OUTLET"] = d.SALES_CHANNEL.eq("OUTLET")
d["IS_ECOMM"] = d.CHANNEL_DETAIL.eq("eComm")
step("derive customer/channel boolean flags", "lines", len(d), len(d), "")

cols = ["TXN_ID", "TXN_DT", "FISCAL_YR", "YEAR", "FISCAL_WK", "WK", "WK_START", "DAY_IN_WK", "IS_FULL_WK",
        "IN_TY_WINDOW", "GEO_REGION", "SALES_CHANNEL", "CHANNEL_DETAIL", "PROD_CATEGORY", "STYLE_GROUP",
        "STYLE_DESC", "PROD_TYPE", "CUST_ID", "COHORT_STATUS", "CUST_AGE_GROUP", "INSIDER_FLAG",
        "DEMAND_AMT", "UNIT_QTY", "UNIT_PRICE", "REF_PRICE", "PRICE_IDX", "IS_GENZ", "IS_NEW",
        "IS_RETURNING", "IS_INSIDER", "IS_OUTLET", "IS_ECOMM"]
d = d[cols].sort_values(["TXN_DT", "TXN_ID"]).reset_index(drop=True)
d.to_csv(PROC / "lines.csv", index=False)
step("write data/processed/lines.csv", "lines", n0, len(d), f"{len(cols)} cols")

# ---------- Inventory ----------
inv = pd.read_excel(RAW, sheet_name="Inventory")
i0 = len(inv)
step("read Inventory sheet", "inventory", "-", i0, "")
for c in inv.select_dtypes("object").columns:
    inv[c] = inv[c].str.strip()
inv["YEAR"] = inv.FISCAL_YR.map({"FY26": "TY", "FY25": "LY"})
inv["WK"] = inv.FISCAL_WK.str.extract(r"W(\d+)$")[0].astype(int)
assert not inv.duplicated(["FISCAL_YR", "WK", "STYLE_GROUP"]).any()
miss = set(inv.STYLE_GROUP) ^ set(d.STYLE_GROUP)
step("validate inventory key (FY, WK, STYLE_GROUP) unique & families match Data", "inventory", i0, len(inv),
     f"symmetric difference of family names: {sorted(miss) or 'none'}")
# family attributes from sales hierarchy (validated many-to-one in 02_profile)
fam = d.groupby("STYLE_GROUP")[["PROD_CATEGORY", "PROD_TYPE"]].first().reset_index()
inv = inv.merge(fam, on="STYLE_GROUP", how="left", validate="many_to_one")
assert len(inv) == i0 and inv.PROD_CATEGORY.notna().all()
step("join PROD_CATEGORY/PROD_TYPE to inventory", "inventory", i0, len(inv), "0 unmatched")
inv.to_csv(PROC / "inventory.csv", index=False)
step("write data/processed/inventory.csv", "inventory", i0, len(inv), "")

# ---------- reconciliation to raw ----------
raw = pd.read_excel(RAW, sheet_name="Data")
log += ["", "## Reconciliation to raw", "| measure | raw | processed | match |", "|---|---|---|---|"]
for fy in ["FY26", "FY25"]:
    for m in ["DEMAND_AMT", "UNIT_QTY"]:
        a, b = raw.loc[raw.FISCAL_YR == fy, m].sum(), d.loc[d.FISCAL_YR == fy, m].sum()
        log.append(f"| {fy} {m} | {a:,.2f} | {b:,.2f} | {np.isclose(a, b)} |")
        assert np.isclose(a, b)
rinv = pd.read_excel(RAW, sheet_name="Inventory")
log.append(f"| inventory ON_HAND_UNITS row-sum (checksum only; never a business metric) | {rinv.ON_HAND_UNITS.sum()} | {inv.ON_HAND_UNITS.sum()} | {rinv.ON_HAND_UNITS.sum()==inv.ON_HAND_UNITS.sum()} |")
log += ["", f"TY as-of date: {asof.date()} (W{last_wk}, day {asof_day}); TY last full week: W{last_wk-1 if asof_day<6 else last_wk}"]

LOG.write_text("\n".join(log))
print("\n".join(log))
