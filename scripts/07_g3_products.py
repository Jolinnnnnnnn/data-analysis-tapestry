"""07 - G3 winning products (PTD like-for-like).

Family (STYLE_GROUP) and style (STYLE_DESC) level:
  * YoY demand/units/txn growth with min-volume threshold (D12) and Poisson significance on txn counts
  * contribution to total YoY demand growth (pts)
  * Gen Z over-index = family Gen Z share of txns / overall Gen Z share (TY)
  * New-customer share & Gen Z-new index (acquisition power)
  * "gateway that sticks" proxy: index among NEW Gen Z AND among RETURNING Gen Z (D8: cohort repeat not measurable)
  * winner classification rule

Outputs: outputs/tables/07_g3_family_scorecard.csv, 07_g3_style_scorecard.csv, 07_g3_summary.md
         outputs/figures/g3_family_growth_vs_genz_index.png, g3_family_growth_contribution.png
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from _common import load_lines, ptd, poisson_count_test, style, save, C, TAB, fmt_pct

MIN_LINES = 30  # TY+LY lines per family (D12)
MIN_LINES_STYLE = 20
d = load_lines()
p = ptd(d)
ty, ly = p[p.YEAR == "TY"], p[p.YEAR == "LY"]
LY_TOT, TY_TOT = ly.DEMAND_AMT.sum(), ty.DEMAND_AMT.sum()
genz_share_ty = ty.IS_GENZ.mean()
genz_share_ly = ly.IS_GENZ.mean()
new_share_ty = ty.IS_NEW.mean()
gz_new_ty = ty[ty.IS_GENZ & ty.IS_NEW]
gz_ret_ty = ty[ty.IS_GENZ & ty.IS_RETURNING]
other_new_ty = ty[~ty.IS_GENZ & ty.IS_NEW]


def scorecard(level):
    keys = [level] + (["STYLE_GROUP"] if level == "STYLE_DESC" else []) + ["PROD_CATEGORY", "PROD_TYPE"]
    g = p.groupby(keys + ["YEAR"]).agg(sales=("DEMAND_AMT", "sum"), units=("UNIT_QTY", "sum"),
                                         txns=("TXN_ID", "nunique")).unstack("YEAR").fillna(0)
    g.columns = [f"{a}_{b}" for a, b in g.columns]
    g = g.reset_index()
    g["sales_yoy_pct"] = g.sales_TY / g.sales_LY - 1
    g["units_yoy_pct"] = g.units_TY / g.units_LY - 1
    g["txns_yoy_pct"] = g.txns_TY / g.txns_LY - 1
    g["txn_count_p"] = [poisson_count_test(a, b)[1] for a, b in zip(g.txns_TY, g.txns_LY)]
    g["contrib_pts"] = (g.sales_TY - g.sales_LY) / LY_TOT
    g["share_of_growth"] = (g.sales_TY - g.sales_LY) / (TY_TOT - LY_TOT)
    g["sales_share_TY"] = g.sales_TY / TY_TOT
    # Gen Z & acquisition indices (TY)
    tg = ty.groupby(level)
    g["genz_share_TY"] = g[level].map(tg.IS_GENZ.mean())
    g["genz_share_LY"] = g[level].map(ly.groupby(level).IS_GENZ.mean())
    g["genz_index_TY"] = g.genz_share_TY / genz_share_ty * 100
    g["genz_txns_TY"] = g[level].map(tg.IS_GENZ.sum()).fillna(0)
    g["genz_txns_LY"] = g[level].map(ly.groupby(level).IS_GENZ.sum()).fillna(0)
    g["genz_txns_yoy_pct"] = g.genz_txns_TY / g.genz_txns_LY - 1
    g["new_share_TY"] = g[level].map(tg.IS_NEW.mean())
    g["new_index_TY"] = g.new_share_TY / new_share_ty * 100
    # index among NEW Gen Z first purchases vs other new; and among RETURNING Gen Z vs all returning
    g["genz_new_n_TY"] = g[level].map(gz_new_ty[level].value_counts()).fillna(0)
    g["genz_new_mix_index"] = (g.genz_new_n_TY / len(gz_new_ty)) / \
        (g[level].map(other_new_ty[level].value_counts()).fillna(0) / len(other_new_ty)) * 100
    ret_all = ty[ty.IS_RETURNING]
    g["genz_ret_n_TY"] = g[level].map(gz_ret_ty[level].value_counts()).fillna(0)
    g["genz_ret_mix_index"] = (g.genz_ret_n_TY / len(gz_ret_ty)) / \
        (g[level].map(ret_all[~ret_all.IS_GENZ][level].value_counts()).fillna(0) / (~ret_all.IS_GENZ).sum()) * 100
    g["outlet_share_TY"] = g[level].map(tg.IS_OUTLET.mean())
    g["vol_ok"] = (g.txns_TY + g.txns_LY) >= (MIN_LINES if level == "STYLE_GROUP" else MIN_LINES_STYLE)
    return g


fam = scorecard("STYLE_GROUP")
# Winner rule: volume OK, demand YoY >= +20%, txn growth significant (p<0.10), positive contribution.
fam["class"] = np.select(
    [fam.vol_ok & (fam.sales_yoy_pct >= 0.20) & (fam.txn_count_p < 0.10),
     fam.vol_ok & (fam.sales_yoy_pct <= -0.15) & (fam.txn_count_p < 0.10)],
    ["Winner", "Decliner"], default="Steady")
fam["genz_gateway"] = (fam.genz_new_mix_index >= 120) & (fam.genz_new_n_TY >= 10)
fam = fam.sort_values("contrib_pts", ascending=False)
fam.to_csv(TAB / "07_g3_family_scorecard.csv", index=False)

sty = scorecard("STYLE_DESC").sort_values("contrib_pts", ascending=False)
sty.to_csv(TAB / "07_g3_style_scorecard.csv", index=False)

# PROD_TYPE rollup
pt = p.groupby(["PROD_TYPE", "YEAR"]).DEMAND_AMT.sum().unstack()
pt["yoy_pct"] = pt.TY / pt.LY - 1
pt["contrib_pts"] = (pt.TY - pt.LY) / LY_TOT
pt["genz_index_TY"] = ty.groupby("PROD_TYPE").IS_GENZ.mean() / genz_share_ty * 100

# concentration: top-3 families' share of growth
top3 = fam.head(3)
S = ["# G3 summary (07_g3_products.py) — PTD like-for-like", "",
     f"Overall TY Gen Z share of txns {genz_share_ty:.1%} (LY {genz_share_ly:.1%}); TY new share {new_share_ty:.1%}",
     f"Min volume: families ≥{MIN_LINES} TY+LY lines (all {int(fam.vol_ok.sum())}/{len(fam)} pass); styles ≥{MIN_LINES_STYLE}", "",
     "## Family scorecard (sorted by contribution)",
     fam[["STYLE_GROUP", "PROD_TYPE", "sales_TY", "sales_LY", "sales_yoy_pct", "txns_TY", "txns_LY", "txn_count_p",
          "contrib_pts", "share_of_growth", "genz_index_TY", "genz_txns_yoy_pct", "new_index_TY", "genz_new_mix_index",
          "genz_ret_mix_index", "outlet_share_TY", "class", "genz_gateway"]].round(3).to_markdown(index=False),
     "", f"- Top-3 families ({', '.join(top3.STYLE_GROUP)}) = {top3.share_of_growth.sum():.0%} of total demand growth",
     f"- Winners: {', '.join(fam[fam['class']=='Winner'].STYLE_GROUP)}",
     f"- Decliners: {', '.join(fam[fam['class']=='Decliner'].STYLE_GROUP)}",
     f"- Gen Z gateways (new Gen Z mix index ≥120, n≥10): {', '.join(fam[fam.genz_gateway].STYLE_GROUP)}",
     "", "## PROD_TYPE", pt.round(3).to_markdown(), "",
     "## Style scorecard (vol ok, top/bottom by contribution)",
     sty[sty.vol_ok][["STYLE_DESC", "STYLE_GROUP", "PROD_TYPE", "sales_TY", "sales_LY", "sales_yoy_pct", "txns_TY",
                      "txns_LY", "txn_count_p", "contrib_pts", "genz_index_TY", "genz_new_mix_index"]].round(3).to_markdown(index=False)]

# ---------- figures ----------
style()
fig, ax = plt.subplots(figsize=(8.5, 5.5))
cols = {"Winner": C["ty"], "Decliner": C["neg"], "Steady": C["ly"]}
for cl, sub in fam.groupby("class"):
    ax.scatter(sub.sales_yoy_pct * 100, sub.genz_index_TY, s=sub.sales_TY / 110, color=cols[cl], alpha=0.85,
               edgecolor=C["surface"], linewidth=2, label=cl, zorder=3)
for r in fam.itertuples():
    left = r.STYLE_GROUP in ("Lowline Sneaker", "Fragrance")
    ax.annotate(r.STYLE_GROUP, (r.sales_yoy_pct * 100, r.genz_index_TY), xytext=(-8 if left else 8, -11 if left else 5),
                textcoords="offset points", ha="right" if left else "left", fontsize=7.5, color=C["ink"])
ax.axhline(100, color=C["ink2"], lw=1, ls="--")
ax.axvline(fam.sales_TY.sum() / fam.sales_LY.sum() * 100 - 100, color=C["ink2"], lw=1, ls=":")
ax.text(ax.get_xlim()[0] + 1, 101, "Gen Z index 100 = avg", fontsize=7.5, color=C["ink2"])
ax.text(fam.sales_TY.sum() / fam.sales_LY.sum() * 100 - 99, ax.get_ylim()[0] + 2, f"total {fmt_pct(TY_TOT/LY_TOT-1)}", fontsize=7.5, color=C["ink2"])
ax.set_xlabel("Demand YoY % (PTD like-for-like)")
ax.set_ylabel("Gen Z over-index (TY; 100 = avg)")
ax.set_title("Product families: growth vs Gen Z appeal (bubble = TY demand)")
from matplotlib.lines import Line2D
ax.legend(handles=[Line2D([], [], marker="o", lw=0, ms=8, color=cols[k], label=k) for k in ["Winner", "Steady", "Decliner"]], loc="lower right")
f1 = save(fig, "g3_family_growth_vs_genz_index.png")

fig, ax = plt.subplots(figsize=(7.5, 6))
t = fam.sort_values("contrib_pts")
ax.barh(t.STYLE_GROUP, t.contrib_pts * 100, color=[cols[c] for c in t["class"]], height=0.6)
for i, r in enumerate(t.itertuples()):
    v = r.contrib_pts * 100
    ax.text(v + (0.08 if v >= 0 else -0.08), i, f"{v:+.1f} pts ({fmt_pct(r.sales_yoy_pct,0)})", va="center",
            ha="left" if v >= 0 else "right", fontsize=7.5)
ax.axvline(0, color=C["ink2"], lw=1)
ax.set_xlabel("Contribution to total YoY demand growth (pts); label = family YoY")
ax.set_title(f"Which families drove the {fmt_pct(TY_TOT/LY_TOT-1)}  (blue = Winner, red = Decliner)")
ax.grid(axis="y", visible=False)
ax.tick_params(axis="y", labelsize=8.5)
lo, hi = ax.get_xlim()
ax.set_xlim(lo - 1.8, hi + 1.4)
f2 = save(fig, "g3_family_growth_contribution.png")

S.append(f"\nFigures: {f1}, {f2}")
(TAB / "07_g3_summary.md").write_text("\n".join(S))
print("\n".join(S))
