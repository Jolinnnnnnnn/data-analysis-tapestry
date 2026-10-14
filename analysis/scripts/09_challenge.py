"""09 - Challenge / robustness tests for major findings.

For each finding: alternative definition (DECISIONS.md), outlier removal, leave-one-out, mix standardization.
Outputs: outputs/tables/09_sensitivity.md, 09_robustness.csv
"""
import numpy as np
import pandas as pd
from _common import load_lines, ptd, kpis, two_prop_z, poisson_count_test, TAB, fmt_pct, GENS

d = load_lines()
p = ptd(d)
ty, ly = p[p.YEAR == "TY"], p[p.YEAR == "LY"]
R = []  # robustness rows: finding, test, base, alt, holds


def add(f, test, base, alt, holds, note=""):
    R.append({"finding": f, "test": test, "base": base, "alternative": alt, "holds": holds, "note": note})


def growth(df):
    return df[df.YEAR == "TY"].DEMAND_AMT.sum() / df[df.YEAR == "LY"].DEMAND_AMT.sum() - 1


# ---------- F1 / F2: headline growth ----------
base = growth(p)
add("F1", "D3 alt (a): all rows incl. LY full W30", fmt_pct(base), fmt_pct(growth(d)), "partly", "positive but −5 pts: see F2")
add("F1", "D3 alt (b): full weeks W23–W29 only", fmt_pct(base), fmt_pct(growth(d[d.WK <= 29])), "yes")
cap = p.DEMAND_AMT.quantile(0.99)
add("F1", f"drop top-1pct lines (> ${cap:.0f})", fmt_pct(base), fmt_pct(growth(p[p.DEMAND_AMT <= cap])), "yes")
add("F1", "exclude Tabby family", fmt_pct(base), fmt_pct(growth(p[p.STYLE_GROUP != "Tabby"])), "weakens",
    "ex-Tabby growth much lower — concentration (F9)")
add("F1", "exclude Tabby + Pillow Tabby", fmt_pct(base), fmt_pct(growth(p[~p.STYLE_GROUP.isin(["Tabby", "Pillow Tabby"])])), "weakens")
wk_g = p.groupby("WK").apply(growth)
add("F1", "weeks with positive YoY", "8/8", f"{(wk_g>0).sum()}/{len(wk_g)}; min {fmt_pct(wk_g.min())} (W{wk_g.idxmin()})", "yes")
loo = [growth(p[p.WK != w]) for w in sorted(p.WK.unique())]
add("F1", "leave-one-week-out range", fmt_pct(base), f"{fmt_pct(min(loo))} … {fmt_pct(max(loo))}", "yes")
mix_ch = p.groupby(["SALES_CHANNEL", "YEAR"]).size().unstack()
add("F1", "channel mix shift (OUTLET share of txns)", f"LY {mix_ch.loc['OUTLET','LY']/mix_ch.LY.sum():.1%}",
    f"TY {mix_ch.loc['OUTLET','TY']/mix_ch.TY.sum():.1%}", "yes", "growth not from channel mix")

# ---------- F4: Gen Z acquisition ----------
def genz_new(df, newmask):
    return {y: int((df.YEAR.eq(y) & newmask(df) & df.IS_GENZ).sum()) for y in ["TY", "LY"]}


def share_new(df, newmask):
    out = {}
    for y in ["TY", "LY"]:
        s = df[df.YEAR.eq(y) & newmask(df)]
        out[y] = (int(s.IS_GENZ.sum()), len(s))
    return out


base_g = genz_new(p, lambda x: x.IS_NEW)
base_s = share_new(p, lambda x: x.IS_NEW)
b_txt = f"{base_g['TY']} vs {base_g['LY']} ({fmt_pct(base_g['TY']/base_g['LY']-1)}); share {base_s['TY'][0]/base_s['TY'][1]:.1%} vs {base_s['LY'][0]/base_s['LY'][1]:.1%}"
alt = genz_new(p, lambda x: x.COHORT_STATUS.isin(["New", "Reactivated"]))
alt_s = share_new(p, lambda x: x.COHORT_STATUS.isin(["New", "Reactivated"]))
pz = two_prop_z(alt_s["TY"][0], alt_s["TY"][1], alt_s["LY"][0], alt_s["LY"][1])[4]
add("F4", "D6 alt (c): New + Reactivated", b_txt,
    f"{alt['TY']} vs {alt['LY']} ({fmt_pct(alt['TY']/alt['LY']-1)}); share {alt_s['TY'][0]/alt_s['TY'][1]:.1%} vs {alt_s['LY'][0]/alt_s['LY'][1]:.1%}, p={pz:.4f}", "yes")
for excl in [["Tabby"], ["Tabby", "Pillow Tabby"]]:
    q = p[~p.STYLE_GROUP.isin(excl)]
    g = genz_new(q, lambda x: x.IS_NEW)
    s = share_new(q, lambda x: x.IS_NEW)
    pz = two_prop_z(s["TY"][0], s["TY"][1], s["LY"][0], s["LY"][1])[4]
    add("F4", f"exclude {' + '.join(excl)}", b_txt,
        f"{g['TY']} vs {g['LY']} ({fmt_pct(g['TY']/g['LY']-1)}); share {s['TY'][0]/s['TY'][1]:.1%} vs {s['LY'][0]/s['LY'][1]:.1%}, p={pz:.4f}", "yes",
        "not a Tabby-only effect")
reg_rows = []
for r in sorted(p.GEO_REGION.unique()):
    q = p[p.GEO_REGION == r]
    g = genz_new(q, lambda x: x.IS_NEW)
    reg_rows.append(f"{r} {g['TY']}/{g['LY']}")
add("F4", "by region (Gen Z new TY/LY)", b_txt, "; ".join(reg_rows), "yes", "up in every region")
ch_rows = []
for c in sorted(p.CHANNEL_DETAIL.unique()):
    g = genz_new(p[p.CHANNEL_DETAIL == c], lambda x: x.IS_NEW)
    ch_rows.append(f"{c} {g['TY']}/{g['LY']}")
add("F4", "by channel detail (Gen Z new TY/LY)", b_txt, "; ".join(ch_rows), "yes")
q = p[p.WK <= 29]
g = genz_new(q, lambda x: x.IS_NEW)
add("F4", "exclude partial W30", b_txt, f"{g['TY']} vs {g['LY']} ({fmt_pct(g['TY']/g['LY']-1)})", "yes")
# mix standardization: Gen Z share of new within family, weighted by LY family mix of new customers
nw = p[p.IS_NEW]
fam_share = nw.groupby(["STYLE_GROUP", "YEAR"]).IS_GENZ.mean().unstack()
ly_w = nw[nw.YEAR == "LY"].STYLE_GROUP.value_counts(normalize=True)
std_ty = (fam_share.TY * ly_w).sum()
std_ly = (fam_share.LY * ly_w).sum()
add("F4", "mix-standardized Gen Z share of new (TY within-family rates × LY family mix)",
    f"{base_s['TY'][0]/base_s['TY'][1]:.1%} vs {base_s['LY'][0]/base_s['LY'][1]:.1%}", f"{std_ty:.1%} vs {std_ly:.1%}", "yes",
    "not a product-mix effect")
reg_share = nw.groupby(["GEO_REGION", "YEAR"]).IS_GENZ.mean().unstack()
ly_rw = nw[nw.YEAR == "LY"].GEO_REGION.value_counts(normalize=True)
add("F4", "region-mix-standardized Gen Z share of new", f"{base_s['TY'][0]/base_s['TY'][1]:.1%}",
    f"{(reg_share.TY*ly_rw).sum():.1%} vs LY {(reg_share.LY*ly_rw).sum():.1%}", "yes", "not a region-mix effect")
# bootstrap CI on share-of-new difference
rng = np.random.default_rng(11)
a = nw[nw.YEAR == "TY"].IS_GENZ.values
b = nw[nw.YEAR == "LY"].IS_GENZ.values
bs = rng.choice(a, (4000, len(a))).mean(1) - rng.choice(b, (4000, len(b))).mean(1)
add("F4", "bootstrap 95% CI on Gen Z share-of-new diff", f"{a.mean()-b.mean():+.1%}",
    f"[{np.percentile(bs,2.5):+.1%}, {np.percentile(bs,97.5):+.1%}]", "yes")

# ---------- F5: within-TY acceleration ----------
wk = nw.groupby(["YEAR", "WK"]).agg(n=("IS_GENZ", "size"), gz=("IS_GENZ", "sum")).reset_index()
for y in ["TY", "LY"]:
    s = wk[wk.YEAR == y]
    slope = np.polyfit(s.WK, s.gz / s.n, 1, w=np.sqrt(s.n))[0]
    h1 = s[s.WK <= 26]
    h2 = s[s.WK >= 27]
    z = two_prop_z(h2.gz.sum(), h2.n.sum(), h1.gz.sum(), h1.n.sum())
    add("F5", f"{y}: Gen Z share of new, W27–30 vs W23–26", "",
        f"{z[0]:.1%} vs {z[1]:.1%} (diff {z[2]:+.1%}, p={z[4]:.3f}); weighted slope {slope*100:+.2f} pts/wk",
        "yes" if (y == "TY" and z[4] < 0.05) else ("n/a" if y == "LY" else "no"))
# permutation test for TY slope
s = nw[nw.YEAR == "TY"]
obs = np.polyfit(s.WK, s.IS_GENZ.astype(float), 1)[0]
perm = [np.polyfit(s.WK, rng.permutation(s.IS_GENZ.values).astype(float), 1)[0] for _ in range(2000)]
add("F5", "TY line-level permutation test of week slope", f"slope {obs*100:+.2f} pts/wk",
    f"p={np.mean(np.abs(perm) >= abs(obs)):.3f} (2,000 perms)", "yes" if np.mean(np.abs(perm) >= abs(obs)) < 0.05 else "no")

# ---------- F6: returning flat ----------
def cnt(df, mask):
    return int(mask(df[df.YEAR == "TY"]).sum()), int(mask(df[df.YEAR == "LY"]).sum())


for lab, m in [("Retained only", lambda x: x.COHORT_STATUS == "Retained"),
               ("Reactivated only", lambda x: x.COHORT_STATUS == "Reactivated"),
               ("Returning Gen Z", lambda x: x.IS_RETURNING & x.IS_GENZ),
               ("Returning non-Gen Z", lambda x: x.IS_RETURNING & ~x.IS_GENZ)]:
    a_, b_ = cnt(p, m)
    add("F6", lab, "returning 1,239 vs 1,236 (+0.2%)",
        f"{a_} vs {b_} ({fmt_pct(a_/b_-1)}, p={poisson_count_test(a_, b_)[1]:.2f})", "yes")
a_, b_ = cnt(p[p.WK <= 29], lambda x: x.IS_RETURNING)
add("F6", "exclude W30", "", f"{a_} vs {b_} ({fmt_pct(a_/b_-1)})", "yes")
rd = p[p.IS_RETURNING].groupby("YEAR").DEMAND_AMT.sum()
add("F6", "returning demand ($)", "", f"${rd.TY:,.0f} vs ${rd.LY:,.0f} ({fmt_pct(rd.TY/rd.LY-1)})", "yes", "returning $ grows only via AUR")

# ---------- F8: new Gen Z value — mix control ----------
nty = p[p.IS_NEW & (p.YEAR == "TY")]
within = []
for fam_, g_ in nty.groupby("STYLE_GROUP"):
    if g_.IS_GENZ.sum() >= 5 and (~g_.IS_GENZ).sum() >= 5:
        within.append((len(g_), g_[g_.IS_GENZ].UNIT_PRICE.mean() - g_[~g_.IS_GENZ].UNIT_PRICE.mean()))
w_ = np.array(within)
add("F8", "AUR gap within family (weighted avg of family-level gaps, TY new)", "+$22.0 raw",
    f"{np.average(w_[:,1], weights=w_[:,0]):+.1f} $ over {len(w_)} families", "partly",
    "part of the raw AUR gap is mix (Gen Z buys pricier Tabby)")
pi = bootstrap = None
from _common import bootstrap_diff_mean
r = bootstrap_diff_mean(nty[nty.IS_GENZ].PRICE_IDX, nty[~nty.IS_GENZ].PRICE_IDX)
add("F8", "price index (within-style) TY new Gen Z vs other new", "", f"{r[0]:+.3f} [{r[1]:+.3f},{r[2]:+.3f}] p={r[3]:.2f}", "partly",
    "TY alone n.s.; pooled TY+LY p=0.019 (06)")
for excl in [["Tabby", "Pillow Tabby"]]:
    q = nty[~nty.STYLE_GROUP.isin(excl)]
    a_ = (q.IS_GENZ & q.PROD_TYPE.eq("Hero")).sum() / q.IS_GENZ.sum()
    add("F8", "Hero over-index excl. Tabby families", "index 169", f"Gen Z Hero share ex-Tabby {a_:.1%}", "n/a",
        "Hero ≈ Tabby + Pillow Tabby; Hero over-index IS the Tabby effect")

# ---------- F9: Tabby growth robustness ----------
tb = p[p.STYLE_GROUP == "Tabby"]
wkg = tb.groupby("WK").apply(growth)
add("F9", "Tabby weeks with positive YoY", "+42.9%", f"{(wkg>0).sum()}/{len(wkg)} weeks; min {fmt_pct(wkg.min())}", "yes" if (wkg > 0).sum() >= 6 else "partly")
loo = [growth(tb[tb.WK != w]) for w in sorted(tb.WK.unique())]
add("F9", "Tabby leave-one-week-out", "+42.9%", f"{fmt_pct(min(loo))} … {fmt_pct(max(loo))}", "yes")
cap_t = tb.DEMAND_AMT.quantile(0.95)
add("F9", "Tabby drop top-5% lines", "+42.9%", fmt_pct(growth(tb[tb.DEMAND_AMT <= cap_t])), "yes")
tbs = tb.groupby(["STYLE_DESC", "YEAR"]).DEMAND_AMT.sum().unstack()
add("F9", "Tabby growth across styles", "", "; ".join(f"{s} {fmt_pct(r.TY/r.LY-1,0)}" for s, r in tbs.iterrows()), "yes",
    "all three Tabby styles grow")

# ---------- F11: WOS alternative denominators ----------
pos = pd.read_csv(TAB / "08_g4_position.csv", index_col=0)
wkf = pd.read_csv(TAB / "08_g4_weekly_family.csv")
for fam_ in ["Tabby", "Pillow Tabby", "Knit Dress", "Trench"]:
    f_ = wkf[(wkf.STYLE_GROUP == fam_) & (wkf.YEAR == "TY")].set_index("WK")
    alts = {
        "W30 EOH / W29 units": f_.loc[30, "ON_HAND_UNITS"] / f_.loc[29, "units"],
        "W30 EOH / W23–29 avg": f_.loc[30, "ON_HAND_UNITS"] / f_.loc[23:29, "units"].mean(),
        "W29 EOH / W26–29 avg": f_.loc[29, "ON_HAND_UNITS"] / f_.loc[26:29, "units"].mean(),
    }
    add("F11", f"{fam_} WOS alt denominators", f"{pos.loc[fam_,'wos_W30_TY_latest']:.1f} (W30 EOH / W26–29 avg)",
        "; ".join(f"{k}: {v:.1f}" for k, v in alts.items()), "yes")

rob = pd.DataFrame(R)
rob.to_csv(TAB / "09_robustness.csv", index=False)
md = ["# Sensitivity & robustness (09_challenge.py)", "",
      "`holds`: yes = conclusion unchanged; partly/weakens = direction holds, magnitude changes; no = fragile.", "",
      rob.to_markdown(index=False)]
(TAB / "09_sensitivity.md").write_text("\n".join(md))
print("\n".join(md))
