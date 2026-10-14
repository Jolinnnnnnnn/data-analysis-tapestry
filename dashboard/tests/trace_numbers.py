"""Trace every number in the AI texts of the hand-check weeks back to metrics.json / anomalies.json.

For each printed number: the facts field the validator matched, the facts value, the ORIGINAL metrics.json
(or anomalies.json) path, and the value re-read independently from that file. A row is OK only if the
independent value equals the facts value (proves the facts layer copied without arithmetic) and the printed
number is a correct display rounding of it. The semantic check (is it the right field for that sentence?)
is done by a human reading the table: see dashboard/HISTORY.md.

Run: .venv/bin/python dashboard/tests/trace_numbers.py [weeks...]   → dashboard/verification/number_trace.md
"""
import importlib.util
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
M = json.loads((ROOT / "analysis/data/processed/metrics.json").read_text())
A = json.loads((ROOT / "analysis/data/processed/anomalies.json").read_text())
AN = {a["id"]: a for a in A["anomalies"]}
spec = importlib.util.spec_from_file_location("v", ROOT / "dashboard/scripts/17_validate_summaries.py")
V = importlib.util.module_from_spec(spec)
spec.loader.exec_module(V)
WEEKS = [int(w) for w in sys.argv[1:]] or [28, 29, 30]

# weekly_facts field → its upstream metrics.json location (independent re-read, not via weekly_facts)
WF = {"l1w_sales_ty": "L1W.sales.ty", "l1w_sales_ly": "L1W.sales.ly", "l1w_sales_yoy_pct": "L1W.sales.yoy_pct",
      "l1w_txns_yoy_pct": "L1W.txns.yoy_pct", "l1w_aov_ty": "L1W.aov.ty", "l1w_aov_yoy_pct": "L1W.aov.yoy_pct",
      "l1w_sales_wow_pct": "L1W.wow.sales", "l4w_sales_yoy_pct": "L4W.sales.yoy_pct", "l4w_txns_yoy_pct": "L4W.txns.yoy_pct",
      "ptd_sales_yoy_pct": "PTD.sales.yoy_pct", "l1w_genz_new_ty": "L1W.genz_new.ty", "l1w_genz_new_ly": "L1W.genz_new.ly",
      "l1w_genz_new_yoy_pct": "L1W.genz_new.yoy_pct", "l1w_genz_share_of_new_ty": "L1W.genz_share_of_new.ty",
      "l1w_genz_share_of_new_ly": "L1W.genz_share_of_new.ly", "l4w_genz_new_ty": "L4W.genz_new.ty",
      "l4w_genz_new_ly": "L4W.genz_new.ly", "l4w_genz_new_yoy_pct": "L4W.genz_new.yoy_pct",
      "l4w_returning_yoy_pct": "L4W.returning_customers.yoy_pct", "l4w_genz_new_insider_rate_ty": "L4W.genz_new_insider_rate.ty",
      "days_in_week": None}


def dig(obj, dotted):
    for k in dotted.split("."):
        obj = obj[k]
    return obj


def resolve_summary(wk, path, facts):
    """Return (source description, independently re-read value)."""
    m = re.match(r"anomalies\[(\d+)\]\.values\.(\w+)", path)
    if m:
        aid = facts["anomalies"][int(m.group(1))]["id"]
        return f"anomalies.json {aid}.values.{m.group(2)}", AN[aid]["values"][m.group(2)]
    m = re.match(r"anomalies\[(\d+)\]\.rule_threshold", path)
    if m:
        a = facts["anomalies"][int(m.group(1))]
        rule = next(r for r in A["rules"] if r["id"] == a["rule_id"])
        return f"anomalies.json rules[{rule['id']}].rule = '{rule['rule']}'", float(re.search(r"[\d.]+", rule["rule"]).group(0))
    m = re.match(r"(l4w_top_families_by_contrib|l4w_bottom_families_by_contrib)\[(\d+)\]\.(\w+)", path)
    if m:
        fam = facts[m.group(1)][int(m.group(2))]["family"]
        r = next(x for x in M["products_by_week"] if x["wk"] == wk and x["window"] == "L4W" and x["family"] == fam)
        return f"products_by_week[wk={wk}, L4W, {fam}].{m.group(3)}", r[m.group(3)]
    m = re.match(r"(lowest_wos_families|highest_wos_families)\[(\d+)\]\.(\w+)", path)
    if m:
        fam = facts[m.group(1)][int(m.group(2))]["family"]
        r = next(x for x in M["inventory_by_week"] if x["year"] == "TY" and x["wk"] == wk and x["family"] == fam)
        return f"inventory_by_week[TY, wk={wk}, {fam}].{m.group(3)}", r[m.group(3)]
    if path == "days_in_week":
        return f"weekly[wk={wk}].days", next(x for x in M["weekly"] if x["wk"] == wk)["days"]
    if path == "l4w_weeks" or path.startswith("l4w_weeks["):
        return f"trailing.{wk}.L4W.weeks", dig(M, f"trailing.{wk}.L4W.weeks")[int(path[10:-1])] if "[" in path else None
    up = WF.get(path)
    return f"trailing.{wk}.{up}", dig(M["trailing"][str(wk)], up)


def resolve_card(wk, src):
    """Independent lookup for the source strings 15_build_facts.py records."""
    m = re.match(r"inventory_by_week\[year=(\w+), wk=(\d+), family=([^\]]+)\]\.(\w+)", src)
    if m:
        return next(x for x in M["inventory_by_week"] if x["year"] == m.group(1) and x["wk"] == int(m.group(2)) and x["family"] == m.group(3))[m.group(4)]
    m = re.match(r"products_by_week\[wk=(\d+), window=(\w+), family=([^\]]+)\]\.(\w+)", src)
    if m:
        return next(x for x in M["products_by_week"] if x["wk"] == int(m.group(1)) and x["window"] == m.group(2) and x["family"] == m.group(3))[m.group(4)]
    m = re.match(r"genz_weekly\[WK=(\d+)\]\.(\w+)", src)
    if m:
        return next(x for x in M["genz_weekly"] if x["WK"] == int(m.group(1)))[m.group(2)]
    m = re.match(r"inventory_position\[([^\]]+)\]\.(\w+)", src)
    if m:
        return next(x for x in M["inventory_position"] if x["STYLE_GROUP"] == m.group(1))[m.group(2)]
    m = re.match(r"new_insider_by_segment\[(\w+)=([^\]]+)\]\.(\w+)", src)
    if m:
        return next(x for x in M["new_insider_by_segment"] if x["dimension"] == m.group(1) and x["segment"] == m.group(2))[m.group(3)]
    m = re.match(r"recommendations_sizing\.R1\.by_family\[([^\]]+)\]\.(\w+)", src)
    if m:
        return next(x for x in M["recommendations_sizing"]["R1"]["by_family"] if x["family"] == m.group(1))[m.group(2)]
    m = re.match(r"recommendations_sizing\.R3\.scenarios\[lift=([\d.]+)\]\.(\w+)", src)
    if m:
        return next(x for x in M["recommendations_sizing"]["R3"]["scenarios"] if x["returning_genz_lift"] == float(m.group(1)))[m.group(2)]
    m = re.match(r"anomalies\[(AN\d+)\]\.values\.(\w+)", src)
    if m:
        return AN[m.group(1)]["values"][m.group(2)]
    if src.startswith("recommendations_sizing.") or src.startswith("trailing."):
        return dig(M, src)
    raise ValueError(src)


def rows_for(text, facts, resolver):
    segs, res = V.annotate(text, facts)
    out = []
    for s in segs:
        if not s["num"]:
            continue
        f = s.get("fact")
        if f is None:
            out.append((s["text"].strip(), "—", "—", "UNMATCHED", "—", "FAIL"))
            continue
        fv = facts
        for part in re.findall(r"[^.\[\]]+|\[\d+\]", f):
            fv = fv[int(part[1:-1])] if part.startswith("[") else fv[part]
        src, iv = resolver(f)
        ok = "OK" if iv == fv else "MISMATCH"
        cands = next((m["candidates"] for m in res["matches"] if m["text"] == s["text"].strip()), [])
        also = [c for c in cands if c != f]
        out.append((s["text"].strip(), f + (f" <br>also: {', '.join(also)}" if also else ""), json.dumps(fv), src, json.dumps(iv), ok))
    return out, res


L = ["# Number trace: AI texts → facts → metrics.json", "",
     "Generated by `dashboard/tests/trace_numbers.py`. *independent* = value re-read from metrics.json/anomalies.json at the "
     "upstream path (not via the facts file). When several facts round to the same printed value, the best unit match is "
     "traced and the others are listed under *also*; the semantic review (which one the sentence means) is in dashboard/HISTORY.md.", ""]
total = bad = 0
for wk in WEEKS:
    S = json.loads((ROOT / "dashboard/summaries.json").read_text())[str(wk)]
    facts = json.loads((ROOT / S["facts_file"]).read_text())
    rows, res = rows_for(S["text"], facts, lambda f, wk=wk, facts=facts: resolve_summary(wk, f, facts))
    L += [f"## W{wk} weekly summary · {res['n_matched']}/{res['n_numbers']} · {S['generated_by']}", "", f"> {S['text']}", "",
          "| printed | facts field | facts value | upstream source | independent | check |", "|---|---|---|---|---|---|"]
    L += [f"| `{a}` | {b} | {c} | {d} | {e} | {g} |" for a, b, c, d, e, g in rows]
    total += len(rows)
    bad += sum(r[-1] != "OK" for r in rows)
    B = json.loads((ROOT / "dashboard/briefing.json").read_text())[str(wk)]
    cf = {c["card_id"]: c for c in json.loads((ROOT / B["cards_file"]).read_text())["cards"]}
    for c in B["cards"]:
        vals, srcs = cf[c["card_id"]]["values"], cf[c["card_id"]]["sources"]
        txt = f"{c['headline']} {c['body']}"
        rows, res = rows_for(txt, vals, lambda f, srcs=srcs, wk=wk: (srcs[f.split("[")[0]], resolve_card(wk, srcs[f.split("[")[0]])))
        L += ["", f"### W{wk} card `{c['card_id']}` ({c['pill']}) · {res['n_matched']}/{res['n_numbers']}", "", f"> **{c['headline']}** {c['body']}", "",
              "| printed | facts field | facts value | upstream source | independent | check |", "|---|---|---|---|---|---|"]
        L += [f"| `{a}` | {b} | {c_} | {d} | {e} | {g} |" for a, b, c_, d, e, g in rows]
        total += len(rows)
        bad += sum(r[-1] != "OK" for r in rows)
    L.append("")
L.insert(4, f"**{total} numbers traced across W{', W'.join(map(str, WEEKS))}: {total - bad} OK, {bad} not OK.**\n")
out = ROOT / "dashboard/verification/number_trace.md"
out.parent.mkdir(exist_ok=True)
out.write_text("\n".join(L))
print(f"{total} numbers traced, {bad} not OK → {out.relative_to(ROOT)}")
sys.exit(1 if bad else 0)
