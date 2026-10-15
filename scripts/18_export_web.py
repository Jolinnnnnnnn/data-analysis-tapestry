"""18 - Export the single JSON file the web dashboard reads: web/src/data/app.json.

Selection only (no arithmetic): the metrics.json sections the UI shows, the anomaly rules and alerts, the timeline,
and for each week the AI texts (summary, headline, cards) together with the exact facts they were written from and
the Python validator's verdict (the web app re-validates in the browser and web/scripts/parity.mjs checks both agree).
"""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data/processed"
DASH = ROOT / "data/dashboard"
OUT = ROOT / "web/src/data/app.json"

M = json.loads((PROC / "metrics.json").read_text())
A = json.loads((PROC / "anomalies.json").read_text())
SUMM = json.loads((DASH / "summaries.json").read_text())
BRIEF = json.loads((DASH / "briefing.json").read_text())
STATS = json.loads((DASH / "build_stats.json").read_text())
TIMELINE = json.loads((DASH / "timeline.json").read_text())
_spec = importlib.util.spec_from_file_location("writer", ROOT / "scripts/16_generate_summaries.py")
W = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(W)

META_KEYS = ["ty_label", "ly_label", "as_of_date", "weeks", "last_full_week", "partial_week", "partial_week_days", "basis",
             "ly_w30_full_week_sales", "definitions", "ratio_rule", "counts", "week_dates_ty", "basis_alternatives", "data_quality"]
SECTIONS = ["headline_ptd", "decomposition_ptd", "weekly", "trailing", "genz_weekly", "generation_ptd", "new_insider_by_segment",
            "products_ptd", "styles_ptd", "products_by_week", "inventory_by_week", "inventory_position", "recommendations_sizing",
            "w30_daily", "stock_demand_shares", "growth_drill"]

weeks = {}
for wk in M["meta"]["weeks"]:
    s, b = SUMM[str(wk)], BRIEF[str(wk)]
    facts = json.loads((ROOT / s["facts_file"]).read_text())
    card_facts = {c["card_id"]: c for c in json.loads((ROOT / b["cards_file"]).read_text())["cards"]}
    weeks[str(wk)] = {
        "headline": s["headline"], "headline_validation": s["headline_validation"],
        "summary": s["text"], "summary_validation": s["validation"], "generated_by": s["generated_by"],
        "facts_file": s["facts_file"], "facts": facts,
        "counts": {k: b[k] for k in ("n_critical_alerts", "n_alerts_by_severity", "n_alerts", "n_rules", "rule_hits", "n_needs_you", "n_fyi", "n_rules_fired", "n_alerts_all_weeks_max")},
        "cards": [{**c, "values": card_facts[c["card_id"]]["values"], "sources": card_facts[c["card_id"]]["sources"]} for c in b["cards"]],
    }

app = {
    "meta": {k: M["meta"][k] for k in META_KEYS},
    **{k: M[k] for k in SECTIONS},
    "rules": A["rules"], "anomalies": A["anomalies"], "alerts_by_week": A["by_week"], "anomaly_meta": A["meta"],
    "timeline": TIMELINE,
    "weeks_ai": weeks,
    "build": {**STATS, "system_prompts": {"summary": W.SYSTEM_SUMMARY, "headline": W.SYSTEM_HEADLINE, "card": W.SYSTEM_CARD},
              "model": W.MODEL},
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(app, ensure_ascii=False, separators=(",", ":")))
print(f"web data written: {OUT.relative_to(ROOT)} ({OUT.stat().st_size / 1024:.0f} KB, {len(weeks)} weeks)")
