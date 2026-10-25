"""12 - Deterministic anomaly rules over metrics.json → data/processed/anomalies.json.
Rules run FIRST (before any LLM). Each anomaly carries the exact metric values that triggered it,
so the UI/LLM can cite them and the validator can check them. Thresholds are documented in RULES.
"""
import json
from _common import PROC, TAB, fixed

M = json.loads((PROC / "metrics.json").read_text())
WEEKS = M["meta"]["weeks"]
pos = {r["STYLE_GROUP"]: r for r in M["inventory_position"]}
WINNERS = {f for f, r in pos.items() if r.get("g3_class") == "Winner"}
GATEWAYS = {f for f, r in pos.items() if r.get("genz_gateway")}

RULES = [
    {"id": "SALES_YOY_NEG", "scope": "total", "metric": "L1W sales yoy_pct", "rule": "< 0", "severity": "warning"},
    {"id": "SALES_YOY_DROP", "scope": "total", "metric": "L1W sales yoy_pct", "rule": "<= -0.10", "severity": "critical"},
    {"id": "SALES_YOY_SPIKE", "scope": "total", "metric": "L1W sales yoy_pct", "rule": ">= +0.20", "severity": "info"},
    {"id": "SALES_WOW_SWING", "scope": "total", "metric": "L1W sales wow_pct (full weeks)", "rule": "|x| >= 0.15", "severity": "warning",
     "note": "driver tagged 'basket (AOV)' if |txns wow| < 0.05 else 'traffic'"},
    {"id": "TXNS_YOY_NEG", "scope": "total", "metric": "L1W txns yoy_pct", "rule": "< 0", "severity": "warning"},
    {"id": "AOV_YOY_SWING", "scope": "total", "metric": "L1W aov yoy_pct", "rule": "|x| >= 0.10", "severity": "info"},
    {"id": "GENZ_NEW_YOY_NEG", "scope": "genz", "metric": "L1W genz_new yoy_pct", "rule": "< 0", "severity": "critical"},
    {"id": "GENZ_NEW_WOW_DROP", "scope": "genz", "metric": "L1W genz_new wow_pct (full weeks)", "rule": "<= -0.25", "severity": "warning"},
    {"id": "GENZ_SHARE_BELOW_LY", "scope": "genz", "metric": "L1W genz_share_of_new ty vs ly", "rule": "ty < ly", "severity": "critical"},
    {"id": "GENZ_NEW_INSIDER_LOW", "scope": "genz", "metric": "L4W genz_new_insider_rate ty", "rule": "< 0.20", "severity": "warning"},
    {"id": "RETURNING_YOY_FLAT", "scope": "retention", "metric": "L4W returning_customers yoy_pct", "rule": "< 0.02", "severity": "warning"},
    {"id": "GENZ_RETURNING_YOY_NEG", "scope": "retention", "metric": "L4W genz_returning yoy_pct", "rule": "< 0", "severity": "warning"},
    {"id": "FAMILY_L4W_DECLINE", "scope": "family", "metric": "L4W family sales_yoy_pct (txns_ly >= 20; full 4-week window only, W26+)", "rule": "<= -0.30", "severity": "warning"},
    {"id": "WOS_LOW", "scope": "family", "metric": "TY wos (all WOS rules require a full 4-week trailing window, W26+)", "rule": "< 3.0 weeks", "severity": "warning",
     "note": "escalated to critical if family is a G3 Winner or Gen Z gateway"},
    {"id": "WOS_HIGH", "scope": "family", "metric": "TY wos", "rule": "> 15.0 weeks", "severity": "warning"},
    {"id": "WOS_COLLAPSE_VS_LY", "scope": "family", "metric": "TY wos / LY same-week wos", "rule": "< 0.5", "severity": "warning"},
    {"id": "RECEIPTS_BELOW_SALES", "scope": "family", "metric": "receipts_to_sales_TY W24-W29 (latest only)", "rule": "< 0.5", "severity": "critical"},
    {"id": "PARTIAL_WEEK", "scope": "data", "metric": "is_partial", "rule": "true", "severity": "info"},
]
SEV = {r["id"]: r["severity"] for r in RULES}
A = []


def add(rule, wk, msg, values, entity="total", severity=None):
    A.append({"rule_id": rule, "wk": wk, "entity": entity, "severity": severity or SEV[rule], "message": msg, "values": values})


def f_pct(x):
    return f"{'-' if x < 0 else '+'}{fixed(abs(x) * 100, 1)}%"


for w in WEEKS:
    tr = M["trailing"][str(w)]
    l1, l4 = tr["L1W"], tr["L4W"]
    wow = l1.get("wow") or {}
    s = l1["sales"]["yoy_pct"]
    if l1["is_partial"]:
        add("PARTIAL_WEEK", w, f"W{w} is a partial week (Sun-Wed); LY compared on the same 4 days.", {"days": 4})
    if s is not None:
        if s <= -0.10:
            add("SALES_YOY_DROP", w, f"W{w} demand {f_pct(s)} YoY.", {"sales_yoy_pct": s})
        elif s < 0:
            add("SALES_YOY_NEG", w, f"W{w} demand {f_pct(s)} YoY.", {"sales_yoy_pct": s})
        if s >= 0.20:
            add("SALES_YOY_SPIKE", w, f"W{w} demand {f_pct(s)} YoY (outperformance).", {"sales_yoy_pct": s})
    if wow.get("sales") is not None and abs(wow["sales"]) >= 0.15:
        drv = "basket (AOV)" if abs(wow["txns"]) < 0.05 else "traffic"
        add("SALES_WOW_SWING", w, f"W{w} demand {f_pct(wow['sales'])} WoW; transactions {f_pct(wow['txns'])}, AOV {f_pct(wow['aov'])} → {drv}-driven.",
            {"sales_wow_pct": wow["sales"], "txns_wow_pct": wow["txns"], "aov_wow_pct": wow["aov"], "driver": drv})
    if l1["txns"]["yoy_pct"] is not None and l1["txns"]["yoy_pct"] < 0:
        add("TXNS_YOY_NEG", w, f"W{w} transactions {f_pct(l1['txns']['yoy_pct'])} YoY.", {"txns_yoy_pct": l1["txns"]["yoy_pct"]})
    a = l1["aov"]["yoy_pct"]
    if a is not None and abs(a) >= 0.10:
        add("AOV_YOY_SWING", w, f"W{w} AOV {f_pct(a)} YoY (${fixed(l1['aov']['ty'], 2)} vs ${fixed(l1['aov']['ly'], 2)}).",
            {"aov_yoy_pct": a, "aov_ty": l1["aov"]["ty"], "aov_ly": l1["aov"]["ly"]})
    g = l1["genz_new"]
    if g["yoy_pct"] is not None and g["yoy_pct"] < 0:
        add("GENZ_NEW_YOY_NEG", w, f"W{w} Gen Z new customers {g['ty']} vs {g['ly']} LY ({f_pct(g['yoy_pct'])}).",
            {"genz_new_ty": g["ty"], "genz_new_ly": g["ly"], "genz_new_yoy_pct": g["yoy_pct"]}, "genz")
    if wow.get("genz_new") is not None and wow["genz_new"] <= -0.25:
        add("GENZ_NEW_WOW_DROP", w, f"W{w} Gen Z new customers {f_pct(wow['genz_new'])} WoW.", {"genz_new_wow_pct": wow["genz_new"]}, "genz")
    sh = l1["genz_share_of_new"]
    if sh["ty"] is not None and sh["ly"] is not None and sh["ty"] < sh["ly"]:
        add("GENZ_SHARE_BELOW_LY", w, f"W{w} Gen Z share of new {fixed(sh['ty']*100, 1)}% vs {fixed(sh['ly']*100, 1)}% LY.",
            {"genz_share_of_new_ty": sh["ty"], "genz_share_of_new_ly": sh["ly"]}, "genz")
    ins = l4["genz_new_insider_rate"]["ty"]
    if ins is not None and ins < 0.20:
        add("GENZ_NEW_INSIDER_LOW", w, f"L4W (W{l4['weeks'][0]}-W{l4['weeks'][-1]}) Insider attach of new Gen Z {fixed(ins*100, 1)}% (< 20%).",
            {"genz_new_insider_rate_ty": ins, "weeks": l4["weeks"]}, "genz")
    ry = l4["returning_customers"]["yoy_pct"]
    if ry is not None and ry < 0.02:
        add("RETURNING_YOY_FLAT", w, f"L4W returning customers {f_pct(ry)} YoY ({l4['returning_customers']['ty']} vs {l4['returning_customers']['ly']}).",
            {"returning_yoy_pct": ry, "returning_ty": l4["returning_customers"]["ty"], "returning_ly": l4["returning_customers"]["ly"], "weeks": l4["weeks"]}, "retention")
    gr = l4["genz_returning"]["yoy_pct"]
    if gr is not None and gr < 0:
        add("GENZ_RETURNING_YOY_NEG", w, f"L4W returning Gen Z {l4['genz_returning']['ty']} vs {l4['genz_returning']['ly']} LY ({f_pct(gr)}).",
            {"genz_returning_ty": l4["genz_returning"]["ty"], "genz_returning_ly": l4["genz_returning"]["ly"], "genz_returning_yoy_pct": gr,
             "weeks": l4["weeks"]}, "retention")
    for prw in [x for x in M["products_by_week"] if x["wk"] == w and x["window"] == "L4W" and not l4["truncated"]]:
        if prw["txns_ly"] >= 20 and prw["sales_yoy_pct"] is not None and prw["sales_yoy_pct"] <= -0.30:
            add("FAMILY_L4W_DECLINE", w, f"{prw['family']} L4W demand {f_pct(prw['sales_yoy_pct'])} YoY.",
                {"sales_yoy_pct": prw["sales_yoy_pct"], "sales_ty": prw["sales_ty"], "sales_ly": prw["sales_ly"]}, prw["family"])
    for iv in [x for x in M["inventory_by_week"] if x["year"] == "TY" and x["wk"] == w and x["wos_window_weeks"] == 4]:
        fam = iv["family"]
        if iv["wos"] is not None and iv["wos"] < 3.0:
            sev = "critical" if (fam in WINNERS or fam in GATEWAYS) else "warning"
            add("WOS_LOW", w, f"{fam} weeks of supply {fixed(iv['wos'], 1)} (LY same week {fixed(iv['wos_ly_same_week'], 1)})"
                + ("; G3 winner and Gen Z gateway." if sev == "critical" else "."),
                {"wos": iv["wos"], "wos_ly_same_week": iv["wos_ly_same_week"], "on_hand_eow": iv["on_hand_eow"]}, fam, sev)
        if iv["wos"] is not None and iv["wos"] > 15.0:
            add("WOS_HIGH", w, f"{fam} weeks of supply {fixed(iv['wos'], 1)} (LY same week {fixed(iv['wos_ly_same_week'], 1)}).",
                {"wos": iv["wos"], "wos_ly_same_week": iv["wos_ly_same_week"], "on_hand_eow": iv["on_hand_eow"]}, fam)
        if iv["wos"] and iv["wos_ly_same_week"] and iv["wos"] / iv["wos_ly_same_week"] < 0.5:
            add("WOS_COLLAPSE_VS_LY", w, f"{fam} weeks of supply {fixed(iv['wos'], 1)} vs {fixed(iv['wos_ly_same_week'], 1)} LY (less than half).",
                {"wos": iv["wos"], "wos_ly_same_week": iv["wos_ly_same_week"]}, fam)

latest = WEEKS[-1]
for fam, r in pos.items():
    if r["receipts_to_sales_TY"] is not None and r["receipts_to_sales_TY"] < 0.5:
        add("RECEIPTS_BELOW_SALES", latest,
            f"{fam} replenishment W24-W29 covered {fixed(r['receipts_to_sales_TY']*100, 0)}% of units sold (LY {fixed(r['receipts_to_sales_LY']*100, 0)}%).",
            {"receipts_to_sales_TY": r["receipts_to_sales_TY"], "receipts_to_sales_LY": r["receipts_to_sales_LY"],
             "receipts_W24_29_TY": r["receipts_W24_29_TY"], "receipts_W24_29_LY": r["receipts_W24_29_LY"]}, fam)

order = {"critical": 0, "warning": 1, "info": 2}
A.sort(key=lambda a: (a["wk"], order[a["severity"]], a["rule_id"], a["entity"]))
for i, a in enumerate(A, 1):
    a["id"] = f"AN{i:03d}"
by_week = {str(w): [a["id"] for a in A if a["wk"] == w] for w in WEEKS}
out = {"meta": {"generated_by": "scripts/12_anomalies.py", "source": "data/processed/metrics.json", "n_anomalies": len(A),
                "counts_by_severity": {s: sum(a["severity"] == s for a in A) for s in order}},
       "rules": RULES, "anomalies": A, "by_week": by_week}
(PROC / "anomalies.json").write_text(json.dumps(out, indent=1))

md = ["# Anomalies (12_anomalies.py)", "", f"Total {len(A)}: " + ", ".join(f"{k} {v}" for k, v in out["meta"]["counts_by_severity"].items()), "",
      "| id | wk | severity | rule | entity | message |", "|---|---|---|---|---|---|"]
md += [f"| {a['id']} | {a['wk']} | {a['severity']} | {a['rule_id']} | {a['entity']} | {a['message']} |" for a in A]
(TAB / "12_anomalies.md").write_text("\n".join(md))
print("\n".join(md))
