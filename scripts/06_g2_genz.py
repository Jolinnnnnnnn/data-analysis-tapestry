"""06 - G2 Gen Z acquisition & retention (PTD like-for-like basis, D3/D6/D7/D8).

1. New customers by generation TY vs LY: count, share of new, acquisition rate; significance.
2. Gen Z share of new customers by week (TY vs LY) + cumulative.
3. Gen Z growth split by cohort status (new vs returning).
4. What new Gen Z buy first: family / category / PROD_TYPE / channel / region vs other new customers (index).
5. Retention proxies by generation: returning share (Retained+Reactivated), returning counts, Insider attach of new.
6. Value of new Gen Z vs other new: AOV, UPT, AUR, outlet share, PRICE_IDX, eComm, Insider (bootstrap CIs).

Outputs: outputs/tables/06_*.csv, 06_g2_summary.md; outputs/figures/g2_*.png
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from _common import (load_lines, ptd, kpis, two_prop_z, poisson_count_test, bootstrap_diff_mean,
                     style, save, C, TAB, fmt_pct, GENS)

d = load_lines()
p = ptd(d)
S = ["# G2 summary (06_g2_genz.py) — PTD like-for-like basis", ""]
new = p[p.IS_NEW]

# ---------- 1. new customers by generation ----------
rows = []
for g in GENS + ["All"]:
    sub = p if g == "All" else p[p.CUST_AGE_GROUP == g]
    r = {"generation": g}
    for y in ["TY", "LY"]:
        s = sub[sub.YEAR == y]
        r[f"new_{y}"] = int(s.IS_NEW.sum())
        r[f"all_{y}"] = len(s)
        r[f"returning_{y}"] = int(s.IS_RETURNING.sum())
        r[f"retained_{y}"] = int((s.COHORT_STATUS == "Retained").sum())
        r[f"reactivated_{y}"] = int((s.COHORT_STATUS == "Reactivated").sum())
        r[f"new_share_of_all_new_{y}"] = r[f"new_{y}"] / int(p[(p.YEAR == y)].IS_NEW.sum())
        r[f"acq_rate_{y}"] = r[f"new_{y}"] / max(len(s), 1)        # share of the generation's txns that are new
        r[f"returning_share_{y}"] = r[f"returning_{y}"] / max(len(s), 1)
        r[f"new_sales_{y}"] = s[s.IS_NEW].DEMAND_AMT.sum()
        r[f"new_insider_rate_{y}"] = s[s.IS_NEW].IS_INSIDER.mean()
    r["new_yoy_pct"] = r["new_TY"] / r["new_LY"] - 1
    r["new_count_p"] = poisson_count_test(r["new_TY"], r["new_LY"])[1]
    r["returning_yoy_pct"] = r["returning_TY"] / r["returning_LY"] - 1
    r["returning_count_p"] = poisson_count_test(r["returning_TY"], r["returning_LY"])[1]
    r["all_yoy_pct"] = r["all_TY"] / r["all_LY"] - 1
    if g != "All":
        nTY, nLY = int(p[(p.YEAR == "TY")].IS_NEW.sum()), int(p[(p.YEAR == "LY")].IS_NEW.sum())
        r["share_of_new_p"] = two_prop_z(r["new_TY"], nTY, r["new_LY"], nLY)[4]
        r["acq_rate_p"] = two_prop_z(r["new_TY"], r["all_TY"], r["new_LY"], r["all_LY"])[4]
        r["returning_share_p"] = two_prop_z(r["returning_TY"], r["all_TY"], r["returning_LY"], r["all_LY"])[4]
        r["new_insider_p"] = two_prop_z(
            p[(p.YEAR == "TY") & p.IS_NEW & (p.CUST_AGE_GROUP == g)].IS_INSIDER.sum(), r["new_TY"],
            p[(p.YEAR == "LY") & p.IS_NEW & (p.CUST_AGE_GROUP == g)].IS_INSIDER.sum(), r["new_LY"])[4]
    rows.append(r)
gen = pd.DataFrame(rows)
gen.to_csv(TAB / "06_g2_by_generation.csv", index=False)
S.append("## 1. New & returning customers by generation")
S.append(gen[["generation", "new_TY", "new_LY", "new_yoy_pct", "new_count_p", "new_share_of_all_new_TY",
              "new_share_of_all_new_LY", "share_of_new_p", "acq_rate_TY", "acq_rate_LY", "acq_rate_p"]].round(3).to_markdown(index=False))
S.append("\n### Returning (retention proxy, D8) by generation")
S.append(gen[["generation", "returning_TY", "returning_LY", "returning_yoy_pct", "returning_count_p",
              "returning_share_TY", "returning_share_LY", "returning_share_p", "retained_TY", "retained_LY",
              "reactivated_TY", "reactivated_LY"]].round(3).to_markdown(index=False))
S.append("\n### Insider (loyalty) attach among NEW customers by generation")
S.append(gen[["generation", "new_insider_rate_TY", "new_insider_rate_LY", "new_insider_p"]].round(3).to_markdown(index=False))

# Gen Z growth split by cohort status (how much of Gen Z txn growth is new vs returning)
gz = gen.set_index("generation").loc["Gen Z"]
alln = gen.set_index("generation").loc["All"]
S.append(f"\n- Gen Z txns TY {gz.all_TY} vs LY {gz.all_LY} ({fmt_pct(gz.all_yoy_pct)}); of the +{gz.all_TY-gz.all_LY} change, "
         f"new = +{gz.new_TY-gz.new_LY}, returning = {int(gz.returning_TY-gz.returning_LY):+d}")
S.append(f"- Total new customers TY {alln.new_TY} vs LY {alln.new_LY} ({fmt_pct(alln.new_yoy_pct)}); Gen Z accounts for "
         f"{(gz.new_TY-gz.new_LY)/(alln.new_TY-alln.new_LY):.0%} of the increase in new customers")
nonz_new_TY, nonz_new_LY = alln.new_TY - gz.new_TY, alln.new_LY - gz.new_LY
S.append(f"- Non-Gen Z new customers TY {nonz_new_TY} vs LY {nonz_new_LY} ({fmt_pct(nonz_new_TY/nonz_new_LY-1)}, "
         f"p={poisson_count_test(nonz_new_TY, nonz_new_LY)[1]:.3f})")

# ---------- 2. Gen Z share of new by week ----------
wk = new.groupby(["YEAR", "WK"]).agg(new=("TXN_ID", "size"), genz_new=("IS_GENZ", "sum")).reset_index()
wk["genz_share_of_new"] = wk.genz_new / wk.new
wkp = wk.pivot(index="WK", columns="YEAR", values=["new", "genz_new", "genz_share_of_new"])
wkp.columns = [f"{a}_{b}" for a, b in wkp.columns]
wkp = wkp.reset_index()
wkp["genz_new_yoy_pct"] = wkp.genz_new_TY / wkp.genz_new_LY - 1
wkp["cum_genz_new_TY"] = wkp.genz_new_TY.cumsum()
wkp["cum_genz_new_LY"] = wkp.genz_new_LY.cumsum()
wkp["weeks_ty_share_above_ly"] = (wkp.genz_share_of_new_TY > wkp.genz_share_of_new_LY)
wkp.to_csv(TAB / "06_g2_genz_new_by_week.csv", index=False)
S.append("\n## 2. Gen Z new customers by week (W30 = Sun–Wed both years)")
S.append(wkp.round(3).to_markdown(index=False))
S.append(f"- Weeks where TY Gen Z share of new > LY: {int(wkp.weeks_ty_share_above_ly.sum())} of {len(wkp)}")

# ---------- 4. first purchase mix: new Gen Z vs other new ----------
mix_rows = []
for dim in ["STYLE_GROUP", "PROD_CATEGORY", "PROD_TYPE", "SALES_CHANNEL", "CHANNEL_DETAIL", "GEO_REGION"]:
    for y in ["TY", "LY"]:
        ny = new[new.YEAR == y]
        a = ny[ny.IS_GENZ][dim].value_counts()
        b = ny[~ny.IS_GENZ][dim].value_counts()
        for seg in sorted(set(a.index) | set(b.index)):
            xa, xb = a.get(seg, 0), b.get(seg, 0)
            mix_rows.append({"dimension": dim, "segment": seg, "YEAR": y, "genz_new_n": xa, "other_new_n": xb,
                             "genz_new_share": xa / a.sum(), "other_new_share": xb / b.sum(),
                             "index_vs_other_new": (xa / a.sum()) / (xb / b.sum()) * 100 if xb else np.nan,
                             "p": two_prop_z(xa, a.sum(), xb, b.sum())[4]})
mix = pd.DataFrame(mix_rows)
mix.to_csv(TAB / "06_g2_first_purchase_mix.csv", index=False)
# pooled TY+LY too (more power) for families
S.append("\n## 4. What NEW Gen Z buy on first purchase vs other new customers (TY)")
for dim in ["PROD_TYPE", "PROD_CATEGORY", "SALES_CHANNEL", "CHANNEL_DETAIL", "GEO_REGION", "STYLE_GROUP"]:
    t = mix[(mix.dimension == dim) & (mix.YEAR == "TY")].sort_values("genz_new_share", ascending=False)
    S.append(f"\n### {dim}\n" + t.drop(columns=["dimension", "YEAR"]).round(3).to_markdown(index=False))

# Gen Z new by family TY vs LY growth
fam = new[new.IS_GENZ].groupby(["STYLE_GROUP", "YEAR"]).size().unstack(fill_value=0)
fam["chg"] = fam.TY - fam.LY
fam = fam.sort_values("chg", ascending=False)
fam.to_csv(TAB / "06_g2_genz_new_by_family_yoy.csv")
S.append("\n### Gen Z NEW customers by first-purchase family, TY vs LY (sorted by change)\n" + fam.to_markdown())
ptype = new[new.IS_GENZ].groupby(["PROD_TYPE", "YEAR"]).size().unstack(fill_value=0)
ptype["yoy_pct"] = ptype.TY / ptype.LY - 1
S.append("\n### Gen Z NEW by PROD_TYPE TY vs LY\n" + ptype.round(3).to_markdown())
reg = new[new.IS_GENZ].groupby(["GEO_REGION", "YEAR"]).size().unstack(fill_value=0)
reg["yoy_pct"] = reg.TY / reg.LY - 1
reg["p"] = [poisson_count_test(a, b)[1] for a, b in zip(reg.TY, reg.LY)]
S.append("\n### Gen Z NEW by region TY vs LY\n" + reg.round(3).to_markdown())
ch = new[new.IS_GENZ].groupby(["SALES_CHANNEL", "CHANNEL_DETAIL", "YEAR"]).size().unstack(fill_value=0)
ch["yoy_pct"] = ch.TY / ch.LY - 1
S.append("\n### Gen Z NEW by channel TY vs LY\n" + ch.round(3).to_markdown())
reg.to_csv(TAB / "06_g2_genz_new_by_region.csv")
ch.to_csv(TAB / "06_g2_genz_new_by_channel.csv")

# ---------- 6. value of new Gen Z vs other new ----------
val_rows = []
for y in ["TY", "LY", "Both"]:
    ny = new if y == "Both" else new[new.YEAR == y]
    a, b = ny[ny.IS_GENZ], ny[~ny.IS_GENZ]
    for m, col in [("AOV $", "DEMAND_AMT"), ("UPT", "UNIT_QTY"), ("AUR $", "UNIT_PRICE"), ("price index", "PRICE_IDX"),
                   ("outlet share", "IS_OUTLET"), ("eComm share", "IS_ECOMM"), ("Insider share", "IS_INSIDER")]:
        diff, lo, hi, pv = bootstrap_diff_mean(a[col].astype(float), b[col].astype(float))
        val_rows.append({"YEAR": y, "metric": m, "new_genz": a[col].astype(float).mean(),
                         "other_new": b[col].astype(float).mean(), "diff": diff, "ci_lo": lo, "ci_hi": hi, "p": pv,
                         "n_genz": len(a), "n_other": len(b)})
val = pd.DataFrame(val_rows)
val.to_csv(TAB / "06_g2_new_genz_value.csv", index=False)
S.append("\n## 6. Value of NEW Gen Z vs other NEW customers (bootstrap 95% CI on difference)")
S.append(val.round(3).to_markdown(index=False))
# AUR is a per-line unit-price mean; also compute $-weighted AUR for TY
ty_new = new[new.YEAR == "TY"]
k_gz, k_ot = kpis(ty_new[ty_new.IS_GENZ]), kpis(ty_new[~ty_new.IS_GENZ])
S.append(f"\n- TY weighted: new Gen Z AOV ${k_gz.aov:.2f}, AUR ${k_gz.aur:.2f}, UPT {k_gz.upt:.3f} | "
         f"other new AOV ${k_ot.aov:.2f}, AUR ${k_ot.aur:.2f}, UPT {k_ot.upt:.3f}")

# Gen Z overall AOV vs others (all cohorts) TY
ty = p[p.YEAR == "TY"]
dz = bootstrap_diff_mean(ty[ty.IS_GENZ].DEMAND_AMT, ty[~ty.IS_GENZ].DEMAND_AMT)
S.append(f"- TY all-cohort Gen Z AOV minus non-Gen Z AOV: ${dz[0]:.2f} [{dz[1]:.2f}, {dz[2]:.2f}], p={dz[3]:.3f}")
# Returning Gen Z AOV vs new Gen Z AOV (value of retaining)
gz_ty = ty[ty.IS_GENZ]
dr = bootstrap_diff_mean(gz_ty[gz_ty.IS_RETURNING].DEMAND_AMT, gz_ty[gz_ty.IS_NEW].DEMAND_AMT)
S.append(f"- TY Gen Z returning AOV minus Gen Z new AOV: ${dr[0]:.2f} [{dr[1]:.2f}, {dr[2]:.2f}], p={dr[3]:.3f}")
coh = p.groupby(["YEAR", "COHORT_STATUS"]).DEMAND_AMT.mean().unstack()
S.append("\nAOV by cohort status (all generations):\n" + coh.round(2).to_markdown())
cohg = p[p.YEAR == "TY"].groupby(["CUST_AGE_GROUP", "COHORT_STATUS"]).DEMAND_AMT.agg(["mean", "size"]).unstack()
S.append("\nTY AOV & n by generation × cohort:\n" + cohg.round(1).to_markdown())
cohg.to_csv(TAB / "06_g2_aov_gen_cohort_ty.csv")

# ---------- 7. Insider attach of NEW customers by channel / region (QN7) ----------
ins_rows = []
for dim in ["CHANNEL_DETAIL", "SALES_CHANNEL", "GEO_REGION"]:
    for seg, g_ in p[p.IS_NEW & (p.YEAR == "TY")].groupby(dim):
        a, b = g_[g_.IS_GENZ], g_[~g_.IS_GENZ]
        ins_rows.append({"dimension": dim, "segment": seg, "genz_new_n": len(a), "genz_new_insider_rate": a.IS_INSIDER.mean(),
                         "other_new_n": len(b), "other_new_insider_rate": b.IS_INSIDER.mean(),
                         "p": two_prop_z(a.IS_INSIDER.sum(), len(a), b.IS_INSIDER.sum(), len(b))[4]})
ins = pd.DataFrame(ins_rows)
ins.to_csv(TAB / "06_g2_new_insider_by_segment.csv", index=False)
S.append("\n## 7. Insider attach of NEW customers (TY) by segment — Gen Z vs other\n" + ins.round(3).to_markdown(index=False))

# ---------- 8. where is the W27+ acceleration coming from? ----------
acc = new[(new.YEAR == "TY") & new.IS_GENZ].assign(half=lambda x: np.where(x.WK >= 27, "W27_30", "W23_26"))
acc_rows = []
for dim in ["GEO_REGION", "CHANNEL_DETAIL", "SALES_CHANNEL", "PROD_TYPE"]:
    t = acc.groupby([dim, "half"]).size().unstack(fill_value=0)
    t["chg"] = t.W27_30 - t.W23_26
    t["dimension"] = dim
    acc_rows.append(t.reset_index().rename(columns={dim: "segment"}))
acc_t = pd.concat(acc_rows)[["dimension", "segment", "W23_26", "W27_30", "chg"]]
acc_t.to_csv(TAB / "06_g2_genz_new_acceleration_split.csv", index=False)
S.append("\n## 8. TY Gen Z new customers: W23–26 vs W27–30 (W30 = 4 days) by segment\n" + acc_t.to_markdown(index=False))

# ---------- figures ----------
style()
# F1: new customers by generation TY vs LY
g4 = gen[gen.generation != "All"].set_index("generation").loc[GENS]
fig, ax = plt.subplots(figsize=(7, 3.6))
x = np.arange(len(g4))
w = 0.38
ax.bar(x - w / 2 - 0.01, g4.new_LY, w, color=C["ly"], label="LY (FY25)")
ax.bar(x + w / 2 + 0.01, g4.new_TY, w, color=[C["genz"] if g == "Gen Z" else C["ty"] for g in g4.index], label="TY (FY26)")
for i, (g, r) in enumerate(g4.iterrows()):
    ax.text(i + w / 2, r.new_TY + 3, f"{int(r.new_TY)}\n{fmt_pct(r.new_yoy_pct,0)}" + ("*" if r.new_count_p < 0.05 else ""),
            ha="center", fontsize=8.5, color=C["ink"])
    ax.text(i - w / 2, r.new_LY + 3, f"{int(r.new_LY)}", ha="center", fontsize=8.5, color=C["ink2"])
ax.set_xticks(x)
ax.set_xticklabels(g4.index)
ax.set_ylabel("New customers (sample, PTD)")
ax.set_ylim(0, g4[["new_TY", "new_LY"]].values.max() * 1.25)
ax.set_title("New customers by generation, TY vs LY   (* p<0.05)")
ax.legend(loc="upper right")
ax.grid(axis="x", visible=False)
f1 = save(fig, "g2_new_customers_by_generation_ty_vs_ly.png")

# F2: Gen Z share of new by week
fig, ax = plt.subplots(figsize=(7.5, 3.6))
ax.plot(wkp.WK, wkp.genz_share_of_new_LY * 100, color=C["ly"], marker="o", ms=5, label="LY")
ax.plot(wkp.WK, wkp.genz_share_of_new_TY * 100, color=C["genz"], marker="o", ms=5, label="TY")
ty_avg = gz.new_share_of_all_new_TY * 100
ly_avg = gz.new_share_of_all_new_LY * 100
ax.axhline(ty_avg, color=C["genz"], lw=1, ls="--")
ax.axhline(ly_avg, color=C["ly"], lw=1, ls="--")
ax.text(30.45, ty_avg, f"TY avg {ty_avg:.0f}%", va="center", fontsize=8, color=C["ink"], bbox=dict(fc=C["surface"], ec="none", pad=1))
ax.text(30.45, ly_avg, f"LY avg {ly_avg:.0f}%", va="center", fontsize=8, color=C["ink2"], bbox=dict(fc=C["surface"], ec="none", pad=1))
ax.set_xticks(wkp.WK)
ax.set_xticklabels([f"W{w}" + ("*" if w == 30 else "") for w in wkp.WK])
ax.set_xlim(22.6, 31.6)
ax.set_ylabel("Gen Z share of new customers (%)")
ax.set_title("Gen Z share of new customers by week  (*W30 Sun–Wed)")
ax.legend(loc="upper left", ncol=2)
f2 = save(fig, "g2_genz_share_of_new_by_week.png")

# F3: first-purchase family mix, new Gen Z vs other new (TY)
t = mix[(mix.dimension == "STYLE_GROUP") & (mix.YEAR == "TY")].sort_values("genz_new_share")
t = t[t.genz_new_n + t.other_new_n >= 10]
fig, ax = plt.subplots(figsize=(7.5, 6))
y = np.arange(len(t))
ax.barh(y + 0.2, t.other_new_share * 100, 0.38, color=C["other"], label="Other new customers")
ax.barh(y - 0.2, t.genz_new_share * 100, 0.38, color=C["genz"], label="New Gen Z")
for i, r in enumerate(t.itertuples()):
    ax.text(r.genz_new_share * 100 + 0.2, i - 0.2, f"{r.genz_new_share*100:.0f}%  (n={r.genz_new_n})" + (" *" if r.p < 0.05 else ""),
            va="center", fontsize=7.5)
ax.set_yticks(y)
ax.set_yticklabels(t.segment, fontsize=8.5)
ax.set_xlabel("Share of first purchases, TY (%)   * Gen Z vs other p<0.05")
ax.set_title("What new Gen Z customers buy first (TY)")
ax.legend(loc="lower right")
ax.grid(axis="y", visible=False)
f3 = save(fig, "g2_genz_first_purchase_family_mix.png")

# F4: returning vs new txns by generation TY vs LY (retention proxy)
fig, axes = plt.subplots(1, 2, figsize=(9, 3.4), sharey=True)
for ax, (col, ttl) in zip(axes, [("new", "New customers"), ("returning", "Returning (Retained + Reactivated)")]):
    vals = g4[f"{col}_yoy_pct"] * 100
    ps = g4[f"{col}_count_p"]
    ax.bar(g4.index, vals, color=[C["genz"] if g == "Gen Z" else (C["pos"] if v >= 0 else C["neg"]) for g, v in vals.items()], width=0.55)
    for i, (v, pv) in enumerate(zip(vals, ps)):
        ax.text(i, v + (1.5 if v >= 0 else -4), f"{v:+.0f}%" + ("*" if pv < 0.05 else ""), ha="center", fontsize=9)
    ax.axhline(0, color=C["ink2"], lw=1)
    ax.set_title(ttl, fontsize=10)
    ax.grid(axis="x", visible=False)
axes[0].set_ylabel("YoY % change in transactions")
fig.suptitle("Growth is acquisition-led: new up sharply, returning flat   (* p<0.05)", x=0.06, ha="left", fontweight="bold")
fig.subplots_adjust(top=0.8)
f4 = save(fig, "g2_new_vs_returning_yoy_by_generation.png")

S.append(f"\nFigures: {f1}, {f2}, {f3}, {f4}")
(TAB / "06_g2_summary.md").write_text("\n".join(S))
print("\n".join(S))
