"""10 - Quantify expected impact of draft recommendations (all assumptions explicit).
Dollar figures are SAMPLE scale; each is also expressed as % of TY PTD demand so it can be
scaled to the full business (D11).

R1  Protect the Tabby franchise (Tabby + Pillow Tabby): 4-week forward stock-out exposure if
    replenishment continues at the TY W24–29 rate, vs. at the LY receipts-to-sales ratio.
R2  Fund it from Halo apparel overstock: units & $ above median weeks of supply.
R3  Gen Z retention via Insider at first purchase: scenario value of lifting returning Gen Z.

Outputs: outputs/tables/10_sizing.md, 10_sizing.json
"""
import json
import numpy as np
import pandas as pd
from _common import load_lines, ptd, TAB

d = load_lines()
p = ptd(d)
ty = p[p.YEAR == "TY"]
TY_DEMAND = ty.DEMAND_AMT.sum()
weeks_ptd = 7 + 4 / 7  # W23–W29 + Sun–Wed of W30
pos = pd.read_csv(TAB / "08_g4_position.csv", index_col=0)
wk = pd.read_csv(TAB / "08_g4_weekly_family.csv")
out, md = {}, ["# Recommendation sizing (10_sizing.py)", "",
               f"TY PTD demand (sample) = ${TY_DEMAND:,.0f} over {weeks_ptd:.2f} weeks → weekly run-rate ${TY_DEMAND/weeks_ptd:,.0f}", ""]

# ---------- R1 ----------
H = 4  # horizon weeks
rows = []
for fam in ["Tabby", "Pillow Tabby"]:
    f = wk[(wk.STYLE_GROUP == fam) & (wk.YEAR == "TY")].set_index("WK")
    demand_wk = f.loc[26:29, "units"].mean()                       # L4W run-rate (D9)
    rec_wk_ty = f.loc[24:29, "implied_receipts"].mean()            # TY replenishment pace
    rts_ly = pos.loc[fam, "receipts_to_sales_LY"]                  # LY policy: receipts ≈ x × sales
    eoh = f.loc[30, "ON_HAND_UNITS"]
    aur = ty[ty.STYLE_GROUP == fam].DEMAND_AMT.sum() / ty[ty.STYLE_GROUP == fam].UNIT_QTY.sum()
    avail_ty = eoh + H * rec_wk_ty
    short_units = max(0.0, H * demand_wk - avail_ty)
    weeks_to_oos = eoh / max(demand_wk - rec_wk_ty, 1e-9)
    # Gen Z new customers whose first purchase is in this family (TY weekly rate)
    gz_new_wk = ((ty.STYLE_GROUP == fam) & ty.IS_GENZ & ty.IS_NEW).sum() / weeks_ptd
    rows.append({"family": fam, "eoh_W30": eoh, "demand_units_wk": demand_wk, "receipts_wk_TY": rec_wk_ty,
                 "receipts_to_sales_LY": rts_ly, "weeks_to_stockout_at_TY_pace": weeks_to_oos,
                 f"shortfall_units_{H}wk": short_units, "aur_TY": aur,
                 f"demand_at_risk_{H}wk": short_units * aur,
                 f"genz_new_at_risk_{H}wk": gz_new_wk * H * (short_units / (H * demand_wk)),
                 "units_needed_to_hold_LY_wos": demand_wk * pos.loc[fam, "wos_W29_LY"] - eoh})
r1 = pd.DataFrame(rows).set_index("family")
tot_risk = r1[f"demand_at_risk_{H}wk"].sum()
md += ["## R1 Protect Tabby franchise stock",
       "Assumptions: demand continues at the L4W (W26–29) unit run-rate; receipts continue at the TY W24–29 average; "
       "lost units are not substituted; AUR = TY family AUR.", "",
       r1.round(2).to_markdown(), "",
       f"- {H}-week demand at risk: ${tot_risk:,.0f} = {tot_risk/(TY_DEMAND/weeks_ptd*H):.1%} of the next {H} weeks' total demand (at TY run-rate)",
       f"- Units to restore LY weeks-of-supply: Tabby {r1.loc['Tabby','units_needed_to_hold_LY_wos']:.0f}, Pillow Tabby {r1.loc['Pillow Tabby','units_needed_to_hold_LY_wos']:.0f}",
       f"- Gen Z new customers at risk over {H} weeks: {r1[f'genz_new_at_risk_{H}wk'].sum():.1f} (sample) vs TY Gen Z new run-rate {(ty.IS_GENZ & ty.IS_NEW).sum()/weeks_ptd:.1f}/wk "
       f"= {r1[f'genz_new_at_risk_{H}wk'].sum()/((ty.IS_GENZ & ty.IS_NEW).sum()/weeks_ptd*H):.1%} of {H}-week Gen Z new", ""]
out["R1"] = {"horizon_weeks": H, "demand_at_risk_usd_sample": round(tot_risk, 2),
             "demand_at_risk_pct_of_next_4wk_demand": round(tot_risk / (TY_DEMAND / weeks_ptd * H), 4),
             "by_family": r1.round(3).reset_index().to_dict(orient="records")}

# ---------- R2 ----------
med = pos.wos_W30_TY_latest.median()
over = pos[pos.risk == "Overstock risk"].copy()
over["avg_units_wk"] = over.l4w_units_TY / 4
over["excess_units_vs_median_wos"] = over.eoh_W30_TY - med * over.avg_units_wk
over["aur_TY"] = [ty[ty.STYLE_GROUP == f].DEMAND_AMT.sum() / ty[ty.STYLE_GROUP == f].UNIT_QTY.sum() for f in over.index]
over["excess_retail_value"] = over.excess_units_vs_median_wos * over.aur_TY
md += ["## R2 Halo apparel overstock to fund reallocation",
       f"Excess = W30 EOH − median family WOS ({med:.1f}) × L4W avg weekly units; valued at TY AUR (retail, not cost).", "",
       over[["eoh_W30_TY", "avg_units_wk", "wos_W30_TY_latest", "excess_units_vs_median_wos", "aur_TY", "excess_retail_value"]].round(1).to_markdown(), "",
       f"- Total excess: {over.excess_units_vs_median_wos.sum():.0f} units, ${over.excess_retail_value.sum():,.0f} retail value "
       f"(vs Tabby-franchise gap to LY WOS of {r1.units_needed_to_hold_LY_wos.sum():.0f} units)",
       f"- Excess retail value = {over.excess_retail_value.sum()/TY_DEMAND:.1%} of TY PTD demand", ""]
out["R2"] = {"median_wos": round(med, 3), "excess_units": round(over.excess_units_vs_median_wos.sum(), 1),
             "excess_retail_value_usd_sample": round(over.excess_retail_value.sum(), 2),
             "families": over.index.tolist()}

# ---------- R3 ----------
gz = ty[ty.IS_GENZ]
gz_new = int(gz.IS_NEW.sum())
gz_new_ins = gz[gz.IS_NEW].IS_INSIDER.mean()
mill_new_ins = ty[(ty.CUST_AGE_GROUP == "Millennial") & ty.IS_NEW].IS_INSIDER.mean()
ret_ins = ty[ty.COHORT_STATUS == "Retained"].IS_INSIDER.mean()
gz_ret = int(gz.IS_RETURNING.sum())
gz_ret_aov = gz[gz.IS_RETURNING].DEMAND_AMT.mean()
scen = []
for lift in [0.05, 0.10, 0.20]:
    extra = gz_ret * lift
    scen.append({"returning_genz_lift": lift, "extra_txns_sample": extra, "extra_demand_usd_sample": extra * gz_ret_aov,
                 "pct_of_TY_demand": extra * gz_ret_aov / TY_DEMAND})
sc = pd.DataFrame(scen)
md += ["## R3 Convert the Gen Z acquisition wave into repeat customers (Insider at first purchase)",
       f"- TY new Gen Z: {gz_new}; Insider attach {gz_new_ins:.1%} vs new Millennial {mill_new_ins:.1%}; Insider share among Retained {ret_ins:.1%}",
       f"- Closing the gap to Millennial attach = +{gz_new*(mill_new_ins-gz_new_ins):.0f} Gen Z Insiders in the sample period ({mill_new_ins/gz_new_ins-1:+.0%} relative)",
       f"- TY returning Gen Z txns {gz_ret}, AOV ${gz_ret_aov:.2f}. Scenario (assumption: Insider enrolment + onboarding lifts returning Gen Z volume):", "",
       sc.round(4).to_markdown(index=False), "",
       "- Not estimable from this file: Insider vs non-Insider repeat rate, time-to-second-purchase, CLV — data request.", ""]
out["R3"] = {"genz_new_TY": gz_new, "genz_new_insider_rate": round(gz_new_ins, 4), "millennial_new_insider_rate": round(mill_new_ins, 4),
             "retained_insider_rate": round(ret_ins, 4), "genz_returning_TY": gz_ret, "genz_returning_aov": round(gz_ret_aov, 2),
             "scenarios": sc.round(4).to_dict(orient="records")}

(TAB / "10_sizing.md").write_text("\n".join(md))
(TAB / "10_sizing.json").write_text(json.dumps(out, indent=2, default=float))
print("\n".join(md))
