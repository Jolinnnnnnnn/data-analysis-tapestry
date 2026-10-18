import { useEffect, useMemo, useRef, useState } from "react";
import { annotate, validateText } from "../lib/validator.js";
import {
  C, D, DEMOS, GOALS, MONO, SEV, WINDOWED, askBus, checkTitle, fmtNum, fmtPct, fmtWos, goalOfFact, setUrl, useReducedMotion, useUrl, weekAI,
} from "../lib/core";

// ---------- helpers ----------
function getPath(obj: any, path: string): any {
  let cur = obj;
  for (const part of path.match(/[^.[\]]+|\[\d+\]/g) || []) {
    cur = part.startsWith("[") ? cur?.[parseInt(part.slice(1, -1), 10)] : cur?.[part];
  }
  return cur;
}
/** Upstream metrics.json / anomalies.json path for a fact path (written by 15_build_facts.py). */
function sourceOf(path: string, sources: Record<string, string>) {
  return sources[path] || sources[path.split("[")[0].split(".")[0]] || path;
}
function rawStr(v: any) {
  return typeof v === "number" ? String(v) : JSON.stringify(v);
}

// ---------- M8: the summary with its number check ----------
type Phase = "checking" | "done" | "failed" | "folding" | "folded";

function Summary() {
  const u = useUrl();
  const rm = useReducedMotion();
  const w = weekAI(u.wk);
  // a demo (&demo=metric ...) swaps in a pipeline-built variant of this week's summary that one check must stop
  const shown = w.demos[u.demo] || { text: w.summary, citations: w.summary_citations };
  const text: string = shown.text;
  const { segs, res } = useMemo(() => annotate(text, w.facts, shown.citations), [shown, w.facts]); // eslint-disable-line react-hooks/exhaustive-deps
  const nums = segs.filter((s: any) => s.num);
  const blocked = res.status !== "PASS";
  const firstBad = nums.findIndex((s: any) => !s.ok);
  // a claim with no number of its own (e.g. a rank word) fails after the last number has been checked
  const failIdx = !blocked ? -1 : firstBad >= 0 ? firstBad : nums.length;
  const [lit, setLit] = useState(0);
  const [phase, setPhase] = useState<Phase>("checking");
  const [flash, setFlash] = useState(false);
  const [factsOpen, setFactsOpen] = useState(false);
  const [hover, setHover] = useState<null | { i: number; x: number; y: number }>(null);
  const [conn, setConn] = useState<null | { d: string; x2: number; y2: number }>(null);
  const [run, setRun] = useState(0);
  const root = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const timers: any[] = [];
    if (rm) { setLit(blocked ? failIdx : nums.length); setPhase(blocked ? "folded" : "done"); return; }
    setLit(0); setPhase("checking"); setFlash(false);
    let n = 0;
    const iv = setInterval(() => {
      if (blocked && n === failIdx) {
        clearInterval(iv); setPhase("failed"); setFlash(true);
        [140, 280, 420, 560].forEach((ms, k) => timers.push(setTimeout(() => setFlash(k % 2 === 1), ms)));
        timers.push(setTimeout(() => setPhase("folding"), 700), setTimeout(() => setPhase("folded"), 1000));
        return;
      }
      if (!blocked && n + 1 >= nums.length) { clearInterval(iv); setLit(nums.length); setPhase("done"); return; }
      n += 1; setLit(n);
    }, 70);
    timers.push(iv);
    return () => timers.forEach((t) => { clearInterval(t); clearTimeout(t); });
  }, [text, run, rm]); // eslint-disable-line react-hooks/exhaustive-deps

  const failed = phase === "failed" || phase === "folding" || phase === "folded";
  const folded = phase === "folded";
  const factsShown = factsOpen || folded;
  const okCount = failed ? failIdx : phase === "done" ? nums.length : lit;
  const bad = blocked ? res.failures[0] : null; // failures are sorted by position: the first one stops the replay
  const badge = phase === "done"
    ? { bg: "#E3F2E8", ink: C.up, l1: "✓ Every number", l2: `checked · ${res.n_matched}/${res.n_numbers}` }
    : failed ? { bg: C.critTint, ink: C.crit, l1: `◆ ${checkTitle(bad.check)} check failed`, l2: `held back · ${okCount}/${res.n_numbers} ok` }
    : { bg: "#E9EDF7", ink: C.sapphireInk, l1: "Checking numbers", l2: `${lit}/${res.n_numbers}` };
  const src = w.facts._sources || {};
  const rows = nums.map((s: any, i: number) => {
    const fact = s.fact as string | null;
    const value = fact ? getPath(w.facts, fact) : undefined;
    return {
      i, fact, ok: s.ok, checks: s.checks as string[], failures: s.failures as any[], text: s.text.trim(),
      path: fact ? sourceOf(fact, src) : "no citation", raw: value === undefined ? "not in facts" : rawStr(value),
    };
  });

  function enter(i: number, e: React.MouseEvent<HTMLSpanElement>) {
    const R = root.current!.getBoundingClientRect();
    const r = e.currentTarget.getBoundingClientRect();
    const x = r.left - R.left, y = r.bottom - R.top;
    const row = root.current!.querySelector(`[data-fact="${i}"]`);
    if (row) {
      const rr = row.getBoundingClientRect();
      const x1 = x + r.width / 2, x2 = rr.left - R.left + 6, y2 = rr.top - R.top + rr.height / 2;
      setConn({ d: `M ${x1} ${y} C ${x1} ${y + 60}, ${x2 - 60} ${y2}, ${x2} ${y2}`, x2, y2 });
    } else setConn(null);
    setHover({ i, x: Math.max(0, Math.min(x, R.width - 300)), y: y + 8 });
  }
  let k = -1;
  const hv = hover ? rows[hover.i] : null;
  return (
    <div ref={root} style={{ position: "relative", display: "flex", flexWrap: "wrap", gap: "16px 28px" }}>
      <div style={{ flex: "0 0 150px" }}>
        <div style={{ fontFamily: MONO, fontSize: 12, fontWeight: 700 }}>SUMMARY</div>
        <div style={{ marginTop: 4, fontFamily: MONO, fontSize: 12, color: C.muted }}>AI-written from facts</div>
        <div aria-live="polite" style={{ display: "inline-flex", flexDirection: "column", gap: 2, marginTop: 12, padding: "8px 11px", borderRadius: 10, fontSize: 12, fontWeight: 700, transition: "background .25s ease, color .25s ease", background: badge.bg, color: badge.ink }}>
          <span style={{ whiteSpace: "nowrap" }}>{badge.l1}</span><span style={{ whiteSpace: "nowrap" }}>{badge.l2}</span>
        </div>
        <div className="link" onClick={() => setRun((x) => x + 1)} style={{ marginTop: 10, fontSize: 12, fontWeight: 600, color: C.muted }}>Replay check</div>
        <div style={{ marginTop: 14, fontFamily: MONO, fontSize: 10.5, fontWeight: 700, color: C.muted }}>TRY A WRONG TEXT</div>
        {DEMOS.map((d) => (
          <div key={d.id} className="link" onClick={() => setUrl({ demo: u.demo === d.id ? "" : d.id })} title={d.hint}
            style={{ marginTop: 5, fontSize: 12, fontWeight: u.demo === d.id ? 700 : 600, color: u.demo === d.id ? C.crit : C.muted }}>
            {u.demo === d.id ? `✕ ${d.label}` : d.label}
          </div>
        ))}
      </div>
      <div style={{ flex: "1 1 460px", minWidth: 0 }}>
        <div style={{ overflow: "hidden", transition: "max-height .3s ease, opacity .3s ease", maxHeight: phase === "folding" || folded ? 0 : 900, opacity: phase === "folding" || folded ? 0 : 1 }}>
          <p style={{ margin: 0, maxWidth: 800, fontSize: 17, lineHeight: 1.7, textWrap: "pretty" as any }}>
            {segs.map((s: any, j: number) => {
              if (!s.num) return <span key={j}>{s.text}</span>;
              k += 1;
              const i = k;
              const g = s.fact ? goalOfFact(sourceOf(s.fact, src)) : 0;
              const failing = failed && i === failIdx;
              const ok = i < lit || phase === "done";
              let bg = "transparent", color: string = C.ink, shadow = `inset 0 -1.5px 0 ${C.ly}`, weight = 400;
              if (failing) { bg = flash ? C.crit : C.critTint; color = flash ? "#fff" : C.crit; shadow = "none"; weight = 700; }
              else if (ok) { bg = GOALS[g].tint; color = GOALS[g].ink; shadow = "none"; weight = 700; }
              if (hover?.i === i) shadow = `0 0 0 1.5px ${GOALS[g].ink}`;
              return (
                <span key={j} onMouseEnter={(e) => enter(i, e)} onMouseLeave={() => { setHover(null); setConn(null); }}
                  style={{ fontFamily: MONO, fontSize: 15.5, padding: "1px 4px", borderRadius: 3, cursor: "help", transition: "background .18s ease, color .18s ease, box-shadow .18s ease", fontWeight: weight, background: bg, color, boxShadow: shadow }}>{s.text}</span>
              );
            })}
          </p>
        </div>
        {folded && bad && (
          <div className="fade-in" style={{ padding: "18px 20px", background: "#fff", boxShadow: `inset 0 0 0 1.5px ${C.crit}` }}>
            <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
              <span style={{ padding: "4px 8px", borderRadius: 4, background: C.crit, color: "#fff", fontFamily: MONO, fontSize: 11, fontWeight: 700, whiteSpace: "nowrap" }}>◆ HELD BACK</span>
              <b style={{ fontSize: 18 }}>The summary is hidden because {failIdx < nums.length ? "one number" : "one claim"} failed the {checkTitle(bad.check).toLowerCase()} check.</b>
            </div>
            <p style={{ margin: "10px 0 0", fontSize: 14.5, lineHeight: 1.6, color: C.body, maxWidth: 760 }}>
              The AI wrote <b style={{ fontFamily: MONO, color: C.crit }}>{bad.text.trim()}</b>
              {bad.key ? <>, citing <span style={{ fontFamily: MONO, fontWeight: 700 }}>{bad.key}</span>{getPath(w.facts, bad.key) !== undefined && <>{" "}(<span style={{ fontFamily: MONO }}>{sourceOf(bad.key, src)}</span> = <span style={{ fontFamily: MONO }}>{rawStr(getPath(w.facts, bad.key))}</span>)</>}</> : bad.check === "citation" ? " without citing a fact" : ""}.
              {" "}What failed: <span style={{ fontFamily: MONO, fontSize: 13 }}>{bad.detail}</span>.
            </p>
            <p style={{ margin: "8px 0 0", fontSize: 14.5, lineHeight: 1.6, color: C.body, maxWidth: 760 }}>
              Nothing unchecked is shown, so you're seeing the raw facts the AI was given. The flagged items below come from the rules and are unaffected.
            </p>
          </div>
        )}
        <div style={{ display: "flex", alignItems: "center", gap: 16, marginTop: 16, fontSize: 13, flexWrap: "wrap" }}>
          <b className="clickable" onClick={() => setFactsOpen(!factsOpen)}>{factsShown ? "− " : "+ "}Facts used ({res.n_numbers})</b>
          <span style={{ color: C.muted }}>Hover any number to see the fact it cites and the checks it passed. Rules decide what's unusual; the AI words the facts.</span>
        </div>
        {factsShown && (
          <div className="panel fade-in" style={{ marginTop: 12, fontSize: 12.5, overflowX: "auto" }}>
            <div style={{ minWidth: 560 }}>
              <div style={{ display: "grid", gridTemplateColumns: "22px minmax(0,1.7fr) minmax(0,.7fr) minmax(0,.5fr)", gap: 10, padding: "9px 12px", borderBottom: `1.5px solid ${C.ink}`, fontFamily: MONO, fontSize: 10.5, fontWeight: 700 }}>
                <span /><span>CITED FACT · SOURCE</span><span>RAW</span><span>SHOWN</span>
              </div>
              {rows.map((r: any) => {
                const fail = failed && r.i === failIdx;
                const done = phase === "done" || r.i < okCount;
                return (
                  <div key={r.i} data-fact={r.i} style={{ display: "grid", gridTemplateColumns: "22px minmax(0,1.7fr) minmax(0,.7fr) minmax(0,.5fr)", gap: 10, padding: "7px 12px", borderBottom: "1px solid rgba(52,64,85,.08)", transition: "background .15s ease", background: hover?.i === r.i ? "#DCE8FA" : fail ? C.critTint : "transparent" }}>
                    <span style={{ fontWeight: 700, color: fail ? C.crit : done ? C.up : C.ly }}>{fail ? "✗" : done ? "✓" : "·"}</span>
                    <span style={{ fontFamily: MONO, fontSize: 11, overflowWrap: "anywhere" }}>
                      <b style={{ color: fail ? C.crit : C.ink }}>{r.fact ?? "no citation"}</b>
                      {r.fact && r.path !== r.fact && <span style={{ display: "block", color: C.muted }}>{r.path}</span>}
                    </span>
                    <span style={{ fontFamily: MONO, fontSize: 11 }}>{r.raw}</span>
                    <span style={{ fontFamily: MONO, fontSize: 11, fontWeight: 700, color: fail ? C.crit : C.ink }}>{r.text}</span>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
      {conn && factsShown && (
        <svg style={{ position: "absolute", left: 0, top: 0, width: "100%", height: "100%", pointerEvents: "none", overflow: "visible" }}>
          <path d={conn.d} fill="none" stroke={C.sapphire} strokeWidth={1.5} strokeDasharray="4 3" />
          <circle cx={conn.x2} cy={conn.y2} r={3.5} fill={C.sapphire} />
        </svg>
      )}
      {hover && hv && (
        <div style={{ position: "absolute", zIndex: 20, width: 320, padding: "10px 12px", borderRadius: 6, background: C.ink, color: "#fff", font: `400 12px/1.5 ${MONO}`, boxShadow: "0 10px 30px rgba(0,0,0,.25)", pointerEvents: "none", left: hover.x, top: hover.y, overflowWrap: "anywhere" }}>
          <span style={{ display: "block", fontWeight: 700, color: hv.ok ? "#9FE0B8" : C.downOnDark }}>
            {hv.ok ? "✓ cites " : hv.fact ? `✗ ${checkTitle(hv.failures[0]?.check || "citation")} check failed · ` : "✗ no citation"}
            {hv.fact && <span style={{ color: "#fff" }}>{hv.fact}</span>}
          </span>
          {hv.fact && <><span style={{ color: C.onDarkMuted }}>{hv.path}</span><br />= {hv.raw} → {hv.text}</>}
          {!hv.ok && hv.failures[0] && <span style={{ display: "block", marginTop: 4, color: C.downOnDark }}>{hv.failures[0].detail}</span>}
          {hv.checks.length > 0 && <span style={{ display: "block", marginTop: 6, color: C.onDarkMuted }}>checked: {hv.checks.map(checkTitle).join(" · ").toLowerCase()}</span>}
        </div>
      )}
    </div>
  );
}

// ---------- flagged cards ----------
const PILL: Record<string, { label: string; bg: string; ink: string; ring?: string }> = {
  "Needs you today": { label: "◆ CRITICAL", bg: C.crit, ink: "#fff" },
  "Needs you": { label: "▲ WARNING", bg: C.warn, ink: C.warnInk },
  Pattern: { label: "∿ PATTERN", bg: "transparent", ink: C.ink, ring: C.muted },
  Win: { label: "↑ WIN", bg: C.winTint, ink: C.winInk },
  Watch: { label: "◎ WATCH", bg: C.lav1, ink: C.body, ring: C.ly },
};
const CARD_GOAL: Record<string, number> = { stock: 3, retention: 1, pattern: 1, win: 2, overstock: 3 };
const TAB_OF: Record<string, number> = { G1: 0, G2: 1, G3: 2, G4: 3 };

function Bar({ value, max, color, ghost, ghostMax }: { value: number; max: number; color: string; ghost?: number | null; ghostMax?: number }) {
  return (
    <div style={{ position: "relative", height: 9 }}>
      <div style={{ position: "absolute", inset: "0 auto 0 0", width: "100%", background: "#F4F0F8" }} />
      {ghost != null && <div style={{ position: "absolute", inset: "0 auto 0 0", width: `${(ghost / (ghostMax || max)) * 100}%`, background: C.lav3, transition: `width .45s ease` }} />}
      <div style={{ position: "absolute", inset: "0 auto 0 0", width: `${(value / max) * 100}%`, background: color, transition: "width .45s ease" }} />
    </div>
  );
}

function MicroChart({ card }: { card: any }) {
  const u = useUrl();
  const v = card.values;
  const hue = GOALS[CARD_GOAL[card.card_id]].hue;
  const box = { flex: "0 0 240px", alignSelf: "center", display: "flex", flexDirection: "column" as const, gap: 10, fontFamily: MONO, fontSize: 11, color: C.muted };
  const rows = card.chart?.rows || [];
  if (card.card_id === "stock" || card.card_id === "overstock") {
    const fams: [string, any, any][] = [];
    for (let i = 0; i < rows.length; i += 2) fams.push([rows[i].label.split(" · ")[0], rows[i], rows[i + 1]]);
    const max = Math.max(...rows.map((r: any) => r.value || 0));
    const median = v.median_wos;
    return (
      <div style={{ ...box, position: "relative" }}>
        {fams.map(([name, ty, ly]) => (
          <div key={name}>
            <div style={{ display: "flex", justifyContent: "space-between", gap: 8, whiteSpace: "nowrap", marginBottom: 4 }}>
              <b style={{ color: C.ink }}>{name}</b><span>{fmtWos(ty.value)}{u.ly && ly ? ` · LY ${fmtWos(ly.value)}` : ""}</span>
            </div>
            <Bar value={ty.value} max={max} color={hue} ghost={u.ly ? ly?.value : null} />
          </div>
        ))}
        <span>weeks of supply{u.ly ? " · grey = LY" : ""}{median != null ? ` · median ${fmtWos(median)}` : ""}</span>
      </div>
    );
  }
  if (card.card_id === "retention") {
    const pairs: [string, any, any][] = [];
    for (let i = 0; i < rows.length; i += 2) {
      const a = rows[i].label.split(" · "), b = rows[i + 1].label.split(" · ");
      pairs.push([a[0] === b[0] ? a[0] : `${a[0]} vs ${b[0]}`, rows[i], rows[i + 1]]);
    }
    const max = Math.max(...rows.map((r: any) => r.value || 0)) * 1.1;
    const segLegend = rows[1]?.label.includes("other");
    return (
      <div style={box}>
        {pairs.map(([name, a, b]) => {
          const showB = segLegend || u.ly;
          const pa = (a.value / max) * 100, pb = (b.value / max) * 100;
          return (
            <div key={name}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 5 }}><b style={{ color: C.ink }}>{segLegend ? name : `${name.split(" vs ")[0]}`}</b><span>{fmtPct(a.value)}{showB ? ` · ${fmtPct(b.value)}` : ""}</span></div>
              <div style={{ position: "relative", height: 10 }}>
                <div style={{ position: "absolute", left: 0, right: 0, top: 4, height: 1, background: C.lav3 }} />
                {showB && <div style={{ position: "absolute", left: `${Math.min(pa, pb)}%`, width: `${Math.abs(pb - pa)}%`, top: 4, height: 2, background: C.ly }} />}
                <div style={{ position: "absolute", left: `calc(${pa}% - 5px)`, top: 0, width: 10, height: 10, borderRadius: "50%", background: hue, transition: "left .45s ease" }} />
                {showB && <div style={{ position: "absolute", left: `calc(${pb}% - 5px)`, top: 0, width: 10, height: 10, borderRadius: "50%", boxShadow: `inset 0 0 0 2px ${C.ly}`, background: "#fff" }} />}
              </div>
            </div>
          );
        })}
        <span><span style={{ color: GOALS[1].ink }}>● {segLegend ? "Gen Z new" : "TY"}</span> {segLegend ? "○ other new" : u.ly ? "○ LY" : ""} · {card.chart.unit}</span>
      </div>
    );
  }
  if (card.card_id === "pattern") {
    const g = D.genz_weekly.filter((r: any) => r.WK <= u.wk);
    const n = g.length;
    const X = (i: number) => (n === 1 ? 110 : 10 + (i * 200) / (n - 1));
    const Y = (x: number) => 70 - (x / 0.6) * 64;
    const solid = (key: string) => g.filter((r: any) => !(r.WK === D.meta.partial_week)).map((r: any, i: number) => `${X(i)},${Y(r[key])}`).join(" ");
    const dash = (key: string) => (g[n - 1]?.WK === D.meta.partial_week && n > 1 ? `${X(n - 2)},${Y(g[n - 2][key])} ${X(n - 1)},${Y(g[n - 1][key])}` : "");
    return (
      <div style={{ flex: "0 0 240px", alignSelf: "center" }}>
        <svg width="240" height="64" viewBox="0 0 220 76" preserveAspectRatio="none" style={{ display: "block" }} role="img" aria-label="Gen Z share of new customers by week, TY vs LY">
          {u.ly && <><polyline points={solid("genz_share_of_new_LY")} fill="none" stroke={C.ly} strokeWidth={1.5} vectorEffect="non-scaling-stroke" /><polyline points={dash("genz_share_of_new_LY")} fill="none" stroke={C.ly} strokeWidth={1.5} strokeDasharray="3 3" vectorEffect="non-scaling-stroke" /></>}
          <polyline points={solid("genz_share_of_new_TY")} fill="none" stroke={GOALS[1].hue} strokeWidth={2.5} vectorEffect="non-scaling-stroke" />
          <polyline points={dash("genz_share_of_new_TY")} fill="none" stroke={GOALS[1].hue} strokeWidth={2.5} strokeDasharray="3 3" vectorEffect="non-scaling-stroke" />
          {n === 1 && <circle cx={X(0)} cy={Y(g[0].genz_share_of_new_TY)} r={3} fill={GOALS[1].hue} />}
        </svg>
        <div style={{ display: "flex", justifyContent: "space-between", fontFamily: MONO, fontSize: 11, color: C.muted, marginTop: 4 }}>
          <span>W23</span><span style={{ whiteSpace: "nowrap" }}><b style={{ color: GOALS[1].ink }}>TY {fmtPct(v.week_genz_share_of_new_ty, false, 0)}</b>{u.ly ? ` · LY ${fmtPct(v.week_genz_share_of_new_ly, false, 0)}` : ""}</span><span>W{u.wk}</span>
        </div>
      </div>
    );
  }
  if (card.card_id === "win") {
    const max = Math.max(v.ptd_genz_new_ty, v.ptd_genz_new_ly);
    return (
      <div style={{ ...box, gap: 8 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}><span style={{ width: 20 }}>TY</span><div style={{ height: 12, width: `${(v.ptd_genz_new_ty / max) * 150}px`, background: C.charcoal, transition: "width .45s ease" }} /><b style={{ color: C.ink }}>{fmtNum(v.ptd_genz_new_ty)}</b></div>
        {u.ly && <div style={{ display: "flex", alignItems: "center", gap: 8 }}><span style={{ width: 20 }}>LY</span><div style={{ height: 12, width: `${(v.ptd_genz_new_ly / max) * 150}px`, background: C.lav3 }} /><span>{fmtNum(v.ptd_genz_new_ly)}</span></div>}
        <span>Gen Z new customers · PTD (sample)</span>
      </div>
    );
  }
  return null;
}

function Card({ card, rank }: { card: any; rank: number }) {
  const pill = PILL[card.pill];
  const goal = GOALS[CARD_GOAL[card.card_id]];
  const check = validateText(`${card.headline} ${card.body}`, card.values, card.citations);
  const why = check.failures[0];
  const ids = card.anomaly_ids as string[];
  const evidence = [...card.findings.filter((f: string) => f.startsWith("F")), ...ids.slice(0, 2)].join(" · ") + (ids.length > 2 ? ` +${ids.length - 2}` : "");
  return (
    <div className="fade-in" style={{ display: "flex", flexWrap: "wrap", gap: "14px 20px", padding: "22px 0", borderBottom: `1px solid ${C.hair}` }}>
      <span style={{ flex: "0 0 28px", fontFamily: MONO, fontWeight: 700, fontSize: 13 }}>{String(rank).padStart(2, "0")}</span>
      <div style={{ flex: "0 0 140px", display: "flex", flexDirection: "column", gap: 6, alignItems: "flex-start", fontFamily: MONO, fontSize: 11, fontWeight: 700 }}>
        <span style={{ whiteSpace: "nowrap", padding: "4px 8px", borderRadius: 4, background: pill.bg, color: pill.ink, boxShadow: pill.ring ? `inset 0 0 0 1.5px ${pill.ring}` : "none" }}>{pill.label}</span>
        <span style={{ display: "flex", alignItems: "center", gap: 6, whiteSpace: "nowrap", color: C.muted }}><span style={{ width: 8, height: 8, borderRadius: 2, background: goal.hue }} />{goal.id} {goal.name.toUpperCase()}</span>
      </div>
      <div style={{ flex: "1 1 340px", minWidth: 0 }}>
        {check.status === "PASS" ? (
          <>
            <h3 className="cond" style={{ margin: "0 0 6px", fontWeight: 700, fontSize: 21, lineHeight: 1.25, fontStretch: "85%" }}>{card.headline}</h3>
            <p style={{ margin: 0, fontSize: 14.5, lineHeight: 1.6, color: C.body }}>{card.body}</p>
          </>
        ) : (
          <p style={{ margin: 0, fontSize: 14, color: C.crit }}>
            <b>◆ Held back:</b> this item failed the {checkTitle(why.check).toLowerCase()} check at <b style={{ fontFamily: MONO }}>{why.text.trim()}</b>
            {why.key && <> (cites <span style={{ fontFamily: MONO }}>{why.key}</span>)</>}: {why.detail}.
          </p>
        )}
        <div style={{ display: "flex", alignItems: "center", gap: 16, marginTop: 12, fontSize: 13, fontWeight: 700, flexWrap: "wrap" }}>
          <button className={rank === 1 ? "btn-dark" : "btn-line"} onClick={() => setUrl({ screen: "explore", tab: TAB_OF[card.explore_tab] }, true)}>Open details</button>
          <span className="clickable" onClick={() => { askBus.pending = card.ask_prefill; setUrl({ screen: "ask" }, true); }} style={{ whiteSpace: "nowrap" }}>Ask why</span>
          <div style={{ flex: 1 }} />
          <span title={ids.map((i) => D.anomalies.find((a: any) => a.id === i)?.message).join("\n")} style={{ fontFamily: MONO, fontWeight: 400, fontSize: 11, whiteSpace: "nowrap", color: C.muted }}>{evidence}</span>
        </div>
      </div>
      <MicroChart card={card} />
    </div>
  );
}

// ---------- rules + alerts rail ----------
function Rail() {
  const u = useUrl();
  const w = weekAI(u.wk);
  const hits = w.counts.rule_hits;
  const off = u.wk < 26;
  const alerts = (D.alerts_by_week[String(u.wk)] || []).map((id: string) => D.anomalies.find((a: any) => a.id === id));
  const sev = w.counts.n_alerts_by_severity;
  return (
    <aside style={{ flex: "1 1 340px", padding: "36px 30px 40px", background: C.thistle, color: C.ink }}>
      <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", paddingBottom: 10, borderBottom: `2px solid ${C.charcoal}` }}>
        <h3 className="cond" style={{ margin: 0, fontWeight: 800, fontSize: 24 }}>Rules</h3>
        <span style={{ fontFamily: MONO, fontSize: 12 }}>{w.counts.n_rules_fired} of {w.counts.n_rules} fired · W{u.wk}</span>
      </div>
      <div style={{ fontFamily: MONO, fontSize: 12 }}>
        {D.rules.map((r: any) => {
          const n = hits[r.id];
          const isOff = off && WINDOWED.includes(r.id);
          const s = SEV[r.severity as keyof typeof SEV];
          const esc = r.id === "WOS_LOW" && alerts.some((a: any) => a.rule_id === "WOS_LOW" && a.severity === "critical");
          const shown = esc ? SEV.critical : s;
          return (
            <div key={r.id} title={`${r.metric}: ${r.rule} (${r.severity}${r.note ? "; " + r.note : ""})`}
              style={{ display: "grid", gridTemplateColumns: "18px 1fr auto", gap: 4, padding: "7px 6px", borderBottom: "1px solid rgba(52,64,85,.15)", transition: "background .25s ease, opacity .25s ease", background: n ? "rgba(255,255,255,.45)" : "transparent", opacity: isOff ? 0.45 : n ? 1 : 0.75 }}>
              <span style={{ color: n ? shown.color : C.info }}>{n ? shown.icon : "·"}</span>
              <span style={{ fontWeight: n ? 700 : 400, overflowWrap: "anywhere" }}>{r.id}</span>
              <span style={{ fontWeight: 700, whiteSpace: "nowrap" }}>{isOff ? "off" : n ? String(n) : ""}</span>
            </div>
          );
        })}
      </div>
      {off && <div style={{ marginTop: 10, fontSize: 12, lineHeight: 1.5, color: C.body }}>Family and stock rules are off before W26: their trailing 4-week window is truncated.</div>}
      <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", marginTop: 32, paddingBottom: 10, borderBottom: `2px solid ${C.charcoal}` }}>
        <h3 className="cond" style={{ margin: 0, fontWeight: 800, fontSize: 24 }}>Alerts</h3>
        <span style={{ fontFamily: MONO, fontSize: 12 }}>{w.counts.n_alerts} in W{u.wk}</span>
      </div>
      {(["critical", "warning", "info"] as const).map((k) => (
        <div key={k}>
          <div style={{ margin: "14px 0 4px", fontFamily: MONO, fontSize: 11, fontWeight: 700, color: SEV[k].color }}>{SEV[k].icon} {SEV[k].label} · {sev[k]}</div>
          {alerts.filter((a: any) => a.severity === k).map((a: any) => (
            <div key={a.id} style={{ padding: "7px 0", borderBottom: "1px solid rgba(52,64,85,.15)", fontSize: 13.5, lineHeight: 1.4 }}>
              <span style={{ fontFamily: MONO, fontSize: 11.5 }}>{a.id}</span> · {a.message}
            </div>
          ))}
        </div>
      ))}
    </aside>
  );
}

export default function Briefing() {
  const u = useUrl();
  const cards = weekAI(u.wk).cards;
  return (
    <main style={{ display: "flex", flexWrap: "wrap" }} key={u.wk}>
      <div className="pad-x" style={{ flex: "999 1 620px", minWidth: 0, padding: "36px 44px 48px 40px" }}>
        <Summary />
        <div style={{ display: "flex", alignItems: "baseline", gap: 14, flexWrap: "wrap", margin: "44px 0 0", paddingBottom: 12, borderBottom: `2px solid ${C.ink}` }}>
          <h2 className="cond" style={{ margin: 0, fontWeight: 800, fontSize: 30, whiteSpace: "nowrap" }}>Flagged this week</h2>
          <span style={{ fontFamily: MONO, fontSize: 12, color: C.muted }}>{cards.length} items · ranked by rule severity · each worded by Claude, numbers checked</span>
        </div>
        {cards.map((c: any, i: number) => <Card key={c.card_id} card={c} rank={i + 1} />)}
      </div>
      <Rail />
    </main>
  );
}
