import { useEffect, useRef, useState } from "react";
import { C, GOALS, LAST_FULL, MONO, askBus, useUrl } from "../lib/core";
import { TEMPLATES, type Route } from "../lib/ask/catalog";
import { parseQuestion, resolveRoute, runPlan, type Content, type Params } from "../lib/ask/engine";

// Ask: Claude (via /api/ask) or, when it is unavailable, a keyword parser maps the question to ONE fixed query
// template + parameters. Code checks that route (week range, named entities the template can't honor, premises
// the question takes for granted) and writes the answer from app.json. The model never sees or writes data values.

type Source = { kind: "claude"; model: string } | { kind: "parser"; why: string };
interface Result {
  id: number;
  q: string;
  pending?: boolean;
  source?: Source;
  reading?: string;
  ok?: boolean;
  reason?: string;
  tid?: string;
  params?: Params;
  notes?: string[];
  premise?: string | null;
  content?: Content;
}

const SUGGESTED: [string, number][] = [
  ["What should we do about Tabby this week?", 3], ["Which families are running out of stock?", 3],
  ["What sold best last month?", 2], ["How is Gen Z doing this week?", 1],
  [`Why did demand fall in week ${LAST_FULL}?`, 0], ["Where is the Insider gap for new Gen Z?", 1],
];
const WHY: Record<string, string> = {
  not_configured: "Claude isn't set up on this deployment",
  unreachable: "the Claude router isn't reachable",
  rate_limited: "the question limit was reached",
  upstream_rate_limited: "Claude is rate limited",
  timeout: "Claude took too long",
  refusal: "Claude declined",
  bad_key: "the API key was rejected",
};
const SEV_STYLE: Record<string, string> = { critical: C.crit, warning: C.warnText };

async function fetchRoute(question: string, wk: number, win: string): Promise<{ route: Route; model: string } | { error: string }> {
  const ctl = new AbortController();
  const timer = setTimeout(() => ctl.abort(), 25_000);
  try {
    const res = await fetch("/api/ask", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ question, wk, win }), signal: ctl.signal });
    const body = await res.json().catch(() => ({}));
    if (!res.ok || !body.route) return { error: body.error || (res.status === 404 ? "unreachable" : `http_${res.status}`) };
    return body;
  } catch (e) {
    return { error: (e as Error).name === "AbortError" ? "timeout" : "unreachable" };
  } finally {
    clearTimeout(timer);
  }
}

const Step = ({ k, children }: { k: number; children: any }) => (
  <li style={{ display: "flex", gap: 10 }}>
    <span style={{ flex: "0 0 22px", height: 22, display: "grid", placeItems: "center", background: C.sapphire, color: "#fff", fontFamily: MONO, fontSize: 11, fontWeight: 700 }}>{k}</span>
    <span style={{ minWidth: 0 }}>{children}</span>
  </li>
);

function SourceChip({ s }: { s: Source }) {
  const live = s.kind === "claude";
  return (
    <div style={{ display: "flex", alignItems: "flex-start", gap: 8, fontFamily: MONO, fontSize: 11, fontWeight: 700, lineHeight: 1.45, color: live ? C.sapphire : C.muted }}>
      <span aria-hidden style={{ flex: "0 0 8px", height: 8, marginTop: 4, borderRadius: 4, background: live ? C.sapphire : C.muted }} />
      <span style={{ minWidth: 0 }}>{live ? `READ BY CLAUDE · ${s.model}` : `READ BY KEYWORD PARSER · ${WHY[s.why] || "Claude returned an error"}`}</span>
    </div>
  );
}

function AnswerCard({ a }: { a: Result }) {
  return (
    <article className="panel fade-in" aria-busy={a.pending || undefined}>
      <div style={{ padding: "16px 20px", background: C.band, color: "#fff", fontSize: 16, fontWeight: 700 }}>{a.q}</div>
      <div style={{ padding: "18px 20px" }}>
        {a.pending ? (
          <p style={{ margin: 0, fontSize: 15, color: C.muted }}>Reading your question…</p>
        ) : (
          <>
            <SourceChip s={a.source!} />
            {a.reading && <p style={{ margin: "8px 0 0", fontSize: 14, lineHeight: 1.5, color: C.body }}>I read this as: <b style={{ color: C.ink }}>{a.reading}</b></p>}
            {!a.ok ? (
              <p style={{ margin: "14px 0 0", fontSize: 15, lineHeight: 1.55 }}><b>No answer.</b> {a.reason}</p>
            ) : (
              <>
                {a.premise && (
                  <div style={{ marginTop: 14, padding: "10px 14px", boxShadow: `inset 3px 0 0 ${C.sapphire}`, background: "rgba(38,109,211,.06)" }}>
                    <div style={{ fontFamily: MONO, fontSize: 10.5, fontWeight: 700, color: C.sapphire }}>PREMISE CHECKED AGAINST THE DATA</div>
                    <p style={{ margin: "4px 0 0", fontSize: 14.5, lineHeight: 1.5 }}>{a.premise}</p>
                  </div>
                )}
                <p style={{ margin: "14px 0 0", fontSize: 16, lineHeight: 1.55 }}>{a.content!.text}</p>
                {a.notes!.map((n) => <p key={n} style={{ margin: "6px 0 0", fontSize: 13, lineHeight: 1.5, color: C.muted }}>{n}</p>)}
                {a.content!.cards && a.content!.cards.length > 0 && (
                  <div style={{ display: "flex", flexDirection: "column", gap: 10, marginTop: 14 }}>
                    {a.content!.cards.map((c) => (
                      <div key={c.title} style={{ padding: "12px 14px", boxShadow: `inset 0 0 0 1px ${C.hair}` }}>
                        <div style={{ fontFamily: MONO, fontSize: 10.5, fontWeight: 700, color: C.muted }}>{c.pill.toUpperCase()}</div>
                        <div style={{ marginTop: 4, fontSize: 15, fontWeight: 700 }}>{c.title}</div>
                        <p style={{ margin: "6px 0 0", fontSize: 14, lineHeight: 1.55 }}>
                          {c.ok ? c.text : <i>Held back: a number in this card didn't match its facts.</i>}
                        </p>
                      </div>
                    ))}
                  </div>
                )}
                <ol style={{ margin: "16px 0 0", padding: 0, listStyle: "none", display: "flex", flexDirection: "column", gap: 6, fontSize: 13 }}>
                  <Step k={1}>Template chosen: <b style={{ fontFamily: MONO, fontSize: 12, overflowWrap: "anywhere" }}>{a.tid}({Object.entries(a.params || {}).map(([k, v]) => `${k}=${v}`).join(", ")})</b></Step>
                  <Step k={2}>Data read: <b style={{ fontFamily: MONO, fontSize: 12, overflowWrap: "anywhere" }}>{a.content!.read}</b></Step>
                  <Step k={3}>{a.content!.method || "Values copied from the file, filtered, sorted and formatted. No new arithmetic, no model-written numbers."}</Step>
                </ol>
                {a.content!.rows.length > 0 && (
                  <div style={{ overflowX: "auto" }}>
                    <table style={{ width: "100%", borderCollapse: "collapse", marginTop: 16, fontSize: 13.5 }}>
                      <thead><tr>{a.content!.cols.map((c) => <th key={c} style={{ padding: "8px 12px 8px 0", borderBottom: `2px solid ${C.ink}`, textAlign: "left", fontFamily: MONO, fontSize: 11 }}>{c}</th>)}</tr></thead>
                      <tbody>
                        {a.content!.rows.map((r, j) => (
                          <tr key={j} style={{ borderBottom: "1px solid rgba(52,64,85,.1)" }}>
                            {r.map((c, k) => <td key={k} style={{ padding: "8px 12px 8px 0", fontFamily: MONO, fontSize: 12.5, color: SEV_STYLE[String(c)] }}>{c}</td>)}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </>
            )}
          </>
        )}
      </div>
    </article>
  );
}

const plainButton = { padding: 0, border: 0, background: "none", font: "inherit", color: "inherit", textAlign: "left" as const, cursor: "pointer" };

export default function Ask() {
  const u = useUrl();
  const [input, setInput] = useState("");
  const [answers, setAnswers] = useState<Result[]>([]);
  const nextId = useRef(1);
  const ask = async (raw: string) => {
    const q = raw.trim();
    if (!q) return;
    const id = nextId.current++;
    setInput("");
    setAnswers((a) => [{ id, q, pending: true }, ...a]);
    const live = await fetchRoute(q, u.wk, u.win);
    const route = "route" in live ? live.route : parseQuestion(q);
    const source: Source = "route" in live ? { kind: "claude", model: live.model } : { kind: "parser", why: live.error };
    const plan = resolveRoute(route, { wk: u.wk, win: u.win });
    const done: Result = plan.ok
      ? { id, q, source, ok: true, reading: plan.reading, tid: plan.tid, params: plan.params, notes: plan.notes, premise: plan.premise, content: runPlan(plan) }
      : { id, q, source, ok: false, reading: plan.reading, reason: plan.reason };
    setAnswers((a) => a.map((x) => (x.id === id ? done : x)));
  };
  useEffect(() => { if (askBus.pending) { const q = askBus.pending; askBus.pending = ""; ask(q); } }, []); // eslint-disable-line react-hooks/exhaustive-deps
  return (
    <main className="pad-x" style={{ display: "flex", flexWrap: "wrap", gap: 28, padding: "32px 40px 56px" }}>
      <div style={{ flex: "999 1 560px", minWidth: 0 }}>
        <form onSubmit={(e) => { e.preventDefault(); ask(input); }} style={{ display: "flex", gap: 8, padding: 6, background: "#fff", boxShadow: `inset 0 0 0 1.5px ${C.charcoal}` }}>
          <input value={input} onChange={(e) => setInput(e.target.value)} aria-label="Ask a question" maxLength={300}
            placeholder="Ask about performance, Gen Z, families or stock…" style={{ flex: 1, minWidth: 0, padding: "10px 12px", border: 0, outline: "none", font: "inherit", fontSize: 16, background: "transparent", color: C.ink }} />
          <button type="submit" style={{ padding: "10px 18px", border: 0, background: C.charcoal, color: "#fff", fontSize: 14, fontWeight: 700, cursor: "pointer" }}>Ask</button>
        </form>
        {answers.length === 0 && (
          <div style={{ marginTop: 28 }}>
            <div style={{ fontFamily: MONO, fontSize: 12, fontWeight: 700 }}>TRY ONE OF THESE</div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(240px,1fr))", gap: 8, marginTop: 12 }}>
              {SUGGESTED.map(([q, g]) => (
                <button key={q} type="button" onClick={() => ask(q)} className="panel hov-ring" style={{ ...plainButton, padding: 16 }}>
                  <span style={{ display: "flex", alignItems: "center", gap: 6, whiteSpace: "nowrap", fontFamily: MONO, fontSize: 10.5, fontWeight: 700, color: C.muted }}>
                    <span style={{ width: 8, height: 8, borderRadius: 2, background: GOALS[g].hue }} />{GOALS[g].id} {GOALS[g].name.toUpperCase()}
                  </span>
                  <span style={{ display: "block", marginTop: 8, fontSize: 15, fontWeight: 700, lineHeight: 1.35 }}>{q}</span>
                </button>
              ))}
            </div>
            <p style={{ margin: "22px 0 0", maxWidth: 640, fontSize: 13.5, lineHeight: 1.6, color: C.body }}>
              Claude reads the question and picks one fixed query template. Code then checks that choice, including any change the question takes for granted, and writes every number from the data.
              If Claude is unavailable, a keyword parser picks the template instead. If the data can't answer the question as asked, you get no answer rather than a broader one.
            </p>
          </div>
        )}
        <div style={{ display: "flex", flexDirection: "column", gap: 16, marginTop: 20 }} aria-live="polite">
          {answers.map((a) => <AnswerCard key={a.id} a={a} />)}
        </div>
      </div>
      <aside style={{ flex: "1 1 300px", alignSelf: "flex-start", padding: 22, background: C.thistle }}>
        <div style={{ fontFamily: MONO, fontSize: 12, fontWeight: 700 }}>QUERY TEMPLATES · {TEMPLATES.length}</div>
        {TEMPLATES.map((t) => (
          <div key={t.id} style={{ padding: "10px 0", borderBottom: "1px solid rgba(52,64,85,.15)" }}>
            <div style={{ fontFamily: MONO, fontSize: 12, fontWeight: 700 }}>{t.id}</div>
            <div style={{ marginTop: 3, fontSize: 12.5, color: C.body }}>{t.pattern}</div>
            <div style={{ marginTop: 2, fontSize: 11.5, color: C.muted }}>reads {t.read}</div>
          </div>
        ))}
        {answers.length > 0 && <button type="button" className="link" onClick={() => setAnswers([])} style={{ ...plainButton, marginTop: 14, fontSize: 13, fontWeight: 700 }}>Clear answers</button>}
      </aside>
    </main>
  );
}
