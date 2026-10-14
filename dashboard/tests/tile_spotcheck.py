"""Spot-check rendered G1 KPI tiles against the analysis outputs (a second, independent path):
analysis/outputs/tables/05_g1_kpi_windows.csv (script 05) and the strings audited in 14_findings_audit.md.

Renders the app headlessly (AppTest), parses the KPI tiles from the HTML, and compares them with the CSV
values formatted the same way. Writes dashboard/verification/tile_spotcheck.md; exits 1 on any mismatch.
"""
import csv
import re
import sys
from pathlib import Path

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[2]
K05 = list(csv.DictReader(open(ROOT / "analysis/outputs/tables/05_g1_kpi_windows.csv")))
AUDIT = (ROOT / "analysis/outputs/tables/14_findings_audit.md").read_text()


def k05(window, metric, col):
    return float(next(r for r in K05 if r["window"] == window and r["metric"] == metric)[col])


def tiles(wk, win):
    at = AppTest.from_file(str(ROOT / "dashboard/app.py"), default_timeout=60)
    at.query_params.update({"page": "explore", "wk": str(wk), "win": win, "ly": "1", "theme": "light", "tab": "G1"})
    at.run()
    html = next(h.proto.body for h in at.get("html") if 'class="kpis"' in h.proto.body)
    out = {}
    for m in re.finditer(r'<div class="l">([^<]+)</div><div class="v">([^<]+)</div><div class="s"><span>LY ([^<]+)</span><span class="\w+">[▲▼ ]*([^<]+?) YoY</span>', html):
        out[m.group(1)] = {"ty": m.group(2), "ly": m.group(3), "yoy": m.group(4)}
    return out


def money_k(x):
    return f"${x / 1000:,.1f}K"


CHECKS = [  # (week, window, tile, field, expected string from CSV, CSV source, audit string or None)
    (29, "L1W", "Demand", "yoy", f"{k05('L1W (W29)', 'sales', 'yoy_pct') * 100:+.1f}%", "05 L1W (W29) sales yoy_pct", "+12.7%"),
    (29, "L4W", "Demand", "yoy", f"{k05('L4W (W26–W29)', 'sales', 'yoy_pct') * 100:+.1f}%", "05 L4W (W26–W29) sales yoy_pct", "+13.2%"),
    (29, "L4W", "Demand", "ty", money_k(k05("L4W (W26–W29)", "sales", "TY")), "05 L4W (W26–W29) sales TY", None),
    (30, "L1W", "Demand", "yoy", f"{k05('WTD (W30 Sun–Wed)', 'sales', 'yoy_pct') * 100:+.1f}%", "05 WTD (W30 Sun–Wed) sales yoy_pct", "+21.7%"),
    (30, "PTD", "Demand", "yoy", f"{k05('PTD (W23–W30 Wed, like-for-like)', 'sales', 'yoy_pct') * 100:+.1f}%", "05 PTD sales yoy_pct", "+12.8%"),
    (30, "PTD", "Transactions", "yoy", f"{k05('PTD (W23–W30 Wed, like-for-like)', 'txns', 'yoy_pct') * 100:+.1f}%", "05 PTD txns yoy_pct", "+8.2%"),
    (30, "PTD", "AOV", "ty", f"${k05('PTD (W23–W30 Wed, like-for-like)', 'aov', 'TY'):,.2f}", "05 PTD aov TY", None),
    (30, "PTD", "AOV", "yoy", f"{k05('PTD (W23–W30 Wed, like-for-like)', 'aov', 'yoy_pct') * 100:+.1f}%", "05 PTD aov yoy_pct", None),
    (29, "L1W", "UPT", "ty", f"{k05('L1W (W29)', 'units', 'TY') / k05('L1W (W29)', 'txns', 'TY'):,.2f}", "05 L1W units/txns (test-side ratio)", None),
    (29, "L4W", "Customers", "ty", f"{k05('L4W (W26–W29)', 'customers', 'TY'):,.0f}", "05 L4W customers TY", None),
]
L = ["# KPI tile spot-check (rendered app vs analysis outputs)", "",
     "| week | window | tile | field | rendered | expected (05_g1_kpi_windows.csv) | in 14_findings_audit.md | result |", "|---|---|---|---|---|---|---|---|"]
bad = 0
cache = {}
for wk, win, tile, field, exp, src, audit in CHECKS:
    t = cache.setdefault((wk, win), tiles(wk, win))
    got = t[tile][field]
    ok = got == exp and (audit is None or (audit == exp and f"`{audit}`" in AUDIT))
    bad += not ok
    L.append(f"| W{wk} | {win} | {tile} | {field} | `{got}` | `{exp}` ({src}) | {'`' + audit + '` PASS' if audit else '—'} | {'PASS' if ok else 'FAIL'} |")
L += ["", f"{len(CHECKS) - bad}/{len(CHECKS)} tiles match."]
(ROOT / "dashboard/verification/tile_spotcheck.md").write_text("\n".join(L))
print("\n".join(L[-len(CHECKS) - 2:]))
sys.exit(1 if bad else 0)
