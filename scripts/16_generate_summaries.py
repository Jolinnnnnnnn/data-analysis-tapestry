"""16 - Word the weekly summary, headline and briefing cards from the facts files (AI step), then validate.

Every text is written as a placeholder source: figures are never typed, each number is {fact key|format}, e.g.
"W29 demand {l1w_sales_ty|money_k}, {l1w_sales_yoy_pct|pct+} YoY." This script renders each source once
(17's render(): shown text + one citation per number) and stores source, shown text and citations together, so the
validator can check that every number IS the fact it cites and that the words around it agree (DECISIONS.md D25).

Writer priority for every text (summary, headline or card):
  1. LIVE   - ANTHROPIC_API_KEY set → Claude (claude-opus-5-5) writes the placeholder source from the facts JSON only.
              If the validator flags it, Claude gets one retry with the failed checks listed; if it still fails,
              the deterministic template is used and the rejection is logged.
  2. PREGEN - placeholder source written by the build session (Claude Code acting as the model, see PROMPTS.md
              P17/P20) from exactly the same facts, stored in ai/session_texts.json with an md5 of the facts it
              was written from. A stale md5 (facts changed) → not used.
  3. TEMPLATE - deterministic placeholder wording of the same facts.

Outputs: data/dashboard/summaries.json  {"<wk>": {text, source, citations, validation, headline..., demos}}
         data/dashboard/briefing.json   {"<wk>": {..., cards:[{headline, body, *_source, citations, validation}]}}
Usage:   python 16_generate_summaries.py            build outputs
         python 16_generate_summaries.py --stamp    record facts md5 for every pregenerated text (run once
                                                    after (re)writing session_texts.json, after checking it)
"""
import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DASH = ROOT / "data/dashboard"
FACTS = DASH / "facts"
PREGEN = ROOT / "ai/session_texts.json"
MODEL = "claude-opus-5-5"

_spec = importlib.util.spec_from_file_location("validator", Path(__file__).with_name("17_validate_summaries.py"))
validator = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(validator)
validate_text, render = validator.validate_text, validator.render

FORMAT_LIST = ", ".join(f"{k} ({v['example'].split(' (')[0]})" for k, v in validator.VOCAB["formats"].items())
PLACEHOLDER_RULES = (
    "Never type a figure. Write every number as a placeholder {key|format}: key is the fact's path in the JSON "
    "(l1w_sales_ty, l4w_top_families_by_contrib[0].contrib_pts, anomalies[2].values.sales_yoy_pct) and format is one of "
    f"{FORMAT_LIST}. Percent fields are fractions and the format does the rounding. No spelled-out numbers (two, half). "
    "Code checks every placeholder: put the metric word (demand, transactions, AOV, weeks of supply, receipts, share, "
    "new customers, returning, Insider, contribution, units) and the subject (Gen Z, Tabby, Outlet) right before its "
    "number, give each number its own clause rather than 'X and Y respectively', use up or down words only where they "
    "match the sign of a cited change, label last-year values 'LY', and use rank words (leads, top, largest drag, "
    "lowest) only for a family that the facts' ranked lists put there."
)
SYSTEM_SUMMARY = (
    "You write a weekly retail performance summary for a merchandising leadership team, from the JSON facts only. "
    "Do not compute or infer new numbers (no differences, ratios, sums or 'x times'). " + PLACEHOLDER_RULES + " "
    "Lead with the most severe anomaly (critical > warning > info). Say 'L4W' and 'period-to-date' for windows. "
    "Plain prose, one paragraph, no headings or bullets. Max 180 words."
)
SYSTEM_HEADLINE = (
    "You write the masthead headline of a weekly retail dashboard: at most two short sentences, about 15 words. "
    "First the week's result (demand and its YoY), then the single most severe alert. State results; never address "
    "the reader. " + PLACEHOLDER_RULES
)
SYSTEM_CARD = (
    "You write one briefing card for a retail analytics agent, in its voice: first person, calm, specific. "
    "Return JSON {\"headline\": str, \"body\": str}. Headline: ONE sentence that states what happened with "
    "the key numbers in it (max 22 words). Body: 2-3 short sentences: why it matters, the evidence, what to do. "
    "Use ONLY the card's `values` (keys are paths inside `values`). Do not compute or infer new numbers. "
    + PLACEHOLDER_RULES + " You may cite finding IDs (F11) and recommendation IDs (R1)."
)


def md5(obj):
    return hashlib.md5(json.dumps(obj, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


SEV_WORD = {"critical": "Critical", "warning": "Warning", "info": "Note"}


# ---------------------------------------------------------------- template writer (placeholder sources)
def anomaly_source(i, a):
    """One alert as a placeholder sentence (the rule's own message has typed figures, so it is not reused)."""
    p, e, r = f"anomalies[{i}].values", a["entity"], a["rule_id"]
    if r in ("WOS_LOW", "WOS_HIGH", "WOS_COLLAPSE_VS_LY"):
        return f"{e} has {{{p}.wos|wos}} weeks of supply vs {{{p}.wos_ly_same_week|wos}} LY."
    if r == "FAMILY_L4W_DECLINE":
        return f"{e} L4W demand {{{p}.sales_yoy_pct|pct+}} YoY."
    if r == "GENZ_NEW_INSIDER_LOW":
        return f"L4W Insider attach of new Gen Z {{{p}.genz_new_insider_rate_ty|pct}}."
    if r == "GENZ_RETURNING_YOY_NEG":
        return f"L4W returning Gen Z {{{p}.genz_returning_ty|int}} vs {{{p}.genz_returning_ly|int}} LY ({{{p}.genz_returning_yoy_pct|pct+}})."
    if r == "RETURNING_YOY_FLAT":
        return f"L4W returning customers {{{p}.returning_yoy_pct|pct+}} YoY ({{{p}.returning_ty|int}} vs {{{p}.returning_ly|int}} LY)."
    if r == "TXNS_YOY_NEG":
        return f"Transactions {{{p}.txns_yoy_pct|pct+}} YoY."
    if r == "AOV_YOY_SWING":
        return f"AOV {{{p}.aov_yoy_pct|pct+}} YoY ({{{p}.aov_ty|money2}} vs {{{p}.aov_ly|money2}} LY)."
    if r == "SALES_WOW_SWING":
        return f"Demand {{{p}.sales_wow_pct|pct+}} WoW; transactions {{{p}.txns_wow_pct|pct+}}, AOV {{{p}.aov_wow_pct|pct+}}."
    if r in ("SALES_YOY_SPIKE", "SALES_YOY_NEG", "SALES_YOY_DROP"):
        return f"Demand {{{p}.sales_yoy_pct|pct+}} YoY."
    if r == "RECEIPTS_BELOW_SALES":
        return f"{e} receipts {{{p}.receipts_to_sales_TY|pct0}} of units sold, LY {{{p}.receipts_to_sales_LY|pct0}}."
    if r == "PARTIAL_WEEK":
        return f"Partial week: {{{p}.days|int}} days, compared with the same days last year."
    return f"{r} alert {a['id']}."


def template_summary(f):
    """Deterministic wording of the weekly facts. Used when no live model and no current pregenerated text."""
    parts = []
    an = f["anomalies"]
    if an:
        parts.append(f"{SEV_WORD[an[0]['severity']]}: {anomaly_source(0, an[0])}")
    parts.append("Demand {l1w_sales_yoy_pct|pct+} YoY at {l1w_sales_ty|money_k}, LY {l1w_sales_ly|money_k}.")
    if f["is_partial_week"]:
        parts.append("This is a partial week, compared on the same days last year.")
    parts.append("Transactions {l1w_txns_yoy_pct|pct+} YoY, AOV {l1w_aov_yoy_pct|pct+}.")
    if f["l1w_sales_wow_pct"] is not None:
        parts.append("Demand {l1w_sales_wow_pct|pct+} WoW.")
    parts.append("L4W demand {l4w_sales_yoy_pct|pct+}; period-to-date {ptd_sales_yoy_pct|pct+}.")
    parts.append("Gen Z new customers {l1w_genz_new_ty|int} vs {l1w_genz_new_ly|int} LY ({l1w_genz_new_yoy_pct|pct+}), "
                 "a {l1w_genz_share_of_new_ty|pct} share of new customers vs {l1w_genz_share_of_new_ly|pct} LY.")
    parts.append("L4W Insider attach of new Gen Z {l4w_genz_new_insider_rate_ty|pct}.")
    t, b = f["l4w_top_families_by_contrib"][0], f["l4w_bottom_families_by_contrib"][0]
    parts.append(f"Top L4W contributor {t['family']} at {{l4w_top_families_by_contrib[0].contrib_pts|pts+}}; "
                 f"largest drag {b['family']} at {{l4w_bottom_families_by_contrib[0].contrib_pts|pts+}}.")
    lo = f["lowest_wos_families"][0]
    parts.append(f"Lowest weeks of supply: {lo['family']} {{lowest_wos_families[0].wos|wos}} vs {{lowest_wos_families[0].wos_ly_same_week|wos}} LY.")
    for i, a in enumerate(an[1:3], start=1):
        parts.append(f"{SEV_WORD[a['severity']]}: {anomaly_source(i, a)}")
    return " ".join(parts)


def template_headline(f):
    part = " so far" if f["is_partial_week"] else ""
    top = f["anomalies"][0] if f["anomalies"] else None
    return (f"{f['week'].split(' ')[-1]}{part}: demand {{l1w_sales_ty|money_k}}, {{l1w_sales_yoy_pct|pct+}} YoY."
            + (f" {anomaly_source(0, top)}" if top and top["severity"] == "critical" else ""))


def template_card(c):
    v, cid = c["values"], c["card_id"]
    if cid == "stock":
        h = ("Tabby has {tabby_wos|wos} weeks of supply and Pillow Tabby {pillow_tabby_wos|wos}, "
             "against {tabby_wos_ly_same_week|wos} and {pillow_tabby_wos_ly_same_week|wos} last year.")
        b = "Units on hand: Tabby {tabby_on_hand_eow|int}, Pillow Tabby {pillow_tabby_on_hand_eow|int}."
        if "r1_demand_at_risk_usd" in v:
            b += (" Tabby receipts {tabby_receipts_to_sales_ty|pct0} of units sold, LY {tabby_receipts_to_sales_ly|pct0}."
                  " Demand at risk {r1_demand_at_risk_usd|money_k} (R1).")
    elif cid == "retention":
        h = ("L4W returning customers {l4w_returning_ty|int} vs {l4w_returning_ly|int} LY ({l4w_returning_yoy_pct|pct+}); "
             "new Gen Z Insider attach {l4w_genz_new_insider_rate_ty|pct}.")
        b = ("L4W returning Gen Z {l4w_genz_returning_ty|int} vs {l4w_genz_returning_ly|int} LY; "
             "period-to-date {ptd_genz_returning_yoy_pct|pct+}. This is a mix proxy (D8).")
    elif cid == "pattern":
        h = ("Gen Z share of new customers is {week_genz_share_of_new_ty|pct} this week, "
             "from {first_week_genz_share_of_new_ty|pct} in the first week.")
        b = "Last year the same week was {week_genz_share_of_new_ly|pct}."
    elif cid == "win":
        h = "Gen Z new customers period-to-date {ptd_genz_new_ty|int} vs {ptd_genz_new_ly|int} LY ({ptd_genz_new_yoy_pct|pct+})."
        b = ("Tabby L4W demand {tabby_l4w_sales_yoy_pct|pct+} YoY, contribution {tabby_l4w_contrib_pts|pts+}; "
             "Pillow Tabby {pillow_tabby_l4w_sales_yoy_pct|pct+}.")
    else:
        fams = [k[:-4] for k in v if k.endswith("_wos") and k != "median_wos"]
        k = fams[0]
        h = f"{k.replace('_', ' ').title()} holds {{{k}_wos|wos}} weeks of supply against {{{k}_wos_ly_same_week|wos}} last year."
        b = "Slow Halo apparel is tying up stock (F10, F11)."
        if "r2_excess_units" in v:
            b += " {r2_excess_units|int} units, about {r2_excess_retail_value_usd|money_k} at retail, sit above median cover (R2)."
    return {"headline": h, "body": b}


# ================================================================ === LIVE MODEL PLUG-IN POINT ===
# Set ANTHROPIC_API_KEY (or an `ant auth login` profile + DASHBOARD_LIVE=1) to have Claude write every text.
# The model only ever sees the facts JSON for that week/card and writes placeholders, never figures. Its output is
# rendered and validated below, so a live model cannot put an unverified or misattributed number on screen.
def _live_enabled():
    return bool(os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("DASHBOARD_LIVE"))


def call_claude(system, user_json, want_json=False, feedback=None):
    import anthropic  # imported lazily: the default (offline) build needs no SDK
    client = anthropic.Anthropic()
    content = "FACTS JSON:\n" + json.dumps(user_json, ensure_ascii=False, indent=1)
    if feedback:
        content += f"\n\nThe validator rejected your previous draft: {feedback}. Rewrite it so every check passes."
    extra = {"fallbacks": "default", "output_config": {"effort": "medium"}}
    if want_json:
        extra["output_config"]["format"] = {"type": "json_schema", "schema": {
            "type": "object", "properties": {"headline": {"type": "string"}, "body": {"type": "string"}},
            "required": ["headline", "body"], "additionalProperties": False}}
    resp = client.messages.create(
        model=MODEL, max_tokens=16000, system=system,
        messages=[{"role": "user", "content": content}],
        extra_headers={"anthropic-beta": "server-side-fallback-2026-07-01"},
        extra_body=extra,
    )
    if resp.stop_reason == "refusal":
        raise RuntimeError("model refused")
    text = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text").strip()
    return json.loads(text) if want_json else text


def live_text(system, facts, check_facts, want_json=False):
    """Two attempts; returns (placeholder source, attempts_log) or (None, log) if both fail validation."""
    log, feedback = [], None
    for _ in range(2):
        out = call_claude(system, facts, want_json, feedback)
        if want_json:
            v = validate_rendered(out, check_facts)
        else:
            text, cites = render(out, check_facts)
            v = validate_text(text, check_facts, cites)
        log.append({"status": v["status"], "failures": [f"{f['check']}: {f['text']} ({f['detail']})" for f in v["failures"]]})
        if v["status"] == "PASS":
            return out, log
        feedback = "; ".join(log[-1]["failures"])
    return None, log
# ================================================================ === END LIVE MODEL PLUG-IN POINT ===


def render_card(out, values):
    """Render a card's headline and body sources; citations cover the validated text "headline body"."""
    h, hc = render(out["headline"], values)
    b, bc = render(out["body"], values)
    off = len(h) + 1
    return h, b, hc + [{**c, "start": c["start"] + off, "end": c["end"] + off} for c in bc]


def validate_rendered(out, values):
    h, b, cites = render_card(out, values)
    return validate_text(f"{h} {b}", values, cites)


def load_pregen():
    return json.loads(PREGEN.read_text()) if PREGEN.exists() else {"summaries": {}, "headlines": {}, "cards": {}}


def _pregen_or_template(kind, wk, facts, pregen, template):
    p = pregen.get(kind, {}).get(str(wk))
    if p and p.get("facts_md5") == md5(facts):
        return p["source"], "pregenerated", None
    if p:
        print(f"  ! W{wk} pregenerated {kind.rstrip('s').replace('summarie', 'summary')} is stale (facts changed) → template", file=sys.stderr)
    return template(facts), "template", None


def generate_summary_with_source(facts, wk, pregen):
    if _live_enabled():
        out, log = live_text(SYSTEM_SUMMARY, facts, facts)
        return (out, f"live:{MODEL}", log) if out else (template_summary(facts), "template", log)
    return _pregen_or_template("summaries", wk, facts, pregen, template_summary)


def generate_headline_with_source(facts, wk, pregen):
    if _live_enabled():
        out, log = live_text(SYSTEM_HEADLINE, facts, facts)
        return (out, f"live:{MODEL}", log) if out else (template_headline(facts), "template", log)
    return _pregen_or_template("headlines", wk, facts, pregen, template_headline)


def generate_summary(facts: dict) -> str:
    """Public API required by the brief: facts → summary text (live model, pregenerated, or template), rendered."""
    wk = int(facts["week"].split("W")[-1])
    return render(generate_summary_with_source(facts, wk, load_pregen())[0], facts)[0]


def generate_card(card, wk, pregen):
    if _live_enabled():
        out, log = live_text(SYSTEM_CARD, {k: card[k] for k in ("card_id", "title", "pill", "findings", "values")},
                             card["values"], want_json=True)
        if out:
            return out, f"live:{MODEL}", log
        return template_card(card), "template", log
    p = pregen["cards"].get(str(wk), {}).get(card["card_id"])
    if p and p.get("facts_md5") == md5(card["values"]):
        return {"headline": p["headline"], "body": p["body"]}, "pregenerated", None
    if p:
        print(f"  ! W{wk} card {card['card_id']} pregenerated text is stale → template", file=sys.stderr)
    return template_card(card), "template", None


# Validator demos (Briefing "&demo=..."): the week's summary with one wrong sentence put in front, or with one
# rendered number edited. Built here from the facts, so the UI types no figures; 17 asserts each is FLAGGED by
# exactly the check it demonstrates.
def demo_sources(facts):
    word = "fell" if facts["l1w_sales_yoy_pct"] > 0 else "rose"
    return {"metric": "Transactions were {l1w_aov_yoy_pct|pct+} YoY.",
            "direction": f"Demand {word} {{l1w_sales_yoy_pct|pct}} YoY.",
            "subject": "Gen Z demand was {l1w_sales_ty|money_k}."}


def build_demos(source, text, cites, facts):
    demos = {}
    bt, bc = validator.inject_error_cited(text, cites)
    demos["blocked"] = {"text": bt, "citations": bc, "expect_check": "citation"}
    for name, lead in demo_sources(facts).items():
        t, c = render(f"{lead} {source}", facts)
        demos[name] = {"text": t, "citations": c, "expect_check": name}
    for d in demos.values():
        d["validation"] = validate_text(d["text"], facts, d["citations"])
    return demos


def stamp():
    pg = load_pregen()
    for kind in ("summaries", "headlines"):
        for wk, s in pg[kind].items():
            s["facts_md5"] = md5(json.loads((FACTS / f"W{wk}.json").read_text()))
    for wk, cards in pg["cards"].items():
        cf = {c["card_id"]: c for c in json.loads((FACTS / f"W{wk}_cards.json").read_text())["cards"]}
        for cid, c in cards.items():
            c["facts_md5"] = md5(cf[cid]["values"])
    PREGEN.write_text(json.dumps(pg, indent=1, ensure_ascii=False) + "\n")
    print(f"stamped {len(pg['summaries'])} summaries, {len(pg['headlines'])} headlines and "
          f"{sum(len(c) for c in pg['cards'].values())} cards")


def main():
    meta = json.loads((ROOT / "data/processed/metrics.json").read_text())["meta"]
    pregen = load_pregen()
    summaries, briefing = {}, {}
    for wk in meta["weeks"]:
        ff = FACTS / f"W{wk}.json"
        facts = json.loads(ff.read_text())
        src, by, log = generate_summary_with_source(facts, wk, pregen)
        text, cites = render(src, facts)
        s = {"text": text, "source": src, "citations": cites, "facts_file": str(ff.relative_to(ROOT)), "generated_by": by,
             "validation": validate_text(text, facts, cites)}
        if log:
            s["live_attempts"] = log
        hsrc, hby, hlog = generate_headline_with_source(facts, wk, pregen)
        h, hc = render(hsrc, facts)
        s.update({"headline": h, "headline_source": hsrc, "headline_citations": hc, "headline_generated_by": hby,
                  "headline_validation": validate_text(h, facts, hc)})
        if hlog:
            s["headline_live_attempts"] = hlog
        s["demos"] = build_demos(src, text, cites, facts)
        summaries[str(wk)] = s
        cf = FACTS / f"W{wk}_cards.json"
        cp = json.loads(cf.read_text())
        cards = []
        for c in cp["cards"]:
            out, by, log = generate_card(c, wk, pregen)
            ch, cb, cc = render_card(out, c["values"])
            cards.append({**{k: c[k] for k in ("card_id", "title", "pill", "pill_rank", "meta", "findings", "anomaly_ids",
                                               "explore_tab", "ask_prefill", "chart")},
                          "headline": ch, "body": cb, "headline_source": out["headline"], "body_source": out["body"],
                          "citations": cc, "generated_by": by, "validation": validate_text(f"{ch} {cb}", c["values"], cc),
                          **({"live_attempts": log} if log else {})})
        briefing[str(wk)] = {"week_label": cp["week_label"], "is_partial_week": cp["is_partial_week"],
                             **{k: cp[k] for k in ("n_critical_alerts", "n_alerts_by_severity", "n_alerts", "n_rules",
                                                   "rule_hits", "n_needs_you", "n_fyi", "n_rules_fired", "n_alerts_all_weeks_max")},
                             "cards_file": str(cf.relative_to(ROOT)), "cards": cards}
    (DASH / "summaries.json").write_text(json.dumps(summaries, indent=1, ensure_ascii=False))
    (DASH / "briefing.json").write_text(json.dumps(briefing, indent=1, ensure_ascii=False))
    src_counts = {}
    for s in summaries.values():
        for k in ("generated_by", "headline_generated_by"):
            src_counts[s[k]] = src_counts.get(s[k], 0) + 1
    for b in briefing.values():
        for c in b["cards"]:
            src_counts[c["generated_by"]] = src_counts.get(c["generated_by"], 0) + 1
    print(f"summaries.json + briefing.json written; writers used: {src_counts}")


if __name__ == "__main__":
    stamp() if "--stamp" in sys.argv else main()
