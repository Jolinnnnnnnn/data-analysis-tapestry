// Ask tests (part of `npm run verify`, so they gate every build). They load the real modules through Vite and check:
// 1. the keyword parser routes everyday questions to the right template, and every card's "Ask why" question works;
// 2. the checks refuse what a route can't honour (unknown weeks, named entities, missing parameters, "none");
// 3. premises are checked against stored YoY / WoW values, and answers about a family use that family's rows;
// 4. every template runs for every week and window without missing values;
// 5. the router contract (schema, prompt, parseRoute) matches the catalog.
// Expected values are read from app.json, never typed in. Exits 1 on any failure.
import { fileURLToPath } from "node:url";
import { createServer } from "vite";

// core.ts touches a few browser globals at import time; give it inert stand-ins.
globalThis.window = { location: { hash: "" }, addEventListener() {}, scrollTo() {}, matchMedia: () => ({ matches: false, addEventListener() {} }) };
globalThis.document = { documentElement: { classList: { toggle() {} } } };

const vite = await createServer({ root: fileURLToPath(new URL("..", import.meta.url)), server: { middlewareMode: true, hmr: false }, appType: "custom", logLevel: "error" });
const E = await vite.ssrLoadModule("/src/lib/ask/engine.ts");
const K = await vite.ssrLoadModule("/src/lib/ask/catalog.ts");
const core = await vite.ssrLoadModule("/src/lib/core.ts");
const { D, WEEKS, LAST_FULL, fmtMoney, fmtPct } = core;
const DEF = { wk: LAST_FULL, win: "L4W" };

let fails = 0;
let n = 0;
const check = (name, cond, detail = "") => {
  n++;
  if (!cond) {
    fails++;
    console.log(`FAIL ${name}${detail ? `\n     ${detail}` : ""}`);
  }
};
const ask = (q, def = DEF) => {
  const route = E.parseQuestion(q);
  const plan = E.resolveRoute(route, def);
  return { route, plan, content: plan.ok ? E.runPlan(plan) : null };
};
const route = (r) => ({ template: "none", subject: null, window: null, week: null, metric: null, direction: null, n: null, op: null, threshold: null, stock: null, premise: null, unmatched: [], reading: "", ...r });

// 1. Parser routing
const routed = [
  ["Show me Tabby performance", { template: "family_kpi", subject: "Tabby" }],
  ["What sold best last month?", { template: "rank_families", metric: "demand", direction: "top", window: "L4W" }],
  ["Which products are running out of stock?", { template: "stock_alerts", stock: "low" }],
  ["Are we overstocked anywhere?", { template: "stock_alerts", stock: "high" }],
  ["What should I do about Tabby?", { template: "actions", subject: "Tabby" }],
  ["How many new customers did we get?", { template: "new_customers" }],
  ["How is Gen Z doing this week?", { template: "new_customers", window: "L1W" }],
  [`Why did sales drop in W${LAST_FULL}?`, { template: "sales_kpi", window: "L1W", week: LAST_FULL }],
  [`Top 3 families by contribution in L4W for week ${LAST_FULL}`, { template: "rank_families", metric: "contribution", n: 3, window: "L4W" }],
  ["Which families have WOS below 3 in week 30?", { template: "wos_threshold", op: "below", threshold: 3, week: 30 }],
  ["What is driving demand growth?", { template: "growth_drivers" }],
  ["Which families are winners?", { template: "winners" }],
];
for (const [q, want] of routed) {
  const { route: r, plan } = ask(q);
  const bad = Object.entries(want).filter(([k, v]) => r[k] !== v);
  check(`route "${q}"`, !bad.length && plan.ok, `got ${JSON.stringify(r)} plan.ok=${plan.ok} ${plan.ok ? "" : plan.reason}`);
}
check("premise parsed from 'Why did sales drop'", ask(`Why did sales drop in W${LAST_FULL}?`).route.premise?.direction === "down");
for (const wk of WEEKS) {
  for (const c of D.weeks_ai[String(wk)].cards) {
    const { plan } = ask(c.ask_prefill, { wk, win: "L4W" });
    check(`card prefill W${wk} ${c.card_id}: "${c.ask_prefill}"`, plan.ok, plan.ok ? "" : plan.reason);
  }
}

// 2. Refusals
const refused = (name, r, needle) => {
  const plan = E.resolveRoute(r, DEF);
  check(name, !plan.ok && (!needle || plan.reason.includes(needle)), plan.ok ? `answered with ${plan.tid}` : plan.reason);
};
refused("region in a sales question", E.parseQuestion("How did sales do in Japan?"), "Japan");
refused("profit question has no template", E.parseQuestion("What's our profit margin?"));
refused("week outside the data", E.parseQuestion("How did sales do in week 31?"), "W31");
refused("model route: none", route({ template: "none", reading: "Profit isn't in the data." }));
refused("model route: unmatched entity", route({ template: "sales_kpi", unmatched: ["Japan"] }), "Insider");
refused("family_kpi without a family", route({ template: "family_kpi", subject: "genz" }));
refused("sales_kpi for Gen Z only", route({ template: "sales_kpi", subject: "genz" }), "Gen Z");
refused("wos_threshold without a number", route({ template: "wos_threshold", op: "below" }));
refused("unknown template", route({ template: "forecast_next_week" }));

// 3. Answers honour the route, and premises are checked against the data
{
  const plan = E.resolveRoute(route({ template: "family_kpi", subject: "Tabby", window: "L4W", week: LAST_FULL }), DEF);
  const text = E.runPlan(plan).text;
  const fam = D.products_by_week.find((r) => r.wk === LAST_FULL && r.window === "L4W" && r.family === "Tabby");
  const total = D.trailing[String(LAST_FULL)].L4W.sales.ty;
  check("family answer uses the family's demand", text.includes(fmtMoney(fam.sales_ty)) && !text.includes(fmtMoney(total)), text);
}
{
  const b = D.trailing[String(LAST_FULL)].L1W;
  const plan = E.resolveRoute(route({ template: "sales_kpi", window: "L1W", week: LAST_FULL, premise: { metric: "demand", direction: "down", basis: "unspecified" } }), DEF);
  const yoy = fmtPct(b.sales.yoy_pct, true);
  const wow = fmtPct(b.wow.sales, true);
  const mixed = Math.sign(b.sales.yoy_pct) !== Math.sign(b.wow.sales);
  check("premise note quotes YoY and WoW from the data", plan.premise?.includes(yoy) && plan.premise?.includes(wow), plan.premise);
  check("premise verdict reflects mixed signs", !mixed || plan.premise?.includes("only"), plan.premise);
  const upYoy = b.sales.yoy_pct > 0;
  const p2 = E.resolveRoute(route({ template: "sales_kpi", window: "L1W", week: LAST_FULL, premise: { metric: "demand", direction: upYoy ? "down" : "up", basis: "yoy" } }), DEF);
  check("false YoY premise is contradicted", p2.premise?.startsWith("Your question assumes") && p2.premise.includes("The data says otherwise"), p2.premise);
  const p3 = E.resolveRoute(route({ template: "sales_kpi", window: "L1W", week: LAST_FULL, premise: { metric: "demand", direction: upYoy ? "up" : "down", basis: "yoy" } }), DEF);
  check("true YoY premise is confirmed", p3.premise?.includes("That matches the data"), p3.premise);
}
{
  const plan = E.resolveRoute(route({ template: "sales_kpi", reading: "Demand in W29 was 71.3K" }), DEF);
  check("a model reading with numbers is replaced by the template reading", plan.ok && !/71/.test(plan.reading) && plan.reading.length > 0, plan.reading);
  const ok = E.resolveRoute(route({ template: "sales_kpi", reading: `How demand did in W${LAST_FULL}` }), DEF);
  check("a model reading with only week labels is kept", ok.ok && ok.reading.includes(`W${LAST_FULL}`), ok.reading);
}

// 4. Every template runs everywhere with no missing values
const leak = /undefined|NaN|null|\[object/;
const variants = [
  ...["sales_kpi", "growth_drivers", "winners", "new_customers", "genz_share_trend", "insider_segments"].map((t) => ({ template: t })),
  ...D.products_ptd.map((p) => ({ template: "family_kpi", subject: p.STYLE_GROUP })),
  ...["contribution", "demand", "growth"].flatMap((metric) => ["top", "bottom"].map((direction) => ({ template: "rank_families", metric, direction }))),
  ...[null, "total", "genz", "retention", "Tabby"].flatMap((subject) => [{ template: "why_flagged", subject }, { template: "actions", subject }]),
  { template: "stock_alerts", stock: "low" }, { template: "stock_alerts", stock: "high" },
  { template: "wos_threshold", op: "below", threshold: 3 }, { template: "wos_threshold", op: "above", threshold: 15 },
];
let runs = 0;
for (const v of variants) for (const week of WEEKS) for (const window of K.WINDOWS) {
  const plan = E.resolveRoute(route({ ...v, week, window }), DEF);
  if (!plan.ok) { check(`matrix ${JSON.stringify(v)} W${week} ${window} resolves`, false, plan.reason); continue; }
  let c;
  try { c = E.runPlan(plan); } catch (e) { check(`matrix ${JSON.stringify(v)} W${week} ${window} runs`, false, String(e)); continue; }
  runs++;
  const all = [c.text, c.read, ...c.rows.flat().map(String), ...(c.cards || []).map((x) => x.text), plan.reading, ...plan.notes].join(" ");
  check(`matrix ${JSON.stringify(v)} W${week} ${window} has no missing values`, !leak.test(all), all.slice(0, 300));
}

// 5. Router contract
{
  const cat = K.catalogFrom(D);
  const prompt = K.systemPrompt(cat);
  check("prompt lists every template", K.TEMPLATE_IDS.every((id) => prompt.includes(`- ${id}:`)));
  check("prompt lists every family", cat.families.every((f) => prompt.includes(f)));
  const schema = K.routeSchema(cat);
  check("schema requires every route field", JSON.stringify(schema.required.slice().sort()) === JSON.stringify(Object.keys(route({})).sort()));
  const good = route({ template: "family_kpi", subject: "Tabby", window: "L4W", week: LAST_FULL });
  check("parseRoute accepts a valid route", JSON.stringify(K.parseRoute(good, cat)) === JSON.stringify(good));
  for (const [name, bad] of [["subject", { subject: "Narnia" }], ["week", { week: 31 }], ["template", { template: "x" }], ["premise", { premise: { metric: "profit", direction: "up", basis: "yoy" } }]]) {
    let threw = false;
    try { K.parseRoute(route({ template: "sales_kpi", ...bad }), cat); } catch { threw = true; }
    check(`parseRoute rejects a bad ${name}`, threw);
  }
}

await vite.close();
console.log(`ask: ${n} checks, ${runs} template runs, ${fails} failures`);
process.exit(fails ? 1 : 0);
