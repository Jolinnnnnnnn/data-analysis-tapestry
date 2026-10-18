// POST /api/ask: Claude reads a question and returns a Route (one query template + parameters). It never sees
// or writes data values; the browser runs the route through the same checks as the offline parser and code
// writes the answer. The key stays here (ANTHROPIC_API_KEY on Vercel). Any failure returns an error code and the
// browser falls back to the keyword parser, so the page never depends on this function being up.
import Anthropic from "@anthropic-ai/sdk";
// A static import bundles the data with the function, so nothing depends on the working directory at runtime.
import appData from "../src/data/app.json" with { type: "json" };
import { WINDOWS, catalogFrom, parseRoute, routeSchema, systemPrompt, type Catalog } from "../src/lib/ask/catalog.js";

const MODEL = process.env.ASK_MODEL || "claude-opus-5-5";
// Server-side refusal fallback is available on the Opus, Sonnet and Fable lines only.
const FALLBACKS = /^claude-(opus|sonnet|fable)-/.test(MODEL);
const MAX_QUESTION = 300;
const RATE = { max: 20, windowMs: 10 * 60 * 1000 }; // per IP, per warm instance (best effort; the console spend limit is the hard cap)
const CACHE_MAX = 200;

let ctx: { cat: Catalog; system: string; schema: Record<string, unknown> } | null = null;
function context() {
  if (!ctx) {
    const cat = catalogFrom(appData);
    ctx = { cat, system: systemPrompt(cat), schema: routeSchema(cat) };
  }
  return ctx;
}

const hits = new Map<string, number[]>();
function rateLimited(ip: string, now: number): boolean {
  const recent = (hits.get(ip) || []).filter((t) => now - t < RATE.windowMs);
  recent.push(now);
  hits.set(ip, recent);
  return recent.length > RATE.max;
}
const cache = new Map<string, unknown>();

const json = (status: number, body: unknown) =>
  new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json", "cache-control": "no-store" } });

/** Browsers send Origin on cross-site POSTs; only this site (or local dev) may call the function from a page. */
function originAllowed(request: Request): boolean {
  const origin = request.headers.get("origin");
  if (!origin) return true;
  try {
    const host = new URL(origin).host;
    return host === new URL(request.url).host || /^(localhost|127\.0\.0\.1)(:\d+)?$/.test(host);
  } catch {
    return false;
  }
}

export async function POST(request: Request): Promise<Response> {
  if (!originAllowed(request)) return json(403, { error: "origin" });
  if (!process.env.ANTHROPIC_API_KEY) return json(503, { error: "not_configured" });

  let body: any;
  try {
    body = await request.json();
  } catch {
    return json(400, { error: "bad_json" });
  }
  let built: ReturnType<typeof context>;
  try {
    built = context();
  } catch (e) {
    console.error("ask: catalog failed", e);
    return json(500, { error: "catalog" });
  }
  const { cat, system, schema } = built;
  const question = typeof body?.question === "string" ? body.question.trim() : "";
  const wk = body?.wk;
  const win = body?.win;
  if (!question || question.length > MAX_QUESTION) return json(400, { error: "bad_question" });
  if (!cat.weeks.includes(wk) || !(WINDOWS as readonly string[]).includes(win)) return json(400, { error: "bad_context" });

  const ip = (request.headers.get("x-forwarded-for") || "").split(",")[0].trim() || "local";
  if (rateLimited(ip, Date.now())) return json(429, { error: "rate_limited" });

  const key = `${wk}|${win}|${question.toLowerCase().replace(/\s+/g, " ")}`;
  if (cache.has(key)) return json(200, cache.get(key));

  const client = new Anthropic({ timeout: 20_000, maxRetries: 1 });
  try {
    const msg = await client.beta.messages.create({
      model: MODEL,
      max_tokens: 4000,
      ...(FALLBACKS ? { betas: ["server-side-fallback-2026-07-01"], fallbacks: "default" as const } : {}),
      output_config: { effort: "low", format: { type: "json_schema", schema } },
      system,
      messages: [{ role: "user", content: `Dashboard week: W${wk}\nDashboard window: ${win}\n<question>${question}</question>` }],
    });
    if (msg.stop_reason === "refusal") return json(422, { error: "refusal" });
    if (msg.stop_reason === "max_tokens") return json(502, { error: "truncated" });
    const text = msg.content.find((b) => b.type === "text");
    if (!text || text.type !== "text") return json(502, { error: "no_text" });
    const route = parseRoute(JSON.parse(text.text), cat);
    const out = { route, model: msg.model };
    if (cache.size >= CACHE_MAX) cache.delete(cache.keys().next().value as string);
    cache.set(key, out);
    return json(200, out);
  } catch (e) {
    if (e instanceof Anthropic.AuthenticationError || e instanceof Anthropic.PermissionDeniedError) return json(503, { error: "bad_key" });
    if (e instanceof Anthropic.RateLimitError) return json(429, { error: "upstream_rate_limited" });
    if (e instanceof Anthropic.APIConnectionTimeoutError) return json(504, { error: "timeout" });
    if (e instanceof Anthropic.APIError) return json(502, { error: `upstream_${e.status ?? "error"}` });
    console.error("ask failed", e);
    return json(502, { error: e instanceof SyntaxError ? "bad_route_json" : "bad_route" });
  }
}
