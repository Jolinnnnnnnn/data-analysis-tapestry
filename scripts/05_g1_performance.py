"""05 - G1 performance: TY vs LY (period-to-date like-for-like), L1W, L4W, WTD, WoW;
weekly trend; YoY decomposition (customers x frequency x AOV; AOV = UPT x AUR);
segment contribution to YoY growth with significance.

Outputs: outputs/tables/05_g1_kpi_windows.csv/.md, 05_g1_weekly.csv, 05_g1_decomposition.csv,
         05_g1_contribution.csv, 05_g1_summary.md
         outputs/figures/g1_weekly_sales_ty_vs_ly.png, g1_yoy_decomposition.png, g1_growth_contribution_by_segment.png
"""
import numpy as np
import pandas as pd
from _common import (load_lines, ptd, kpis, yoy_table, bootstrap_diff_mean, poisson_count_test,
                     style, save, C, TAB, fmt_pct, LAST_FULL_WK, L4W, WTD_WK)
import matplotlib.pyplot as plt

d = load_lines()
p = ptd(d)
assert len(d) - len(p) == 90  # 03_clean log: 90 LY W30 lines outside window

# ---------- KPI windows ----------
win = {
    "PTD (W23–W30 Wed, like-for-like)": p,
    "PTD alt-a (all rows, LY full W30)": d,
    "Full weeks W23–W29": d[d.WK <= LAST_FULL_WK],
    "L1W (W29)": d[d.WK == LAST_FULL_WK],
    "L4W (W26–W29)": d[d.WK.isin(L4W)],
    "WTD (W30 Sun–Wed)": p[p.WK == WTD_WK],
}
rows = []
for k, df in win.items():
    t = yoy_table(df, k)
    rows.append(t.reset_index().rename(columns={"index": "metric"}))
kw = pd.concat(rows)
kw.to_csv(TAB / "05_g1_kpi_windows.csv", index=False)

# WoW and vs prior period (TY only)
ty = d[d.YEAR == "TY"]
w29, w28 = kpis(ty[ty.WK == 29]), kpis(ty[ty.WK == 28])
l4, prior3 = kpis(ty[ty.WK.isin(L4W)]), kpis(ty[ty.WK.isin([23, 24, 25])])
wow = pd.DataFrame({"W29": w29, "W28": w28, "wow_pct": w29 / w28 - 1,
                    "L4W_wkly_avg": l4 / 4, "prior_W23-25_wkly_avg": prior3 / 3,
                    "l4w_vs_prior_pct": (l4 / 4) / (prior3 / 3) - 1})
# ratios shouldn't be averaged per week; recompute ratio rows from totals
for r in ["aov", "upt", "aur", "freq"]:
    wow.loc[r, "L4W_wkly_avg"], wow.loc[r, "prior_W23-25_wkly_avg"] = l4[r], prior3[r]
    wow.loc[r, "l4w_vs_prior_pct"] = l4[r] / prior3[r] - 1
wow.to_csv(TAB / "05_g1_wow_prior.csv")

# ---------- weekly trend ----------
wk = (p.groupby(["YEAR", "WK"])[p.columns.tolist()].apply(kpis).reset_index())
wk_full_ly30 = kpis(d[(d.YEAR == "LY") & (d.WK == 30)])
wkw = wk.pivot(index="WK", columns="YEAR")
weekly = pd.DataFrame({
    "wk": wkw.index, "sales_ty": wkw[("sales", "TY")].values, "sales_ly": wkw[("sales", "LY")].values,
    "txns_ty": wkw[("txns", "TY")].values, "txns_ly": wkw[("txns", "LY")].values,
    "units_ty": wkw[("units", "TY")].values, "units_ly": wkw[("units", "LY")].values,
    "aov_ty": wkw[("aov", "TY")].values, "aov_ly": wkw[("aov", "LY")].values,
})
weekly["sales_yoy_pct"] = weekly.sales_ty / weekly.sales_ly - 1
weekly["txns_yoy_pct"] = weekly.txns_ty / weekly.txns_ly - 1
weekly["aov_yoy_pct"] = weekly.aov_ty / weekly.aov_ly - 1
weekly["sales_ty_wow_pct"] = weekly.sales_ty.pct_change()
weekly["partial_week"] = weekly.wk == WTD_WK
weekly.loc[weekly.wk == WTD_WK, "sales_ty_wow_pct"] = np.nan  # not comparable (4 days vs 7)
weekly.to_csv(TAB / "05_g1_weekly.csv", index=False)

# ---------- decomposition (PTD) ----------
T, Lr = kpis(p[p.YEAR == "TY"]), kpis(p[p.YEAR == "LY"])
comp = {"customers": T.customers / Lr.customers, "frequency (txn/cust)": T.freq / Lr.freq,
        "UPT": T.upt / Lr.upt, "AUR": T.aur / Lr.aur}
total_log = np.log(T.sales / Lr.sales)
dec = pd.DataFrame({"factor": list(comp), "ratio": list(comp.values())})
dec["pct_chg"] = dec.ratio - 1
dec["log_contrib"] = np.log(dec.ratio)
dec["share_of_growth"] = dec.log_contrib / total_log
dec["usd_contrib"] = dec.share_of_growth * (T.sales - Lr.sales)
assert np.isclose(dec.log_contrib.sum(), total_log)
dec.to_csv(TAB / "05_g1_decomposition.csv", index=False)

# AOV significance (bootstrap) and txn-count significance
aov_d, aov_lo, aov_hi, aov_p = bootstrap_diff_mean(p[p.YEAR == "TY"].DEMAND_AMT, p[p.YEAR == "LY"].DEMAND_AMT)
z_tx, p_tx = poisson_count_test(T.txns, Lr.txns)
# robustness: AOV excl top 1% lines
cap = p.DEMAND_AMT.quantile(0.99)
pt = p[p.DEMAND_AMT <= cap]
aov_trim = pt[pt.YEAR == "TY"].DEMAND_AMT.mean() / pt[pt.YEAR == "LY"].DEMAND_AMT.mean() - 1

# ---------- segment contribution ----------
seg_rows = []
LY_tot = Lr.sales
for dim in ["SALES_CHANNEL", "CHANNEL_DETAIL", "GEO_REGION", "PROD_CATEGORY", "PROD_TYPE",
            "COHORT_STATUS", "CUST_AGE_GROUP", "INSIDER_FLAG"]:
    g = p.groupby([dim, "YEAR"]).agg(sales=("DEMAND_AMT", "sum"), txns=("TXN_ID", "nunique")).unstack("YEAR").fillna(0)
    for seg, r in g.iterrows():
        z, pv = poisson_count_test(r[("txns", "TY")], r[("txns", "LY")])
        seg_rows.append({
            "dimension": dim, "segment": seg,
            "sales_ty": r[("sales", "TY")], "sales_ly": r[("sales", "LY")],
            "sales_yoy_pct": r[("sales", "TY")] / r[("sales", "LY")] - 1,
            "contrib_pts": (r[("sales", "TY")] - r[("sales", "LY")]) / LY_tot,
            "share_ty": r[("sales", "TY")] / T.sales, "share_ly": r[("sales", "LY")] / LY_tot,
            "txns_ty": r[("txns", "TY")], "txns_ly": r[("txns", "LY")], "txn_count_p": pv,
        })
seg = pd.DataFrame(seg_rows)
seg["share_chg_pts"] = seg.share_ty - seg.share_ly
seg.to_csv(TAB / "05_g1_contribution.csv", index=False)

# ---------- figures ----------
style()
fig, ax = plt.subplots(figsize=(8, 4))
x = weekly.wk
ax.plot(x, weekly.sales_ly / 1e3, color=C["ly"], marker="o", ms=5, label="LY (FY25)")
ax.plot(x, weekly.sales_ty / 1e3, color=C["ty"], marker="o", ms=5, label="TY (FY26)")
ax.plot([30], [wk_full_ly30.sales / 1e3], marker="o", ms=6, mfc="none", color=C["ly"], lw=0)
ax.annotate("LY W30\nfull week", (30, wk_full_ly30.sales / 1e3), xytext=(0, 9), textcoords="offset points",
            ha="center", fontsize=8, color=C["ink2"])
ax.axvspan(29.5, 30.5, color=C["grid"], alpha=0.5, lw=0)
ax.text(30, ax.get_ylim()[0] + 1, "W30 = Sun–Wed\n(both years)", ha="center", fontsize=8, color=C["ink2"])
for _, r in weekly.iterrows():
    ax.annotate(fmt_pct(r.sales_yoy_pct, 0), (r.wk, r.sales_ty / 1e3), xytext=(0, 8), textcoords="offset points",
                ha="center", fontsize=8, color=C["ink2"])
ax.set_xticks(x)
ax.set_xticklabels([f"W{w}" for w in x])
ax.set_ylabel("Demand ($K, sample)")
ax.set_title("Weekly demand, TY vs LY (labels = YoY %)")
ax.legend(loc="upper left", ncol=2)
f1 = save(fig, "g1_weekly_sales_ty_vs_ly.png")

fig, ax = plt.subplots(figsize=(7, 3.2))
labels = ["Customers", "Frequency", "Units / txn", "$ / unit (AUR)", "Total demand"]
vals = list(dec.pct_chg) + [T.sales / Lr.sales - 1]
cols = [C["pos"] if v >= 0 else C["neg"] for v in vals[:-1]] + [C["ink2"]]
ax.barh(labels[::-1], [v * 100 for v in vals[::-1]], color=cols[::-1], height=0.55)
for i, v in enumerate(vals[::-1]):
    ax.text(v * 100 + (0.2 if v >= 0 else -0.2), i, fmt_pct(v), va="center", ha="left" if v >= 0 else "right",
            fontsize=9, color=C["ink"])
ax.axvline(0, color=C["ink2"], lw=1)
ax.set_xlabel("YoY % change (PTD like-for-like)")
ax.set_title("Demand growth decomposition: TY vs LY")
ax.grid(axis="y", visible=False)
f2 = save(fig, "g1_yoy_decomposition.png")

fig, ax = plt.subplots(figsize=(8, 5.5))
show = seg[seg.dimension.isin(["SALES_CHANNEL", "CHANNEL_DETAIL", "GEO_REGION", "PROD_CATEGORY", "CUST_AGE_GROUP", "COHORT_STATUS"])].copy()
show["label"] = show.dimension.str.replace("_", " ").str.title() + ": " + show.segment.astype(str)
show = show.sort_values(["dimension", "contrib_pts"])
ax.barh(show.label, show.contrib_pts * 100, color=[C["pos"] if v >= 0 else C["neg"] for v in show.contrib_pts], height=0.6)
for i, (v, pv) in enumerate(zip(show.contrib_pts, show.txn_count_p)):
    ax.text(v * 100 + (0.1 if v >= 0 else -0.1), i, f"{v*100:+.1f}" + ("*" if pv < 0.05 else ""), va="center",
            ha="left" if v >= 0 else "right", fontsize=8)
ax.axvline(0, color=C["ink2"], lw=1)
ax.set_xlabel("Contribution to total YoY demand growth (pts)   * txn-count change p<0.05")
ax.set_title(f"Where the {fmt_pct(T.sales/Lr.sales-1)} came from (each dimension sums to total)")
ax.grid(axis="y", visible=False)
ax.tick_params(axis="y", labelsize=8)
f3 = save(fig, "g1_growth_contribution_by_segment.png")

# ---------- summary md ----------
S = ["# G1 summary (05_g1_performance.py)", ""]
for k in ["PTD (W23–W30 Wed, like-for-like)", "L1W (W29)", "L4W (W26–W29)", "WTD (W30 Sun–Wed)", "PTD alt-a (all rows, LY full W30)", "Full weeks W23–W29"]:
    t = kw[kw.window == k].set_index("metric")
    S.append(f"## {k}")
    S.append(t[["TY", "LY", "chg", "yoy_pct"]].round(3).to_markdown())
    S.append("")
S.append("## TY W29 vs W28 (WoW) and L4W vs prior 3 weeks (weekly avg; ratios from totals)")
S.append(wow.round(3).to_markdown())
S.append("\n## Decomposition (PTD)\n" + dec.round(4).to_markdown(index=False))
S.append(f"\n- Txn count TY {T.txns:.0f} vs LY {Lr.txns:.0f}: z={z_tx:.2f}, p={p_tx:.3f}")
S.append(f"- AOV TY ${T.aov:.2f} vs LY ${Lr.aov:.2f}: diff ${aov_d:.2f}, 95% CI [{aov_lo:.2f}, {aov_hi:.2f}], p={aov_p:.3f}")
S.append(f"- AOV YoY excl. top-1% lines (>${cap:.0f}): {fmt_pct(aov_trim)}")
S.append("\n## Weekly\n" + weekly.round(3).to_markdown(index=False))
S.append("\n## Segment contribution (top by |contrib|)\n" +
         seg.reindex(seg.contrib_pts.abs().sort_values(ascending=False).index).head(20).round(3).to_markdown(index=False))
S.append(f"\nFigures: {f1}, {f2}, {f3}")
(TAB / "05_g1_summary.md").write_text("\n".join(S))
print("\n".join(S))
