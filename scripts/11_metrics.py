"""11 - Build the single source of truth for the dashboard: data/processed/metrics.json + tidy CSVs.
Everything a dashboard shows is PRECOMPUTED here and indexed by fiscal week (23..30), so the app
does no arithmetic. Definitions follow DECISIONS.md (D3 like-for-like LY; D4 KPI formulas; D6–D10).

Sections (see data/processed/metrics_schema.md):
  meta, headline (PTD), decomposition, weekly (TY/LY by week), trailing (per selected week: L1W/L4W/PTD),
  generation_weekly, genz_weekly, genz_ptd, first_purchase_mix, products_ptd, products_by_week,
  inventory_by_week, inventory_position, recommendations_sizing, weekly_facts (compact facts for the LLM)
"""
import hashlib
import json
import numpy as np
import pandas as pd
from _common import ROOT, PROC, TAB, load_lines, load_inventory, ptd, kpis, GENS, LAST_FULL_WK

d = load_lines()
p = ptd(d)
WEEKS = sorted(p.WK.unique().tolist())
KPI = ["sales", "units", "txns", "customers", "aov", "upt", "aur"]
raw_path = ROOT / "data/raw/TYLY_data_sample.xlsx"


def r(x, n=6):  # 6 dp so 1-dp percentages never hit a rounding tie (dashboard D19)
    if x is None or (isinstance(x, float) and (np.isnan(x) or np.isinf(x))):
        return None
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (np.floating, float)):
        return round(float(x), n)
    return x


def pct(a, b):
    return (a / b - 1) if (b not in (0, None) and a is not None and not pd.isna(b) and b != 0) else None


def kp(df):
    k = kpis(df)
    extra = {
        "new_customers": int(df.IS_NEW.sum()),
        "returning_customers": int(df.IS_RETURNING.sum()),
        "genz_txns": int(df.IS_GENZ.sum()),
        "genz_new": int((df.IS_GENZ & df.IS_NEW).sum()),
        "genz_returning": int((df.IS_GENZ & df.IS_RETURNING).sum()),
    }
    out = {m: float(k[m]) for m in KPI}
    out.update(extra)
    out["genz_share_of_new"] = extra["genz_new"] / extra["new_customers"] if extra["new_customers"] else None
    out["genz_share_of_txns"] = extra["genz_txns"] / len(df) if len(df) else None
    out["returning_share"] = extra["returning_customers"] / len(df) if len(df) else None
    nw = df[df.IS_NEW]
    gzn = df[df.IS_NEW & df.IS_GENZ]
    out["new_insider_rate"] = nw.IS_INSIDER.mean() if len(nw) else None
    out["genz_new_insider_rate"] = gzn.IS_INSIDER.mean() if len(gzn) else None
    out["outlet_share"] = df.IS_OUTLET.mean() if len(df) else None
    out["ecomm_share"] = df.IS_ECOMM.mean() if len(df) else None
    return out


COMP = ["sales", "units", "txns", "customers", "aov", "upt", "aur", "new_customers", "returning_customers",
        "genz_txns", "genz_new", "genz_returning", "genz_share_of_new", "genz_share_of_txns", "returning_share",
        "new_insider_rate", "genz_new_insider_rate", "outlet_share", "ecomm_share"]
SHARES = {"genz_share_of_new", "genz_share_of_txns", "returning_share", "new_insider_rate", "genz_new_insider_rate",
          "outlet_share", "ecomm_share"}


def compare(ty_df, ly_df):
    t, l = kp(ty_df), kp(ly_df)
    out = {}
    for m in COMP:
        out[m] = {"ty": r(t[m]), "ly": r(l[m])}
        if m in SHARES:
            out[m]["chg_pts"] = r((t[m] - l[m]) * 100, 2) if (t[m] is not None and l[m] is not None) else None
        else:
            out[m]["yoy_pct"] = r(pct(t[m], l[m]))
    return out


ty_all, ly_all = p[p.YEAR == "TY"], p[p.YEAR == "LY"]
asof = d[d.YEAR == "TY"].TXN_DT.max()

# ---------- meta ----------
meta = {
    "generated_by": "scripts/11_metrics.py",
    "source_file": "data/raw/TYLY_data_sample.xlsx",
    "source_md5": hashlib.md5(raw_path.read_bytes()).hexdigest(),
    "ty_label": "FY26", "ly_label": "FY25",
    "as_of_date": str(asof.date()),
    "weeks": WEEKS,
    "last_full_week": LAST_FULL_WK,
    "partial_week": 30, "partial_week_days": "Sun–Wed (4 of 7)",
    "basis": "PTD like-for-like: LY W30 restricted to Sun–Wed to match TY (DECISIONS D3). Counts are SAMPLE-scale (D11).",
    "ly_w30_full_week_sales": r(d[(d.YEAR == "LY") & (d.WK == 30)].DEMAND_AMT.sum(), 2),
    "definitions": {
        "sales": "sum DEMAND_AMT (USD, after discounts)", "txns": "distinct TXN_ID (= lines)",
        "customers": "distinct CUST_ID in period", "aov": "sales / txns", "upt": "units / txns", "aur": "sales / units",
        "new_customers": "txns with COHORT_STATUS = New", "returning_customers": "txns with Retained or Reactivated",
        "genz": "CUST_AGE_GROUP = Gen Z", "wos": "end-of-week ON_HAND_UNITS / avg weekly units over trailing <=4 full weeks",
        "L1W": "selected week", "L4W": "selected week and 3 prior (truncated before W26)", "PTD": "W23 through selected week",
    },
    "ratio_rule": "Ratios are computed from totals, never averaged across weeks.",
}

# ---------- meta additions for the dashboard (counts, calendar, basis alternatives, data quality) ----------
inv_rows = load_inventory()
meta["counts"] = {
    "lines_total": int(len(d)), "lines_ty": int((d.YEAR == "TY").sum()), "lines_ly": int((d.YEAR == "LY").sum()),
    "lines_ly_excluded_like_for_like": int((~d.IN_TY_WINDOW).sum()),
    "txn_ids_total": int(d.TXN_ID.nunique()), "cust_ids_total": int(d.CUST_ID.nunique()),
    "inventory_snapshots": int(len(inv_rows)), "families": int(inv_rows.STYLE_GROUP.nunique()),
}
# TY fiscal calendar per week: Sunday start, Saturday end, and last day with sales (W30 is partial).
_ty = d[d.YEAR == "TY"]
meta["week_dates_ty"] = {
    str(w): {"start": str(g.WK_START.min().date()),
             "end": str((g.WK_START.min() + pd.Timedelta(days=6)).date()),
             "last_sale": str(g.TXN_DT.max().date())}
    for w, g in _ty.groupby("WK")
}
assert all(pd.Timestamp(v["start"]).dayofweek == 6 for v in meta["week_dates_ty"].values()), "TY weeks must start on Sunday"
# Alternative YoY bases (D3 sensitivity, F2) copied from script 05.
_k05 = pd.read_csv(TAB / "05_g1_kpi_windows.csv")
_s05 = _k05[_k05.metric == "sales"].set_index("window")
meta["basis_alternatives"] = {
    "like_for_like_sales_yoy_pct": r(_s05.loc["PTD (W23–W30 Wed, like-for-like)", "yoy_pct"]),
    "naive_all_rows_sales_yoy_pct": r(_s05.loc["PTD alt-a (all rows, LY full W30)", "yoy_pct"]),
    "full_weeks_only_sales_yoy_pct": r(_s05.loc["Full weeks W23–W29", "yoy_pct"]),
    "naive_ly_sales": r(_s05.loc["PTD alt-a (all rows, LY full W30)", "LY"], 2),
}
# CUST_ID diagnostics (F14), same closed form as script 04: surplus lines on repeated IDs vs C(n,2)/N for random 6-digit IDs.
_n, _N = len(d), 999_999 - 100_000 + 1
meta["data_quality"] = {
    "cust_id_repeat_surplus_observed": int(_n - d.CUST_ID.nunique()),
    "cust_id_repeat_surplus_expected_random": r(_n * (_n - 1) / 2 / _N, 2),
    "lines_per_txn": r(len(d) / d.TXN_ID.nunique(), 2),
    "ty_last_sale_date": str(asof.date()),
    "ty_w30_stock_snapshot_present": bool(((inv_rows.YEAR == "TY") & (inv_rows.WK == 30)).any()),
}

# ---------- headline & decomposition ----------
headline = compare(ty_all, ly_all)
dec = pd.read_csv(TAB / "05_g1_decomposition.csv")
decomposition = [{k: r(v) if not isinstance(v, str) else v for k, v in row.items()} for row in dec.to_dict("records")]

# ---------- weekly ----------
weekly = []
for w in WEEKS:
    t, l = p[(p.YEAR == "TY") & (p.WK == w)], p[(p.YEAR == "LY") & (p.WK == w)]
    row = {"wk": w, "is_partial": w == 30, "days": 4 if w == 30 else 7}
    row.update(compare(t, l))
    weekly.append(row)
# WoW for TY sales/txns/aov/genz_new (full weeks only)
for i, row in enumerate(weekly):
    for m in ["sales", "txns", "aov", "genz_new", "new_customers"]:
        prev = weekly[i - 1][m]["ty"] if i > 0 else None
        row[m]["wow_pct"] = r(pct(row[m]["ty"], prev)) if (i > 0 and not row["is_partial"]) else None

# ---------- trailing per selected week ----------
trailing = {}
for w in WEEKS:
    l4 = [x for x in WEEKS if w - 3 <= x <= w]
    sel = lambda df, ws: df[df.WK.isin(ws)]
    trailing[str(w)] = {
        "L1W": {"weeks": [w], "is_partial": w == 30, **compare(sel(ty_all, [w]), sel(ly_all, [w]))},
        "L4W": {"weeks": l4, "n_weeks": len(l4), "truncated": len(l4) < 4, **compare(sel(ty_all, l4), sel(ly_all, l4))},
        "PTD": {"weeks": [x for x in WEEKS if x <= w], **compare(sel(ty_all, [x for x in WEEKS if x <= w]), sel(ly_all, [x for x in WEEKS if x <= w]))},
    }
    # prior period (TY): previous week for L1W
    if w - 1 in WEEKS and w != 30:
        prev = kp(sel(ty_all, [w - 1]))
        cur = kp(sel(ty_all, [w]))
        trailing[str(w)]["L1W"]["wow"] = {m: r(pct(cur[m], prev[m])) for m in ["sales", "txns", "aov", "units", "new_customers", "genz_new"]}
    else:
        trailing[str(w)]["L1W"]["wow"] = None

# ---------- generation weekly & Gen Z ----------
gen_weekly = []
for (y, w, g), s in p.groupby(["YEAR", "WK", "CUST_AGE_GROUP"]):
    gen_weekly.append({"year": y, "wk": int(w), "generation": g, "txns": int(len(s)), "sales": r(s.DEMAND_AMT.sum(), 2),
                       "new": int(s.IS_NEW.sum()), "returning": int(s.IS_RETURNING.sum()),
                       "new_insider_rate": r(s[s.IS_NEW].IS_INSIDER.mean()) if s.IS_NEW.any() else None})
gw = pd.read_csv(TAB / "06_g2_genz_new_by_week.csv")
genz_weekly = [{k: r(v) for k, v in row.items()} for row in gw.to_dict("records")]
gen_ptd = pd.read_csv(TAB / "06_g2_by_generation.csv")
genz_ptd = [{k: (r(v) if not isinstance(v, str) else v) for k, v in row.items()} for row in gen_ptd.to_dict("records")]
fpm = pd.read_csv(TAB / "06_g2_first_purchase_mix.csv")
first_purchase_mix = [{k: (r(v) if not isinstance(v, str) else v) for k, v in row.items()} for row in fpm.to_dict("records")]
val = pd.read_csv(TAB / "06_g2_new_genz_value.csv")
new_genz_value = [{k: (r(v) if not isinstance(v, str) else v) for k, v in row.items()} for row in val.to_dict("records")]
ins_seg = pd.read_csv(TAB / "06_g2_new_insider_by_segment.csv")
new_insider_by_segment = [{k: (r(v) if not isinstance(v, str) else v) for k, v in row.items()} for row in ins_seg.to_dict("records")]

# ---------- products ----------
fam = pd.read_csv(TAB / "07_g3_family_scorecard.csv")
products_ptd = [{k: (r(v) if not isinstance(v, (str, bool, np.bool_)) else (bool(v) if isinstance(v, (bool, np.bool_)) else v))
                 for k, v in row.items()} for row in fam.to_dict("records")]
sty = pd.read_csv(TAB / "07_g3_style_scorecard.csv")
styles_ptd = [{k: (r(v) if not isinstance(v, (str, bool, np.bool_)) else (bool(v) if isinstance(v, (bool, np.bool_)) else v))
               for k, v in row.items()} for row in sty.to_dict("records")]
products_by_week = []
for w in WEEKS:
    l4 = [x for x in WEEKS if w - 3 <= x <= w]
    for win, ws in [("L1W", [w]), ("L4W", l4)]:
        t = ty_all[ty_all.WK.isin(ws)]
        l = ly_all[ly_all.WK.isin(ws)]
        gz_overall = t.IS_GENZ.mean()
        tg, lg = t.groupby("STYLE_GROUP"), l.groupby("STYLE_GROUP")
        for f in sorted(p.STYLE_GROUP.unique()):
            st, sl = t[t.STYLE_GROUP == f], l[l.STYLE_GROUP == f]
            products_by_week.append({
                "wk": w, "window": win, "family": f, "sales_ty": r(st.DEMAND_AMT.sum(), 2), "sales_ly": r(sl.DEMAND_AMT.sum(), 2),
                "sales_yoy_pct": r(pct(st.DEMAND_AMT.sum(), sl.DEMAND_AMT.sum())),
                "units_ty": int(st.UNIT_QTY.sum()), "units_ly": int(sl.UNIT_QTY.sum()),
                "txns_ty": int(len(st)), "txns_ly": int(len(sl)),
                "contrib_pts": r((st.DEMAND_AMT.sum() - sl.DEMAND_AMT.sum()) / l.DEMAND_AMT.sum() * 100, 3),
                "genz_txns_ty": int(st.IS_GENZ.sum()), "genz_new_ty": int((st.IS_GENZ & st.IS_NEW).sum()),
                "genz_index_ty": r(st.IS_GENZ.mean() / gz_overall * 100, 1) if len(st) else None,
            })

# ---------- inventory ----------
wkf = pd.read_csv(TAB / "08_g4_weekly_family.csv")
inventory_by_week = []
for (y, w), s in wkf.groupby(["YEAR", "WK"]):
    med = s.wos.median()
    for row in s.itertuples():
        ly_row = wkf[(wkf.YEAR == "LY") & (wkf.WK == w) & (wkf.STYLE_GROUP == row.STYLE_GROUP)]
        inventory_by_week.append({
            "year": y, "wk": int(w), "family": row.STYLE_GROUP, "prod_type": row.PROD_TYPE,
            "on_hand_eow": int(row.ON_HAND_UNITS), "units_sold": int(row.units), "partial_sales_week": bool(row.partial_sales_wk),
            "avg_weekly_units_trailing": r(row.avg_units_trailing, 3), "wos_window_weeks": int(row.wos_window_weeks),
            "wos": r(row.wos, 2), "wos_vs_week_median": r(row.wos / med, 3),
            "wos_ly_same_week": r(ly_row.wos.iloc[0], 2) if (y == "TY" and len(ly_row)) else None,
            "sell_through_wk": r(row.sell_through_wk), "implied_receipts": r(row.implied_receipts, 1),
        })
pos = pd.read_csv(TAB / "08_g4_position.csv")
inventory_position = [{k: (r(v) if not isinstance(v, (str, bool, np.bool_)) else (bool(v) if isinstance(v, (bool, np.bool_)) else v))
                       for k, v in row.items()} for row in pos.to_dict("records")]
inv_tot = []
for (y, w), s in wkf.groupby(["YEAR", "WK"]):
    inv_tot.append({"year": y, "wk": int(w), "on_hand_eow_all_families": int(s.ON_HAND_UNITS.sum()), "units_sold": int(s.units.sum())})

sizing = json.loads((TAB / "10_sizing.json").read_text())

# ---------- weekly facts (compact, for the LLM summary; every number here is citable) ----------
anom_placeholder = "see anomalies.json"
weekly_facts = {}
for w in WEEKS:
    tr = trailing[str(w)]
    l1, l4w, ptdw = tr["L1W"], tr["L4W"], tr["PTD"]
    inv_w = [x for x in inventory_by_week if x["year"] == "TY" and x["wk"] == w]
    low = sorted(inv_w, key=lambda x: x["wos"])[:2]
    high = sorted(inv_w, key=lambda x: -x["wos"])[:2]
    pw = [x for x in products_by_week if x["wk"] == w and x["window"] == "L4W"]
    top = sorted(pw, key=lambda x: -(x["contrib_pts"] or 0))[:3]
    bot = sorted(pw, key=lambda x: (x["contrib_pts"] or 0))[:2]
    weekly_facts[str(w)] = {
        "week": f"FY26 W{w}", "is_partial_week": w == 30, "days_in_week": 4 if w == 30 else 7,
        "l1w_sales_ty": l1["sales"]["ty"], "l1w_sales_ly": l1["sales"]["ly"], "l1w_sales_yoy_pct": l1["sales"]["yoy_pct"],
        "l1w_txns_yoy_pct": l1["txns"]["yoy_pct"], "l1w_aov_ty": l1["aov"]["ty"], "l1w_aov_yoy_pct": l1["aov"]["yoy_pct"],
        "l1w_sales_wow_pct": (l1["wow"] or {}).get("sales"),
        "l4w_weeks": l4w["weeks"], "l4w_sales_yoy_pct": l4w["sales"]["yoy_pct"], "l4w_txns_yoy_pct": l4w["txns"]["yoy_pct"],
        "ptd_sales_yoy_pct": ptdw["sales"]["yoy_pct"],
        "l1w_genz_new_ty": l1["genz_new"]["ty"], "l1w_genz_new_ly": l1["genz_new"]["ly"], "l1w_genz_new_yoy_pct": l1["genz_new"]["yoy_pct"],
        "l1w_genz_share_of_new_ty": l1["genz_share_of_new"]["ty"], "l1w_genz_share_of_new_ly": l1["genz_share_of_new"]["ly"],
        "l4w_genz_new_ty": l4w["genz_new"]["ty"], "l4w_genz_new_ly": l4w["genz_new"]["ly"], "l4w_genz_new_yoy_pct": l4w["genz_new"]["yoy_pct"],
        "l4w_returning_yoy_pct": l4w["returning_customers"]["yoy_pct"],
        "l4w_genz_new_insider_rate_ty": l4w["genz_new_insider_rate"]["ty"],
        "l4w_top_families_by_contrib": [{"family": x["family"], "contrib_pts": x["contrib_pts"], "sales_yoy_pct": x["sales_yoy_pct"]} for x in top],
        "l4w_bottom_families_by_contrib": [{"family": x["family"], "contrib_pts": x["contrib_pts"], "sales_yoy_pct": x["sales_yoy_pct"]} for x in bot],
        "lowest_wos_families": [{"family": x["family"], "wos": x["wos"], "wos_ly_same_week": x["wos_ly_same_week"]} for x in low],
        "highest_wos_families": [{"family": x["family"], "wos": x["wos"], "wos_ly_same_week": x["wos_ly_same_week"]} for x in high],
        "anomalies": anom_placeholder,
    }

# ---------- dashboard views (web app; precomputed so the front end does no arithmetic) ----------
# Basis gap (F2): what the 3 extra LY days are worth and how many points they shave off the headline.
meta["basis_alternatives"]["naive_gap_pts"] = r((meta["basis_alternatives"]["like_for_like_sales_yoy_pct"]
                                                 - meta["basis_alternatives"]["naive_all_rows_sales_yoy_pct"]) * 100, 2)
meta["basis_alternatives"]["ly_extra_days_sales"] = r(meta["basis_alternatives"]["naive_ly_sales"] - headline["sales"]["ly"], 2)
# W30 by weekday (M6): TY has Sun–Wed only; LY Thu–Sat are outside the like-for-like window.
_w30 = d[d.WK == 30].groupby(["YEAR", "DAY_IN_WK"]).DEMAND_AMT.sum()
_DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
w30_daily = [{"day": _DAYS[i], "ty": r(_w30.get(("TY", i)), 2) if ("TY", i) in _w30.index else None,
              "ly": r(_w30.get(("LY", i)), 2), "ly_in_like_for_like": bool(i <= 3)} for i in range(7)]
assert abs(sum(x["ly"] for x in w30_daily) - meta["ly_w30_full_week_sales"]) < 0.05
assert abs(sum(x["ly"] for x in w30_daily if x["ly_in_like_for_like"]) - weekly[-1]["sales"]["ly"]) < 0.05
# Stock share vs demand share per family (M5), same definitions as script 08: TY stock = W30 EOH, LY stock = W29 EOH,
# demand = L4W (W26–W29) units of the same year.
_pos = pd.DataFrame(inventory_position)
_shares = pd.DataFrame({
    "family": _pos.STYLE_GROUP,
    "stock_share_ly": _pos.eoh_W29_LY / _pos.eoh_W29_LY.sum(), "demand_share_ly": _pos.l4w_units_LY / _pos.l4w_units_LY.sum(),
    "stock_share_ty": _pos.eoh_W30_TY / _pos.eoh_W30_TY.sum(), "demand_share_ty": _pos.l4w_units_TY / _pos.l4w_units_TY.sum(),
    "g3_class": _pos.g3_class, "prod_type": _pos.PROD_TYPE})
stock_demand_shares = {
    "families": [{k: (r(v) if isinstance(v, float) else v) for k, v in row.items()} for row in _shares.to_dict("records")],
    "corr_ly": r(np.corrcoef(_pos.eoh_W29_LY, _pos.l4w_units_LY)[0, 1]),
    "corr_ty": r(np.corrcoef(_pos.eoh_W30_TY, _pos.l4w_units_TY)[0, 1]),
    "basis": "stock = end-of-week on hand (TY W30, LY W29); demand = L4W W26–W29 units; shares of the 21-family total",
}
assert round(stock_demand_shares["corr_ly"], 2) == 0.96 and round(stock_demand_shares["corr_ty"], 2) == 0.33, "corr vs FINDINGS F11"
# Growth drill-down (M3): PTD demand growth → drivers → families → styles. Shares of total growth (sum to 1).
_fam = sorted(products_ptd, key=lambda x: -x["share_of_growth"])
_hero = [x for x in _fam if x["STYLE_GROUP"] in ("Tabby", "Pillow Tabby")]
_dec = {x["factor"]: x for x in decomposition}
growth_drill = {
    "total": {"ty": headline["sales"]["ty"], "ly": headline["sales"]["ly"], "yoy_pct": headline["sales"]["yoy_pct"],
              "usd_change": r(headline["sales"]["ty"] - headline["sales"]["ly"], 2)},
    "drivers": [
        {"label": "More customers", "share_of_growth": _dec["customers"]["share_of_growth"], "pct_chg": _dec["customers"]["pct_chg"]},
        {"label": "Higher price per unit", "share_of_growth": _dec["AUR"]["share_of_growth"], "pct_chg": _dec["AUR"]["pct_chg"]},
        {"label": "Basket & frequency", "share_of_growth": r(_dec["UPT"]["share_of_growth"] + _dec["frequency (txn/cust)"]["share_of_growth"]),
         "pct_chg": None},
    ],
    "families": [{"family": x["STYLE_GROUP"], "share_of_growth": x["share_of_growth"], "sales_yoy_pct": x["sales_yoy_pct"],
                  "class": x["class"]} for x in _fam],
    "hero_share_of_growth": r(sum(x["share_of_growth"] for x in _hero)),
    "other_gainers_share_of_growth": r(sum(x["share_of_growth"] for x in _fam if x["share_of_growth"] > 0 and x not in _hero)),
    "drags_share_of_growth": r(sum(x["share_of_growth"] for x in _fam if x["share_of_growth"] < 0)),
    "styles": {},
}
for fam_name in ("Tabby", "Pillow Tabby"):
    sty = sorted([s for s in styles_ptd if s["STYLE_GROUP"] == fam_name], key=lambda s: -s["share_of_growth"])
    fam_share = next(x["share_of_growth"] for x in _fam if x["STYLE_GROUP"] == fam_name)
    growth_drill["styles"][fam_name] = {
        "family_share_of_growth": fam_share,
        "styles": [{"style": s["STYLE_DESC"], "share_of_growth": s["share_of_growth"], "sales_yoy_pct": s["sales_yoy_pct"]} for s in sty],
        "other_styles_share_of_growth": r(fam_share - sum(s["share_of_growth"] for s in sty)),
    }
assert abs(growth_drill["hero_share_of_growth"] + growth_drill["other_gainers_share_of_growth"]
           + growth_drill["drags_share_of_growth"] - 1) < 0.002, "family shares of growth must sum to 1"

metrics = {
    "meta": meta, "headline_ptd": headline, "decomposition_ptd": decomposition, "weekly": weekly, "trailing": trailing,
    "w30_daily": w30_daily, "stock_demand_shares": stock_demand_shares, "growth_drill": growth_drill,
    "generation_weekly": gen_weekly, "genz_weekly": genz_weekly, "generation_ptd": genz_ptd,
    "first_purchase_mix": first_purchase_mix, "new_genz_value": new_genz_value, "new_insider_by_segment": new_insider_by_segment,
    "products_ptd": products_ptd, "styles_ptd": styles_ptd, "products_by_week": products_by_week,
    "inventory_by_week": inventory_by_week, "inventory_totals_by_week": inv_tot, "inventory_position": inventory_position,
    "recommendations_sizing": sizing, "weekly_facts": weekly_facts,
}
(PROC / "metrics.json").write_text(json.dumps(metrics, indent=1, default=lambda o: r(o) if isinstance(o, (np.generic,)) else str(o)))

# tidy CSVs mirroring JSON sections
wk_rows = []
for row in weekly:
    flat = {"wk": row["wk"], "is_partial": row["is_partial"]}
    for m in COMP:
        for k, v in row[m].items():
            flat[f"{m}_{k}"] = v
    wk_rows.append(flat)
pd.DataFrame(wk_rows).to_csv(PROC / "metrics_weekly.csv", index=False)
tr_rows = []
for w, blk in trailing.items():
    for win in ["L1W", "L4W", "PTD"]:
        flat = {"selected_wk": int(w), "window": win, "weeks": "-".join(map(str, blk[win]["weeks"]))}
        for m in COMP:
            for k, v in blk[win][m].items():
                flat[f"{m}_{k}"] = v
        tr_rows.append(flat)
pd.DataFrame(tr_rows).to_csv(PROC / "metrics_trailing.csv", index=False)
pd.DataFrame(gen_weekly).to_csv(PROC / "metrics_generation_weekly.csv", index=False)
pd.DataFrame(products_by_week).to_csv(PROC / "metrics_products_by_week.csv", index=False)
pd.DataFrame(inventory_by_week).to_csv(PROC / "metrics_inventory_by_week.csv", index=False)

# ---------- self-checks (cross-method) ----------
chk = []
assert abs(headline["sales"]["ty"] - d[d.YEAR == "TY"].DEMAND_AMT.sum()) < 0.01
assert abs(headline["sales"]["ly"] - (d[d.YEAR == "LY"].DEMAND_AMT.sum() - d[~d.IN_TY_WINDOW].DEMAND_AMT.sum())) < 0.01
assert abs(sum(x["sales"]["ty"] for x in weekly) - headline["sales"]["ty"]) < 0.05
assert trailing["30"]["PTD"]["sales"]["ty"] == headline["sales"]["ty"]
assert sum(x["genz_new"]["ty"] for x in weekly) == headline["genz_new"]["ty"] == 240
k05 = pd.read_csv(TAB / "05_g1_kpi_windows.csv")
v05 = k05[(k05.window == "L4W (W26–W29)") & (k05.metric == "sales")].TY.iloc[0]
assert abs(v05 - trailing["29"]["L4W"]["sales"]["ty"]) < 0.01, "L4W mismatch vs 05"
for w in WEEKS:  # weekly facts must equal trailing values
    assert weekly_facts[str(w)]["l1w_sales_ty"] == trailing[str(w)]["L1W"]["sales"]["ty"]
print(f"metrics.json written: {len(json.dumps(metrics))/1024:.0f} KB; weeks {WEEKS}; "
      f"{len(products_by_week)} product-week rows; {len(inventory_by_week)} inventory rows; all self-checks passed")
