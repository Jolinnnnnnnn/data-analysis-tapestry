// Number validator: a line-for-line port of scripts/17_validate_summaries.py (validate_text, annotate, inject_error).
// The build runs the Python version; the browser runs this one before showing any AI text, and
// web/scripts/parity.mjs checks that both give identical verdicts and fact matches on every text.

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
const NON_METRIC_KEYS = new Set(["weeks", "l4w_weeks", "wk", "week", "WK"]);
const ALNUM = /[\p{L}\p{N}]/u;

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

function unitPenalty(n, path, v) {
  const p = path.toLowerCase();
  if (n.unit === "pct") return /pct|rate|share|_to_sales|lift/.test(p) ? 0 : 1;
  if (n.currency || n.unit === "thousand" || n.unit === "million") return /sales|usd|aov|aur|value/.test(p) ? 0 : 1;
  if (n.unit === "pts") return p.includes("pts") ? 0 : 1;
  return Number.isInteger(v) === n.tol >= 0.5 ? 0 : 1;
}

const cmp = (a, b) => (a[0] - b[0]) || (a[1] - b[1]) || (a[2] < b[2] ? -1 : a[2] > b[2] ? 1 : 0);

export function validateText(text, facts) {
  const leaves = factNumbers(facts);
  const nums = extractNumbers(text || "");
  const matches = [];
  const unmatched = [];
  for (const n of nums) {
    const eps = n.tol * 1e-6 + 1e-9;
    const hits = [];
    for (const [path, v] of leaves) {
      const cand = n.signed ? v : Math.abs(v);
      const diff = Math.abs(cand - n.value);
      if (diff <= n.tol + eps) hits.push([unitPenalty(n, path, v), diff, path]);
    }
    if (!hits.length) unmatched.push(n.raw);
    else {
      hits.sort(cmp);
      matches.push({ text: n.raw, fact: hits[0][2], alternatives: hits.length - 1, candidates: hits.slice(0, 6).map((h) => h[2]) });
    }
  }
  return {
    n_numbers: nums.length, n_matched: matches.length, unmatched, matches,
    status: !unmatched.length && text ? "PASS" : "FLAGGED",
  };
}

/** Split text into plain / number segments; each number carries its matched fact path (or null). */
export function annotate(text, facts) {
  const res = validateText(text, facts);
  const byRaw = new Map();
  for (const m of res.matches) if (!byRaw.has(m.text)) byRaw.set(m.text, m.fact);
  const segs = [];
  let pos = 0;
  for (const n of extractNumbers(text)) {
    let a = n.start;
    while (a < n.end && text[a] === " ") a++;
    segs.push({ text: text.slice(pos, a), num: false });
    const raw = text.slice(a, n.end);
    segs.push({ text: raw, num: true, fact: byRaw.has(raw.trim()) ? byRaw.get(raw.trim()) : null });
    pos = n.end;
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

/** For the held-back message only: the fact closest to an unmatched printed number. */
export function nearestFact(raw, facts) {
  const [n] = extractNumbers(raw);
  if (!n) return null;
  let best = null;
  for (const [path, v] of factNumbers(facts)) {
    const d = Math.abs((n.signed ? v : Math.abs(v)) - n.value) / (Math.abs(n.value) || 1);
    if (!best || d < best.d) best = { path, value: v, d };
  }
  return best;
}
