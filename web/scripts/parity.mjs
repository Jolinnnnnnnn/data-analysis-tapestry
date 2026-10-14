// Parity check: the browser validator (src/lib/validator.js) must reach exactly the same verdict as the Python
// build validator (scripts/17_validate_summaries.py) on every AI text: status, counts, unmatched numbers and
// the fact each number matched. Also re-runs the injected-error self-test. Exits 1 on any difference.
import { readFileSync } from "node:fs";
import { validateText, injectError } from "../src/lib/validator.js";

const app = JSON.parse(readFileSync(new URL("../src/data/app.json", import.meta.url)));
const texts = [];
for (const [wk, w] of Object.entries(app.weeks_ai)) {
  texts.push({ id: `W${wk} summary`, text: w.summary, facts: w.facts, py: w.summary_validation });
  texts.push({ id: `W${wk} headline`, text: w.headline, facts: w.facts, py: w.headline_validation });
  for (const c of w.cards)
    texts.push({ id: `W${wk} card ${c.card_id}`, text: `${c.headline} ${c.body}`, facts: c.values, py: c.validation });
}
const strip = (v) => JSON.stringify({ s: v.status, n: v.n_numbers, k: v.n_matched, u: v.unmatched, m: v.matches.map((x) => [x.text, x.fact]) });
let bad = 0;
let nums = 0;
for (const t of texts) {
  const js = validateText(t.text, t.facts);
  nums += js.n_numbers;
  if (strip(js) !== strip(t.py)) {
    bad++;
    console.log(`MISMATCH ${t.id}\n  py: ${strip(t.py)}\n  js: ${strip(js)}`);
  }
  if (js.status !== "PASS") {
    bad++;
    console.log(`FLAGGED ${t.id}: ${js.unmatched}`);
  }
}
const w29 = app.weeks_ai[String(app.meta.last_full_week)];
const injected = validateText(injectError(w29.summary), w29.facts);
if (injected.status !== "FLAGGED") {
  bad++;
  console.log("self-test: injected error NOT flagged");
}
console.log(`parity: ${texts.length} texts, ${nums} numbers, ${bad} problems; injected error → ${injected.status} ${injected.unmatched}`);
process.exit(bad ? 1 : 0);
