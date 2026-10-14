"""16 - Word the weekly summary and the briefing cards from the facts files (AI step), then validate.

Writer priority for every text (summary or card):
  1. LIVE   - ANTHROPIC_API_KEY set → Claude (claude-opus-5-5) writes it from the facts JSON only.
              If the validator flags a number, Claude gets one retry with the unmatched numbers listed;
              if it still fails, the deterministic template is used and the rejection is logged.
  2. PREGEN - text written by the build session (Claude Code acting as the model, see PROMPTS.md
              P17) from exactly the same facts, stored in ai/session_texts.json with an
              md5 of the facts it was written from. A stale md5 (facts changed) → not used.
  3. TEMPLATE - deterministic f-string wording of the same facts (always passes by construction).

Outputs: data/dashboard/summaries.json  {"<wk>": {text, facts_file, generated_by, validation}}
         data/dashboard/briefing.json   {"<wk>": {week_label, n_critical_alerts, n_needs_you, cards_file, cards:[...]}}
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
validate_text = validator.validate_text

SYSTEM_SUMMARY = (
    "You write a weekly retail performance summary for a merchandising leadership team. "
    "Use ONLY numbers that appear in the JSON facts. Do not compute, round differently, or infer new numbers "
    "(no differences, ratios, sums or 'x times'). Percent fields are fractions; render 0.1265 as 12.7% "
    "(YoY above 100% as a whole percent, e.g. 1.5625 → +156%). Money as $71.3K. Weeks of supply to 1 decimal. "
    "Lead with the most severe anomaly (critical > warning > info). Say 'L4W' and 'period-to-date' for windows. "
    "Plain prose, one paragraph, no headings or bullets. Max 180 words."
)
SYSTEM_HEADLINE = (
    "You write the masthead headline of a weekly retail dashboard: at most two short sentences, about 15 words. "
    "First the week's result (demand and its YoY), then the single most severe alert. State results; never address "
    "the reader. Use ONLY numbers that appear in the JSON facts, formatted as in the summary rules ($71.3K, +12.7%)."
)
SYSTEM_CARD = (
    "You write one briefing card for a retail analytics agent, in its voice: first person, calm, specific. "
    "Return JSON {\"headline\": str, \"body\": str}. Headline: ONE sentence that states what happened with "
    "the key numbers in it (max 22 words). Body: 2-3 short sentences: why it matters, the evidence, what to do. "
    "Use ONLY numbers that appear in the card's `values`. Do not compute, round differently, or infer new numbers. "
    "Percent fields are fractions (0.2826 → 28%, or 28.3%). *_pts fields are percentage points (+5.0 pts). "
    "Weeks of supply to 1 decimal. Money as $23.1K. You may cite finding IDs (F11) and recommendation IDs (R1)."
)


def md5(obj):
    return hashlib.md5(json.dumps(obj, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


# ---------------------------------------------------------------- formatting helpers (template writer)
def pct(x, signed=False):
    v = x * 100
    s = f"{v:+.0f}%" if abs(v) >= 100 and signed else f"{v:.0f}%" if abs(v) >= 100 else (f"{v:+.1f}%" if signed else f"{v:.1f}%")
    return s


def money(x):
    return f"${x/1000:.1f}K" if abs(x) >= 1000 else f"${x:,.2f}"


def wos(x):
    return f"{x:.1f}"


SEV_WORD = {"critical": "Critical", "warning": "Warning", "info": "Note"}


def template_summary(f):
    """Deterministic wording of the weekly facts. Used when no live model and no current pregenerated text."""
    parts = []
    an = f["anomalies"]
    if an:
        top = an[0]
        parts.append(f"{SEV_WORD[top['severity']]}: {top['message']}")
    part = " (partial week, same days LY)" if f["is_partial_week"] else ""
    parts.append(f"Demand {pct(f['l1w_sales_yoy_pct'], True)} YoY{part} at {money(f['l1w_sales_ty'])} vs {money(f['l1w_sales_ly'])}; "
                 f"transactions {pct(f['l1w_txns_yoy_pct'], True)}, AOV {pct(f['l1w_aov_yoy_pct'], True)}.")
    if f["l1w_sales_wow_pct"] is not None:
        parts.append(f"WoW demand {pct(f['l1w_sales_wow_pct'], True)}.")
    parts.append(f"L4W demand {pct(f['l4w_sales_yoy_pct'], True)}; period-to-date {pct(f['ptd_sales_yoy_pct'], True)}.")
    parts.append(f"Gen Z new customers {f['l1w_genz_new_ty']} vs {f['l1w_genz_new_ly']} ({pct(f['l1w_genz_new_yoy_pct'], True)}), "
                 f"{pct(f['l1w_genz_share_of_new_ty'])} of new vs {pct(f['l1w_genz_share_of_new_ly'])} LY.")
    parts.append(f"L4W new Gen Z Insider attach {pct(f['l4w_genz_new_insider_rate_ty'])}.")
    t, b = f["l4w_top_families_by_contrib"][0], f["l4w_bottom_families_by_contrib"][0]
    parts.append(f"Top L4W contributor {t['family']} ({t['contrib_pts']:+.1f} pts); biggest drag {b['family']} ({b['contrib_pts']:+.1f} pts).")
    lo = f["lowest_wos_families"][0]
    parts.append(f"Lowest weeks of supply: {lo['family']} {wos(lo['wos'])} (LY {wos(lo['wos_ly_same_week'])}).")
    for a in an[1:3]:
        parts.append(f"{SEV_WORD[a['severity']]}: {a['message']}")
    return " ".join(parts)


def template_card(c):
    v, cid = c["values"], c["card_id"]
    if cid == "stock":
        h = f"Tabby has {wos(v['tabby_wos'])} weeks of supply and Pillow Tabby {wos(v['pillow_tabby_wos'])}, against {wos(v['tabby_wos_ly_same_week'])} and {wos(v['pillow_tabby_wos_ly_same_week'])} last year."
        b = f"Units on hand: Tabby {v['tabby_on_hand_eow']}, Pillow Tabby {v['pillow_tabby_on_hand_eow']}."
        if "r1_demand_at_risk_usd" in v:
            b += f" Receipts covered {pct(v['tabby_receipts_to_sales_ty'])} of Tabby units sold (LY {pct(v['tabby_receipts_to_sales_ly'])}); {money(v['r1_demand_at_risk_usd'])} of demand is at risk (R1)."
    elif cid == "retention":
        h = f"Returning customers L4W {v['l4w_returning_ty']} vs {v['l4w_returning_ly']} ({pct(v['l4w_returning_yoy_pct'], True)}); new Gen Z Insider attach {pct(v['l4w_genz_new_insider_rate_ty'])}."
        b = f"Returning Gen Z L4W {v['l4w_genz_returning_ty']} vs {v['l4w_genz_returning_ly']}; period-to-date {pct(v['ptd_genz_returning_yoy_pct'], True)}. This is a mix proxy (D8)."
    elif cid == "pattern":
        h = f"Gen Z share of new customers is {pct(v['week_genz_share_of_new_ty'])} this week, from {pct(v['first_week_genz_share_of_new_ty'])} in the first week."
        b = f"Last year the same week was {pct(v['week_genz_share_of_new_ly'])}."
    elif cid == "win":
        h = f"Gen Z new customers period-to-date {v['ptd_genz_new_ty']} vs {v['ptd_genz_new_ly']} ({pct(v['ptd_genz_new_yoy_pct'], True)})."
        b = f"Tabby L4W {pct(v['tabby_l4w_sales_yoy_pct'], True)} ({v['tabby_l4w_contrib_pts']:+.1f} pts); Pillow Tabby {pct(v['pillow_tabby_l4w_sales_yoy_pct'], True)}."
    else:
        fams = [k[:-4] for k in v if k.endswith("_wos") and not k.endswith("_ly_same_week")]
        k = fams[0]
        h = f"{k.replace('_', ' ').title()} holds {wos(v[k + '_wos'])} weeks of supply against {wos(v[k + '_wos_ly_same_week'])} last year."
        b = "Slow Halo apparel is tying up stock (F10, F11)."
        if "r2_excess_units" in v:
            b += f" {v['r2_excess_units']:.0f} units / {money(v['r2_excess_retail_value_usd'])} above median cover (R2)."
    return {"headline": h, "body": b}


# ================================================================ === LIVE MODEL PLUG-IN POINT ===
# Set ANTHROPIC_API_KEY (or an `ant auth login` profile + DASHBOARD_LIVE=1) to have Claude write every text.
# The model only ever sees the facts JSON for that week/card. Its output is still validated below,
# so a live model cannot put an unverified number on screen.
def _live_enabled():
    return bool(os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("DASHBOARD_LIVE"))


def call_claude(system, user_json, want_json=False, feedback=None):
    import anthropic  # imported lazily: the default (offline) build needs no SDK
    client = anthropic.Anthropic()
    content = "FACTS JSON:\n" + json.dumps(user_json, ensure_ascii=False, indent=1)
    if feedback:
        content += f"\n\nYour previous draft used numbers that are NOT in the facts: {feedback}. Rewrite using only numbers from the facts."
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
    """Two attempts; returns (output, attempts_log) or (None, log) if both fail validation."""
    log, feedback = [], None
    for _ in range(2):
        out = call_claude(system, facts, want_json, feedback)
        txt = f"{out['headline']} {out['body']}" if want_json else out
        v = validate_text(txt, check_facts)
        log.append({"status": v["status"], "unmatched": v["unmatched"]})
        if v["status"] == "PASS":
            return out, log
        feedback = v["unmatched"]
    return None, log
# ================================================================ === END LIVE MODEL PLUG-IN POINT ===


def load_pregen():
    return json.loads(PREGEN.read_text()) if PREGEN.exists() else {"summaries": {}, "cards": {}}


def generate_summary_with_source(facts, wk, pregen):
    if _live_enabled():
        out, log = live_text(SYSTEM_SUMMARY, facts, facts)
        if out:
            return out, f"live:{MODEL}", log
        return template_summary(facts), "template", log
    p = pregen["summaries"].get(str(wk))
    if p and p.get("facts_md5") == md5(facts):
        return p["text"], "pregenerated", None
    if p:
        print(f"  ! W{wk} pregenerated summary is stale (facts changed) → template", file=sys.stderr)
    return template_summary(facts), "template", None


def template_headline(f):
    part = " so far" if f["is_partial_week"] else ""
    return (f"{f['week'].split(' ')[-1]}{part}: demand {money(f['l1w_sales_ty'])}, {pct(f['l1w_sales_yoy_pct'], True)} YoY."
            + (f" {f['anomalies'][0]['message']}" if f["anomalies"] and f["anomalies"][0]["severity"] == "critical" else ""))


def generate_headline_with_source(facts, wk, pregen):
    if _live_enabled():
        out, log = live_text(SYSTEM_HEADLINE, facts, facts)
        return (out, f"live:{MODEL}", log) if out else (template_headline(facts), "template", log)
    p = pregen.get("headlines", {}).get(str(wk))
    if p and p.get("facts_md5") == md5(facts):
        return p["text"], "pregenerated", None
    if p:
        print(f"  ! W{wk} pregenerated headline is stale (facts changed) → template", file=sys.stderr)
    return template_headline(facts), "template", None


def generate_summary(facts: dict) -> str:
    """Public API required by the brief: facts → summary text (live model, pregenerated, or template)."""
    wk = int(facts["week"].split("W")[-1])
    return generate_summary_with_source(facts, wk, load_pregen())[0]


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


def stamp():
    pg = load_pregen()
    for wk, s in pg["summaries"].items():
        s["facts_md5"] = md5(json.loads((FACTS / f"W{wk}.json").read_text()))
    for wk, s in pg.get("headlines", {}).items():
        s["facts_md5"] = md5(json.loads((FACTS / f"W{wk}.json").read_text()))
    for wk, cards in pg["cards"].items():
        cf = {c["card_id"]: c for c in json.loads((FACTS / f"W{wk}_cards.json").read_text())["cards"]}
        for cid, c in cards.items():
            c["facts_md5"] = md5(cf[cid]["values"])
    PREGEN.write_text(json.dumps(pg, indent=1, ensure_ascii=False))
    print(f"stamped {len(pg['summaries'])} summaries and {sum(len(c) for c in pg['cards'].values())} cards")


def main():
    meta = json.loads((ROOT / "data/processed/metrics.json").read_text())["meta"]
    pregen = load_pregen()
    summaries, briefing = {}, {}
    for wk in meta["weeks"]:
        ff = FACTS / f"W{wk}.json"
        facts = json.loads(ff.read_text())
        text, src, log = generate_summary_with_source(facts, wk, pregen)
        summaries[str(wk)] = {"text": text, "facts_file": str(ff.relative_to(ROOT)), "generated_by": src,
                              "validation": validate_text(text, facts)}
        if log:
            summaries[str(wk)]["live_attempts"] = log
        h, hsrc, hlog = generate_headline_with_source(facts, wk, pregen)
        summaries[str(wk)].update({"headline": h, "headline_generated_by": hsrc, "headline_validation": validate_text(h, facts)})
        cf = FACTS / f"W{wk}_cards.json"
        cp = json.loads(cf.read_text())
        cards = []
        for c in cp["cards"]:
            out, src, log = generate_card(c, wk, pregen)
            cards.append({**{k: c[k] for k in ("card_id", "title", "pill", "pill_rank", "meta", "findings", "anomaly_ids",
                                               "explore_tab", "ask_prefill", "chart")},
                          "headline": out["headline"], "body": out["body"], "generated_by": src,
                          "validation": validate_text(f"{out['headline']} {out['body']}", c["values"]),
                          **({"live_attempts": log} if log else {})})
        briefing[str(wk)] = {"week_label": cp["week_label"], "is_partial_week": cp["is_partial_week"],
                             **{k: cp[k] for k in ("n_critical_alerts", "n_alerts_by_severity", "n_alerts", "n_rules",
                                                   "rule_hits", "n_needs_you", "n_fyi", "n_rules_fired", "n_alerts_all_weeks_max")},
                             "cards_file": str(cf.relative_to(ROOT)), "cards": cards}
    (DASH / "summaries.json").write_text(json.dumps(summaries, indent=1, ensure_ascii=False))
    (DASH / "briefing.json").write_text(json.dumps(briefing, indent=1, ensure_ascii=False))
    src_counts = {}
    for s in summaries.values():
        src_counts[s["generated_by"]] = src_counts.get(s["generated_by"], 0) + 1
    for b in briefing.values():
        for c in b["cards"]:
            src_counts[c["generated_by"]] = src_counts.get(c["generated_by"], 0) + 1
    print(f"summaries.json + briefing.json written; writers used: {src_counts}")


if __name__ == "__main__":
    stamp() if "--stamp" in sys.argv else main()
