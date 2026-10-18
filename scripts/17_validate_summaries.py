"""17 - Validator for every AI-worded text (weekly summaries, headlines, briefing cards).

AI texts are written with placeholders, not figures: "W29 demand {l1w_sales_ty|money_k}, {l1w_sales_yoy_pct|pct+} YoY."
render() turns a placeholder text into the shown text plus one citation per number (span, fact key, format, value).
validate_text(text, facts, citations) then asks, for every printed number, "is this the fact it cites, and do the
words around it agree with that fact?" Six checks, identical in web/src/lib/validator.js (DECISIONS.md D25):

  citation    every printed number (and every spelled-out number) is covered by a citation; the key exists in the
              facts, the format fits the kind of value, and the shown figure re-reads to the cited value within half
              a unit of its printed precision (so editing a rendered number is caught)
  metric      the metric word nearest the number in its clause must name the cited key's metric
  subject     a named generation / family / segment / group must own the cited key (a total key under one is FLAGGED)
  period      window words (L1W, L4W, period-to-date), YoY / WoW and last-year labels must agree with the key
  direction   up-words / down-words must agree with the sign of a cited change (YoY, WoW, contribution, lift)
  comparison  "less than half", "majority", "doubled" and rank words must hold against the facts; a claim with
              nothing to check it against is FLAGGED

The words come from one shared vocabulary (web/src/lib/vocabulary.json). Attribution is deterministic: clauses split
at sentence ends, ; : and top-level commas and spaced dashes; a word belongs to the nearest citation it precedes or,
failing that, follows in its clause (a last-year label attaches to the number right after it, else the nearest one
before it). The previous existence check (does ANY fact match this number?) stays as a second layer, and is still
what validate_text(text, facts) runs when a caller has no citations.

Run directly: validates summaries.json + briefing.json and every demo, runs the shared adversarial corpus
(web/scripts/validator_cases.json) and the injected-error self-test, writes data/dashboard/build_stats.json,
exits 1 on any FLAGGED text or any corpus case that does not give its expected verdict.
"""
import json
import math
import re
import sys
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DASH = ROOT / "data/dashboard"
VOCAB = json.loads((ROOT / "web/src/lib/vocabulary.json").read_text())
CASES_FILE = ROOT / "web/scripts/validator_cases.json"
CHECKS = [c["id"] for c in VOCAB["checks"]]

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
PLACEHOLDER_RE = re.compile(r"\{([A-Za-z0-9_.\[\]]+)\|([a-z0-9_+]+)\}")
MARKED_RE = re.compile(r"\{\{([^|{}]*)\|([^|{}]+)\|([^|{}]+)\}\}")


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


# ================================================================ formats (render) and key kinds
def _q(x, places, sep=""):
    """Round a float like the UI's Number.toFixed: on its exact binary value, ties up (so 0.3125 → 31.3%, 21.25 → 21.3
    in the AI text exactly as in the charts; Python's own format() would round those ties to even)."""
    d = Decimal(x).quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)
    return f"{d:{sep}.{places}f}"


def fmt_value(v, fmt):
    """Display a fact value in one of the fixed formats (CLAUDE.md display formats). Python-only: the UI never formats AI numbers."""
    a = abs(v)
    if fmt == "money_k":
        s = f"${_q(a / 1000, 1)}K"
    elif fmt == "money":
        s = f"${_q(a, 0, ',')}"
    elif fmt == "money2":
        s = f"${_q(a, 2, ',')}"
    elif fmt in ("pct", "pct+", "pct0", "pct_abs"):
        x = a * 100
        s = f"{_q(x, 0)}%" if fmt == "pct0" or float(_q(x, 1)) >= 100 else f"{_q(x, 1)}%"
        if fmt == "pct_abs":
            return s  # the sign is carried by the up/down word in front of it (checked by the direction check)
    elif fmt == "pct2":
        s = f"{_q(a * 100, 2)}%"
    elif fmt == "pts+":
        s = f"{_q(a, 1)} pts"
    elif fmt == "int":
        s = _q(a, 0, ",")
    elif fmt == "wos":
        s = _q(a, 1)
    elif fmt == "ratio2":
        s = _q(a, 2)
    else:
        raise KeyError(fmt)
    zero = float(re.sub(r"[^\d.]", "", s) or 0) == 0
    if v < 0 and not zero:
        return "-" + s
    if v > 0 and not zero and fmt in ("pct+", "pts+"):
        return "+" + s
    return s


def leaf_name(key):
    return re.split(r"[.\]]", key)[-1].lower()


def key_tokens(key):
    return [t for t in re.split(r"[_.\[\]]+", key.lower()) if t]


def key_kind(key):
    leaf = leaf_name(key)
    for kind, rx in VOCAB["key_kinds"]:
        if re.search(rx, leaf):
            return kind
    return None


def key_metric_classes(key):
    leaf = leaf_name(key)
    return [m["class"] for m in VOCAB["metrics"] if re.search(m["key"], leaf)]


def is_change(key):
    return re.search(VOCAB["change_keys"], leaf_name(key)) is not None


def is_ly(key):
    return re.search(VOCAB["ly_keys"], leaf_name(key)) is not None


def key_window(key):
    return next((t for t in key_tokens(key) if t in VOCAB["windows"]), None)


def key_basis(key):
    return next((t for t in key_tokens(key) if t in VOCAB["bases"]), None)


def path_parts(key):
    return [int(p[1:-1]) if p.startswith("[") else p for p in re.findall(r"[^.\[\]]+|\[\d+\]", key)]


def get_path(facts, key):
    cur = facts
    for p in path_parts(key):
        if isinstance(p, int):
            cur = cur[p] if isinstance(cur, list) and p < len(cur) else None
        else:
            cur = cur.get(p) if isinstance(cur, dict) else None
        if cur is None:
            return None
    return cur


MLABEL = {m["class"]: m["label"] for m in VOCAB["metrics"]}
ENT_BY_NAME = {n.lower(): e for e in VOCAB["entities"] for n in e["names"]}
ENT_BY_SLUG = {e["slug"]: e for e in VOCAB["entities"]}
SLUGS = sorted([e["slug"] for e in VOCAB["entities"] if e["kind"] != "group"], key=lambda s: (-len(s), s))


def key_entities(key, facts):
    """Entities a fact belongs to: slugs in its key name (longest first, no overlaps) plus its list record's name."""
    leaf = re.split(r"[.\]]", key)[-1].lower()
    found, taken = [], []
    for s in SLUGS:
        for m in re.finditer(r"(?<![a-z0-9])" + s + r"(?![a-z0-9])", leaf):
            if not any(m.start() < b and a < m.end() for a, b in taken):
                taken.append((m.start(), m.end()))
                found.append(s)
    cur, rec = facts, None
    for p in path_parts(key)[:-1]:
        cur = cur[p] if isinstance(p, int) else cur.get(p)
        if isinstance(cur, dict) and isinstance(cur.get("family") or cur.get("entity"), str):
            rec = cur.get("family") or cur.get("entity")
    if rec is not None:
        e = ENT_BY_NAME.get(rec.lower()) or ENT_BY_SLUG.get(rec.lower())
        if e:
            found.append(e["slug"])
    return sorted(set(found))


def render(source, facts):
    """Placeholder text → (shown text, citations). An unknown key or format is left as the raw placeholder (it fails
    the citation check rather than crashing the build)."""
    leaves = dict(fact_numbers(facts))
    out, cites, pos = "", [], 0
    for m in PLACEHOLDER_RE.finditer(source):
        out += source[pos:m.start()]
        key, fmt = m.group(1), m.group(2)
        v = leaves.get(key)
        shown = fmt_value(v, fmt) if v is not None and fmt in VOCAB["formats"] else m.group(0)
        cites.append({"start": len(out), "end": len(out) + len(shown), "key": key, "fmt": fmt, "value": v})
        out += shown
        pos = m.end()
    out += source[pos:]
    assert all(ord(ch) <= 0xFFFF for ch in out), "AI text outside the BMP: JS string offsets would differ"
    return out, cites


def parse_marked(s):
    """Corpus form "{{shown|key|fmt}}" → (text, citations). Same parser in validator.js."""
    out, cites, pos = "", [], 0
    for m in MARKED_RE.finditer(s):
        out += s[pos:m.start()]
        cites.append({"start": len(out), "end": len(out) + len(m.group(1)), "key": m.group(2), "fmt": m.group(3)})
        out += m.group(1)
        pos = m.end()
    return out + s[pos:], cites


# ================================================================ vocabulary matching
def _esc(p):
    out = ""
    for ch in p:
        if ch in ".*+?^${}()|[]\\/":
            out += "\\" + ch
        elif ch == " ":
            out += r"\s+"
        else:
            out += ch
    return out


def _norm(s):
    return re.sub(r"\s+", " ", s.lower())


class Lexicon:
    """One regex per category, longest phrase first; each phrase maps to a value (class, slug, rule...)."""

    def __init__(self, items):
        self.map = {}
        for phrase, val in items:
            k = _norm(phrase)
            assert k not in self.map or self.map[k] == val, f"vocabulary phrase listed twice: {phrase}"
            self.map[k] = val
        alts = sorted(self.map, key=lambda p: (-len(p), p))
        self.re = re.compile(r"(?<![A-Za-z0-9])(?:" + "|".join(_esc(p) for p in alts) + r")(?![A-Za-z0-9])", re.I)

    def hits(self, text, spans):
        out = []
        for m in self.re.finditer(text):
            if any(m.start() < b and a < m.end() for a, b in spans):
                continue  # words inside a printed number (e.g. "pts") are not vocabulary
            out.append({"start": m.start(), "end": m.end(), "text": m.group(0), "val": self.map[_norm(m.group(0))]})
        return out


LEX = {
    "metric": Lexicon([(w, m["class"]) for m in VOCAB["metrics"] for w in m["words"]]),
    "entity": Lexicon([(n, e["slug"]) for e in VOCAB["entities"] for n in e["names"]]),
    "direction": Lexicon([(w, d) for d, ws in VOCAB["directions"].items() for w in ws]),
    "window": Lexicon([(w, k) for k, ws in VOCAB["windows"].items() for w in ws]),
    "basis": Lexicon([(w, k) for k, ws in VOCAB["bases"].items() for w in ws]),
    "ly": Lexicon([(w, "ly") for w in VOCAB["ly_markers"]]),
    "comparison": Lexicon([(p, i) for i, c in enumerate(VOCAB["comparisons"]) for p in c["phrases"]]),
    "rank": Lexicon([(p, i) for i, r in enumerate(VOCAB["ranks"]) for p in r["phrases"]]),
    "numword": Lexicon([(w, "word") for w in VOCAB["number_words"]]),
}
FMT_UNIT = {"money_k": "money", "money": "money", "money2": "money", "pct": "pct", "pct+": "pct", "pct0": "pct", "pct2": "pct", "pct_abs": "pct",
            "pts+": "pts", "int": "plain", "wos": "plain", "ratio2": "plain"}


def _num_unit(n):
    if n["currency"]:
        return "money"
    return n["unit"] if n["unit"] in ("pct", "pts") else "plain" if n["unit"] == "plain" else "other"


DIGITS = "0123456789"


def split_ranges(text, spans, clause):
    """Sentence ranges (clause=False) or clause ranges (clause=True). Never splits inside a citation span."""
    cuts, depth, i, n = [], 0, 0, len(text)
    while i < n:
        if any(a <= i < b for a, b in spans):
            i += 1
            continue
        ch = text[i]
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
        if ch in ".!?" and (i + 1 == n or text[i + 1].isspace()):
            cuts.append(i + 1)
        elif clause and ch in ";:\u2014\u2013":
            cuts.append(i + 1)
        elif clause and ch == "," and depth == 0 and not (0 < i < n - 1 and text[i - 1] in DIGITS and text[i + 1] in DIGITS):
            cuts.append(i + 1)
        elif clause and ch == "-" and 0 < i < n - 1 and text[i - 1] == " " and text[i + 1] == " ":
            cuts.append(i + 1)
        i += 1
    out, start = [], 0
    for c in cuts + [n]:
        if c > start:
            out.append((start, c))
        start = c
    return out


def _range_of(ranges, pos):
    return next((r for r in ranges if r[0] <= pos < r[1]), (0, 0))


def nearest_hit(hits, a, b, rng, text):
    """The word that governs [a, b) inside rng: one attached right after it ("2.1 weeks of supply", "+12.7% YoY"),
    else the nearest one before it, else the nearest one after it."""
    inside = [h for h in hits if rng[0] <= h["start"] and h["end"] <= rng[1]]
    after = [h for h in inside if h["start"] >= b]
    first_after = min(after, key=lambda h: h["start"]) if after else None
    if first_after and re.fullmatch(r"\s*", text[b:first_after["start"]]):
        return first_after
    before = [h for h in inside if h["end"] <= a]
    if before:
        return max(before, key=lambda h: h["end"])
    return first_after


def nearest_cite(cites, h, rng):
    inside = [c for c in cites if rng[0] <= c["start"] and c["end"] <= rng[1]]
    before = [c for c in inside if c["end"] <= h["start"]]
    if before:
        return max(before, key=lambda c: c["end"])
    after = [c for c in inside if c["start"] >= h["end"]]
    return min(after, key=lambda c: c["start"]) if after else None


def _exists(n, leaves):
    """All facts a printed number matches within half a unit of its precision, best-fitting first."""
    eps = n["tol"] * 1e-6 + 1e-9
    hits = []
    for path, v in leaves:
        cand = v if n["signed"] else abs(v)
        diff = abs(cand - n["value"])
        if diff <= n["tol"] + eps:
            hits.append((_unit_penalty(n, path, v), diff, path))
    return hits


def _existence(text, facts):
    """The previous check, kept as the second layer: every printed number equals SOME fact (no attribution)."""
    leaves = fact_numbers(facts)
    nums = extract_numbers(text or "")
    matches, unmatched = [], []
    for n in nums:
        hits = _exists(n, leaves)
        if not hits:
            unmatched.append(n["raw"])
        else:
            hits.sort()
            matches.append({"text": n["raw"], "fact": hits[0][2], "alternatives": len(hits) - 1,
                            "candidates": [h[2] for h in hits[:6]]})
    return {"n_numbers": len(nums), "n_matched": len(matches), "unmatched": unmatched, "matches": matches,
            "status": "PASS" if not unmatched and text else "FLAGGED", "mode": "existence"}


def _unit_penalty(n, path, v):
    p = path.lower()
    if n["unit"] == "pct":
        return 0 if re.search(r"pct|rate|share|_to_sales|lift", p) else 1
    if n["currency"] or n["unit"] in ("thousand", "million"):
        return 0 if re.search(r"sales|usd|aov|aur|value", p) else 1
    if n["unit"] == "pts":
        return 0 if "pts" in p else 1
    return 0 if (float(v).is_integer() == (n["tol"] >= 0.5)) else 1


def _ent_label(slugs):
    return "/".join(slugs) if slugs else "the total business"


def validate_text(text, facts, citations=None):
    """citations=None → existence check only (callers without citations). Otherwise all six checks.
    Returns {status, n_numbers, n_matched, unmatched, matches, mode, failures, checks}."""
    if citations is None:
        return _existence(text, facts)
    text = text or ""
    leaves = dict(fact_numbers(facts))
    cites = sorted([{**c, "ran": set()} for c in citations], key=lambda c: (c["start"], c["end"]))
    spans = [(c["start"], c["end"]) for c in cites]
    nums = extract_numbers(text)
    sentences = split_ranges(text, spans, False)
    clauses = split_ranges(text, spans, True)
    H = {k: lex.hits(text, spans) for k, lex in LEX.items()}
    # a metric word inside a subject's name ("other new customers") names the subject, not a metric
    H["metric"] = [m for m in H["metric"] if not any(e["start"] <= m["start"] and m["end"] <= e["end"] for e in H["entity"])]
    comp_spans = [(h["start"], h["end"]) for h in H["comparison"]]
    words = [h for h in H["numword"] if not any(h["start"] < b and a < h["end"] for a, b in comp_spans)]
    failures = []
    runs = {c: 0 for c in CHECKS}

    def fail(check, pos, shown, key, detail):
        failures.append({"check": check, "pos": pos, "text": shown, "key": key, "detail": detail})

    def mark(c, check):  # a check ran on this citation (counted, and listed on the number's hover)
        runs[check] += 1
        c["ran"].add(check)

    for c in cites:
        key, fmt, a, b = c["key"], c["fmt"], c["start"], c["end"]
        shown = text[a:b]
        mark(c, "citation")
        if key not in leaves:
            fail("citation", a, shown, key, "not a citable number in this text's facts")
            continue
        kind = key_kind(key)
        inside = [n for n in nums if a <= n["start"] and n["end"] <= b]
        if fmt not in VOCAB["formats"]:
            fail("citation", a, shown, key, f"unknown format {fmt}")
        elif kind not in VOCAB["formats"][fmt]["kinds"]:
            fail("citation", a, shown, key, f"format {fmt} does not fit a {kind or 'unclassified'} value")
        elif len(inside) != 1 or inside[0]["raw"] != shown.strip() or _num_unit(inside[0]) != FMT_UNIT[fmt]:
            fail("citation", a, shown, key, "the printed figure does not read as one number in its format")
        else:
            n, v = inside[0], leaves[key]
            cand = v if n["signed"] else abs(v)
            if abs(cand - n["value"]) > n["tol"] + n["tol"] * 1e-6 + 1e-9:
                fail("citation", a, shown, key, "the printed figure does not match the cited value")
        cl = _range_of(clauses, a)
        m = nearest_hit(H["metric"], a, b, cl, text)
        if m:
            mark(c, "metric")
            classes = key_metric_classes(key)
            if m["val"] not in classes:
                fail("metric", a, shown, key, f"'{m['text']}' means {MLABEL[m['val']]}, but {key} is "
                                              f"{' / '.join(MLABEL[c] for c in classes) or 'not a named metric'}")
        e = nearest_hit(H["entity"], a, b, cl, text)
        if e:
            mark(c, "subject")
            ent = ENT_BY_SLUG[e["val"]]
            owners = key_entities(key, facts)
            want = ent.get("members", [ent["slug"]])
            if not set(want) & set(owners):
                fail("subject", a, shown, key, f"'{e['text']}' is named, but {key} belongs to {_ent_label(owners)}")
        w = nearest_hit(H["window"], a, b, cl, text)
        kw = key_window(key)
        if w and kw:
            mark(c, "period")
            if w["val"] != kw:
                fail("period", a, shown, key, f"'{w['text']}' is a {w['val'].upper()} window, but {key} is {kw.upper()}")
        bs = nearest_hit(H["basis"], a, b, cl, text)
        kb = key_basis(key)
        if bs and kb:
            mark(c, "period")
            if bs["val"] != kb:
                fail("period", a, shown, key, f"'{bs['text']}' is {bs['val'].upper()}, but {key} is {kb.upper()}")
        if is_change(key):
            d = nearest_hit(H["direction"], a, b, cl, text)
            if d:
                mark(c, "direction")
                v = leaves[key]
                if not (v > 0 if d["val"] == "up" else v < 0):
                    fail("direction", a, shown, key, f"'{d['text']}' says {d['val']}, but {key} is {'positive' if v > 0 else 'negative' if v < 0 else 'zero'}")
            elif fmt == "pct_abs":
                mark(c, "direction")
                fail("direction", a, shown, key, "an unsigned change (pct_abs) needs an up or down word in its clause")
        elif fmt == "pct_abs":
            fail("citation", a, shown, key, "pct_abs is only for a change (YoY, WoW)")

    for h in H["ly"]:  # a last-year label: the number right after it, else the nearest before it, else after it
        cl = _range_of(clauses, h["start"])
        nxt = [c for c in cites if c["start"] >= h["end"] and re.fullmatch(r"[\s:]*", text[h["end"]:c["start"]])]
        c = nxt[0] if nxt else nearest_cite(cites, h, cl)
        if c is None or c["key"] not in leaves or is_change(c["key"]):
            continue
        mark(c, "period")
        if not is_ly(c["key"]):
            fail("period", c["start"], text[c["start"]:c["end"]], c["key"], f"'{h['text']}' labels a last-year number, but {c['key']} is this year")

    for n in nums:
        if not any(c["start"] <= n["start"] and n["end"] <= c["end"] for c in cites):
            fail("citation", n["start"], n["raw"], None, "printed number with no citation")
    for h in words:
        fail("citation", h["start"], h["text"], None, "spelled-out number with no citation")

    for h in H["comparison"]:
        runs["comparison"] += 1
        rule = VOCAB["comparisons"][h["val"]]
        sent = _range_of(sentences, h["start"])
        if rule["on"] == "change":
            elig = [c for c in cites if c["key"] in leaves and is_change(c["key"]) and key_basis(c["key"])]
        else:
            elig = [c for c in cites if c["key"] in leaves and not is_change(c["key"]) and key_kind(c["key"]) == "fraction"]
        c = nearest_cite(elig, h, _range_of(clauses, h["start"])) or nearest_cite(elig, h, sent)  # clause first, then sentence
        if c is None:
            fail("comparison", h["start"], h["text"], None, f"'{h['text']}' has no cited {rule['on']} in its sentence to check against")
            continue
        c["ran"].add("comparison")
        v, t = leaves[c["key"]], rule["test"]
        ok = (v < rule["value"] if t == "lt" else v > rule["value"] if t == "gt" else v >= rule["value"] if t == "ge"
              else v <= rule["value"] if t == "le" else rule["value"] <= v < rule["upper"])
        if not ok:
            fail("comparison", h["start"], h["text"], c["key"], f"'{h['text']}' does not hold for {c['key']}")

    lists = [(k, v) for k, v in facts.items() if isinstance(v, list) and v and all(isinstance(r, dict) and "family" in r for r in v)]
    for h in H["rank"]:
        runs["comparison"] += 1
        rule = VOCAB["ranks"][h["val"]]
        sent = _range_of(sentences, h["start"])
        fams = [e for e in H["entity"] if ENT_BY_SLUG[e["val"]]["kind"] == "family"]
        e = nearest_hit(fams, h["start"], h["end"], _range_of(clauses, h["start"]), text) or nearest_hit(fams, h["start"], h["end"], sent, text)
        if e is None:
            fail("comparison", h["start"], h["text"], None, f"'{h['text']}' names no product family to rank")
            continue
        named = {m["val"] for m in H["metric"] if sent[0] <= m["start"] and m["end"] <= sent[1]}
        elig = []
        for name, rows in lists:
            pol = next((r["polarity"] for r in VOCAB["rank_lists"] if re.search(r["name"], name)), None)
            cls = next((c for c, rx in VOCAB["rank_list_metrics"] if re.search(rx, name)), None)
            if pol == rule["polarity"] and (not named or cls in named):
                elig.append((name, [ENT_BY_NAME.get(r["family"].lower(), {}).get("slug") for r in rows]))
        if not elig:
            fail("comparison", h["start"], h["text"], None, f"'{h['text']}': the facts hold no {rule['polarity']} ranking for it")
            continue
        pos = rule["position"]
        ok = any((e["val"] in slugs) if pos == "member" else (len(slugs) > pos and slugs[pos] == e["val"]) for _, slugs in elig)
        if not ok:
            fail("comparison", h["start"], h["text"], elig[0][0], f"'{h['text']}' does not hold for {e['text']} in {', '.join(n for n, _ in elig)}")

    # second layer: the old existence check on every printed number (implied by the citation check; kept as a guard)
    all_leaves = fact_numbers(facts)
    for n in nums:
        if not _exists(n, all_leaves) and not any(f["pos"] == n["start"] for f in failures):
            fail("citation", n["start"], n["raw"], None, "matches no fact at all")
    failures.sort(key=lambda f: (f["pos"], CHECKS.index(f["check"])))

    items = [{"start": c["start"], "end": c["end"], "text": text[c["start"]:c["end"]], "key": c["key"],
              "ran": [k for k in CHECKS if k in c["ran"]]} for c in cites]
    items += [{"start": n["start"], "end": n["end"], "text": n["raw"], "key": None, "ran": []} for n in nums
              if not any(c["start"] <= n["start"] and n["end"] <= c["end"] for c in cites)]
    items += [{"start": h["start"], "end": h["end"], "text": h["text"], "key": None, "ran": []} for h in words]
    items.sort(key=lambda x: x["start"])
    bad_pos = {f["pos"] for f in failures}
    for it in items:
        it["ok"] = it["key"] is not None and it["start"] not in bad_pos
    matches = [{"text": it["text"].strip(), "fact": it["key"], "alternatives": 0, "candidates": [it["key"]], "ok": it["ok"],
                "checks": it["ran"]} for it in items if it["key"] is not None]
    return {
        "n_numbers": len(items), "n_matched": sum(it["ok"] for it in items),
        "unmatched": [it["text"].strip() for it in items if not it["ok"]], "matches": matches,
        "status": "PASS" if not failures and text else "FLAGGED", "mode": "semantic",
        "failures": failures, "checks": runs, "n_citations": len(cites),
    }


def annotate(text, facts, citations=None):
    """Split text into plain / number segments for the UI; each number carries its cited key and its failures."""
    res = validate_text(text, facts, citations)
    segs, pos = [], 0
    if citations is None:
        by_raw = {}
        for mt in res["matches"]:
            by_raw.setdefault(mt["text"], mt["fact"])
        spans = [(n["start"], n["end"], by_raw.get(n["raw"])) for n in extract_numbers(text)]
    else:
        spans = [(c["start"], c["end"], c["key"]) for c in sorted(citations, key=lambda c: c["start"])]
        cov = lambda s, e: any(a <= s and e <= b for a, b, _ in spans)
        spans += [(n["start"], n["end"], None) for n in extract_numbers(text) if not cov(n["start"], n["end"])]
        spans.sort()
    k = 0  # cited spans come in the same order as res["matches"]
    for a, b, key in spans:
        while a < b and text[a] == " ":
            a += 1
        segs.append({"text": text[pos:a], "num": False})
        fails = [f for f in res.get("failures", []) if f["pos"] == a]
        checks = []
        if citations is not None and key is not None:
            checks, k = res["matches"][k]["checks"], k + 1
        segs.append({"text": text[a:b], "num": True, "fact": key, "checks": checks,
                     "ok": (key is not None and not fails) if citations is not None else key is not None, "failures": fails})
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


def inject_error_cited(text, citations):
    """inject_error on a rendered text, keeping every citation on its number (spans shift if the length changes)."""
    m = re.search(r"(\d+)(\.\d+)?%", text)
    new = inject_error(text)
    if not m:
        return new, [dict(c) for c in citations]
    delta = len(new) - len(text)
    out = []
    for c in citations:
        c = dict(c)
        if c["start"] > m.start():
            c["start"] += delta
        if c["end"] > m.start():
            c["end"] += delta
        out.append(c)
    return new, out


# ================================================================ corpus + build check
def card_text(c):
    return f"{c.get('headline', '')} {c.get('body', '')}"


def resolve_facts(ref):
    if isinstance(ref, dict):
        return ref
    wk, _, card = ref.partition(":")
    if not card:
        return json.loads((DASH / f"facts/{wk}.json").read_text())
    return next(c for c in json.loads((DASH / f"facts/{wk}_cards.json").read_text())["cards"] if c["card_id"] == card)["values"]


def verdict(v):
    return {"status": v["status"], "checks": sorted({f["check"] for f in v.get("failures", [])}),
            "failures": [[f["check"], f["key"], f["text"], f["detail"]] for f in v.get("failures", [])],
            "unmatched": v["unmatched"]}


def run_corpus():
    """Every case gives its expected status and exactly its expected failed checks. Returns (results, problems)."""
    spec = json.loads(CASES_FILE.read_text())
    results, problems = [], []
    for case in spec["cases"]:
        facts = resolve_facts(case["facts"])
        text, cites = parse_marked(case["text"])
        if case.get("citations") == "none":
            v = validate_text(text, facts)
        else:
            v = validate_text(text, facts, cites)
            if not case.get("edited"):  # the fixture's typed figures must be what render() prints for those keys
                leaves = dict(fact_numbers(facts))
                for c in cites:
                    if c["key"] in leaves and c["fmt"] in VOCAB["formats"] and fmt_value(leaves[c["key"]], c["fmt"]) != text[c["start"]:c["end"]]:
                        problems.append(f"{case['id']}: fixture shows {text[c['start']:c['end']]!r}, render gives {fmt_value(leaves[c['key']], c['fmt'])!r}")
        got = verdict(v)
        exp = case["expect"]
        if got["status"] != exp["status"] or got["checks"] != sorted(exp.get("checks", [])):
            problems.append(f"{case['id']}: expected {exp['status']} {exp.get('checks', [])}, got {got['status']} {got['checks']} {got['failures']}")
        results.append({"id": case["id"], **got})
    return results, problems


def write_trace(summaries, briefing):
    """outputs/tables/17_number_trace.md: every printed number → cited key → value → upstream metrics path, per text,
    so a reviewer can hand-check meaning (the validator checks attribution, a person checks the sentence)."""
    lines = ["# 17 - Number trace of every AI text", "",
             "Each printed number, the fact key it cites, the value of that key, and the metrics.json / anomalies.json "
             "path the value was copied from. Generated by scripts/17_validate_summaries.py.", ""]

    def table(title, text, cites, facts, sources):
        lines.extend([f"## {title}", "", f"> {text}", "", "| shown | cited key | value | source |", "|---|---|---|---|"])
        for c in cites:
            base = re.split(r"[.\[]", c["key"])[0]
            src = sources.get(c["key"]) or sources.get(base) or "(facts)"
            lines.append(f"| {text[c['start']:c['end']]} | `{c['key']}` | {get_path(facts, c['key'])} | `{src}` |")
        lines.append("")

    for wk, s in sorted(summaries.items(), key=lambda kv: int(kv[0])):
        facts = json.loads((ROOT / s["facts_file"]).read_text())
        table(f"W{wk} headline", s["headline"], s["headline_citations"], facts, facts["_sources"])
        table(f"W{wk} summary", s["text"], s["citations"], facts, facts["_sources"])
        cards = {c["card_id"]: c for c in json.loads((ROOT / briefing[wk]["cards_file"]).read_text())["cards"]}
        for c in briefing[wk]["cards"]:
            table(f"W{wk} card {c['card_id']}", card_text(c), c["citations"], cards[c["card_id"]]["values"], cards[c["card_id"]]["sources"])
    (ROOT / "outputs/tables/17_number_trace.md").write_text("\n".join(lines))


def main():
    summaries = json.loads((DASH / "summaries.json").read_text())
    briefing = json.loads((DASH / "briefing.json").read_text())
    report, flagged, n_nums = [], 0, 0
    totals = {c: 0 for c in CHECKS}

    def check(kind, wk, cid, text, facts, cites, stored=None):
        nonlocal flagged, n_nums
        v = validate_text(text, facts, cites)
        if stored is not None and verdict(v) != verdict(stored):
            print(f"  ! W{wk} {kind} {cid}: stored validation differs from re-check (re-check wins)")
        n_nums += v["n_numbers"]
        flagged += v["status"] != "PASS"
        for k, n in v["checks"].items():
            totals[k] += n
        report.append((kind, wk, cid, v))
        return v

    for wk, s in sorted(summaries.items(), key=lambda kv: int(kv[0])):
        facts = json.loads((ROOT / s["facts_file"]).read_text())
        check("summary", wk, "-", s["text"], facts, s["citations"], s["validation"])
        check("headline", wk, "-", s["headline"], facts, s["headline_citations"], s["headline_validation"])
    n_cards = 0
    for wk, b in sorted(briefing.items(), key=lambda kv: int(kv[0])):
        card_facts = {c["card_id"]: c for c in json.loads((ROOT / b["cards_file"]).read_text())["cards"]}
        for c in b["cards"]:
            check("card", wk, c["card_id"], card_text(c), card_facts[c["card_id"]]["values"], c["citations"], c["validation"])
            n_cards += 1

    # demos: every week's demo variants must be FLAGGED by exactly the check they demonstrate
    demo_problems = []
    for wk, s in summaries.items():
        facts = json.loads((ROOT / s["facts_file"]).read_text())
        for name, d in s["demos"].items():
            v = validate_text(d["text"], facts, d["citations"])
            got = sorted({f["check"] for f in v["failures"]})
            if v["status"] != "FLAGGED" or got != [d["expect_check"]] or verdict(v) != verdict(d["validation"]):
                demo_problems.append(f"W{wk} demo {name}: expected FLAGGED [{d['expect_check']}], got {v['status']} {got}")

    corpus, corpus_problems = run_corpus()

    # self-test: an edited number in the latest full week's summary must be FLAGGED
    lf = str(json.loads((ROOT / "data/processed/metrics.json").read_text())["meta"]["last_full_week"])
    s29 = summaries[lf]
    f29 = json.loads((ROOT / s29["facts_file"]).read_text())
    bad_text, bad_cites = inject_error_cited(s29["text"], s29["citations"])
    st = validate_text(bad_text, f29, bad_cites)
    selftest_ok = st["status"] == "FLAGGED"

    write_trace(summaries, briefing)
    for kind, wk, cid, v in report:
        tag = "PASS   " if v["status"] == "PASS" else "FLAGGED"
        print(f"  {tag} W{wk} {kind:<8} {cid:<10} {v['n_matched']}/{v['n_numbers']} numbers"
              + (f"  {[(f['check'], f['text'], f['detail']) for f in v['failures']]}" if v["failures"] else ""))
    print(f"  self-test (edited number): {'FLAGGED as expected' if selftest_ok else 'NOT FLAGGED: validator broken'} → {st['unmatched']}")
    for p in demo_problems + corpus_problems:
        print(f"  ! {p}")
    n_case_ok = len(corpus) - len({p.split(':')[0] for p in corpus_problems})
    print(f"  corpus: {n_case_ok}/{len(corpus)} cases give their expected verdict; demos: {len(demo_problems)} problems")

    audit = (ROOT / "outputs/tables/14_findings_audit.md").read_text()
    m = re.search(r"(\d+)/(\d+) PASS", audit)
    scripts = sorted(p.name for p in (ROOT / "scripts").glob("[0-9][0-9]_*.py"))
    gen = {}
    for s in summaries.values():
        for k in ("generated_by", "headline_generated_by"):
            gen[s[k]] = gen.get(s[k], 0) + 1
    for b in briefing.values():
        for c in b["cards"]:
            gen[c["generated_by"]] = gen.get(c["generated_by"], 0) + 1
    stats = {
        "findings_audit_pass": int(m.group(1)) if m else None, "findings_audit_total": int(m.group(2)) if m else None,
        "texts_total": len(report), "texts_pass": sum(v["status"] == "PASS" for *_, v in report),
        "summaries_total": len(summaries), "cards_total": n_cards, "numbers_checked": n_nums,
        "checks_run": totals,
        "selftest_injected": {"original_status": validate_text(s29["text"], f29, s29["citations"])["status"],
                              "injected_status": st["status"], "unmatched": st["unmatched"],
                              "failed_checks": sorted({f["check"] for f in st["failures"]})},
        "corpus": corpus, "corpus_total": len(corpus), "corpus_pass": n_case_ok,
        "scripts": scripts, "n_scripts": len(scripts), "generated_by_counts": gen,
    }
    (DASH / "build_stats.json").write_text(json.dumps(stats, indent=1, ensure_ascii=False))
    print(f"validated {len(report)} texts ({stats['texts_pass']} PASS, {flagged} FLAGGED), {n_nums} numbers, "
          f"checks run {totals}; build_stats.json written")
    if flagged or not selftest_ok or demo_problems or corpus_problems:
        print("FAIL: an AI text, demo or corpus case did not give its expected verdict", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
