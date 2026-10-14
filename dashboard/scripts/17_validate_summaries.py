"""17 - Number validator for every AI-worded text (weekly summaries + briefing cards).

Rule: every number printed in a text must equal some value in the facts JSON that text was written
from, within display-rounding tolerance (half a unit of the printed precision). Anything else is
FLAGGED, the UI blocks it (falls back to a facts table), and this script exits non-zero so that
./run_all.sh fails.

Normalisation: "12.7%" → 0.127 (± 0.0005) · "$71.3K" → 71300 (± 50) · "$564,028" → 564028 (± 0.5)
· "+16.9 pts" → 16.9 (± 0.05) · "1.9" → 1.9 (± 0.05). An explicit sign (+/-/−) must match the sign
of the fact; an unsigned number is compared with the fact's absolute value ("down 18.8%").
Not numbers (masked before extraction): week labels (W29, W26–W29), FY26/FY25, L1W/L4W, ISO dates,
and hyphenated window words such as "4-week" (dashboard/DECISIONS.md D18).

Imported by 16_generate_summaries.py and by dashboard/app.py (importlib), so the build and the UI
run the *same* check. Run directly: validates summaries.json + briefing.json, runs the injected-error
self-test, writes dashboard/build_stats.json, exits 1 if anything is FLAGGED.
"""
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DASH = ROOT / "dashboard"

MASKS = [
    r"\bW\d{1,2}\s*[–-]\s*W?\d{1,2}\b",      # W26–W29, W23-30
    r"\bW\d{1,2}\b",                          # W29
    r"\bFY\d{2,4}\b",                          # FY26
    r"\bL\d+W\b",                              # L1W / L4W
    r"\b\d{4}-\d{2}-\d{2}\b",                  # 2026-08-19
    r"\b\d+-(?:week|day|month)s?\b",           # 4-week window words
    r"\bGen\s?Z\b",
]
NUM_RE = re.compile(
    r"(?<![\w.$])"
    r"(?P<sign>[+\-−–])?"
    r"(?P<cur>\$)?"
    r"(?P<num>\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)"
    r"(?P<suf>%|\s?pts?\b|\s?pp\b|K\b|k\b|M\b)?"
)


def extract_numbers(text):
    masked = text
    for m in MASKS:
        masked = re.sub(m, lambda x: " " * len(x.group(0)), masked)
    out = []
    for m in NUM_RE.finditer(masked):
        sign, cur, num, suf = m.group("sign"), m.group("cur"), m.group("num"), (m.group("suf") or "").strip()
        # a dash directly after a word/number character is a hyphen or range dash, not a minus sign
        if sign and m.start() > 0 and (masked[m.start() - 1].isalnum()):
            sign = None
        dec = len(num.split(".")[1]) if "." in num else 0
        val = float(num.replace(",", ""))
        unit, scale = "plain", 1.0
        if suf == "%":
            unit, scale = "pct", 0.01
        elif suf in ("K", "k"):
            unit, scale = "thousand", 1000.0
        elif suf == "M":
            unit, scale = "million", 1e6
        elif suf in ("pt", "pts", "pp"):
            unit = "pts"
        neg = sign in ("-", "−", "–")
        out.append({
            "start": m.start(), "end": m.end(),
            "raw": text[m.start():m.end()].strip(),
            "value": (-val if neg else val) * scale,
            "signed": sign is not None,
            "tol": 0.5 * 10 ** (-dec) * scale,
            "unit": unit, "currency": bool(cur),
        })
    return out


NON_METRIC_KEYS = {"weeks", "l4w_weeks", "wk", "week", "WK"}  # week indices are labels, never citable values


def fact_numbers(obj, path=""):
    """All numeric leaves of a facts payload with their JSON path (booleans and week-index fields excluded)."""
    if isinstance(obj, bool) or obj is None:
        return []
    if isinstance(obj, (int, float)):
        return [(path, float(obj))] if math.isfinite(obj) else []
    if isinstance(obj, dict):
        return [x for k, v in obj.items() if k not in NON_METRIC_KEYS for x in fact_numbers(v, f"{path}.{k}" if path else k)]
    if isinstance(obj, list):
        return [x for i, v in enumerate(obj) for x in fact_numbers(v, f"{path}[{i}]")]
    return []


def _unit_penalty(n, path, v):
    """0 when the fact's name fits the printed unit (pct → *_pct/rate/share, $ → sales/usd/aov), else 1."""
    p = path.lower()
    if n["unit"] == "pct":
        return 0 if re.search(r"pct|rate|share|_to_sales|lift", p) else 1
    if n["currency"] or n["unit"] in ("thousand", "million"):
        return 0 if re.search(r"sales|usd|aov|aur|value", p) else 1
    if n["unit"] == "pts":
        return 0 if "pts" in p else 1
    return 0 if (float(v).is_integer() == (n["tol"] >= 0.5)) else 1


def validate_text(text, facts):
    """Return {n_numbers, n_matched, unmatched, matches, status}. status PASS only if every number matches."""
    leaves = fact_numbers(facts)
    nums = extract_numbers(text or "")
    matches, unmatched = [], []
    for n in nums:
        eps = n["tol"] * 1e-6 + 1e-9
        hits = []
        for path, v in leaves:
            cand = v if n["signed"] else abs(v)
            diff = abs(cand - n["value"])
            if diff <= n["tol"] + eps:
                hits.append((_unit_penalty(n, path, v), diff, path))
        if not hits:
            unmatched.append(n["raw"])
        else:
            # pass/fail only needs one hit; the ranking just reports the most plausible source for audit trails
            hits.sort()
            matches.append({"text": n["raw"], "fact": hits[0][2], "alternatives": len(hits) - 1,
                            "candidates": [h[2] for h in hits[:6]]})
    return {"n_numbers": len(nums), "n_matched": len(matches), "unmatched": unmatched, "matches": matches,
            "status": "PASS" if not unmatched and text else "FLAGGED"}


def annotate(text, facts):
    """Split text into plain / number segments; each number carries the fact path it matched (or None).
    Used by the UI to show where every number came from (hover) and to mark unverified numbers."""
    v_by_raw = {}
    res = validate_text(text, facts)
    for mt in res["matches"]:
        v_by_raw.setdefault(mt["text"], mt["fact"])
    segs, pos = [], 0
    for n in extract_numbers(text):
        a, b = n["start"], n["end"]
        while a < b and text[a] == " ":
            a += 1
        segs.append({"text": text[pos:a], "num": False})
        segs.append({"text": text[a:b], "num": True, "fact": v_by_raw.get(text[a:b].strip())})
        pos = b
    segs.append({"text": text[pos:], "num": False})
    return segs, res


def inject_error(text):
    """Self-test helper: bump the first percentage by one whole point (e.g. 12.7% → 13.7%)."""
    m = re.search(r"(\d+)(\.\d+)?%", text)
    if not m:
        return text + " 999.9%"
    bumped = f"{int(m.group(1)) + 1}{m.group(2) or ''}%"
    return text[:m.start()] + bumped + text[m.end():]


def _card_text(c):
    return f"{c.get('headline', '')} {c.get('body', '')}"


def main():
    summaries = json.loads((DASH / "summaries.json").read_text())
    briefing = json.loads((DASH / "briefing.json").read_text())
    report, flagged, n_nums = [], 0, 0
    for wk, s in sorted(summaries.items(), key=lambda kv: int(kv[0])):
        facts = json.loads((ROOT / s["facts_file"]).read_text())
        v = validate_text(s["text"], facts)
        n_nums += v["n_numbers"]
        flagged += v["status"] != "PASS"
        if v != s["validation"]:
            print(f"  ! W{wk} summary: stored validation differs from re-check (re-check wins)")
        report.append(("summary", wk, "-", v))
    n_cards = 0
    for wk, b in sorted(briefing.items(), key=lambda kv: int(kv[0])):
        card_facts = {c["card_id"]: c for c in json.loads((ROOT / b["cards_file"]).read_text())["cards"]}
        for c in b["cards"]:
            v = validate_text(_card_text(c), card_facts[c["card_id"]]["values"])
            n_nums += v["n_numbers"]
            n_cards += 1
            flagged += v["status"] != "PASS"
            report.append(("card", wk, c["card_id"], v))

    # self-test: an injected wrong number must be FLAGGED
    s29 = summaries[str(json.loads((ROOT / "analysis/data/processed/metrics.json").read_text())["meta"]["last_full_week"])]
    bad = inject_error(s29["text"])
    st = validate_text(bad, json.loads((ROOT / s29["facts_file"]).read_text()))
    selftest_ok = st["status"] == "FLAGGED"

    for kind, wk, cid, v in report:
        tag = "PASS   " if v["status"] == "PASS" else "FLAGGED"
        print(f"  {tag} W{wk} {kind:<7} {cid:<10} {v['n_matched']}/{v['n_numbers']} numbers matched"
              + (f"  unmatched={v['unmatched']}" if v["unmatched"] else ""))
    print(f"  self-test (inject error): {'FLAGGED as expected' if selftest_ok else 'NOT FLAGGED — validator broken'}"
          f" → unmatched {st['unmatched']}")

    # build stats for the 'How it was built' page (read by the app; nothing typed by hand)
    audit = (ROOT / "analysis/outputs/tables/14_findings_audit.md").read_text()
    m = re.search(r"(\d+)/(\d+) PASS", audit)
    scripts = sorted(p.name for p in (ROOT / "analysis/scripts").glob("[0-9][0-9]_*.py")) + \
        sorted(p.name for p in (DASH / "scripts").glob("[0-9][0-9]_*.py"))
    gen = {}
    for s in summaries.values():
        gen[s["generated_by"]] = gen.get(s["generated_by"], 0) + 1
    for b in briefing.values():
        for c in b["cards"]:
            gen[c["generated_by"]] = gen.get(c["generated_by"], 0) + 1
    stats = {
        "findings_audit_pass": int(m.group(1)) if m else None, "findings_audit_total": int(m.group(2)) if m else None,
        "texts_total": len(report), "texts_pass": sum(v["status"] == "PASS" for *_, v in report),
        "summaries_total": len(summaries), "cards_total": n_cards, "numbers_checked": n_nums,
        "selftest_injected": {"original_status": "PASS" if validate_text(s29["text"], json.loads((ROOT / s29["facts_file"]).read_text()))["status"] == "PASS" else "FLAGGED",
                              "injected_status": st["status"], "unmatched": st["unmatched"]},
        "scripts": scripts, "n_scripts": len(scripts), "generated_by_counts": gen,
    }
    (DASH / "build_stats.json").write_text(json.dumps(stats, indent=1))
    print(f"validated {len(report)} texts ({stats['texts_pass']} PASS, {flagged} FLAGGED), {n_nums} numbers; "
          f"build_stats.json written")
    if flagged or not selftest_ok:
        print("FAIL: unverified numbers in AI text (or validator self-test failed)", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
