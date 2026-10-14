"""08 - G4 inventory alignment (D9).

Join weekly sales units to end-of-week on-hand snapshots at FY x WK x STYLE_GROUP.
  WOS_t      = EOH_t / avg weekly units over trailing <=4 FULL weeks ending at t (TY W30 uses W26–W29)
  ST_t       = units_t / (units_t + EOH_t)     (weekly sell-through, ≈ units / BOH)
  window ST  = units W23–W29 / (units W23–W29 + EOH W29)
Like-for-like position: as of W29 (both years complete). TY latest: W30 snapshot / W26–W29 avg.
Snapshots are NEVER summed across weeks.

Classification (relative thresholds because the sample-vs-stock scale is unknown, D9):
  Overstock risk : WOS >= 1.5 x median family WOS  AND  (L4W units YoY < 0 OR PTD demand YoY < 0)
  Understock risk: WOS <= 0.67 x median family WOS AND  L4W units YoY > 0
Plus stock-vs-demand share gap: share of total EOH minus share of L4W units.

Outputs: outputs/tables/08_g4_weekly_family.csv, 08_g4_position.csv, 08_g4_summary.md
         outputs/figures/g4_weeks_of_supply_by_family.png, g4_stock_vs_demand_share.png
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from _common import load_lines, load_inventory, style, save, C, TAB, fmt_pct, L4W

d = load_lines()
inv = load_inventory()
n_inv = len(inv)

# weekly units per family (actual weeks; TY W30 is partial and flagged)
u = d.groupby(["YEAR", "WK", "STYLE_GROUP"]).agg(units=("UNIT_QTY", "sum"), sales=("DEMAND_AMT", "sum")).reset_index()
w = inv.merge(u, on=["YEAR", "WK", "STYLE_GROUP"], how="left", validate="one_to_one")
assert len(w) == n_inv, "row count changed on join"
n_zero = int(w.units.isna().sum())
w[["units", "sales"]] = w[["units", "sales"]].fillna(0)
w["partial_sales_wk"] = (w.YEAR == "TY") & (w.WK == 30)
w = w.sort_values(["YEAR", "STYLE_GROUP", "WK"])


def trailing_avg(g):
    full = g.units.where(~g.partial_sales_wk)
    # trailing mean of up to 4 full weeks, ending at t; for a partial week use the previous 4 full weeks
    out, win = [], []
    for wk, val, part in zip(g.WK, full, g.partial_sales_wk):
        hist = [v for (k, v) in zip(g.WK, full) if k <= wk and not np.isnan(v)][-4:]
        out.append(np.mean(hist))
        win.append(len(hist))
    return pd.DataFrame({"avg_units_trailing": out, "wos_window_weeks": win}, index=g.index)


w = w.join(w.groupby(["YEAR", "STYLE_GROUP"], group_keys=False).apply(trailing_avg))
w["wos"] = w.ON_HAND_UNITS / w.avg_units_trailing
w["sell_through_wk"] = np.where(w.partial_sales_wk, np.nan, w.units / (w.units + w.ON_HAND_UNITS))
# scale check (D9): implied receipts = EOH_t - EOH_{t-1} + units_t. If sample sales and stock are on the
# same scale, receipts should be >= 0 (stock can't fall by more than what was sold).
w["implied_receipts"] = w.groupby(["YEAR", "STYLE_GROUP"]).ON_HAND_UNITS.diff() + w.units
w.loc[w.partial_sales_wk, "implied_receipts"] = np.nan
w.to_csv(TAB / "08_g4_weekly_family.csv", index=False)
rc = w.implied_receipts.dropna()
scale_line = (f"- Scale check (D9): implied receipts (ΔEOH + units) over {len(rc)} family-weeks: "
              f"{(rc < 0).mean():.1%} negative, median {rc.median():.1f} units/wk, min {rc.min():.0f}. "
              "Few negatives ⇒ sample sales and stock snapshots are on a consistent scale.")

# ---------- position table ----------
def pos(year, wk):
    s = w[(w.YEAR == year) & (w.WK == wk)].set_index("STYLE_GROUP")
    return s


ty29, ly29, ty30 = pos("TY", 29), pos("LY", 29), pos("TY", 30)
l4 = d[d.WK.isin(L4W)].groupby(["STYLE_GROUP", "YEAR"]).UNIT_QTY.sum().unstack()
win_units = d[d.WK <= 29].groupby(["STYLE_GROUP", "YEAR"]).UNIT_QTY.sum().unstack()
P = pd.DataFrame({
    "PROD_TYPE": ty29.PROD_TYPE, "PROD_CATEGORY": ty29.PROD_CATEGORY,
    "eoh_W29_TY": ty29.ON_HAND_UNITS, "eoh_W29_LY": ly29.ON_HAND_UNITS, "eoh_W30_TY": ty30.ON_HAND_UNITS,
    "l4w_units_TY": l4.TY, "l4w_units_LY": l4.LY,
    "wos_W29_TY": ty29.wos, "wos_W29_LY": ly29.wos, "wos_W30_TY_latest": ty30.wos,
})
P["eoh_yoy_pct"] = P.eoh_W29_TY / P.eoh_W29_LY - 1
P["l4w_units_yoy_pct"] = P.l4w_units_TY / P.l4w_units_LY - 1
P["wos_chg_W29"] = P.wos_W29_TY - P.wos_W29_LY
P["st_W23_29_TY"] = win_units.TY / (win_units.TY + P.eoh_W29_TY)
P["st_W23_29_LY"] = win_units.LY / (win_units.LY + P.eoh_W29_LY)
P["eoh_share_TY"] = P.eoh_W30_TY / P.eoh_W30_TY.sum()
P["demand_share_TY"] = P.l4w_units_TY / P.l4w_units_TY.sum()
P["stock_minus_demand_share_pts"] = (P.eoh_share_TY - P.demand_share_TY) * 100
P["eoh_trend_W23_W30_TY_pct"] = ty30.ON_HAND_UNITS / pos("TY", 23).ON_HAND_UNITS - 1
med = P.wos_W30_TY_latest.median()
P["wos_vs_median"] = P.wos_W30_TY_latest / med
# join G3 scorecard flags (PTD demand YoY, winner class, Gen Z index)
g3 = pd.read_csv(TAB / "07_g3_family_scorecard.csv").set_index("STYLE_GROUP")
P["ptd_sales_yoy_pct"] = g3.sales_yoy_pct
P["risk"] = np.select([(P.wos_vs_median >= 1.5) & ((P.l4w_units_yoy_pct < 0) | (P.ptd_sales_yoy_pct < 0)),
                       (P.wos_vs_median <= 0.67) & (P.l4w_units_yoy_pct > 0)],
                      ["Overstock risk", "Understock risk"], default="In band")
P["g3_class"] = g3["class"]
P["genz_index_TY"] = g3.genz_index_TY
P["genz_gateway"] = g3.genz_gateway
# replenishment: implied receipts W24–W29 (complete weeks with a prior snapshot) TY vs LY
rec = w[w.WK.between(24, 29)].groupby(["STYLE_GROUP", "YEAR"]).implied_receipts.sum().unstack()
P["receipts_W24_29_TY"] = rec.TY
P["receipts_W24_29_LY"] = rec.LY
P["receipts_yoy_pct"] = rec.TY / rec.LY - 1
units_24_29 = d[d.WK.between(24, 29)].groupby(["STYLE_GROUP", "YEAR"]).UNIT_QTY.sum().unstack()
P["receipts_to_sales_TY"] = rec.TY / units_24_29.TY   # <1 = drawing stock down
P["receipts_to_sales_LY"] = rec.LY / units_24_29.LY
P = P.sort_values("wos_W30_TY_latest")
P.to_csv(TAB / "08_g4_position.csv")
corr_rec_ty = np.corrcoef(rec.TY, units_24_29.TY)[0, 1]
corr_rec_ly = np.corrcoef(rec.LY, units_24_29.LY)[0, 1]

# aggregate (sum of snapshots ACROSS FAMILIES within the same week is valid)
agg = w.groupby(["YEAR", "WK"]).agg(eoh=("ON_HAND_UNITS", "sum"), units=("units", "sum")).unstack("YEAR")
corr_ty = np.corrcoef(P.eoh_W30_TY, P.l4w_units_TY)[0, 1]
corr_ly = np.corrcoef(P.eoh_W29_LY, P.l4w_units_LY)[0, 1]

S = ["# G4 summary (08_g4_inventory.py)", "",
     f"- Inventory rows {n_inv}; joined to sales 1:1 (validate one_to_one), {n_zero} family-weeks with zero sales units",
     scale_line,
     f"- Median family WOS (TY latest, W30 EOH / W26–29 avg): {med:.2f} weeks",
     f"- Total EOH W29 TY {int(P.eoh_W29_TY.sum())} vs LY {int(P.eoh_W29_LY.sum())} ({fmt_pct(P.eoh_W29_TY.sum()/P.eoh_W29_LY.sum()-1)}); "
     f"L4W units TY {int(P.l4w_units_TY.sum())} vs LY {int(P.l4w_units_LY.sum())} ({fmt_pct(P.l4w_units_TY.sum()/P.l4w_units_LY.sum()-1)})",
     f"- Aggregate WOS W29: TY {P.eoh_W29_TY.sum()/(P.l4w_units_TY.sum()/4):.2f} vs LY {P.eoh_W29_LY.sum()/(P.l4w_units_LY.sum()/4):.2f}",
     f"- Correlation of family stock with family L4W units: TY {corr_ty:.2f} (W30 EOH), LY {corr_ly:.2f} (W29 EOH)",
     f"- Replenishment W24–29: total implied receipts TY {rec.TY.sum():.0f} vs LY {rec.LY.sum():.0f}; receipts-to-units ratio TY {rec.TY.sum()/units_24_29.TY.sum():.2f} vs LY {rec.LY.sum()/units_24_29.LY.sum():.2f}; "
     f"correlation of family receipts with family units TY {corr_rec_ty:.2f} vs LY {corr_rec_ly:.2f}",
     "", "## Replenishment by family (W24–W29)",
     P[["receipts_W24_29_TY", "receipts_W24_29_LY", "receipts_yoy_pct", "receipts_to_sales_TY", "receipts_to_sales_LY", "l4w_units_yoy_pct", "risk"]].sort_values("receipts_to_sales_TY").round(2).to_markdown(),
     "", "## Family position (sorted by TY latest WOS)",
     P.round(3).to_markdown(), "",
     "## Weekly totals (sum across families within week; NOT across weeks)", agg.to_markdown()]

# ---------- figures ----------
style()
fig, ax = plt.subplots(figsize=(8, 6.2))
t = P.sort_values("wos_W30_TY_latest")
y = np.arange(len(t))
for i, r in enumerate(t.itertuples()):
    ax.plot([r.wos_W29_LY, r.wos_W30_TY_latest], [i, i], color=C["grid"], lw=2, zorder=1)
ax.scatter(t.wos_W29_LY, y, color=C["ly"], s=40, zorder=2, label="LY (W29 EOH / W26–29 avg)")
riskcol = {"Overstock risk": C["serious"], "Understock risk": C["critical"], "In band": C["ty"]}
ax.scatter(t.wos_W30_TY_latest, y, color=[riskcol[r] for r in t.risk], s=55, zorder=3, edgecolor=C["surface"], linewidth=1.5,
           label="TY latest (W30 EOH / W26–29 avg)")
for i, r in enumerate(t.itertuples()):
    tag = {"Overstock risk": "  ▲ overstock", "Understock risk": "  ▼ understock", "In band": ""}[r.risk]
    ax.text(max(r.wos_W30_TY_latest, r.wos_W29_LY) + 0.3, i, f"{r.wos_W30_TY_latest:.1f} wks ({fmt_pct(r.l4w_units_yoy_pct,0)} units){tag}",
            va="center", fontsize=7.5, color=C["ink"])
ax.axvline(med, color=C["ink2"], ls="--", lw=1)
ax.text(med, len(t) - 0.3, f" median {med:.1f}", fontsize=7.5, color=C["ink2"])
ax.set_yticks(y)
ax.set_yticklabels([f"{s}{' ★' if P.loc[s, 'g3_class']=='Winner' else ''}" for s in t.index], fontsize=8.5)
ax.set_xlabel("Weeks of supply (label: TY WOS, L4W units YoY)    ★ = G3 winner")
ax.set_title("Weeks of supply by family: TY latest vs LY")
from matplotlib.lines import Line2D
ax.legend(handles=[Line2D([], [], marker="o", lw=0, ms=7, color=C["ly"], label="LY (W29 EOH / W26–29 avg units)"),
                   Line2D([], [], marker="o", lw=0, ms=7, color=C["ty"], label="TY latest, in band (W30 EOH / W26–29 avg)"),
                   Line2D([], [], marker="o", lw=0, ms=7, color=C["serious"], label="TY overstock risk"),
                   Line2D([], [], marker="o", lw=0, ms=7, color=C["critical"], label="TY understock risk")],
          loc="lower right", fontsize=8)
ax.set_xlim(0, P[["wos_W30_TY_latest", "wos_W29_LY"]].values.max() * 1.55)
ax.grid(axis="y", visible=False)
f1 = save(fig, "g4_weeks_of_supply_by_family.png")

fig, ax = plt.subplots(figsize=(7.5, 6))
t = P.sort_values("stock_minus_demand_share_pts")
ax.barh(t.index, t.stock_minus_demand_share_pts, color=[C["pos"] if v >= 0 else C["neg"] for v in t.stock_minus_demand_share_pts], height=0.6)
for i, v in enumerate(t.stock_minus_demand_share_pts):
    ax.text(v + (0.1 if v >= 0 else -0.1), i, f"{v:+.1f}", va="center", ha="left" if v >= 0 else "right", fontsize=8)
ax.axvline(0, color=C["ink2"], lw=1)
ax.set_xlabel("Share of TY stock (W30) minus share of L4W unit demand (pts)")
ax.set_title("Stock vs demand: + = over-allocated, − = under-allocated")
ax.grid(axis="y", visible=False)
ax.tick_params(axis="y", labelsize=8.5)
lo, hi = ax.get_xlim()
ax.set_xlim(lo - 0.8, hi + 0.8)
f2 = save(fig, "g4_stock_vs_demand_share.png")

# F3: Tabby franchise — stock vs demand over time (small multiples, no dual axis)
fr = w[w.STYLE_GROUP.isin(["Tabby", "Pillow Tabby"])].groupby(["YEAR", "WK"]).agg(eoh=("ON_HAND_UNITS", "sum"), units=("units", "sum")).reset_index()
fig, axes = plt.subplots(1, 2, figsize=(10, 3.6))
for ax, (col, ttl) in zip(axes, [("eoh", "End-of-week stock (units)"), ("units", "Units sold per week")]):
    for yr, colr in [("LY", C["ly"]), ("TY", C["ty"])]:
        s_ = fr[fr.YEAR == yr]
        if col == "units":
            s_ = s_[~((s_.YEAR == "TY") & (s_.WK == 30))]
        ax.plot(s_.WK, s_[col], color=colr, marker="o", ms=4, label=yr)
        ax.annotate(f"{s_[col].iloc[-1]:.0f}", (s_.WK.iloc[-1], s_[col].iloc[-1]), xytext=(6, 0), textcoords="offset points",
                    va="center", fontsize=8.5, color=C["ink"])
    ax.set_title(ttl, fontsize=10)
    ax.set_xticks(range(23, 31))
    ax.set_xticklabels([f"W{x}" for x in range(23, 31)], fontsize=8)
    ax.set_ylim(0, None)
axes[0].legend(loc="lower left")
axes[1].text(29.9, ax.get_ylim()[1] * 0.05, "TY W30 partial\n(omitted)", fontsize=7.5, color=C["ink2"], ha="right")
drawdown = 1 - fr[(fr.YEAR == "TY") & (fr.WK == 30)].eoh.iloc[0] / fr[(fr.YEAR == "TY") & (fr.WK == 23)].eoh.iloc[0]
fig.suptitle(f"Tabby + Pillow Tabby: demand up, stock drawn down {drawdown:.0%} — not replenished", x=0.06, ha="left", fontweight="bold")
fig.subplots_adjust(top=0.8, wspace=0.25)
f3 = save(fig, "g4_tabby_franchise_stock_vs_demand.png")
fr.to_csv(TAB / "08_g4_tabby_franchise_weekly.csv", index=False)
S.append(f"\n## Tabby franchise weekly (Tabby + Pillow Tabby)\n" + fr.pivot(index="WK", columns="YEAR", values=["eoh", "units"]).to_markdown())
S.append(f"- Tabby franchise EOH W23→W30 TY: {fr[(fr.YEAR=='TY')&(fr.WK==23)].eoh.iloc[0]} → {fr[(fr.YEAR=='TY')&(fr.WK==30)].eoh.iloc[0]} "
         f"({fr[(fr.YEAR=='TY')&(fr.WK==30)].eoh.iloc[0]/fr[(fr.YEAR=='TY')&(fr.WK==23)].eoh.iloc[0]-1:+.1%})")
S.append(f"\nFigures: {f1}, {f2}, {f3}")
(TAB / "08_g4_summary.md").write_text("\n".join(S))
print("\n".join(S))
