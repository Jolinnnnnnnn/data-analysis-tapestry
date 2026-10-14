"""14 - Audit: every headline number quoted in FINDINGS.md is re-derived from metrics.json / output tables
(second read path, independent of the script that first printed it) and must appear verbatim in FINDINGS.md.

Output: outputs/tables/14_findings_audit.md (fails loudly if any check fails)
"""
import json
import re
import pandas as pd
from _common import ROOT, PROC, TAB

M = json.loads((PROC / "metrics.json").read_text())
A = json.loads((PROC / "anomalies.json").read_text())
F = (ROOT / "FINDINGS.md").read_text()
h = M["headline_ptd"]
pos = pd.read_csv(TAB / "08_g4_position.csv", index_col=0)
fam = pd.read_csv(TAB / "07_g3_family_scorecard.csv", index_col="STYLE_GROUP")
gen = pd.read_csv(TAB / "06_g2_by_generation.csv", index_col="generation")
siz = json.loads((TAB / "10_sizing.json").read_text())
kw = pd.read_csv(TAB / "05_g1_kpi_windows.csv")


def pc(x, d=1):
    return f"{x*100:+.{d}f}%"


def pp(x, d=1):
    return f"{x*100:.{d}f}%"


checks = [
    ("F1", "PTD demand YoY", pc(h["sales"]["yoy_pct"])),
    ("F1", "PTD txns YoY", pc(h["txns"]["yoy_pct"])),
    ("F1", "TY demand $", f"${h['sales']['ty']:,.0f}"),
    ("F1", "LY demand $", f"${h['sales']['ly']:,.0f}"),
    ("F1", "L1W W29 YoY", pc(M["trailing"]["29"]["L1W"]["sales"]["yoy_pct"])),
    ("F1", "L4W YoY", pc(M["trailing"]["29"]["L4W"]["sales"]["yoy_pct"])),
    ("F1", "WTD W30 YoY", pc(M["trailing"]["30"]["L1W"]["sales"]["yoy_pct"])),
    ("F2", "naive all-rows YoY", pc(kw[(kw.window.str.startswith("PTD alt-a")) & (kw.metric == "sales")].yoy_pct.iloc[0])),
    ("F3", "W29 WoW", pc(M["trailing"]["29"]["L1W"]["wow"]["sales"])),
    ("F4", "Gen Z new TY", f"{h['genz_new']['ty']} vs {h['genz_new']['ly']}"),
    ("F4", "Gen Z new YoY", f"{h['genz_new']['yoy_pct']*100:+.0f}%"),
    ("F4", "Gen Z share of new TY", pp(h["genz_share_of_new"]["ty"])),
    ("F4", "Gen Z share of new LY", pp(h["genz_share_of_new"]["ly"])),
    ("F6", "returning TY vs LY", f"{h['returning_customers']['ty']:,} vs {h['returning_customers']['ly']:,}"),
    ("F7", "new Gen Z Insider TY", pp(gen.loc["Gen Z", "new_insider_rate_TY"])),
    ("F9", "Tabby YoY", pc(fam.loc["Tabby", "sales_yoy_pct"])),
    ("F9", "Pillow Tabby YoY", pc(fam.loc["Pillow Tabby", "sales_yoy_pct"])),
    ("F9", "Tabby share of growth", f"{fam.loc['Tabby','share_of_growth']*100:.0f}%"),
    ("F9", "Tabby+PT share of growth", f"{(fam.loc['Tabby','share_of_growth']+fam.loc['Pillow Tabby','share_of_growth'])*100:.0f}%"),
    ("F10", "Rogue YoY", pc(fam.loc["Rogue", "sales_yoy_pct"])),
    ("F10", "Knit Dress YoY", pc(fam.loc["Knit Dress", "sales_yoy_pct"])),
    ("F11", "Tabby WOS", f"WOS {pos.loc['Tabby','wos_W30_TY_latest']:.1f}"),
    ("F11", "Pillow Tabby WOS", f"WOS {pos.loc['Pillow Tabby','wos_W30_TY_latest']:.1f}"),
    ("F11", "Knit Dress WOS", f"WOS {pos.loc['Knit Dress','wos_W30_TY_latest']:.1f}"),
    ("F11", "median WOS", f"{pos.wos_W30_TY_latest.median():.1f}"),
    ("F12", "Tabby receipts/sales", f"{pos.loc['Tabby','receipts_to_sales_TY']:.2f} vs {pos.loc['Tabby','receipts_to_sales_LY']:.2f}"),
    ("R1", "4wk demand at risk %", f"{siz['R1']['demand_at_risk_pct_of_next_4wk_demand']*100:.1f}%"),
    ("R1", "4wk demand at risk $", f"${siz['R1']['demand_at_risk_usd_sample']/1000:.1f}K"),
    ("R2", "apparel excess units", f"{siz['R2']['excess_units']:.0f} units"),
    ("R2", "apparel excess $", f"${siz['R2']['excess_retail_value_usd_sample']/1000:.1f}K"),
]
rows, fails = [], 0
for fid, label, val in checks:
    ok = val in F
    fails += (not ok)
    rows.append(f"| {fid} | {label} | `{val}` | {'PASS' if ok else 'FAIL'} |")

# anomaly cross-check: the first critical Tabby alert week
first_crit = min(a["wk"] for a in A["anomalies"] if a["severity"] == "critical" and a["entity"] == "Tabby")
md = ["# FINDINGS audit (14_verify_findings.py)", "",
      "Each value is re-derived from metrics.json / output tables and must appear verbatim in FINDINGS.md.", "",
      "| finding | check | expected string | result |", "|---|---|---|---|"] + rows + [
      "", f"- {len(checks)-fails}/{len(checks)} PASS", f"- First critical Tabby anomaly fires in W{first_crit} (rules engine early-warning lead time)"]
(TAB / "14_findings_audit.md").write_text("\n".join(md))
print("\n".join(md))
if fails:
    raise SystemExit(f"{fails} audit failures")
