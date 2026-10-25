// Ask catalog: the fixed query templates, the entities a question may name, and the routing contract.
// Shared by the browser (offline parser, resolver, answers) and the serverless router (api/ask.ts), so the
// model and the code always see the same list. No data values live here: lists are read from app.json.

export const WINDOWS = ["L1W", "L4W", "PTD"] as const;
export type Win = (typeof WINDOWS)[number];
export const SPECIAL_SUBJECTS = ["total", "genz", "retention"] as const;
export const RANK_METRICS = ["contribution", "demand", "growth"] as const;
export const PREMISE_METRICS = ["demand", "transactions", "aov", "new_customers", "genz_new"] as const;

export interface TemplateDef {
  id: string;
  pattern: string; // shown in the UI and used as the parser's reading
  read: string; // which app.json fields the answer reads
  goal: number; // index into GOALS
  params: string; // what the router must fill, in words (goes into the model prompt)
}

export const TEMPLATES: TemplateDef[] = [
  { id: "sales_kpi", pattern: "How did demand do in {window} ending {week}?", read: "trailing", goal: 0,
    params: "Whole-business demand, transactions and AOV vs last year (plus vs the previous week for a single week). Uses window, week." },
  { id: "growth_drivers", pattern: "What is driving demand growth this period?", read: "decomposition_ptd", goal: 0,
    params: "Splits period-to-date demand growth into customers, frequency, units per transaction and price. No parameters." },
  { id: "family_kpi", pattern: "How is {subject} doing in {window} ending {week}?", read: "products_by_week · products_ptd · inventory_by_week", goal: 2,
    params: "One product family: demand vs last year, contribution to growth, weeks of supply and alerts. Uses subject (a family), window, week." },
  { id: "rank_families", pattern: "Top/bottom {n} families by {metric} in {window} ending {week}", read: "products_by_week · products_ptd", goal: 2,
    params: "Ranks families. metric: contribution (points of total growth), demand (biggest sellers, 'sold best'), growth (fastest % growth). Uses metric, direction, n, window, week." },
  { id: "winners", pattern: "Which families are winners and decliners this period?", read: "products_ptd", goal: 2,
    params: "Period-to-date Winner / Decliner classes. No parameters." },
  { id: "new_customers", pattern: "How many new customers, and how many Gen Z, in {window} ending {week}?", read: "trailing", goal: 1,
    params: "New customers in total and Gen Z, and Gen Z share of new customers, vs last year. Uses window, week." },
  { id: "genz_share_trend", pattern: "Gen Z share of new customers by week up to {week}", read: "genz_weekly", goal: 1,
    params: "Week-by-week Gen Z share of new customers. Uses week." },
  { id: "insider_segments", pattern: "Where is the Insider gap for new Gen Z?", read: "new_insider_by_segment", goal: 1,
    params: "Loyalty (Insider) sign-up of new Gen Z vs other new customers by channel and region. No parameters." },
  { id: "why_flagged", pattern: "Why is {subject} flagged in {week}?", read: "anomalies by week", goal: 3,
    params: "The rule alerts that fired. Uses subject (a family, total, genz or retention; null for every alert), week." },
  { id: "actions", pattern: "What should we do about {subject} this week?", read: "weeks_ai cards (number-checked AI text)", goal: 3,
    params: "The week's flagged cards with their recommendations. Uses subject (null for all cards), week." },
  { id: "stock_alerts", pattern: "Which families are running low on stock, or overstocked, in {week}?", read: "anomalies (stock rules) · inventory_by_week", goal: 3,
    params: "Families flagged by the stock rules. stock: low (running out, understock) or high (overstock, excess). Uses stock, week." },
  { id: "wos_threshold", pattern: "Which families have weeks of supply below/above {x} in {week}?", read: "inventory_by_week", goal: 3,
    params: "Families with weeks of supply past a number the question gives. Uses op, threshold, week." },
];
export const TEMPLATE_IDS = TEMPLATES.map((t) => t.id);

export interface Catalog { families: string[]; segments: string[]; weeks: number[]; lastFull: number; partial: number }

export function catalogFrom(D: any): Catalog {
  return {
    families: D.products_ptd.map((p: any) => p.STYLE_GROUP),
    segments: D.new_insider_by_segment.map((s: any) => s.segment),
    weeks: D.meta.weeks,
    lastFull: D.meta.last_full_week,
    partial: D.meta.partial_week,
  };
}

/** The router's output. The parser produces the same shape, so one resolver checks both. */
export interface Route {
  template: string; // a template id or "none"
  subject: string | null;
  window: Win | null;
  week: number | null;
  metric: (typeof RANK_METRICS)[number] | null;
  direction: "top" | "bottom" | null;
  n: number | null;
  op: "below" | "above" | null;
  threshold: number | null;
  stock: "low" | "high" | null;
  premise: { metric: (typeof PREMISE_METRICS)[number]; direction: "up" | "down"; basis: "yoy" | "wow" | "unspecified" } | null;
  unmatched: string[];
  reading: string;
}

const nullable = (s: object) => ({ anyOf: [s, { type: "null" }] });

export function routeSchema(cat: Catalog) {
  return {
    type: "object",
    additionalProperties: false,
    required: ["template", "subject", "window", "week", "metric", "direction", "n", "op", "threshold", "stock", "premise", "unmatched", "reading"],
    properties: {
      template: { type: "string", enum: [...TEMPLATE_IDS, "none"] },
      subject: nullable({ type: "string", enum: [...SPECIAL_SUBJECTS, ...cat.families] }),
      window: nullable({ type: "string", enum: [...WINDOWS] }),
      week: nullable({ type: "integer", enum: cat.weeks }),
      metric: nullable({ type: "string", enum: [...RANK_METRICS] }),
      direction: nullable({ type: "string", enum: ["top", "bottom"] }),
      n: nullable({ type: "integer" }),
      op: nullable({ type: "string", enum: ["below", "above"] }),
      threshold: nullable({ type: "number" }),
      stock: nullable({ type: "string", enum: ["low", "high"] }),
      premise: nullable({
        type: "object",
        additionalProperties: false,
        required: ["metric", "direction", "basis"],
        properties: {
          metric: { type: "string", enum: [...PREMISE_METRICS] },
          direction: { type: "string", enum: ["up", "down"] },
          basis: { type: "string", enum: ["yoy", "wow", "unspecified"] },
        },
      }),
      unmatched: { type: "array", items: { type: "string" } },
      reading: { type: "string" },
    },
  };
}

export function systemPrompt(cat: Catalog): string {
  const first = cat.weeks[0];
  const last = cat.weeks[cat.weeks.length - 1];
  return [
    "You route questions about a retail brand's weekly performance dashboard to exactly one fixed query template.",
    "Code then runs that template over the dashboard's data and writes the answer, so you never answer the question yourself and never state any business figure.",
    "",
    "<templates>",
    ...TEMPLATES.map((t) => `- ${t.id}: ${t.params}`),
    "- none: use when no template answers the question, or it needs data this extract does not have (profit, margin, cost, forecasts, individual customers or stores, anything outside the weeks below).",
    "</templates>",
    "",
    "<data>",
    `Fiscal weeks W${first}-W${last} of this year vs the same weeks last year. W${cat.partial} is a partial week; W${cat.lastFull} is the last full week.`,
    "Windows: L1W is one week, L4W is that week and the three before it, PTD is the period to date from the first week.",
    `Product families (use these exact names for subject): ${cat.families.join(", ")}.`,
    `Channels and regions exist only inside insider_segments: ${cat.segments.join(", ")}. No other template can filter by them.`,
    "Special subjects: total (the whole business), genz (Gen Z customers), retention (returning or repeat customers).",
    "</data>",
    "",
    "<fields>",
    "- week: the week the question names, as a number. Use null when it names none or says this week, latest or now, so the dashboard's week is used.",
    "- window: L1W when the question is about a single week (\"in W29\", \"this week\", \"last week\"); L4W for \"last month\", \"last four weeks\" or \"recently\"; PTD for \"so far\", \"to date\", \"this season\" or \"overall\"; otherwise null.",
    "- subject: the family, or total / genz / retention, the question is about; null when it names none. Map plain words to a family only when the match is clear (\"dresses\" to Knit Dress); never guess between families.",
    "- metric, direction, n: for rank_families only (\"sold best\" is demand, top; \"fastest growing\" is growth, top). Use null for n unless the question gives a count.",
    "- op, threshold: for wos_threshold only, from the number the question gives. stock: for stock_alerts only.",
    "- premise: fill it when the question takes a change for granted (\"why did sales drop\", \"since Gen Z is growing\"): which metric, which direction, and whether it is vs last year (yoy), vs the previous week (wow) or unspecified. It is about the subject, or the whole business when subject is null, whichever template you pick. Code checks the premise against the data. Use null when the question assumes nothing, and for a question about which families rose or fell, since that assumes nothing about the whole business.",
    "- unmatched: every product, category, place, channel, store or customer group the question names that is not in the lists above or that the chosen template cannot filter by (a region in a sales question, a single style, a store). Code refuses rather than answering a broader question, so list them even when you still pick a template.",
    `- reading: one short plain sentence restating the question as you understood it. Use week labels like W${cat.lastFull} if needed but no other numbers. For none, say what is missing.`,
    "</fields>",
  ].join("\n");
}

/** Validates a router output against the catalog; throws on anything outside the contract. */
export function parseRoute(x: any, cat: Catalog): Route {
  const oneOf = <T>(v: any, allowed: readonly T[], field: string): T | null => {
    if (v === null || v === undefined) return null;
    if (!allowed.includes(v)) throw new Error(`route.${field} out of range: ${JSON.stringify(v)}`);
    return v;
  };
  if (!x || typeof x !== "object") throw new Error("route is not an object");
  const template = oneOf(x.template, [...TEMPLATE_IDS, "none"], "template");
  if (!template) throw new Error("route.template missing");
  const num = (v: any, field: string) => {
    if (v === null || v === undefined) return null;
    if (typeof v !== "number" || !Number.isFinite(v)) throw new Error(`route.${field} is not a number`);
    return v;
  };
  const p = x.premise;
  const premise = p
    ? {
        metric: oneOf(p.metric, PREMISE_METRICS, "premise.metric"),
        direction: oneOf(p.direction, ["up", "down"] as const, "premise.direction"),
        basis: oneOf(p.basis, ["yoy", "wow", "unspecified"] as const, "premise.basis"),
      }
    : null;
  if (premise && (!premise.metric || !premise.direction || !premise.basis)) throw new Error("route.premise incomplete");
  return {
    template,
    subject: oneOf(x.subject, [...SPECIAL_SUBJECTS, ...cat.families], "subject"),
    window: oneOf(x.window, WINDOWS, "window"),
    week: oneOf(x.week, cat.weeks, "week"),
    metric: oneOf(x.metric, RANK_METRICS, "metric"),
    direction: oneOf(x.direction, ["top", "bottom"] as const, "direction"),
    n: num(x.n, "n"),
    op: oneOf(x.op, ["below", "above"] as const, "op"),
    threshold: num(x.threshold, "threshold"),
    stock: oneOf(x.stock, ["low", "high"] as const, "stock"),
    premise: premise as Route["premise"],
    unmatched: Array.isArray(x.unmatched) ? x.unmatched.filter((s: any) => typeof s === "string" && s.trim()).slice(0, 10) : [],
    reading: typeof x.reading === "string" ? x.reading.slice(0, 300) : "",
  };
}
