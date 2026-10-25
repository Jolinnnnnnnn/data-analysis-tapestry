"""15 - Build the compact facts payloads the AI writer is allowed to use (selection only, NO arithmetic).

Inputs : data/processed/metrics.json, data/processed/anomalies.json
Outputs: data/dashboard/facts/W<wk>.json        weekly summary facts = metrics.weekly_facts[wk] with the
                                           "anomalies" placeholder replaced by that week's rule hits
         data/dashboard/facts/W<wk>_cards.json  briefing-card facts: card type, pill, finding/anomaly IDs,
                                           the exact values each card may cite (+ their metrics.json
                                           paths), and the micro-chart series

Every number in these files is copied from metrics.json / anomalies.json. Card choice and pill are
rule-driven (anomaly severities), never decided by the LLM (DECISIONS.md D17).
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data/processed"
OUT = ROOT / "data/dashboard/facts"
OUT.mkdir(parents=True, exist_ok=True)

M = json.loads((PROC / "metrics.json").read_text())
A = json.loads((PROC / "anomalies.json").read_text())
META = M["meta"]
WEEKS = META["weeks"]
LAST_FULL = META["last_full_week"]
AN = {a["id"]: a for a in A["anomalies"]}
SEV_RANK = {"critical": 0, "warning": 1, "info": 2}
PILL_RANK = {"Needs you today": 0, "Needs you": 1, "Pattern": 2, "Win": 3, "Watch": 4}

INV = {(r["year"], r["wk"], r["family"]): r for r in M["inventory_by_week"]}
POS = {r["STYLE_GROUP"]: r for r in M["inventory_position"]}
PBW = {(r["wk"], r["window"], r["family"]): r for r in M["products_by_week"]}
SEG = {(r["dimension"], r["segment"]): r for r in M["new_insider_by_segment"]}
GZW = {r["WK"]: r for r in M["genz_weekly"]}
SIZ = M["recommendations_sizing"]
HERO = ["Tabby", "Pillow Tabby"]
KEYF = {"Tabby": "tabby", "Pillow Tabby": "pillow_tabby"}


def week_anoms(w):
    out = [AN[i] for i in A["by_week"].get(str(w), [])]
    return sorted(out, key=lambda a: (SEV_RANK[a["severity"]], a["rule_id"], a["entity"]))


RULE_THRESHOLD = {}
for _r in A["rules"]:  # the documented rule constant, copied from the rule text (e.g. "< 0.20" → 0.2)
    _m = re.search(r"([+-]?\d+(?:\.\d+)?)", _r["rule"])
    RULE_THRESHOLD[_r["id"]] = float(_m.group(1)) if _m else None


def slim(a):
    out = {k: a[k] for k in ("id", "severity", "rule_id", "entity", "message", "values")}
    out["rule_threshold"] = RULE_THRESHOLD[a["rule_id"]]  # messages quote it, e.g. "(< 20%)"
    return out


class Card:
    """Collects values together with the metrics.json path each value was copied from."""

    def __init__(self, card_id, title, meta, findings, explore_tab, ask):
        self.d = {"card_id": card_id, "title": title, "meta": meta, "findings": findings, "anomaly_ids": [],
                  "explore_tab": explore_tab, "ask_prefill": ask, "values": {}, "sources": {}, "chart": None}

    def put(self, name, value, src):
        self.d["values"][name] = value
        self.d["sources"][name] = src

    def pill(self, p):
        self.d["pill"] = p
        self.d["pill_rank"] = PILL_RANK[p]


def stock_card(w, anoms):
    c = Card("stock", "Tabby franchise stock-out", f"Inventory · Tabby franchise · W{w}", ["F11", "F12", "R1"], "G4",
             f"Why is Tabby flagged in week {w}?")
    hits = [a for a in anoms if a["entity"] in HERO and a["rule_id"] in ("WOS_LOW", "WOS_COLLAPSE_VS_LY", "RECEIPTS_BELOW_SALES")]
    c.d["anomaly_ids"] = [a["id"] for a in hits]
    sev = min((SEV_RANK[a["severity"]] for a in hits), default=9)
    c.pill("Needs you today" if sev == 0 else "Needs you" if sev == 1 else "Watch")
    rows = []
    for fam in HERO:
        k = KEYF[fam]
        r = INV[("TY", w, fam)]
        src = f"inventory_by_week[year=TY, wk={w}, family={fam}]"
        c.put(f"{k}_wos", r["wos"], f"{src}.wos")
        c.put(f"{k}_wos_ly_same_week", r["wos_ly_same_week"], f"{src}.wos_ly_same_week")
        c.put(f"{k}_on_hand_eow", r["on_hand_eow"], f"{src}.on_hand_eow")
        c.put(f"{k}_wos_window_weeks", r["wos_window_weeks"], f"{src}.wos_window_weeks")
        tone = "red" if any(a["entity"] == fam and a["severity"] == "critical" for a in hits) else \
            "amber" if any(a["entity"] == fam for a in hits) else "accent"
        rows += [{"label": f"{fam} · TY", "value": r["wos"], "fmt": "wos", "tone": tone},
                 {"label": f"{fam} · LY", "value": r["wos_ly_same_week"], "fmt": "wos", "tone": "ly"}]
    if w >= LAST_FULL:  # latest-position facts (receipts window W24–29, R1 sizing) are only valid from W29
        for fam in HERO:
            k, p = KEYF[fam], POS[fam]
            c.put(f"{k}_receipts_to_sales_ty", p["receipts_to_sales_TY"], f"inventory_position[{fam}].receipts_to_sales_TY")
            c.put(f"{k}_receipts_to_sales_ly", p["receipts_to_sales_LY"], f"inventory_position[{fam}].receipts_to_sales_LY")
        r1 = SIZ["R1"]
        c.put("r1_demand_at_risk_usd", r1["demand_at_risk_usd_sample"], "recommendations_sizing.R1.demand_at_risk_usd_sample")
        c.put("r1_demand_at_risk_pct_of_next_4wk", r1["demand_at_risk_pct_of_next_4wk_demand"],
              "recommendations_sizing.R1.demand_at_risk_pct_of_next_4wk_demand")
        for b in r1["by_family"]:
            k = KEYF[b["family"]]
            c.put(f"{k}_weeks_to_stockout", b["weeks_to_stockout_at_TY_pace"],
                  f"recommendations_sizing.R1.by_family[{b['family']}].weeks_to_stockout_at_TY_pace")
    c.d["chart"] = {"type": "bars", "unit": "weeks of supply", "rows": rows}
    return c


def retention_card(w, anoms):
    c = Card("retention", "Retention leak and Insider gap", f"Retention proxy · L4W ending W{w}", ["F6", "F7", "R3"], "G2",
             f"Why is retention flagged in week {w}?")
    hits = [a for a in anoms if a["rule_id"] in ("RETURNING_YOY_FLAT", "GENZ_RETURNING_YOY_NEG", "GENZ_NEW_INSIDER_LOW")]
    c.d["anomaly_ids"] = [a["id"] for a in hits]
    sev = min((SEV_RANK[a["severity"]] for a in hits), default=9)
    c.pill("Needs you today" if sev == 0 else "Needs you" if sev == 1 else "Watch")
    tr = M["trailing"][str(w)]
    for win in ("L4W", "PTD"):
        b, lw = tr[win], win.lower()
        src = f"trailing.{w}.{win}"
        c.put(f"{lw}_returning_ty", b["returning_customers"]["ty"], f"{src}.returning_customers.ty")
        c.put(f"{lw}_returning_ly", b["returning_customers"]["ly"], f"{src}.returning_customers.ly")
        c.put(f"{lw}_returning_yoy_pct", b["returning_customers"]["yoy_pct"], f"{src}.returning_customers.yoy_pct")
        c.put(f"{lw}_genz_returning_ty", b["genz_returning"]["ty"], f"{src}.genz_returning.ty")
        c.put(f"{lw}_genz_returning_ly", b["genz_returning"]["ly"], f"{src}.genz_returning.ly")
        c.put(f"{lw}_genz_returning_yoy_pct", b["genz_returning"]["yoy_pct"], f"{src}.genz_returning.yoy_pct")
        c.put(f"{lw}_genz_new_insider_rate_ty", b["genz_new_insider_rate"]["ty"], f"{src}.genz_new_insider_rate.ty")
        c.put(f"{lw}_genz_new_insider_rate_ly", b["genz_new_insider_rate"]["ly"], f"{src}.genz_new_insider_rate.ly")
        c.put(f"{lw}_new_insider_rate_ty", b["new_insider_rate"]["ty"], f"{src}.new_insider_rate.ty")
    c.d["values"]["l4w_weeks"] = tr["L4W"]["weeks"]
    c.d["sources"]["l4w_weeks"] = f"trailing.{w}.L4W.weeks"
    if w >= LAST_FULL:  # TY segment gaps (F7) and R3 sizing describe the whole TY period
        rows = []
        for dim, seg, lab in (("SALES_CHANNEL", "OUTLET", "Outlet"), ("CHANNEL_DETAIL", "eComm", "eComm"),
                              ("GEO_REGION", "Greater China", "Greater China")):
            s, k = SEG[(dim, seg)], lab.lower().replace(" ", "_")
            c.put(f"{k}_genz_new_insider_rate", s["genz_new_insider_rate"], f"new_insider_by_segment[{dim}={seg}].genz_new_insider_rate")
            c.put(f"{k}_other_new_insider_rate", s["other_new_insider_rate"], f"new_insider_by_segment[{dim}={seg}].other_new_insider_rate")
            rows += [{"label": f"{lab} · Gen Z new", "value": s["genz_new_insider_rate"], "fmt": "pct", "tone": "accent"},
                     {"label": f"{lab} · other new", "value": s["other_new_insider_rate"], "fmt": "pct", "tone": "neutral"}]
        r3 = SIZ["R3"]
        c.put("millennial_new_insider_rate", r3["millennial_new_insider_rate"], "recommendations_sizing.R3.millennial_new_insider_rate")
        sc = next(s for s in r3["scenarios"] if s["returning_genz_lift"] == 0.1)
        c.put("r3_returning_genz_lift", sc["returning_genz_lift"], "recommendations_sizing.R3.scenarios[lift=0.1].returning_genz_lift")
        c.put("r3_pct_of_ty_demand", sc["pct_of_TY_demand"], "recommendations_sizing.R3.scenarios[lift=0.1].pct_of_TY_demand")
        c.d["chart"] = {"type": "bars", "unit": "Insider attach of new customers (TY)", "rows": rows}
    else:
        b = tr["L4W"]
        c.d["chart"] = {"type": "bars", "unit": "Insider attach of new customers, L4W", "rows": [
            {"label": "Gen Z new · TY", "value": b["genz_new_insider_rate"]["ty"], "fmt": "pct", "tone": "accent"},
            {"label": "Gen Z new · LY", "value": b["genz_new_insider_rate"]["ly"], "fmt": "pct", "tone": "ly"},
            {"label": "All new · TY", "value": b["new_insider_rate"]["ty"], "fmt": "pct", "tone": "neutral"},
            {"label": "All new · LY", "value": b["new_insider_rate"]["ly"], "fmt": "pct", "tone": "ly"}]}
    return c


def pattern_card(w, anoms):
    c = Card("pattern", "Gen Z share of new customers", f"Acquisition · Gen Z share of new · W{WEEKS[0]}-W{w}", ["F5"], "G2",
             f"Gen Z share of new customers by week up to week {w}?")
    c.d["anomaly_ids"] = [a["id"] for a in anoms if a["rule_id"] in ("GENZ_SHARE_BELOW_LY", "GENZ_NEW_YOY_NEG", "GENZ_NEW_WOW_DROP")]
    c.pill("Needs you" if c.d["anomaly_ids"] else "Pattern")
    first, last = GZW[WEEKS[0]], GZW[w]
    c.put("first_week_genz_share_of_new_ty", first["genz_share_of_new_TY"], f"genz_weekly[WK={WEEKS[0]}].genz_share_of_new_TY")
    c.put("first_week_genz_share_of_new_ly", first["genz_share_of_new_LY"], f"genz_weekly[WK={WEEKS[0]}].genz_share_of_new_LY")
    c.put("week_genz_share_of_new_ty", last["genz_share_of_new_TY"], f"genz_weekly[WK={w}].genz_share_of_new_TY")
    c.put("week_genz_share_of_new_ly", last["genz_share_of_new_LY"], f"genz_weekly[WK={w}].genz_share_of_new_LY")
    c.put("first_week_genz_new_ty", first["genz_new_TY"], f"genz_weekly[WK={WEEKS[0]}].genz_new_TY")
    c.put("week_genz_new_ty", last["genz_new_TY"], f"genz_weekly[WK={w}].genz_new_TY")
    c.put("week_genz_new_ly", last["genz_new_LY"], f"genz_weekly[WK={w}].genz_new_LY")
    cols = [{"label": f"W{x}", "value": GZW[x]["genz_share_of_new_TY"], "partial": x == META["partial_week"]}
            for x in WEEKS if x <= w]
    c.d["chart"] = {"type": "columns", "unit": "Gen Z share of new customers, TY", "fmt": "pct0", "cols": cols}
    return c


def win_card(w, anoms):
    c = Card("win", "Gen Z acquisition and Tabby growth", f"Growth · PTD W{WEEKS[0]}-W{w} · L4W families", ["F4", "F9"], "G3",
             f"Top 3 families by contribution in L4W for week {w}")
    c.d["anomaly_ids"] = [a["id"] for a in anoms if a["rule_id"] == "SALES_YOY_SPIKE"]
    c.pill("Win")
    ptd = M["trailing"][str(w)]["PTD"]
    src = f"trailing.{w}.PTD"
    c.put("ptd_genz_new_ty", ptd["genz_new"]["ty"], f"{src}.genz_new.ty")
    c.put("ptd_genz_new_ly", ptd["genz_new"]["ly"], f"{src}.genz_new.ly")
    c.put("ptd_genz_new_yoy_pct", ptd["genz_new"]["yoy_pct"], f"{src}.genz_new.yoy_pct")
    c.put("ptd_genz_share_of_new_ty", ptd["genz_share_of_new"]["ty"], f"{src}.genz_share_of_new.ty")
    c.put("ptd_genz_share_of_new_ly", ptd["genz_share_of_new"]["ly"], f"{src}.genz_share_of_new.ly")
    c.put("ptd_sales_yoy_pct", ptd["sales"]["yoy_pct"], f"{src}.sales.yoy_pct")
    for fam in HERO:
        r, k = PBW[(w, "L4W", fam)], KEYF[fam]
        s = f"products_by_week[wk={w}, window=L4W, family={fam}]"
        c.put(f"{k}_l4w_sales_yoy_pct", r["sales_yoy_pct"], f"{s}.sales_yoy_pct")
        c.put(f"{k}_l4w_contrib_pts", r["contrib_pts"], f"{s}.contrib_pts")
    c.put("l4w_sales_yoy_pct", M["trailing"][str(w)]["L4W"]["sales"]["yoy_pct"], f"trailing.{w}.L4W.sales.yoy_pct")
    # the ranked list lets the validator check rank words ("Tabby leads L4W growth") against the facts
    c.put("l4w_top_families_by_contrib", M["weekly_facts"][str(w)]["l4w_top_families_by_contrib"],
          f"weekly_facts.{w}.l4w_top_families_by_contrib (products_by_week[wk={w}, L4W] ranked by contrib_pts)")
    c.d["chart"] = {"type": "bars", "unit": f"Gen Z new customers, PTD W{WEEKS[0]}-W{w} (sample)", "rows": [
        {"label": "Gen Z new · LY", "value": ptd["genz_new"]["ly"], "fmt": "int", "tone": "ly"},
        {"label": "Gen Z new · TY", "value": ptd["genz_new"]["ty"], "fmt": "int", "tone": "green"}]}
    return c


def overstock_card(w, anoms):
    c = Card("overstock", "Apparel overstock", f"Inventory · Halo apparel · W{w}", ["F10", "F11", "R2"], "G4",
             f"Which families have WOS above 15 in week {w}?")
    high = [a for a in anoms if a["rule_id"] == "WOS_HIGH"]
    decl = [a for a in anoms if a["rule_id"] == "FAMILY_L4W_DECLINE"]
    c.d["anomaly_ids"] = [a["id"] for a in high + decl]
    c.pill("Watch")
    fams = [a["entity"] for a in high] or [x["family"] for x in M["weekly_facts"][str(w)]["highest_wos_families"]]
    rows = []
    for fam in fams:
        r = INV[("TY", w, fam)]
        k = fam.lower().replace(" ", "_")
        s = f"inventory_by_week[year=TY, wk={w}, family={fam}]"
        c.put(f"{k}_wos", r["wos"], f"{s}.wos")
        c.put(f"{k}_wos_ly_same_week", r["wos_ly_same_week"], f"{s}.wos_ly_same_week")
        c.put(f"{k}_wos_window_weeks", r["wos_window_weeks"], f"{s}.wos_window_weeks")
        rows += [{"label": f"{fam} · TY", "value": r["wos"], "fmt": "wos", "tone": "amber" if high else "accent"},
                 {"label": f"{fam} · LY", "value": r["wos_ly_same_week"], "fmt": "wos", "tone": "ly"}]
    for a in decl:
        k = a["entity"].lower().replace(" ", "_")
        c.put(f"{k}_l4w_sales_yoy_pct", a["values"]["sales_yoy_pct"], f"anomalies[{a['id']}].values.sales_yoy_pct")
    if w >= LAST_FULL:
        r2 = SIZ["R2"]
        c.put("r2_excess_units", r2["excess_units"], "recommendations_sizing.R2.excess_units")
        c.put("r2_excess_retail_value_usd", r2["excess_retail_value_usd_sample"], "recommendations_sizing.R2.excess_retail_value_usd_sample")
        c.put("median_wos", r2["median_wos"], "recommendations_sizing.R2.median_wos")
    c.d["chart"] = {"type": "bars", "unit": "weeks of supply", "rows": rows}
    return c


# weekly_facts field → the upstream metrics.json location it was copied from (shown on hover in the UI)
WF_SRC = {"l1w_sales_ty": "L1W.sales.ty", "l1w_sales_ly": "L1W.sales.ly", "l1w_sales_yoy_pct": "L1W.sales.yoy_pct",
          "l1w_txns_yoy_pct": "L1W.txns.yoy_pct", "l1w_aov_ty": "L1W.aov.ty", "l1w_aov_yoy_pct": "L1W.aov.yoy_pct",
          "l1w_sales_wow_pct": "L1W.wow.sales", "l4w_sales_yoy_pct": "L4W.sales.yoy_pct", "l4w_txns_yoy_pct": "L4W.txns.yoy_pct",
          "ptd_sales_yoy_pct": "PTD.sales.yoy_pct", "l1w_genz_new_ty": "L1W.genz_new.ty", "l1w_genz_new_ly": "L1W.genz_new.ly",
          "l1w_genz_new_yoy_pct": "L1W.genz_new.yoy_pct", "l1w_genz_share_of_new_ty": "L1W.genz_share_of_new.ty",
          "l1w_genz_share_of_new_ly": "L1W.genz_share_of_new.ly", "l4w_genz_new_ty": "L4W.genz_new.ty",
          "l4w_genz_new_ly": "L4W.genz_new.ly", "l4w_genz_new_yoy_pct": "L4W.genz_new.yoy_pct",
          "l4w_returning_yoy_pct": "L4W.returning_customers.yoy_pct", "l4w_genz_new_insider_rate_ty": "L4W.genz_new_insider_rate.ty"}


def weekly_sources(w, facts):
    """Map every numeric leaf path of a weekly facts payload to its upstream metrics.json / anomalies.json path."""
    src = {}
    for k, path in WF_SRC.items():
        src[k] = f"trailing.{w}.{path}"
    src["days_in_week"] = f"weekly[wk={w}].days"
    for lst, table in (("l4w_top_families_by_contrib", "products_by_week"), ("l4w_bottom_families_by_contrib", "products_by_week"),
                       ("lowest_wos_families", "inventory_by_week"), ("highest_wos_families", "inventory_by_week")):
        for i, row in enumerate(facts[lst]):
            for k in row:
                if k != "family":
                    sel = f"wk={w}, L4W, {row['family']}" if table == "products_by_week" else f"TY, wk={w}, {row['family']}"
                    src[f"{lst}[{i}].{k}"] = f"{table}[{sel}].{k}"
    for i, a in enumerate(facts["anomalies"]):
        for k in a["values"]:
            src[f"anomalies[{i}].values.{k}"] = f"anomalies.json {a['id']}.values.{k}"
        src[f"anomalies[{i}].rule_threshold"] = f"anomalies.json rules[{a['rule_id']}].rule"
    return src


# Playhead timeline (M1): one event per week, chosen by rule priority; text is the rule's deterministic message.
def timeline():
    seen, events = set(), []
    first_crit = lambda a: a["severity"] == "critical" and a["rule_id"] not in seen
    stock_rules = ["RECEIPTS_BELOW_SALES", "WOS_LOW", "WOS_COLLAPSE_VS_LY", "WOS_HIGH"]
    for w in WEEKS:
        an = week_anoms(w)
        pick, tag = None, ""
        crit = [a for a in an if first_crit(a)]
        stock_first = [a for a in an if a["rule_id"] in stock_rules and not (seen & set(stock_rules))]
        if crit:
            pick, tag = sorted(crit, key=lambda a: (a["entity"] != "Tabby", a["id"]))[0], "first critical"
        elif stock_first:
            pick, tag = sorted(stock_first, key=lambda a: (stock_rules.index(a["rule_id"]), a["entity"] != "Tabby"))[0], "first stock warning"
        else:
            for rid in ("SALES_WOW_SWING", "SALES_YOY_SPIKE", "TXNS_YOY_NEG", "PARTIAL_WEEK"):
                hit = [a for a in an if a["rule_id"] == rid]
                if hit:
                    pick = hit[0]
                    break
        seen |= {a["rule_id"] for a in an}
        if pick:
            events.append({"wk": w, "tag": tag, "severity": pick["severity"], "rule_id": pick["rule_id"],
                           "anomaly_id": pick["id"], "message": pick["message"]})
    return events


(OUT.parent / "timeline.json").write_text(json.dumps(timeline(), indent=1, ensure_ascii=False))

written = []
for w in WEEKS:
    anoms = week_anoms(w)
    facts = dict(M["weekly_facts"][str(w)])
    assert facts["anomalies"] == "see anomalies.json", "weekly_facts placeholder changed"
    facts["anomalies"] = [slim(a) for a in anoms]
    facts["_sources"] = weekly_sources(w, facts)
    (OUT / f"W{w}.json").write_text(json.dumps(facts, indent=1, ensure_ascii=False))
    cards = [f(w, anoms).d for f in (stock_card, retention_card, pattern_card, win_card, overstock_card)]
    cards.sort(key=lambda c: c["pill_rank"])  # stable: severity first, then the fixed order above
    payload = {"week": w, "week_label": facts["week"], "is_partial_week": facts["is_partial_week"],
               "n_critical_alerts": None, "cards": cards}
    # alert counts are counts of rule hits (selection), recorded for the badge/h1
    payload["n_critical_alerts"] = len([a for a in anoms if a["severity"] == "critical"])
    payload["n_alerts_by_severity"] = {s: len([a for a in anoms if a["severity"] == s]) for s in SEV_RANK}
    payload["n_alerts"] = len(anoms)
    payload["n_rules"] = len(A["rules"])
    payload["rule_hits"] = {r["id"]: len([a for a in anoms if a["rule_id"] == r["id"]]) for r in A["rules"]}
    payload["n_needs_you"] = len([c for c in cards if c["pill_rank"] <= 1])
    payload["n_rules_fired"] = len([k for k, v in payload["rule_hits"].items() if v])
    payload["n_alerts_all_weeks_max"] = max(len(A["by_week"].get(str(x), [])) for x in WEEKS)
    payload["n_fyi"] = len(cards) - payload["n_needs_you"]
    (OUT / f"W{w}_cards.json").write_text(json.dumps(payload, indent=1, ensure_ascii=False))
    written.append(w)

# Cross-check: every anomaly value and weekly fact made it through untouched
for w in WEEKS:
    f = json.loads((OUT / f"W{w}.json").read_text())
    for k, v in M["weekly_facts"][str(w)].items():
        if k != "anomalies":
            assert f[k] == v, (w, k)
    assert [a["id"] for a in f["anomalies"]] == [a["id"] for a in week_anoms(w)]
print(f"facts written for weeks {written} → {OUT.relative_to(ROOT)} (W<wk>.json + W<wk>_cards.json)")
