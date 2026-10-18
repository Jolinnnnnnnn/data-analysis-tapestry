// Parity check: the browser validator (src/lib/validator.js) must reach exactly the same verdict as the Python build
// validator (scripts/17_validate_summaries.py) on every AI text and every demo (status, failed checks with their keys,
// texts and details, unmatched numbers, cited keys), every AI text must PASS, every demo must be FLAGGED by its own
// check, the edited-number self-test must be FLAGGED, and every case of the shared corpus (validator_cases.json) must
// give its expected verdict in JS and the same verdict as Python. Exits 1 on any difference, so the Vercel build fails.
import { readFileSync } from "node:fs";
import { injectErrorCited, parseMarked, validateText } from "../src/lib/validator.js";

const app = JSON.parse(readFileSync(new URL("../src/data/app.json", import.meta.url)));
const corpus = JSON.parse(readFileSync(new URL("./validator_cases.json", import.meta.url)));

const verdict = (v) => ({
  status: v.status,
  checks: [...new Set((v.failures || []).map((f) => f.check))].sort(),
  failures: (v.failures || []).map((f) => [f.check, f.key, f.text, f.detail]),
  unmatched: v.unmatched,
});
const strip = (v) => JSON.stringify({ ...verdict(v), m: v.matches.map((x) => [x.text, x.fact, x.checks]) });

let bad = 0;
let nums = 0;
const texts = [];
for (const [wk, w] of Object.entries(app.weeks_ai)) {
  texts.push({ id: `W${wk} summary`, text: w.summary, cites: w.summary_citations, facts: w.facts, py: w.summary_validation });
  texts.push({ id: `W${wk} headline`, text: w.headline, cites: w.headline_citations, facts: w.facts, py: w.headline_validation });
  for (const c of w.cards)
    texts.push({ id: `W${wk} card ${c.card_id}`, text: `${c.headline} ${c.body}`, cites: c.citations, facts: c.values, py: c.validation });
}
for (const t of texts) {
  const js = validateText(t.text, t.facts, t.cites);
  nums += js.n_numbers;
  if (strip(js) !== strip(t.py)) {
    bad++;
    console.log(`MISMATCH ${t.id}\n  py: ${strip(t.py)}\n  js: ${strip(js)}`);
  }
  if (js.status !== "PASS") {
    bad++;
    console.log(`FLAGGED ${t.id}: ${JSON.stringify(verdict(js).failures)}`);
  }
}

let demos = 0;
for (const [wk, w] of Object.entries(app.weeks_ai)) {
  for (const [name, d] of Object.entries(w.demos)) {
    demos++;
    const js = validateText(d.text, w.facts, d.citations);
    const checks = verdict(js).checks;
    const same = JSON.stringify(verdict(js)) === JSON.stringify(verdict(d.validation));
    if (!same || js.status !== "FLAGGED" || checks.join() !== d.expect_check) {
      bad++;
      console.log(`DEMO W${wk} ${name}: expected FLAGGED [${d.expect_check}], js ${js.status} [${checks}]\n  py: ${JSON.stringify(verdict(d.validation))}\n  js: ${JSON.stringify(verdict(js))}`);
    }
  }
}

const w29 = app.weeks_ai[String(app.meta.last_full_week)];
const inj = injectErrorCited(w29.summary, w29.summary_citations);
const injected = validateText(inj.text, w29.facts, inj.citations);
if (injected.status !== "FLAGGED" || injected.status !== app.build.selftest_injected.injected_status) {
  bad++;
  console.log("self-test: edited number NOT flagged, or Python and JS disagree");
}
if (inj.text !== w29.demos.blocked.text) {
  bad++;
  console.log("self-test: JS injectErrorCited differs from the Python blocked demo");
}

function resolveFacts(ref) {
  if (typeof ref === "object") return ref;
  const [wk, card] = ref.split(":");
  const w = app.weeks_ai[wk.slice(1)];
  return card ? w.cards.find((c) => c.card_id === card).values : w.facts;
}
const pyCases = new Map(app.build.corpus.map((c) => [c.id, c]));
let casesOk = 0;
for (const c of corpus.cases) {
  const { text, citations } = parseMarked(c.text);
  const js = validateText(text, resolveFacts(c.facts), c.citations === "none" ? undefined : citations);
  const got = verdict(js);
  const py = pyCases.get(c.id);
  const expOk = got.status === c.expect.status && got.checks.join() === [...(c.expect.checks || [])].sort().join();
  const pyOk = py && JSON.stringify(got) === JSON.stringify({ status: py.status, checks: py.checks, failures: py.failures, unmatched: py.unmatched });
  if (expOk && pyOk) casesOk++;
  else {
    bad++;
    console.log(`CORPUS ${c.id}: expected ${c.expect.status} [${c.expect.checks || []}], js ${got.status} [${got.checks}]${pyOk ? "" : `, python differs: ${JSON.stringify(py)}`}`);
  }
}

console.log(`parity: ${texts.length} texts, ${nums} numbers, ${demos} demos, ${bad} problems; edited number → ${injected.status} [${verdict(injected).checks}]; corpus ${casesOk}/${corpus.cases.length} cases as expected in Python and JS`);
process.exit(bad ? 1 : 0);
