import { useEffect, useState } from "react";
import { SEGMENT_NAME } from "./Explore";
import { C, D, GOALS, LAST_FULL, MONO, WEEKS, askBus, fmtMoney, fmtNum, fmtPct, fmtPts, fmtWos, useUrl } from "../lib/core";

// Ask: the question is mapped to ONE fixed query template + parameters; code reads app.json and renders the answer.
// Offline this picker is rule-based. LIVE MODEL PLUG-IN POINT: a model may replace parseQuestion() and return the
// same {template, params} JSON; it never sees or writes data values (see PROMPTS.md / scripts/16_generate_summaries.py).

type Params = Record<string, any>;
interface Answer { q: string; ok: boolean; tid?: string; params?: Params; read?: string; answer?: string; cols?: string[]; rows?: (string | number)[][] }

const FAMILIES: string[] = D.products_ptd.map((p: any) => p.STYLE_GROUP);
const TEMPLATES: { id: string; pattern: string; read: string; goal: number }[] = [
  { id: "why_flagged", pattern: "Why is {entity} flagged in week {w}?", read: "anomalies.json by week", goal: 3 },
  { id: "wos_threshold", pattern: "Which families have WOS below/above {x} in week {w}?", read: "inventory_by_week", goal: 3 },
  { id: "top_contrib", pattern: "Top/bottom {n} families by contribution in {window} for week {w}", read: "products_by_week / products_ptd", goal: 2 },
  { id: "genz_new", pattern: "Gen Z new customers in {window} ending week {w}?", read: "trailing", goal: 1 },
  { id: "genz_share_trend", pattern: "Gen Z share of new customers by week up to week {w}?", read: "genz_weekly", goal: 1 },
  { id: "insider_segments", pattern: "Where is the Insider gap for new Gen Z?", read: "new_insider_by_segment", goal: 1 },
  { id: "sales_kpi", pattern: "How did sales do in {window} ending week {w}?", read: "trailing", goal: 0 },
  { id: "winners", pattern: "Which families are winners / decliners?", read: "products_ptd", goal: 2 },
];
const SUGGESTED: [string, number][] = [
  ["Why is Tabby flagged in week 29?", 3], ["Which families have WOS below 3 in week 30?", 3],
  ["Top 3 families by contribution in L4W for week 29", 2], ["Gen Z share of new customers by week up to week 30?", 1],
  ["Why did demand fall in L1W ending week 29?", 0], ["Where is the Insider gap for new Gen Z?", 1],
];
const RETENTION_RULES = ["RETURNING_YOY_FLAT", "GENZ_RETURNING_YOY_NEG", "GENZ_NEW_INSIDER_LOW"];

export function parseQuestion(q: string, defWk: number, defWin: string): [string | null, Params] {
  const t = q.toLowerCase();
  const m = /\b(?:w|wk|week)\s*(\d{2})\b/.exec(t);
  const w = m && WEEKS.includes(+m[1]) ? +m[1] : defWk;
  const wm = /\b(l1w|l4w|ptd)\b/.exec(t);
  const window = wm ? wm[1].toUpperCase() : t.includes("last week") ? "L1W" : t.includes("to date") || t.includes("period") ? "PTD" : defWin;
  const fam = [...FAMILIES].sort((a, b) => b.length - a.length).find((f) => t.includes(f.toLowerCase()));
  if (t.includes("why") && /flag|alert|why is/.test(t))
    return ["why_flagged", { entity: fam || (/retention|returning/.test(t) ? "retention" : /gen ?z/.test(t) ? "genz" : "total"), w }];
  if (t.includes("why") && /demand|sales|fall|drop/.test(t)) return ["sales_kpi", { window: "L1W", w }];
  if (/wos|weeks of supply|stock/.test(t)) {
    const x = /(below|under|less than|<|above|over|more than|>)\s*(\d+(?:\.\d+)?)/.exec(t);
    if (x) return ["wos_threshold", { op: /above|over|more|>/.test(x[1]) ? "above" : "below", x: +x[2], w }];
  }
  const tm = /\b(top|bottom)\s*(\d+)?/.exec(t);
  if (tm && /contribut|famil|growth/.test(t)) return ["top_contrib", { dir: tm[1], n: +(tm[2] || 5), window, w }];
  if (t.includes("insider")) return ["insider_segments", {}];
  if (/gen ?z/.test(t) && t.includes("share")) return ["genz_share_trend", { w }];
  if (/gen ?z/.test(t) && t.includes("new")) return ["genz_new", { window, w }];
  if (/winner|decliner|winning/.test(t)) return ["winners", {}];
  if (/sales|demand|perform|how did|aov|transactions/.test(t)) return ["sales_kpi", { window, w }];
  return [null, {}];
}

function answer(tid: string, p: Params): Omit<Answer, "q" | "ok"> {
  const w = p.w ?? LAST_FULL;
  const win = p.window ?? "L4W";
  const range = (b: any) => (b.weeks.length > 1 ? `W${b.weeks[0]}–W${b.weeks[b.weeks.length - 1]}` : `W${b.weeks[0]}`);
  if (tid === "why_flagged") {
    const ent = String(p.entity);
    const hits = (D.alerts_by_week[String(w)] || []).map((id: string) => D.anomalies.find((a: any) => a.id === id))
      .filter((a: any) => (ent === "retention" ? RETENTION_RULES.includes(a.rule_id) : a.entity.toLowerCase() === ent.toLowerCase()));
    if (!hits.length) return { read: `anomalies.json · by_week[${w}] · entity=${ent}`, answer: `No rule fired for ${ent} in W${w}.`, cols: [], rows: [] };
    return {
      read: `anomalies.json · by_week[${w}] · ${hits.length} rows`,
      answer: `${hits.length} rule${hits.length > 1 ? "s" : ""} fired for ${ent} in W${w}. ${hits.map((h: any) => h.message).join(" ")}`,
      cols: ["Alert", "Severity", "Rule", "Threshold"],
      rows: hits.map((h: any) => [h.id, h.severity, h.rule_id, D.rules.find((r: any) => r.id === h.rule_id).rule]),
    };
  }
  if (tid === "wos_threshold") {
    const rows = D.inventory_by_week.filter((r: any) => r.year === "TY" && r.wk === w && r.wos != null && (p.op === "below" ? r.wos < p.x : r.wos > p.x))
      .sort((a: any, b: any) => (p.op === "below" ? a.wos - b.wos : b.wos - a.wos));
    const trunc = rows.length && rows[0].wos_window_weeks < 4;
    return {
      read: `inventory_by_week · year=TY · wk=${w} · wos ${p.op === "below" ? "<" : ">"} ${p.x} · ${rows.length} rows`,
      answer: rows.length
        ? `${rows.length} famil${rows.length === 1 ? "y has" : "ies have"} weeks of supply ${p.op} ${p.x} in W${w}: ${rows.map((r: any) => `${r.family} at ${fmtWos(r.wos)}`).join(", ")}.${trunc ? " The window is truncated before W26, so these are early readings." : ""}`
        : `No family has weeks of supply ${p.op} ${p.x} in W${w}.`,
      cols: ["Family", "WOS TY", "WOS LY same week", "On hand"], rows: rows.map((r: any) => [r.family, fmtWos(r.wos), fmtWos(r.wos_ly_same_week), fmtNum(r.on_hand_eow)]),
    };
  }
  if (tid === "top_contrib") {
    const n = p.n ?? 5, top = p.dir !== "bottom";
    if (win === "PTD") {
      const rows = [...D.products_ptd].sort((a: any, b: any) => (top ? b.contrib_pts - a.contrib_pts : a.contrib_pts - b.contrib_pts)).slice(0, n);
      return {
        read: `products_ptd · sorted by contrib_pts · ${rows.length} rows`,
        answer: `${top ? "Top" : "Bottom"} ${n} families by contribution to PTD growth: ${rows.map((r: any) => `${r.STYLE_GROUP} (${fmtPts(r.contrib_pts * 100)})`).join(", ")}.`,
        cols: ["Family", "Contribution", "Demand YoY", "Class"], rows: rows.map((r: any) => [r.STYLE_GROUP, fmtPts(r.contrib_pts * 100), fmtPct(r.sales_yoy_pct, true), r.class]),
      };
    }
    const rows = D.products_by_week.filter((r: any) => r.wk === w && r.window === win).sort((a: any, b: any) => (top ? b.contrib_pts - a.contrib_pts : a.contrib_pts - b.contrib_pts)).slice(0, n);
    return {
      read: `products_by_week · wk=${w} · window=${win} · ${rows.length} rows`,
      answer: `${top ? "Top" : "Bottom"} ${n} families by contribution, ${win} ending W${w}: ${rows.map((r: any) => `${r.family} (${fmtPts(r.contrib_pts)})`).join(", ")}.`,
      cols: ["Family", "Contribution", "Demand YoY", "Demand TY"], rows: rows.map((r: any) => [r.family, fmtPts(r.contrib_pts), fmtPct(r.sales_yoy_pct, true), fmtMoney(r.sales_ty)]),
    };
  }
  if (tid === "genz_new") {
    const b = D.trailing[String(w)][win];
    return {
      read: `trailing.${w}.${win} · genz_new, genz_share_of_new`,
      answer: `Gen Z new customers, ${win} ending W${w} (${range(b)}): ${fmtNum(b.genz_new.ty)} vs ${fmtNum(b.genz_new.ly)} LY (${fmtPct(b.genz_new.yoy_pct, true)}), ${fmtPct(b.genz_share_of_new.ty)} of all new customers vs ${fmtPct(b.genz_share_of_new.ly)} LY.`,
      cols: [], rows: [],
    };
  }
  if (tid === "genz_share_trend") {
    const rows = D.genz_weekly.filter((r: any) => r.WK <= w);
    const f = rows[0], l = rows[rows.length - 1];
    return {
      read: `genz_weekly · WK ≤ ${w} · ${rows.length} rows`,
      answer: `Gen Z share of new customers went from ${fmtPct(f.genz_share_of_new_TY)} in W${f.WK} to ${fmtPct(l.genz_share_of_new_TY)} in W${l.WK} (LY that week: ${fmtPct(l.genz_share_of_new_LY)}).${l.WK === D.meta.partial_week ? ` W${l.WK} is a partial week.` : ""}`,
      cols: ["Week", "TY", "LY", "Gen Z new TY"], rows: rows.map((r: any) => [`W${r.WK}${r.WK === D.meta.partial_week ? " (partial)" : ""}`, fmtPct(r.genz_share_of_new_TY), fmtPct(r.genz_share_of_new_LY), fmtNum(r.genz_new_TY)]),
    };
  }
  if (tid === "insider_segments") {
    const rows = [...D.new_insider_by_segment].sort((a: any, b: any) => a.genz_new_insider_rate - b.genz_new_insider_rate);
    const sig = rows.filter((r: any) => r.p < 0.05);
    return {
      read: `new_insider_by_segment · ${rows.length} rows`,
      answer: `Insider attach of new Gen Z vs other new customers (TY), lowest first. The gap is significant (p < 0.05) in ${sig.map((r: any) => `${SEGMENT_NAME[r.segment] || r.segment} (${fmtPct(r.genz_new_insider_rate)} vs ${fmtPct(r.other_new_insider_rate)})`).join(" and ")}.`,
      cols: ["Segment", "Gen Z new", "Other new", "n Gen Z", "p"], rows: rows.map((r: any) => [SEGMENT_NAME[r.segment] || r.segment, fmtPct(r.genz_new_insider_rate), fmtPct(r.other_new_insider_rate), r.genz_new_n, r.p.toFixed(3)]),
    };
  }
  if (tid === "winners") {
    const rows = D.products_ptd.filter((r: any) => r.class !== "Steady").sort((a: any, b: any) => b.sales_yoy_pct - a.sales_yoy_pct);
    return {
      read: `products_ptd · class in (Winner, Decliner) · ${rows.length} rows`,
      answer: `Winners: ${rows.filter((r: any) => r.class === "Winner").map((r: any) => r.STYLE_GROUP).join(", ")}. Decliners: ${rows.filter((r: any) => r.class === "Decliner").map((r: any) => r.STYLE_GROUP).join(", ")}.`,
      cols: ["Family", "Class", "Demand YoY", "Contribution"], rows: rows.map((r: any) => [r.STYLE_GROUP, r.class, fmtPct(r.sales_yoy_pct, true), fmtPts(r.contrib_pts * 100)]),
    };
  }
  const b = D.trailing[String(w)][win];
  const wow = win === "L1W" ? b.wow : null;
  return {
    read: `trailing.${w}.${win}${wow ? ` · trailing.${w}.L1W.wow` : ""}`,
    answer: `${win} ending W${w} (${range(b)}): demand ${fmtMoney(b.sales.ty)} vs ${fmtMoney(b.sales.ly)} LY (${fmtPct(b.sales.yoy_pct, true)}); transactions ${fmtPct(b.txns.yoy_pct, true)}; AOV ${fmtMoney(b.aov.ty, false)} (${fmtPct(b.aov.yoy_pct, true)}).` +
      (wow ? ` Vs the previous week: demand ${fmtPct(wow.sales, true)}, transactions ${fmtPct(wow.txns, true)}, AOV ${fmtPct(wow.aov, true)}.` : ""),
    cols: wow ? ["Metric", "vs previous week"] : [], rows: wow ? [["Demand", fmtPct(wow.sales, true)], ["Transactions", fmtPct(wow.txns, true)], ["AOV", fmtPct(wow.aov, true)]] : [],
  };
}

export default function Ask() {
  const u = useUrl();
  const [input, setInput] = useState("");
  const [answers, setAnswers] = useState<Answer[]>([]);
  const ask = (q: string) => {
    q = q.trim();
    if (!q) return;
    const [tid, params] = parseQuestion(q, u.wk, u.win);
    setAnswers((a) => [tid ? { q, ok: true, tid, params, ...answer(tid, params) } : { q, ok: false }, ...a]);
    setInput("");
  };
  useEffect(() => { if (askBus.pending) { const q = askBus.pending; askBus.pending = ""; ask(q); } }, []); // eslint-disable-line react-hooks/exhaustive-deps
  return (
    <main className="pad-x" style={{ display: "flex", flexWrap: "wrap", gap: 28, padding: "32px 40px 56px" }}>
      <div style={{ flex: "999 1 560px", minWidth: 0 }}>
        <div style={{ display: "flex", gap: 8, padding: 6, background: "#fff", boxShadow: `inset 0 0 0 1.5px ${C.charcoal}` }}>
          <input value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => e.key === "Enter" && ask(input)} aria-label="Ask a question"
            placeholder="Ask about performance, Gen Z, families or stock…" style={{ flex: 1, minWidth: 0, padding: "10px 12px", border: 0, outline: "none", font: "inherit", fontSize: 16, background: "transparent", color: C.ink }} />
          <button onClick={() => ask(input)} style={{ padding: "10px 18px", border: 0, background: C.charcoal, color: "#fff", fontSize: 14, fontWeight: 700 }}>Ask</button>
        </div>
        {answers.length === 0 && (
          <div style={{ marginTop: 28 }}>
            <div style={{ fontFamily: MONO, fontSize: 12, fontWeight: 700 }}>TRY ONE OF THESE</div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(240px,1fr))", gap: 8, marginTop: 12 }}>
              {SUGGESTED.map(([q, g]) => (
                <div key={q} onClick={() => ask(q)} className="panel hov-ring clickable" style={{ padding: 16 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 6, whiteSpace: "nowrap", fontFamily: MONO, fontSize: 10.5, fontWeight: 700, color: C.muted }}>
                    <span style={{ width: 8, height: 8, borderRadius: 2, background: GOALS[g].hue }} />{GOALS[g].id} {GOALS[g].name.toUpperCase()}
                  </div>
                  <div style={{ marginTop: 8, fontSize: 15, fontWeight: 700, lineHeight: 1.35 }}>{q}</div>
                </div>
              ))}
            </div>
            <p style={{ margin: "22px 0 0", maxWidth: 640, fontSize: 13.5, lineHeight: 1.6, color: C.body }}>Questions are matched to a fixed query template. The answer shows which template ran, what it read and the rows it returned. If nothing matches, it says so instead of guessing.</p>
          </div>
        )}
        <div style={{ display: "flex", flexDirection: "column", gap: 16, marginTop: 20 }}>
          {answers.map((a, i) => (
            <article key={answers.length - i} className="panel fade-in">
              <div style={{ padding: "16px 20px", background: C.band, color: "#fff", fontSize: 16, fontWeight: 700 }}>{a.q}</div>
              <div style={{ padding: "18px 20px" }}>
                {a.ok ? (
                  <>
                    <p style={{ margin: 0, fontSize: 16, lineHeight: 1.55 }}>{a.answer}</p>
                    <ol style={{ margin: "16px 0 0", padding: 0, listStyle: "none", display: "flex", flexDirection: "column", gap: 6, fontSize: 13 }}>
                      {[<>Template chosen: <b style={{ fontFamily: MONO, fontSize: 12 }}>{a.tid}({Object.entries(a.params || {}).map(([k, v]) => `${k}=${v}`).join(", ")})</b></>,
                        <>Data read: <b style={{ fontFamily: MONO, fontSize: 12 }}>{a.read}</b></>,
                        <>Values copied from the file, filtered, sorted and formatted. No new arithmetic, no model-written numbers.</>].map((s, k) => (
                        <li key={k} style={{ display: "flex", gap: 10 }}>
                          <span style={{ flex: "0 0 22px", height: 22, display: "grid", placeItems: "center", background: C.sapphire, color: "#fff", fontFamily: MONO, fontSize: 11, fontWeight: 700 }}>{k + 1}</span><span>{s}</span>
                        </li>))}
                    </ol>
                    {a.rows && a.rows.length > 0 && (
                      <div style={{ overflowX: "auto" }}>
                        <table style={{ width: "100%", borderCollapse: "collapse", marginTop: 16, fontSize: 13.5 }}>
                          <thead><tr>{a.cols!.map((c) => <th key={c} style={{ padding: "8px 12px 8px 0", borderBottom: `2px solid ${C.ink}`, textAlign: "left", fontFamily: MONO, fontSize: 11 }}>{c}</th>)}</tr></thead>
                          <tbody>{a.rows.map((r, j) => <tr key={j} style={{ borderBottom: "1px solid rgba(52,64,85,.1)" }}>{r.map((c, k) => <td key={k} style={{ padding: "8px 12px 8px 0", fontFamily: MONO, fontSize: 12.5 }}>{c}</td>)}</tr>)}</tbody>
                        </table>
                      </div>
                    )}
                  </>
                ) : (
                  <p style={{ margin: 0, fontSize: 15, lineHeight: 1.55 }}><b>No template matches this question, so there's no answer.</b> Try one of the templates on the right: weeks of supply, family contributions, Gen Z new customers or share, Insider attach, demand by window, or why something was flagged.</p>
                )}
              </div>
            </article>
          ))}
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
        {answers.length > 0 && <div className="link" onClick={() => setAnswers([])} style={{ marginTop: 14, fontSize: 13, fontWeight: 700 }}>Clear answers</div>}
      </aside>
    </main>
  );
}
