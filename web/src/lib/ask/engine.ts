// Ask engine: route -> checks -> answer. The route comes from Claude (api/ask.ts) or, offline, from the keyword
// parser below; both have the same shape, so the same checks run on either. Code, not the model, decides whether
// a route can be honoured, checks any premise the question takes for granted, and writes every number.
import { D, PARTIAL, SEGMENT_NAME, WEEKS, alertsFor, anomaly, fmtMoney, fmtNum, fmtPct, fmtPts, fmtWos, ruleById, trailing, weekAI } from "../core";
import { extractNumbers, validateText } from "../validator.js";
import { TEMPLATES, catalogFrom, type Route, type Win } from "./catalog";

export const CATALOG = catalogFrom(D);
const FIRST = WEEKS[0];
const LAST = WEEKS[WEEKS.length - 1];
const FIRST_FULL_L4W: number = WEEKS.find((w) => !trailing(w, "L4W").truncated) ?? LAST;
const STOCK_RULES = { low: ["WOS_LOW", "WOS_COLLAPSE_VS_LY", "RECEIPTS_BELOW_SALES"], high: ["WOS_HIGH"] };
const PTD_ONLY = ["growth_drivers", "winners", "insider_segments"];
const WEEKLESS = [...PTD_ONLY];
const WINDOWLESS = [...PTD_ONLY, "genz_share_trend", "why_flagged", "actions", "stock_alerts", "wos_threshold"];

export type Params = Record<string, string | number>;
export interface CardOut { title: string; pill: string; text: string; ok: boolean }
export interface Content { text: string; read: string; method?: string; cols: string[]; rows: (string | number)[][]; cards?: CardOut[] }
export type Plan =
  | { ok: true; tid: string; params: Params; notes: string[]; premise: string | null; reading: string }
  | { ok: false; reason: string; reading: string };

// ---------- names and small helpers (display only) ----------
const subjectName = (s: string | null) => (s === "genz" ? "Gen Z" : s === "retention" ? "retention" : s === "total" ? "the whole business" : s || "everything");
const range = (weeks: number[]) => (weeks.length > 1 ? `W${weeks[0]}-W${weeks[weeks.length - 1]}` : `W${weeks[0]}`);
const plural = (n: number, one: string, many: string) => (n === 1 ? one : many);
/** "W29", "L4W ending W29 (W26-W29)" or "PTD to W29 (W23-W29)": the span a window covers, from the stored weeks. */
const span = (w: number, win: Win) =>
  win === "L1W" ? `W${w}` : win === "PTD" ? `PTD to W${w} (${range(trailing(w, win).weeks)})` : `${win} ending W${w} (${range(trailing(w, win).weeks)})`;
const famRow = (w: number, fam: string) => D.inventory_by_week.find((r: any) => r.year === "TY" && r.wk === w && r.family === fam);

/** Fills a template's pattern with the parameters that actually ran: the plain-words reading of the route. */
export function readingFor(tid: string, p: Params): string {
  const t = TEMPLATES.find((x) => x.id === tid);
  if (!t) return "";
  const when = p.window === "L1W" ? `W${p.week}` : p.window === "PTD" ? `PTD to W${p.week}` : `${p.window} ending W${p.week}`;
  let s = t.pattern
    .replace("{window} ending {week}", when)
    .replace("{window}", String(p.window ?? ""))
    .replace("{week}", p.week != null ? `W${p.week}` : "")
    .replace("{subject}", subjectName((p.subject as string) ?? null))
    .replace("{n}", String(p.n ?? ""))
    .replace("{metric}", String(p.metric ?? ""))
    .replace("{x}", String(p.threshold ?? ""));
  if (tid === "rank_families") s = s.replace("Top/bottom", p.direction === "bottom" ? "Bottom" : "Top");
  if (tid === "wos_threshold") s = s.replace("below/above", String(p.op));
  if (tid === "stock_alerts") s = p.stock === "high" ? `Which families are overstocked in W${p.week}?` : `Which families are running low on stock in W${p.week}?`;
  return s;
}

/** A model-written reading is shown only if it carries no numbers beyond week and window labels. */
export function safeReading(r: string): string | null {
  const t = (r || "").trim();
  return t && extractNumbers(t).length === 0 ? t : null;
}

// ---------- offline keyword parser (same output shape as the model router) ----------
const SEGMENT_WORDS: [RegExp, string][] = [
  [/\bjapan\b/, "Japan"], [/\beurope\b/, "Europe"], [/\b(greater )?china\b/, "Greater China"], [/\bnorth america\b|\b(us|usa)\b/, "North America"],
  [/\becomm\b|\be-?commerce\b|\bonline\b/, "eComm"], [/\boutlets?\b/, "Outlet"], [/\bstores?\b/, "stores"], [/\bfull[- ]price\b/, "full-price retail"],
];

export function parseQuestion(q: string): Route {
  const t = q.toLowerCase();
  const wm = /\b(?:w|wk|week)\s*(\d{1,2})\b/.exec(t);
  const week = wm ? +wm[1] : null;
  const xw = /\b(l1w|l4w|ptd)\b/.exec(t);
  const window: Win | null = xw ? (xw[1].toUpperCase() as Win)
    : /\b(last|past) (month|4 weeks|four weeks)\b|\brecent(ly)?\b/.test(t) ? "L4W"
    : /\bso far\b|\bto date\b|\bthis season\b|\boverall\b|\bseason\b/.test(t) ? "PTD"
    : /\b(this|last) week\b/.test(t) || week != null ? "L1W" : null;
  const fam = [...CATALOG.families].sort((a, b) => b.length - a.length).find((f) => t.includes(f.toLowerCase())) ?? null;
  const genz = /\bgen ?z\b/.test(t);
  const subject = fam ?? (genz ? "genz" : /\bretention\b|\breturning\b|\brepeat\b/.test(t) ? "retention" : null);
  const base: Route = { template: "none", subject, window, week, metric: null, direction: null, n: null, op: null, threshold: null, stock: null, premise: null, unmatched: [], reading: "" };
  const route = (template: string, extra: Partial<Route> = {}): Route => {
    const r = { ...base, template, ...extra };
    if (r.template !== "insider_segments") r.unmatched = SEGMENT_WORDS.filter(([re]) => re.test(t)).map(([, name]) => name);
    if (["sales_kpi", "family_kpi", "new_customers"].includes(r.template)) r.premise = parsePremise(t, r.template);
    return r;
  };
  if (/\bwhat should\b|\brecommend|\bactions?\b|\bwhat to do\b|\bdo about\b/.test(t)) return route("actions");
  if (/\bwhy\b/.test(t) && /\bflag|\balert/.test(t)) return route("why_flagged");
  if (/\bout of stock\b|\brun(ning)? out\b|\blow (on )?stock\b|\bstock-?outs?\b|\bunderstock/.test(t)) return route("stock_alerts", { stock: "low" });
  if (/\boverstock|\btoo much stock\b|\bexcess (stock|inventory)\b|\boverhang\b/.test(t)) return route("stock_alerts", { stock: "high" });
  if (/\bwos\b|\bweeks of supply\b|\bstock\b/.test(t)) {
    const x = /(below|under|less than|<|above|over|more than|>)\s*(\d+(?:\.\d+)?)/.exec(t);
    if (x) return route("wos_threshold", { op: /above|over|more|>/.test(x[1]) ? "above" : "below", threshold: +x[2] });
  }
  const rank = /\b(top|bottom|best|worst|biggest|smallest|fastest|slowest)\b/.exec(t);
  if (rank && /\bfamil|\bproduct|\bsold\b|\bsell|\bgrow|\bcontribut/.test(t)) {
    const n = /\b(?:top|bottom|best|worst)\s+(\d{1,2})\b/.exec(t);
    const metric = /\bcontribut/.test(t) ? "contribution" : /\bfast|\bslow|\bgrow/.test(t) ? "growth" : /\bsold\b|\bsell|\bbiggest|\bsmallest|\bdemand\b|\bsales\b|\brevenue\b/.test(t) ? "demand" : "contribution";
    return route("rank_families", { metric, direction: /\b(bottom|worst|smallest|slowest)\b/.test(rank[1]) ? "bottom" : "top", n: n ? +n[1] : null });
  }
  if (/\binsider\b|\bloyalty\b/.test(t)) return route("insider_segments");
  if (genz && /\bshare\b/.test(t)) return route("genz_share_trend");
  if (/\bnew customers?\b|\bacquisition\b|\bacquir/.test(t) || (genz && !fam)) return route("new_customers");
  if (/\bdriv|\bdecompos|\bbigger baskets\b|\bmore customers\b/.test(t)) return route("growth_drivers");
  if (/\bwinners?\b|\bdecliners?\b|\bwinning\b|\blosing\b/.test(t)) return route("winners");
  if (fam) return route("family_kpi");
  if (/\bsales\b|\bdemand\b|\brevenue\b|\bperform|\bhow did\b|\bhow are we\b|\baov\b|\btransactions\b|\bbusiness\b/.test(t)) return route("sales_kpi");
  return base;
}

function parsePremise(t: string, tid: string): Route["premise"] {
  const down = /\b(drop(ped|s)?|fall|falls|fell|falling|declin\w*|decreas\w*|down|slump\w*|dip(ped)?|lower)\b/.test(t);
  const up = /\b(rise|rises|rising|rose|grew|grow|grows|growing|up|increas\w*|jump\w*|surg\w*|higher|spik\w*)\b/.test(t);
  if (down === up) return null;
  const metric = /\bgen ?z\b/.test(t) && /\bnew\b/.test(t) ? "genz_new" : /\bnew customers?\b/.test(t) ? "new_customers"
    : /\baov\b|\bbasket|\border value\b/.test(t) ? "aov" : /\btransactions?\b|\borders?\b|\btraffic\b/.test(t) ? "transactions"
    : /\bsales\b|\bdemand\b|\brevenue\b/.test(t) || tid === "family_kpi" ? "demand" : null;
  if (!metric) return null;
  const basis = /\byoy\b|\blast year\b|\byear[- ]over[- ]year\b/.test(t) ? "yoy" : /\bwow\b|\bweek[- ]over[- ]week\b|\b(previous|prior) week\b/.test(t) ? "wow" : "unspecified";
  return { metric, direction: down ? "down" : "up", basis };
}

// ---------- checks: can this route be honoured? ----------
export function resolveRoute(r: Route, defaults: { wk: number; win: string }): Plan {
  const reading = safeReading(r.reading) ?? "";
  const refuse = (reason: string): Plan => ({ ok: false, reason, reading });
  if (r.template === "none" || !TEMPLATES.some((t) => t.id === r.template)) {
    return refuse("None of the query templates can answer this from the data, so there's no answer rather than a guess.");
  }
  const tid = r.template;
  if (r.week != null && !WEEKS.includes(r.week)) return refuse(`The data covers ${range([FIRST, LAST])}, so W${r.week} isn't available.`);
  if (r.unmatched.length) {
    const segs = r.unmatched.filter((u) => CATALOG.segments.some((s) => s.toLowerCase() === u.toLowerCase() || (SEGMENT_NAME[s] || "").toLowerCase() === u.toLowerCase()) || ["stores", "full-price retail"].includes(u));
    return refuse(
      `The question names ${r.unmatched.map((u) => `"${u}"`).join(" and ")}, and the template that fits can't filter by ${plural(r.unmatched.length, "it", "them")}. ` +
        `Answering for the whole business would answer a different question, so there's no answer.` +
        (segs.length ? " Channel and region splits exist only for Insider sign-up of new Gen Z (try: Where is the Insider gap for new Gen Z?)." : ""),
    );
  }
  const week = WEEKLESS.includes(tid) ? null : r.week ?? defaults.wk;
  const window = WINDOWLESS.includes(tid) ? null : ((r.window ?? defaults.win) as Win);
  const isFamily = r.subject != null && CATALOG.families.includes(r.subject);
  const params: Params = {};
  if (week != null) params.week = week;
  if (window) params.window = window;
  const notes: string[] = [];

  if (tid === "family_kpi") {
    if (!isFamily) return refuse("This template needs one product family, and the question doesn't name one I can match exactly.");
    params.subject = r.subject!;
  }
  if (tid === "why_flagged" || tid === "actions") if (r.subject) params.subject = r.subject;
  if (tid === "rank_families") {
    params.metric = r.metric ?? "contribution";
    params.direction = r.direction ?? "top";
    params.n = Math.min(Math.max(Math.round(r.n ?? 5), 1), CATALOG.families.length);
  }
  if (tid === "wos_threshold") {
    if (!r.op || r.threshold == null || r.threshold <= 0) return refuse("This template needs a weeks-of-supply number to compare against, such as below 3.");
    params.op = r.op;
    params.threshold = r.threshold;
  }
  if (tid === "stock_alerts") params.stock = r.stock ?? "low";
  if (["sales_kpi", "new_customers"].includes(tid) && r.subject && r.subject !== "total" && !(tid === "new_customers" && r.subject === "genz")) {
    return refuse(`This template covers the whole business, so it can't answer for ${subjectName(r.subject)} specifically.`);
  }

  if (PTD_ONLY.includes(tid) && ((r.window && r.window !== "PTD") || r.week != null)) {
    notes.push(`This breakdown exists only for the period to date (${range([FIRST, LAST])}), so the week or window you named isn't applied.`);
  }
  if (tid === "family_kpi" && window === "PTD" && week !== LAST) notes.push(`Family figures for PTD always run ${range([FIRST, LAST])}.`);
  if (week === PARTIAL) notes.push(`W${PARTIAL} is a partial week (${D.meta.partial_week_days}), compared with the same days last year.`);
  if (window === "L4W" && week != null && trailing(week, "L4W").truncated) {
    notes.push(`L4W ending W${week} has only ${trailing(week, "L4W").n_weeks} ${plural(trailing(week, "L4W").n_weeks, "week", "weeks")} because the data starts at W${FIRST}.`);
  }
  const premise = r.premise ? premiseNote(r.premise, tid, params) : null;
  return { ok: true, tid, params, notes, premise, reading: reading || readingFor(tid, params) };
}

const PREMISE_KEY = { demand: "sales", transactions: "txns", aov: "aov", new_customers: "new_customers", genz_new: "genz_new" } as const;
const PREMISE_LABEL = { demand: "demand", transactions: "transactions", aov: "AOV", new_customers: "new customers", genz_new: "Gen Z new customers" } as const;

/** Checks the change a question takes for granted against the stored YoY / WoW values, and says what the data shows. */
export function premiseNote(pr: NonNullable<Route["premise"]>, tid: string, p: Params): string | null {
  const w = p.week as number | undefined;
  const win = p.window as Win | undefined;
  if (w == null || !win) return null;
  const checks: { label: string; v: number | null | undefined }[] = [];
  let label: string = PREMISE_LABEL[pr.metric];
  const extra: string[] = [];
  if (tid === "family_kpi") {
    if (pr.metric !== "demand") return `Your question assumes a change in ${label} for ${p.subject}; only demand is stored per family, so that part isn't checked.`;
    label = `${p.subject} demand`;
    const row = win === "PTD" ? D.products_ptd.find((r: any) => r.STYLE_GROUP === p.subject) : D.products_by_week.find((r: any) => r.wk === w && r.window === win && r.family === p.subject);
    checks.push({ label: "vs last year", v: row?.sales_yoy_pct });
    if (pr.basis === "wow") extra.push("A change vs the previous week isn't stored per family.");
  } else {
    const key = PREMISE_KEY[pr.metric];
    const wow = win === "L1W" ? trailing(w, "L1W").wow?.[key] : null;
    if (pr.basis !== "wow") checks.push({ label: "vs last year", v: trailing(w, win)[key]?.yoy_pct });
    if (pr.basis !== "yoy") {
      if (wow != null) checks.push({ label: "vs the previous week", v: wow });
      else if (pr.basis === "wow") {
        extra.push(win === "L1W" ? `There is no previous week before W${w} in the data.` : "A change vs the previous week is only stored for a single week (L1W).");
        checks.push({ label: "vs last year", v: trailing(w, win)[key]?.yoy_pct });
      }
    }
  }
  const known = checks.filter((c): c is { label: string; v: number } => c.v != null);
  if (!known.length) return null;
  const holds = (v: number) => (pr.direction === "up" ? v > 0 : v < 0);
  const held = known.filter((c) => holds(c.v));
  const verdict = held.length === known.length ? "That matches the data" : held.length === 0 ? "The data says otherwise" : `That holds ${held.map((c) => c.label).join(" and ")} only`;
  const where = tid === "family_kpi" && win === "PTD" ? `PTD (${range([FIRST, LAST])})` : span(w, win);
  return [`Your question assumes ${label} ${pr.direction === "up" ? "rose" : "fell"}. ${verdict}: in ${where} it was ${known.map((c) => `${fmtPct(c.v, true)} ${c.label}`).join(" and ")}.`, ...extra].join(" ");
}

// ---------- answers: every value copied from app.json, then filtered, sorted and formatted ----------
export function runPlan(plan: Extract<Plan, { ok: true }>): Content {
  const p = plan.params;
  const w = p.week as number;
  const win = p.window as Win;
  switch (plan.tid) {
    case "sales_kpi": {
      const b = trailing(w, win);
      const wow = win === "L1W" ? b.wow : null;
      return {
        read: `trailing.${w}.${win}${wow ? ` · trailing.${w}.L1W.wow` : ""}`,
        text: `${span(w, win)}: demand ${fmtMoney(b.sales.ty)} vs ${fmtMoney(b.sales.ly)} LY (${fmtPct(b.sales.yoy_pct, true)}); transactions ${fmtPct(b.txns.yoy_pct, true)}; AOV ${fmtMoney(b.aov.ty, false)} (${fmtPct(b.aov.yoy_pct, true)}).` +
          (wow ? ` Vs the previous week: demand ${fmtPct(wow.sales, true)}, transactions ${fmtPct(wow.txns, true)}, AOV ${fmtPct(wow.aov, true)}.` : ""),
        cols: wow ? ["Metric", "vs last year", "vs previous week"] : ["Metric", "TY", "LY", "vs last year"],
        rows: wow
          ? [["Demand", fmtPct(b.sales.yoy_pct, true), fmtPct(wow.sales, true)], ["Transactions", fmtPct(b.txns.yoy_pct, true), fmtPct(wow.txns, true)], ["AOV", fmtPct(b.aov.yoy_pct, true), fmtPct(wow.aov, true)]]
          : [["Demand", fmtMoney(b.sales.ty), fmtMoney(b.sales.ly), fmtPct(b.sales.yoy_pct, true)], ["Transactions", fmtNum(b.txns.ty), fmtNum(b.txns.ly), fmtPct(b.txns.yoy_pct, true)], ["AOV", fmtMoney(b.aov.ty, false), fmtMoney(b.aov.ly, false), fmtPct(b.aov.yoy_pct, true)]],
      };
    }
    case "growth_drivers": {
      const rows = D.decomposition_ptd;
      return {
        read: `decomposition_ptd · ${rows.length} rows`,
        text: `Period-to-date demand growth (${range([FIRST, LAST])}) splits into ${rows.map((r: any) => `${r.factor} ${fmtPct(r.share_of_growth)} of growth (${fmtPct(r.pct_chg, true)})`).join(", ")}.`,
        cols: ["Factor", "Change vs LY", "Share of growth", "Demand added"],
        rows: rows.map((r: any) => [r.factor, fmtPct(r.pct_chg, true), fmtPct(r.share_of_growth), fmtMoney(r.usd_contrib)]),
      };
    }
    case "family_kpi": {
      const fam = p.subject as string;
      const ptd = win === "PTD";
      const row = ptd ? D.products_ptd.find((r: any) => r.STYLE_GROUP === fam) : D.products_by_week.find((r: any) => r.wk === w && r.window === win && r.family === fam);
      const inv = famRow(w, fam);
      const alerts = alertsFor(w).filter((a: any) => a.entity === fam);
      const where = ptd ? `PTD (${range([FIRST, LAST])})` : span(w, win);
      const demand = row
        ? ptd
          ? `demand ${fmtMoney(row.sales_TY)} vs ${fmtMoney(row.sales_LY)} LY (${fmtPct(row.sales_yoy_pct, true)}), ${fmtPts(row.contrib_pts * 100)} of total growth, class ${row.class}.`
          : `demand ${fmtMoney(row.sales_ty)} vs ${fmtMoney(row.sales_ly)} LY (${fmtPct(row.sales_yoy_pct, true)}), ${fmtPts(row.contrib_pts)} of total growth.`
        : "no demand recorded.";
      const stock = inv ? ` Weeks of supply at the end of W${w}: ${fmtWos(inv.wos)} vs ${fmtWos(inv.wos_ly_same_week)} LY same week, ${fmtNum(inv.on_hand_eow)} units on hand.` : "";
      const flags = alerts.length ? ` ${alerts.length} ${plural(alerts.length, "alert", "alerts")} fired in W${w}: ${alerts.map((a: any) => `${a.rule_id} (${a.severity})`).join(", ")}.` : ` No alert fired for ${fam} in W${w}.`;
      return {
        read: `${ptd ? "products_ptd" : `products_by_week · wk=${w} · window=${win}`} · inventory_by_week · wk=${w} · alerts W${w} · family=${fam}`,
        text: `${fam}, ${where}: ${demand}${stock}${flags}`,
        cols: alerts.length ? ["Alert", "Severity", "Rule", "Threshold"] : [],
        rows: alerts.map((a: any) => [a.id, a.severity, a.rule_id, ruleById(a.rule_id).rule]),
      };
    }
    case "rank_families": {
      const top = p.direction !== "bottom";
      const n = p.n as number;
      const metric = p.metric as string;
      const ptd = win === "PTD";
      const val = (r: any) => (metric === "demand" ? (ptd ? r.sales_TY : r.sales_ty) : metric === "growth" ? r.sales_yoy_pct : r.contrib_pts);
      const pool = (ptd ? D.products_ptd.filter((r: any) => metric !== "growth" || r.vol_ok) : D.products_by_week.filter((r: any) => r.wk === w && r.window === win)).filter((r: any) => val(r) != null);
      const rows = [...pool].sort((a, b) => (top ? val(b) - val(a) : val(a) - val(b))).slice(0, n);
      const name = (r: any) => (ptd ? r.STYLE_GROUP : r.family);
      const contrib = (r: any) => fmtPts(ptd ? r.contrib_pts * 100 : r.contrib_pts);
      const show = (r: any) => (metric === "demand" ? fmtMoney(val(r)) : metric === "growth" ? fmtPct(val(r), true) : contrib(r));
      const label = metric === "demand" ? "demand" : metric === "growth" ? "demand growth vs LY" : "contribution to growth";
      return {
        read: `${ptd ? "products_ptd" : `products_by_week · wk=${w} · window=${win}`} · sorted by ${metric === "demand" ? "sales" : metric === "growth" ? "sales_yoy_pct" : "contrib_pts"} · ${rows.length} rows`,
        text: `${top ? "Top" : "Bottom"} ${rows.length} families by ${label}, ${ptd ? `PTD (${range([FIRST, LAST])})` : span(w, win)}: ${rows.map((r: any) => `${name(r)} (${show(r)})`).join(", ")}.` +
          (metric === "growth" ? (ptd ? " Only families with enough volume are ranked." : " Growth rates on small families are noisy at sample scale.") : ""),
        cols: ["Family", "Demand TY", "Demand YoY", "Contribution"],
        rows: rows.map((r: any) => [name(r), fmtMoney(ptd ? r.sales_TY : r.sales_ty), fmtPct(r.sales_yoy_pct, true), contrib(r)]),
      };
    }
    case "winners": {
      const rows = D.products_ptd.filter((r: any) => r.class !== "Steady").sort((a: any, b: any) => b.sales_yoy_pct - a.sales_yoy_pct);
      return {
        read: `products_ptd · class in (Winner, Decliner) · ${rows.length} rows`,
        text: `Winners: ${rows.filter((r: any) => r.class === "Winner").map((r: any) => r.STYLE_GROUP).join(", ")}. Decliners: ${rows.filter((r: any) => r.class === "Decliner").map((r: any) => r.STYLE_GROUP).join(", ")}.`,
        cols: ["Family", "Class", "Demand YoY", "Contribution"],
        rows: rows.map((r: any) => [r.STYLE_GROUP, r.class, fmtPct(r.sales_yoy_pct, true), fmtPts(r.contrib_pts * 100)]),
      };
    }
    case "new_customers": {
      const b = trailing(w, win);
      return {
        read: `trailing.${w}.${win} · new_customers, genz_new, genz_share_of_new`,
        text: `${span(w, win)}: ${fmtNum(b.new_customers.ty)} new customers vs ${fmtNum(b.new_customers.ly)} LY (${fmtPct(b.new_customers.yoy_pct, true)}). ` +
          `Gen Z: ${fmtNum(b.genz_new.ty)} vs ${fmtNum(b.genz_new.ly)} (${fmtPct(b.genz_new.yoy_pct, true)}), ${fmtPct(b.genz_share_of_new.ty)} of new customers vs ${fmtPct(b.genz_share_of_new.ly)} LY. Counts are sample-scale.`,
        cols: ["Metric", "TY", "LY", "vs last year"],
        rows: [
          ["New customers", fmtNum(b.new_customers.ty), fmtNum(b.new_customers.ly), fmtPct(b.new_customers.yoy_pct, true)],
          ["Gen Z new customers", fmtNum(b.genz_new.ty), fmtNum(b.genz_new.ly), fmtPct(b.genz_new.yoy_pct, true)],
          ["Gen Z share of new", fmtPct(b.genz_share_of_new.ty), fmtPct(b.genz_share_of_new.ly), ""],
        ],
      };
    }
    case "genz_share_trend": {
      const rows = D.genz_weekly.filter((r: any) => r.WK <= w);
      const f = rows[0];
      const l = rows[rows.length - 1];
      return {
        read: `genz_weekly · WK ≤ ${w} · ${rows.length} rows`,
        text: `Gen Z share of new customers went from ${fmtPct(f.genz_share_of_new_TY)} in W${f.WK} to ${fmtPct(l.genz_share_of_new_TY)} in W${l.WK} (LY that week: ${fmtPct(l.genz_share_of_new_LY)}).${l.WK === PARTIAL ? ` W${l.WK} is a partial week.` : ""}`,
        cols: ["Week", "TY", "LY", "Gen Z new TY"],
        rows: rows.map((r: any) => [`W${r.WK}${r.WK === PARTIAL ? " (partial)" : ""}`, fmtPct(r.genz_share_of_new_TY), fmtPct(r.genz_share_of_new_LY), fmtNum(r.genz_new_TY)]),
      };
    }
    case "insider_segments": {
      const rows = [...D.new_insider_by_segment].sort((a: any, b: any) => a.genz_new_insider_rate - b.genz_new_insider_rate);
      const sig = rows.filter((r: any) => r.p < 0.05);
      const seg = (r: any) => SEGMENT_NAME[r.segment] || r.segment;
      return {
        read: `new_insider_by_segment · ${rows.length} rows`,
        text: `Insider attach of new Gen Z vs other new customers (TY), lowest first. ` +
          (sig.length ? `The gap is significant (p < 0.05) in ${sig.map((r: any) => `${seg(r)} (${fmtPct(r.genz_new_insider_rate)} vs ${fmtPct(r.other_new_insider_rate)})`).join(" and ")}.` : "No segment's gap is significant at p < 0.05."),
        cols: ["Segment", "Gen Z new", "Other new", "n Gen Z", "p"],
        rows: rows.map((r: any) => [seg(r), fmtPct(r.genz_new_insider_rate), fmtPct(r.other_new_insider_rate), r.genz_new_n, r.p.toFixed(3)]),
      };
    }
    case "why_flagged": {
      const s = (p.subject as string) ?? null;
      const hits = alertsFor(w).filter((a: any) => !s || a.entity.toLowerCase() === s.toLowerCase());
      return {
        read: `anomalies.json · by_week[${w}]${s ? ` · entity=${s}` : ""} · ${hits.length} rows`,
        text: hits.length
          ? `${hits.length} ${plural(hits.length, "rule", "rules")} fired for ${subjectName(s)} in W${w}. ${hits.map((h: any) => h.message).join(" ")}`
          : `No rule fired for ${subjectName(s)} in W${w}.`,
        cols: hits.length ? ["Alert", "Severity", "Rule", "Threshold"] : [],
        rows: hits.map((h: any) => [h.id, h.severity, h.rule_id, ruleById(h.rule_id).rule]),
      };
    }
    case "actions": {
      const s = (p.subject as string) ?? null;
      const all = weekAI(w).cards;
      const cards = !s || s === "total" ? all : all.filter((c: any) => c.anomaly_ids.some((id: string) => anomaly(id)?.entity === s));
      return {
        read: `weeks_ai.${w}.cards${s && s !== "total" ? ` · alerts with entity=${s}` : ""} · ${cards.length} cards`,
        method: "Card text was written by AI ahead of time; every number in it was re-checked against that card's facts just now, and a card that fails is held back.",
        text: cards.length
          ? `${cards.length === 1 ? "One flagged card" : `${cards.length} flagged cards`} for ${subjectName(s)} in W${w}, with the action the rules point to.`
          : `No flagged card is about ${subjectName(s)} in W${w}. Try: Why is ${s === "genz" ? "Gen Z" : s} flagged in week ${w}?`,
        cols: [],
        rows: [],
        cards: cards.map((c: any) => {
          const text = `${c.headline} ${c.body}`;
          return { title: c.title, pill: c.pill, text, ok: validateText(text, c.values).status === "PASS" };
        }),
      };
    }
    case "stock_alerts": {
      const kind = p.stock as "low" | "high";
      const l4 = trailing(w, "L4W");
      const what = kind === "low" ? "for low stock" : "for overstock";
      if (l4.truncated) {
        return {
          read: `trailing.${w}.L4W.truncated`, cols: [], rows: [],
          text: `Stock rules only run on full four-week windows, and L4W ending W${w} has ${l4.n_weeks} ${plural(l4.n_weeks, "week", "weeks")}, so nothing is checked yet. The first checked week is W${FIRST_FULL_L4W}.`,
        };
      }
      const rules = STOCK_RULES[kind];
      const hits = alertsFor(w).filter((a: any) => rules.includes(a.rule_id));
      const wosOf = (f: string) => famRow(w, f)?.wos ?? 0;
      const fams: string[] = [...new Set<string>(hits.map((a: any) => a.entity))].sort((a, b) => (kind === "low" ? wosOf(a) - wosOf(b) : wosOf(b) - wosOf(a)));
      const rows = fams.map((f) => {
        const inv = famRow(w, f);
        const mine = hits.filter((a: any) => a.entity === f);
        return [f, mine.map((a: any) => `${a.rule_id} (${a.severity})`).join(", "), fmtWos(inv?.wos), fmtWos(inv?.wos_ly_same_week), fmtNum(inv?.on_hand_eow)];
      });
      return {
        read: `anomalies.json · by_week[${w}] · rules ${rules.join(", ")} · inventory_by_week · ${fams.length} families`,
        text: fams.length
          ? `${fams.length} ${plural(fams.length, "family is", "families are")} flagged ${what} in W${w}: ${rows.map((r) => `${r[0]} (${r[2]} weeks of supply)`).join(", ")}. Rules: ${rules.map((id) => `${id} ${ruleById(id).rule}`).join("; ")}.`
          : `No family is flagged ${what} in W${w}. Rules checked: ${rules.map((id) => `${id} ${ruleById(id).rule}`).join("; ")}.`,
        cols: ["Family", "Rules fired", "WOS TY", "WOS LY same week", "On hand"],
        rows,
      };
    }
    case "wos_threshold": {
      const below = p.op === "below";
      const x = p.threshold as number;
      const rows = D.inventory_by_week.filter((r: any) => r.year === "TY" && r.wk === w && r.wos != null && (below ? r.wos < x : r.wos > x)).sort((a: any, b: any) => (below ? a.wos - b.wos : b.wos - a.wos));
      const trunc = rows.length && rows[0].wos_window_weeks < 4;
      return {
        read: `inventory_by_week · year=TY · wk=${w} · wos ${below ? "<" : ">"} ${x} · ${rows.length} rows`,
        text: rows.length
          ? `${rows.length} ${plural(rows.length, "family has", "families have")} weeks of supply ${p.op} ${x} in W${w}: ${rows.map((r: any) => `${r.family} at ${fmtWos(r.wos)}`).join(", ")}.${trunc ? ` The window is truncated before W${FIRST_FULL_L4W}, so these are early readings.` : ""}`
          : `No family has weeks of supply ${p.op} ${x} in W${w}.`,
        cols: ["Family", "WOS TY", "WOS LY same week", "On hand"],
        rows: rows.map((r: any) => [r.family, fmtWos(r.wos), fmtWos(r.wos_ly_same_week), fmtNum(r.on_hand_eow)]),
      };
    }
  }
  throw new Error(`unknown template ${plan.tid}`);
}
