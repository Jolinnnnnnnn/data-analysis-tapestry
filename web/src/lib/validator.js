// AI-text validator: a line-for-line port of scripts/17_validate_summaries.py (validate_text, annotate, inject_error,
// parse_marked). The build runs the Python version; the browser runs this one before showing any AI text, and
// web/scripts/parity.mjs checks that both give identical verdicts on every text, every demo and the shared corpus
// (web/scripts/validator_cases.json). Both read the same vocabulary (./vocabulary.json).
//
// With citations, six checks run: citation, metric, subject, period, direction, comparison (see the Python docstring
// and DECISIONS.md D25). Without citations, validateText(text, facts) runs only the older existence check.
import VOCAB from "./vocabulary.json" with { type: "json" };

export { VOCAB };
export const CHECKS = VOCAB.checks.map((c) => c.id);

const MASKS = [
  /\bW\d{1,2}\s*[–-]\s*W?\d{1,2}\b/g, // W26–W29
  /\bW\d{1,2}\b/g, // W29
  /\bFY\d{2,4}\b/g, // FY26
  /\bL\d+W\b/g, // L1W / L4W
  /\b\d{4}-\d{2}-\d{2}\b/g, // ISO dates
  /\b\d+-(?:week|day|month)s?\b/g, // "4-week" window words
  /\bGen\s?Z\b/g,
];
const NUM_RE =
  /(?<![\w.$])(?<sign>[+\-−–])?(?<cur>\$)?(?<num>\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)(?<suf>%|\s?pts?\b|\s?pp\b|K\b|k\b|M\b)?/g;
const MARKED_RE = /\{\{([^|{}]*)\|([^|{}]+)\|([^|{}]+)\}\}/g;
const NON_METRIC_KEYS = new Set(["weeks", "l4w_weeks", "wk", "week", "WK"]);
const ALNUM = /[\p{L}\p{N}]/u;
const DIGITS = "0123456789";

export function extractNumbers(text) {
  let masked = text;
  for (const m of MASKS) masked = masked.replace(m, (x) => " ".repeat(x.length));
  const out = [];
  for (const m of masked.matchAll(NUM_RE)) {
    let { sign, cur, num, suf } = m.groups;
    suf = (suf || "").trim();
    const start = m.index;
    const end = start + m[0].length;
    if (sign && start > 0 && ALNUM.test(masked[start - 1])) sign = undefined;
    const dec = num.includes(".") ? num.split(".")[1].length : 0;
    const val = parseFloat(num.replace(/,/g, ""));
    let unit = "plain";
    let scale = 1;
    if (suf === "%") [unit, scale] = ["pct", 0.01];
    else if (suf === "K" || suf === "k") [unit, scale] = ["thousand", 1000];
    else if (suf === "M") [unit, scale] = ["million", 1e6];
    else if (suf === "pt" || suf === "pts" || suf === "pp") unit = "pts";
    const neg = sign === "-" || sign === "−" || sign === "–";
    out.push({
      start, end, raw: text.slice(start, end).trim(), value: (neg ? -val : val) * scale,
      signed: sign !== undefined, tol: 0.5 * 10 ** -dec * scale, unit, currency: !!cur,
    });
  }
  return out;
}

export function factNumbers(obj, path = "") {
  if (obj === null || obj === undefined || typeof obj === "boolean") return [];
  if (typeof obj === "number") return Number.isFinite(obj) ? [[path, obj]] : [];
  if (Array.isArray(obj)) return obj.flatMap((v, i) => factNumbers(v, `${path}[${i}]`));
  if (typeof obj === "object")
    return Object.entries(obj).flatMap(([k, v]) => (NON_METRIC_KEYS.has(k) ? [] : factNumbers(v, path ? `${path}.${k}` : k)));
  return [];
}

// ---------------------------------------------------------------- key kinds and classes
const leafName = (key) => key.split(/[.\]]/).pop().toLowerCase();
const keyTokens = (key) => key.toLowerCase().split(/[_.[\]]+/).filter(Boolean);
const rx = (s) => new RegExp(s);
export function keyKind(key) {
  const leaf = leafName(key);
  for (const [kind, r] of VOCAB.key_kinds) if (rx(r).test(leaf)) return kind;
  return null;
}
export const keyMetricClasses = (key) => VOCAB.metrics.filter((m) => rx(m.key).test(leafName(key))).map((m) => m.class);
export const isChange = (key) => rx(VOCAB.change_keys).test(leafName(key));
const isLy = (key) => rx(VOCAB.ly_keys).test(leafName(key));
const keyWindow = (key) => keyTokens(key).find((t) => t in VOCAB.windows) ?? null;
const keyBasis = (key) => keyTokens(key).find((t) => t in VOCAB.bases) ?? null;
const pathParts = (key) => (key.match(/[^.[\]]+|\[\d+\]/g) || []).map((p) => (p.startsWith("[") ? parseInt(p.slice(1, -1), 10) : p));

const MLABEL = Object.fromEntries(VOCAB.metrics.map((m) => [m.class, m.label]));
const ENT_BY_NAME = new Map(VOCAB.entities.flatMap((e) => e.names.map((n) => [n.toLowerCase(), e])));
const ENT_BY_SLUG = new Map(VOCAB.entities.map((e) => [e.slug, e]));
const SLUGS = VOCAB.entities.filter((e) => e.kind !== "group").map((e) => e.slug)
  .sort((a, b) => b.length - a.length || (a < b ? -1 : a > b ? 1 : 0));

export function keyEntities(key, facts) {
  const leaf = key.split(/[.\]]/).pop().toLowerCase();
  const found = [];
  const taken = [];
  for (const s of SLUGS) {
    for (const m of leaf.matchAll(new RegExp(`(?<![a-z0-9])${s}(?![a-z0-9])`, "g"))) {
      const a = m.index, b = m.index + m[0].length;
      if (!taken.some(([x, y]) => a < y && x < b)) { taken.push([a, b]); found.push(s); }
    }
  }
  let cur = facts;
  let rec = null;
  for (const p of pathParts(key).slice(0, -1)) {
    cur = cur?.[p];
    if (cur && typeof cur === "object" && !Array.isArray(cur) && typeof (cur.family || cur.entity) === "string") rec = cur.family || cur.entity;
  }
  if (rec !== null) {
    const e = ENT_BY_NAME.get(rec.toLowerCase()) || ENT_BY_SLUG.get(rec.toLowerCase());
    if (e) found.push(e.slug);
  }
  return [...new Set(found)].sort();
}

/** Corpus form "{{shown|key|fmt}}" → { text, citations }. Same parser in Python. */
export function parseMarked(s) {
  let out = "";
  const cites = [];
  let pos = 0;
  for (const m of s.matchAll(MARKED_RE)) {
    out += s.slice(pos, m.index);
    cites.push({ start: out.length, end: out.length + m[1].length, key: m[2], fmt: m[3] });
    out += m[1];
    pos = m.index + m[0].length;
  }
  return { text: out + s.slice(pos), citations: cites };
}

// ---------------------------------------------------------------- vocabulary matching
function esc(p) {
  let out = "";
  for (const ch of p) {
    if (".*+?^${}()|[]\\/".includes(ch)) out += "\\" + ch;
    else if (ch === " ") out += "\\s+";
    else out += ch;
  }
  return out;
}
const norm = (s) => s.toLowerCase().replace(/\s+/g, " ");

class Lexicon {
  constructor(items) {
    this.map = new Map();
    for (const [phrase, val] of items) {
      const k = norm(phrase);
      if (this.map.has(k) && this.map.get(k) !== val) throw new Error(`vocabulary phrase listed twice: ${phrase}`);
      this.map.set(k, val);
    }
    const alts = [...this.map.keys()].sort((a, b) => b.length - a.length || (a < b ? -1 : a > b ? 1 : 0));
    this.re = new RegExp(`(?<![A-Za-z0-9])(?:${alts.map(esc).join("|")})(?![A-Za-z0-9])`, "gi");
  }
  hits(text, spans) {
    const out = [];
    for (const m of text.matchAll(this.re)) {
      const a = m.index, b = m.index + m[0].length;
      if (spans.some(([x, y]) => a < y && x < b)) continue;
      out.push({ start: a, end: b, text: m[0], val: this.map.get(norm(m[0])) });
    }
    return out;
  }
}

const LEX = {
  metric: new Lexicon(VOCAB.metrics.flatMap((m) => m.words.map((w) => [w, m.class]))),
  entity: new Lexicon(VOCAB.entities.flatMap((e) => e.names.map((n) => [n, e.slug]))),
  direction: new Lexicon(Object.entries(VOCAB.directions).flatMap(([d, ws]) => ws.map((w) => [w, d]))),
  window: new Lexicon(Object.entries(VOCAB.windows).flatMap(([k, ws]) => ws.map((w) => [w, k]))),
  basis: new Lexicon(Object.entries(VOCAB.bases).flatMap(([k, ws]) => ws.map((w) => [w, k]))),
  ly: new Lexicon(VOCAB.ly_markers.map((w) => [w, "ly"])),
  comparison: new Lexicon(VOCAB.comparisons.flatMap((c, i) => c.phrases.map((p) => [p, i]))),
  rank: new Lexicon(VOCAB.ranks.flatMap((r, i) => r.phrases.map((p) => [p, i]))),
  numword: new Lexicon(VOCAB.number_words.map((w) => [w, "word"])),
};
const FMT_UNIT = { money_k: "money", money: "money", money2: "money", pct: "pct", "pct+": "pct", pct0: "pct", pct2: "pct", pct_abs: "pct", "pts+": "pts", int: "plain", wos: "plain", ratio2: "plain" };
const numUnit = (n) => (n.currency ? "money" : n.unit === "pct" || n.unit === "pts" ? n.unit : n.unit === "plain" ? "plain" : "other");

function splitRanges(text, spans, clause) {
  const cuts = [];
  let depth = 0;
  const n = text.length;
  for (let i = 0; i < n; i++) {
    if (spans.some(([a, b]) => a <= i && i < b)) continue;
    const ch = text[i];
    if (ch === "(") depth += 1;
    else if (ch === ")") depth = Math.max(0, depth - 1);
    if (".!?".includes(ch) && (i + 1 === n || /\s/.test(text[i + 1]))) cuts.push(i + 1);
    else if (clause && ";:\u2014\u2013".includes(ch)) cuts.push(i + 1);
    else if (clause && ch === "," && depth === 0 && !(0 < i && i < n - 1 && DIGITS.includes(text[i - 1]) && DIGITS.includes(text[i + 1]))) cuts.push(i + 1);
    else if (clause && ch === "-" && 0 < i && i < n - 1 && text[i - 1] === " " && text[i + 1] === " ") cuts.push(i + 1);
  }
  const out = [];
  let start = 0;
  for (const c of [...cuts, n]) {
    if (c > start) out.push([start, c]);
    start = c;
  }
  return out;
}
const rangeOf = (ranges, pos) => ranges.find((r) => r[0] <= pos && pos < r[1]) || [0, 0];
const maxBy = (xs, f) => xs.reduce((best, x) => (best === null || f(x) > f(best) ? x : best), null);
const minBy = (xs, f) => xs.reduce((best, x) => (best === null || f(x) < f(best) ? x : best), null);

// The word that governs [a, b) inside rng: one attached right after it ("2.1 weeks of supply", "+12.7% YoY"),
// else the nearest one before it, else the nearest one after it.
function nearestHit(hits, a, b, rng, text) {
  const inside = hits.filter((h) => rng[0] <= h.start && h.end <= rng[1]);
  const firstAfter = minBy(inside.filter((h) => h.start >= b), (h) => h.start);
  if (firstAfter && /^\s*$/.test(text.slice(b, firstAfter.start))) return firstAfter;
  const before = inside.filter((h) => h.end <= a);
  if (before.length) return maxBy(before, (h) => h.end);
  return firstAfter;
}
function nearestCite(cites, h, rng) {
  const inside = cites.filter((c) => rng[0] <= c.start && c.end <= rng[1]);
  const before = inside.filter((c) => c.end <= h.start);
  if (before.length) return maxBy(before, (c) => c.end);
  return minBy(inside.filter((c) => c.start >= h.end), (c) => c.start);
}

// ---------------------------------------------------------------- existence (second layer / no-citation mode)
function unitPenalty(n, path, v) {
  const p = path.toLowerCase();
  if (n.unit === "pct") return /pct|rate|share|_to_sales|lift/.test(p) ? 0 : 1;
  if (n.currency || n.unit === "thousand" || n.unit === "million") return /sales|usd|aov|aur|value/.test(p) ? 0 : 1;
  if (n.unit === "pts") return p.includes("pts") ? 0 : 1;
  return Number.isInteger(v) === n.tol >= 0.5 ? 0 : 1;
}
const cmp = (a, b) => (a[0] - b[0]) || (a[1] - b[1]) || (a[2] < b[2] ? -1 : a[2] > b[2] ? 1 : 0);
function exists(n, leaves) {
  const eps = n.tol * 1e-6 + 1e-9;
  const hits = [];
  for (const [path, v] of leaves) {
    const cand = n.signed ? v : Math.abs(v);
    const diff = Math.abs(cand - n.value);
    if (diff <= n.tol + eps) hits.push([unitPenalty(n, path, v), diff, path]);
  }
  return hits;
}
function existence(text, facts) {
  const leaves = factNumbers(facts);
  const nums = extractNumbers(text || "");
  const matches = [];
  const unmatched = [];
  for (const n of nums) {
    const hits = exists(n, leaves);
    if (!hits.length) unmatched.push(n.raw);
    else {
      hits.sort(cmp);
      matches.push({ text: n.raw, fact: hits[0][2], alternatives: hits.length - 1, candidates: hits.slice(0, 6).map((h) => h[2]) });
    }
  }
  return { n_numbers: nums.length, n_matched: matches.length, unmatched, matches, status: !unmatched.length && text ? "PASS" : "FLAGGED", mode: "existence" };
}

const entLabel = (slugs) => (slugs.length ? slugs.join("/") : "the total business");

/** citations undefined → existence check only. Otherwise all six checks (same result shape as Python). */
export function validateText(text, facts, citations) {
  if (citations === undefined || citations === null) return existence(text, facts);
  text = text || "";
  const leaves = new Map(factNumbers(facts));
  const cites = citations.map((c) => ({ ...c, ran: new Set() })).sort((a, b) => a.start - b.start || a.end - b.end);
  const spans = cites.map((c) => [c.start, c.end]);
  const nums = extractNumbers(text);
  const sentences = splitRanges(text, spans, false);
  const clauses = splitRanges(text, spans, true);
  const H = Object.fromEntries(Object.entries(LEX).map(([k, lex]) => [k, lex.hits(text, spans)]));
  // a metric word inside a subject's name ("other new customers") names the subject, not a metric
  H.metric = H.metric.filter((m) => !H.entity.some((e) => e.start <= m.start && m.end <= e.end));
  const compSpans = H.comparison.map((h) => [h.start, h.end]);
  const words = H.numword.filter((h) => !compSpans.some(([a, b]) => h.start < b && a < h.end));
  const failures = [];
  const runs = Object.fromEntries(CHECKS.map((c) => [c, 0]));
  const fail = (check, pos, shown, key, detail) => failures.push({ check, pos, text: shown, key, detail });
  // a check ran on this citation (counted, and listed on the number's hover)
  const mark = (c, check) => { runs[check] += 1; c.ran.add(check); };

  for (const c of cites) {
    const { key, fmt, start: a, end: b } = c;
    const shown = text.slice(a, b);
    mark(c, "citation");
    if (!leaves.has(key)) {
      fail("citation", a, shown, key, "not a citable number in this text's facts");
      continue;
    }
    const kind = keyKind(key);
    const inside = nums.filter((n) => a <= n.start && n.end <= b);
    if (!(fmt in VOCAB.formats)) fail("citation", a, shown, key, `unknown format ${fmt}`);
    else if (!VOCAB.formats[fmt].kinds.includes(kind)) fail("citation", a, shown, key, `format ${fmt} does not fit a ${kind || "unclassified"} value`);
    else if (inside.length !== 1 || inside[0].raw !== shown.trim() || numUnit(inside[0]) !== FMT_UNIT[fmt])
      fail("citation", a, shown, key, "the printed figure does not read as one number in its format");
    else {
      const n = inside[0];
      const v = leaves.get(key);
      const cand = n.signed ? v : Math.abs(v);
      if (Math.abs(cand - n.value) > n.tol + n.tol * 1e-6 + 1e-9) fail("citation", a, shown, key, "the printed figure does not match the cited value");
    }
    const cl = rangeOf(clauses, a);
    const m = nearestHit(H.metric, a, b, cl, text);
    if (m) {
      mark(c, "metric");
      const classes = keyMetricClasses(key);
      if (!classes.includes(m.val))
        fail("metric", a, shown, key, `'${m.text}' means ${MLABEL[m.val]}, but ${key} is ${classes.map((c) => MLABEL[c]).join(" / ") || "not a named metric"}`);
    }
    const e = nearestHit(H.entity, a, b, cl, text);
    if (e) {
      mark(c, "subject");
      const ent = ENT_BY_SLUG.get(e.val);
      const owners = keyEntities(key, facts);
      const want = ent.members || [ent.slug];
      if (!want.some((s) => owners.includes(s))) fail("subject", a, shown, key, `'${e.text}' is named, but ${key} belongs to ${entLabel(owners)}`);
    }
    const w = nearestHit(H.window, a, b, cl, text);
    const kw = keyWindow(key);
    if (w && kw) {
      mark(c, "period");
      if (w.val !== kw) fail("period", a, shown, key, `'${w.text}' is a ${w.val.toUpperCase()} window, but ${key} is ${kw.toUpperCase()}`);
    }
    const bs = nearestHit(H.basis, a, b, cl, text);
    const kb = keyBasis(key);
    if (bs && kb) {
      mark(c, "period");
      if (bs.val !== kb) fail("period", a, shown, key, `'${bs.text}' is ${bs.val.toUpperCase()}, but ${key} is ${kb.toUpperCase()}`);
    }
    if (isChange(key)) {
      const d = nearestHit(H.direction, a, b, cl, text);
      if (d) {
        mark(c, "direction");
        const v = leaves.get(key);
        if (!(d.val === "up" ? v > 0 : v < 0)) fail("direction", a, shown, key, `'${d.text}' says ${d.val}, but ${key} is ${v > 0 ? "positive" : v < 0 ? "negative" : "zero"}`);
      } else if (fmt === "pct_abs") {
        mark(c, "direction");
        fail("direction", a, shown, key, "an unsigned change (pct_abs) needs an up or down word in its clause");
      }
    } else if (fmt === "pct_abs") fail("citation", a, shown, key, "pct_abs is only for a change (YoY, WoW)");
  }

  for (const h of H.ly) {
    const cl = rangeOf(clauses, h.start);
    const nxt = cites.filter((c) => c.start >= h.end && /^[\s:]*$/.test(text.slice(h.end, c.start)));
    const c = nxt.length ? nxt[0] : nearestCite(cites, h, cl);
    if (c === null || !leaves.has(c.key) || isChange(c.key)) continue;
    mark(c, "period");
    if (!isLy(c.key)) fail("period", c.start, text.slice(c.start, c.end), c.key, `'${h.text}' labels a last-year number, but ${c.key} is this year`);
  }

  for (const n of nums)
    if (!cites.some((c) => c.start <= n.start && n.end <= c.end)) fail("citation", n.start, n.raw, null, "printed number with no citation");
  for (const h of words) fail("citation", h.start, h.text, null, "spelled-out number with no citation");

  for (const h of H.comparison) {
    runs.comparison += 1;
    const rule = VOCAB.comparisons[h.val];
    const sent = rangeOf(sentences, h.start);
    const elig = rule.on === "change"
      ? cites.filter((c) => leaves.has(c.key) && isChange(c.key) && keyBasis(c.key))
      : cites.filter((c) => leaves.has(c.key) && !isChange(c.key) && keyKind(c.key) === "fraction");
    const c = nearestCite(elig, h, rangeOf(clauses, h.start)) ?? nearestCite(elig, h, sent); // clause first, then sentence
    if (c === null) {
      fail("comparison", h.start, h.text, null, `'${h.text}' has no cited ${rule.on} in its sentence to check against`);
      continue;
    }
    c.ran.add("comparison");
    const v = leaves.get(c.key);
    const t = rule.test;
    const ok = t === "lt" ? v < rule.value : t === "gt" ? v > rule.value : t === "ge" ? v >= rule.value
      : t === "le" ? v <= rule.value : rule.value <= v && v < rule.upper;
    if (!ok) fail("comparison", h.start, h.text, c.key, `'${h.text}' does not hold for ${c.key}`);
  }

  const lists = Object.entries(facts).filter(([, v]) => Array.isArray(v) && v.length && v.every((r) => r && typeof r === "object" && !Array.isArray(r) && "family" in r));
  for (const h of H.rank) {
    runs.comparison += 1;
    const rule = VOCAB.ranks[h.val];
    const sent = rangeOf(sentences, h.start);
    const fams = H.entity.filter((e) => ENT_BY_SLUG.get(e.val).kind === "family");
    const e = nearestHit(fams, h.start, h.end, rangeOf(clauses, h.start), text) ?? nearestHit(fams, h.start, h.end, sent, text);
    if (e === null) {
      fail("comparison", h.start, h.text, null, `'${h.text}' names no product family to rank`);
      continue;
    }
    const named = new Set(H.metric.filter((m) => sent[0] <= m.start && m.end <= sent[1]).map((m) => m.val));
    const elig = [];
    for (const [name, rows] of lists) {
      const pol = VOCAB.rank_lists.find((r) => rx(r.name).test(name))?.polarity ?? null;
      const cls = VOCAB.rank_list_metrics.find(([, r]) => rx(r).test(name))?.[0] ?? null;
      if (pol === rule.polarity && (!named.size || named.has(cls)))
        elig.push([name, rows.map((r) => ENT_BY_NAME.get(r.family.toLowerCase())?.slug)]);
    }
    if (!elig.length) {
      fail("comparison", h.start, h.text, null, `'${h.text}': the facts hold no ${rule.polarity} ranking for it`);
      continue;
    }
    const pos = rule.position;
    const ok = elig.some(([, slugs]) => (pos === "member" ? slugs.includes(e.val) : slugs.length > pos && slugs[pos] === e.val));
    if (!ok) fail("comparison", h.start, h.text, elig[0][0], `'${h.text}' does not hold for ${e.text} in ${elig.map(([n]) => n).join(", ")}`);
  }

  // second layer: the old existence check on every printed number (implied by the citation check; kept as a guard)
  const allLeaves = factNumbers(facts);
  for (const n of nums)
    if (!exists(n, allLeaves).length && !failures.some((f) => f.pos === n.start)) fail("citation", n.start, n.raw, null, "matches no fact at all");
  failures.sort((x, y) => x.pos - y.pos || CHECKS.indexOf(x.check) - CHECKS.indexOf(y.check));

  const covered = (n) => cites.some((c) => c.start <= n.start && n.end <= c.end);
  const items = [
    ...cites.map((c) => ({ start: c.start, end: c.end, text: text.slice(c.start, c.end), key: c.key, ran: CHECKS.filter((k) => c.ran.has(k)) })),
    ...nums.filter((n) => !covered(n)).map((n) => ({ start: n.start, end: n.end, text: n.raw, key: null, ran: [] })),
    ...words.map((h) => ({ start: h.start, end: h.end, text: h.text, key: null, ran: [] })),
  ].sort((x, y) => x.start - y.start);
  for (const it of items) it.ok = it.key !== null && !failures.some((f) => f.pos === it.start);
  const matches = items.filter((it) => it.key !== null)
    .map((it) => ({ text: it.text.trim(), fact: it.key, alternatives: 0, candidates: [it.key], ok: it.ok, checks: it.ran }));
  return {
    n_numbers: items.length, n_matched: items.filter((it) => it.ok).length,
    unmatched: items.filter((it) => !it.ok).map((it) => it.text.trim()), matches,
    status: !failures.length && text ? "PASS" : "FLAGGED", mode: "semantic",
    failures, checks: runs, n_citations: cites.length,
  };
}

/** Split text into plain / number segments; each number carries its cited key, ok flag and failures. */
export function annotate(text, facts, citations) {
  const res = validateText(text, facts, citations);
  const segs = [];
  let pos = 0;
  let spans;
  if (citations === undefined || citations === null) {
    const byRaw = new Map();
    for (const m of res.matches) if (!byRaw.has(m.text)) byRaw.set(m.text, m.fact);
    spans = extractNumbers(text).map((n) => [n.start, n.end, byRaw.has(n.raw) ? byRaw.get(n.raw) : null]);
  } else {
    spans = [...citations].sort((a, b) => a.start - b.start).map((c) => [c.start, c.end, c.key]);
    const cov = (s, e) => spans.some(([a, b]) => a <= s && e <= b);
    spans = [...spans, ...extractNumbers(text).filter((n) => !cov(n.start, n.end)).map((n) => [n.start, n.end, null])]
      .sort((x, y) => x[0] - y[0] || x[1] - y[1]);
  }
  let k = 0; // cited spans come in the same order as res.matches
  for (let [a, b, key] of spans) {
    while (a < b && text[a] === " ") a++;
    segs.push({ text: text.slice(pos, a), num: false });
    const fails = (res.failures || []).filter((f) => f.pos === a);
    const checks = citations != null && key !== null ? res.matches[k++].checks : [];
    segs.push({ text: text.slice(a, b), num: true, fact: key, ok: citations == null ? key !== null : key !== null && !fails.length, failures: fails, checks });
    pos = b;
  }
  segs.push({ text: text.slice(pos), num: false });
  return { segs, res };
}

/** Validator self-test: bump the first percentage by one whole point (12.7% → 13.7%). */
export function injectError(text) {
  const m = /(\d+)(\.\d+)?%/.exec(text);
  if (!m) return text + " 999.9%";
  return text.slice(0, m.index) + `${parseInt(m[1], 10) + 1}${m[2] || ""}%` + text.slice(m.index + m[0].length);
}

/** injectError on a rendered text, keeping every citation on its number (spans shift if the length changes). */
export function injectErrorCited(text, citations) {
  const m = /(\d+)(\.\d+)?%/.exec(text);
  const next = injectError(text);
  if (!m) return { text: next, citations: citations.map((c) => ({ ...c })) };
  const delta = next.length - text.length;
  return {
    text: next,
    citations: citations.map((c) => ({ ...c, start: c.start > m.index ? c.start + delta : c.start, end: c.end > m.index ? c.end + delta : c.end })),
  };
}
