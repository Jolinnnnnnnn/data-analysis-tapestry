// Live router check (spends API credits, so it is not part of verify). Sends everyday questions to Claude and runs
// each route through the same checks the browser uses, printing what would be shown.
//   npm run ask-live                      -> calls api/ask.ts locally (needs ANTHROPIC_API_KEY in web/.env.local)
//   npm run ask-live -- --url https://...   -> calls a deployed /api/ask
import { fileURLToPath } from "node:url";
import { createServer, loadEnv } from "vite";

const root = fileURLToPath(new URL("..", import.meta.url));
const urlArg = process.argv.indexOf("--url");
const base = urlArg > 0 ? process.argv[urlArg + 1] : null;
const env = loadEnv("development", root, "");
for (const k of ["ANTHROPIC_API_KEY", "ASK_MODEL"]) if (env[k] && !process.env[k]) process.env[k] = env[k];

globalThis.window = { location: { hash: "" }, addEventListener() {}, scrollTo() {}, matchMedia: () => ({ matches: false, addEventListener() {} }) };
globalThis.document = { documentElement: { classList: { toggle() {} } } };
const vite = await createServer({ root, server: { middlewareMode: true, hmr: false }, appType: "custom", logLevel: "error" });
const E = await vite.ssrLoadModule("/src/lib/ask/engine.ts");
const { LAST_FULL } = await vite.ssrLoadModule("/src/lib/core.ts");
const api = base ? null : await vite.ssrLoadModule("/api/ask.ts");

const QUESTIONS = [
  "How is Gen Z doing this week?", "What sold best last month?", "Which products are running out of stock?", `Why did sales drop in W${LAST_FULL}?`,
  "Show me Tabby performance", "Are we overstocked anywhere?", "What should I do about Tabby?", "How many new customers did we get?",
  "How did sales do in Japan?", "What's our profit margin?", "Is the Tabby 20 style selling?", "why are dresses not selling",
  "Since Gen Z acquisition is slowing, what should we change?", "Which families grew fastest so far?",
];

for (const q of QUESTIONS) {
  const body = JSON.stringify({ question: q, wk: LAST_FULL, win: "L4W" });
  const t0 = Date.now();
  const res = base
    ? await fetch(`${base.replace(/\/$/, "")}/api/ask`, { method: "POST", headers: { "content-type": "application/json" }, body })
    : await api.POST(new Request("http://localhost/api/ask", { method: "POST", headers: { "content-type": "application/json" }, body }));
  const out = await res.json();
  const ms = Date.now() - t0;
  console.log(`\nQ: ${q}   [${res.status}, ${ms} ms${out.model ? `, ${out.model}` : ""}]`);
  if (!out.route) { console.log(`   error: ${out.error}`); continue; }
  const r = out.route;
  console.log(`   route: ${r.template} ${JSON.stringify(Object.fromEntries(Object.entries(r).filter(([k, v]) => k !== "template" && k !== "reading" && v != null && !(Array.isArray(v) && !v.length))))}`);
  console.log(`   reading: ${r.reading}`);
  const plan = E.resolveRoute(r, { wk: LAST_FULL, win: "L4W" });
  if (!plan.ok) { console.log(`   NO ANSWER: ${plan.reason}`); continue; }
  if (plan.premise) console.log(`   premise: ${plan.premise}`);
  console.log(`   answer: ${E.runPlan(plan).text.slice(0, 220)}`);
}
await vite.close();
