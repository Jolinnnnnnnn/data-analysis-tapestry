import { useEffect, useMemo, useRef, useState } from "react";
import {
  C, D, EASE, FIRST_WEEK, GOALS, LAST_FULL, LAST_WEEK, MONO, PARTIAL, PTD_RANGE, SEV, WEEKS, WINDOWED, arrow, fmtMoney, fmtNum, fmtPct, fmtPts, fmtUsd0, fmtWos,
  SEGMENT_NAME, ruleThreshold, setUrl, tone, trailing, useReducedMotion, useUrl, weekAI, wkRange,
} from "../lib/core";
import { PartialNote } from "./Header";

export const drillBus = { weekMode: false };
// implied receipts need a prior snapshot, so they cover the complete weeks after the first one
const RECEIPT_WEEKS = wkRange(FIRST_WEEK + 1, LAST_FULL);

// ---------- shared pieces ----------
function Panel({ title, note, children, style }: { title: string; note?: string; children: any; style?: any }) {
  return (
    <section className="panel" style={{ padding: "22px 24px", minWidth: 0, ...style }}>
      <h2 className="cond" style={{ margin: 0, fontWeight: 800, fontSize: 24 }}>{title}</h2>
      {note && <div style={{ marginTop: 4, fontSize: 13, color: C.muted }}>{note}</div>}
      {children}
    </section>
  );
}

type Col = { key: string; label: string; align?: "l" | "r"; sort?: (r: any) => any; cell: (r: any) => any; color?: (r: any) => string; mono?: boolean; bold?: boolean };
function Table({ title, note, cols, rows, initial, highlight }: { title: string; note?: string; cols: Col[]; rows: any[]; initial: [string, number]; highlight?: (r: any) => boolean }) {
  const [sort, setSort] = useState(initial);
  const col = cols.find((c) => c.key === sort[0])!;
  const sorted = [...rows].sort((a, b) => {
    const A = (col.sort || col.cell)(a), B = (col.sort || col.cell)(b);
    if (A == null) return 1;
    if (B == null) return -1;
    return (typeof A === "string" ? A.localeCompare(B) : A - B) * sort[1];
  });
  return (
    <section className="panel" style={{ overflowX: "auto" }}>
      <div style={{ display: "flex", alignItems: "baseline", gap: 12, padding: "18px 20px 12px", flexWrap: "wrap" }}>
        <h2 className="cond" style={{ margin: 0, fontWeight: 800, fontSize: 22 }}>{title}</h2>
        {note && <span style={{ fontSize: 12.5, color: C.muted }}>{note}</span>}
      </div>
      <table className="tbl" style={{ minWidth: 620 }}>
        <thead><tr>{cols.map((c) => (
          <th key={c.key} style={{ textAlign: c.align === "r" ? "right" : "left" }}
            aria-sort={sort[0] === c.key ? (sort[1] > 0 ? "ascending" : "descending") : "none"}>
            <button type="button" className="btn-plain" onClick={() => setSort([c.key, sort[0] === c.key ? -sort[1] : -1])} style={{ fontWeight: 700 }}>
              {c.label} <span style={{ color: C.sapphireInk }}>{sort[0] === c.key ? (sort[1] > 0 ? "↑" : "↓") : ""}</span>
            </button>
          </th>))}</tr></thead>
        <tbody>{sorted.map((r, i) => (
          <tr key={i} className={highlight?.(r) ? "hl" : ""}>{cols.map((c) => (
            <td key={c.key} style={{ textAlign: c.align === "r" ? "right" : "left", fontFamily: c.mono || c.align === "r" ? MONO : undefined, fontSize: c.align === "r" ? 12.5 : undefined, fontWeight: c.bold ? 700 : c.align === "r" ? 400 : 600, color: c.color ? c.color(r) : C.ink }}>{c.cell(r)}</td>
          ))}</tr>))}</tbody>
      </table>
    </section>
  );
}

function Kpis({ items }: { items: { label: string; value: string; delta: string; color?: string }[] }) {
  return (
    <div className="panel" style={{ overflow: "hidden" }}>
      {/* one row when they fit, else half a row each (6 → 3 + 3, never 5 + 1), then pairs on a phone */}
      <div className="kpi-grid" style={{ "--n": items.length, "--mid": Math.ceil(items.length / 2) } as any}>
        {items.map((k) => (
          <div key={k.label} style={{ padding: "16px 18px", boxShadow: `1px 1px 0 ${C.hair}` }}>
            <div style={{ fontSize: 12, fontWeight: 600, color: C.muted }}>{k.label}</div>
            <div className="cond swap" style={{ marginTop: 6, fontWeight: 700, fontSize: 28, fontStretch: "80%" }}>{k.value}</div>
            <div style={{ fontFamily: MONO, fontSize: 12, color: k.color || C.muted }}>{k.delta}</div>
          </div>
        ))}
      </div>
      <PartialNote />
    </div>
  );
}

function Seg({ opts, value, onChange, dark }: { opts: [string, string][]; value: string; onChange: (v: string) => void; dark?: boolean }) {
  return (
    <div className="seg" role="radiogroup" style={{ background: C.lav2 }}>
      {opts.map(([v, l]) => (
        <button type="button" key={v} role="radio" aria-checked={value === v} className="btn-plain" onClick={() => onChange(v)} style={{ background: value === v ? (dark ? C.charcoal : C.charcoal) : "transparent", color: value === v ? "#fff" : C.ink, fontWeight: 700 }}>{l}</button>
      ))}
    </div>
  );
}

const yTicks = (lo: number, hi: number) => {
  const step = Math.ceil((hi - lo) / 4 / 10000) * 10000; // axis geometry: round $10K steps
  const out: number[] = [];
  for (let v = Math.ceil(lo / step) * step; v <= hi; v += step) out.push(v);
  return out;
};

// ---------- G1: M1 season playhead ----------
function Playhead() {
  const u = useUrl();
  const wk = D.weekly as any[];
  const n = wk.length;
  const [p, setP] = useState(u.wk - WEEKS[0]);
  const [playing, setPlaying] = useState(false);
  const raf = useRef(0);
  const paused = useRef(false);
  const lastWk = useRef(u.wk);
  useEffect(() => { if (!playing) { setP(u.wk - WEEKS[0]); lastWk.current = u.wk; } }, [u.wk]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => () => cancelAnimationFrame(raf.current), []);
  const setWeekFromP = (np: number) => {
    const w = WEEKS[0] + Math.round(np);
    if (w !== lastWk.current) { lastWk.current = w; setUrl({ wk: w }); }
  };
  const moved = useRef(false);
  const seek = (np: number) => {
    cancelAnimationFrame(raf.current); setPlaying(false); paused.current = true;
    const v = Math.max(0, Math.min(n - 1, np));
    setP(v); setWeekFromP(v);
  };
  function play() {
    if (playing) { cancelAnimationFrame(raf.current); setPlaying(false); paused.current = true; return; }
    const p0 = paused.current && p < n - 1 ? p : 0; // replay the season unless resuming a pause
    paused.current = false;
    const t0 = performance.now() - p0 * 900;
    setPlaying(true);
    const step = (t: number) => {
      let np = Math.max(0, (t - t0) / 900); // rAF timestamps can precede t0 slightly
      const end = np >= n - 1;
      if (end) np = n - 1;
      setP(np); setWeekFromP(np);
      if (end) setPlaying(false); else raf.current = requestAnimationFrame(step);
    };
    raf.current = requestAnimationFrame(step);
  }
  const vals = [...wk.map((r) => r.sales.ty), ...wk.map((r) => r.sales.ly), D.meta.ly_w30_full_week_sales];
  const lo = Math.floor((Math.min(...vals) * 0.85) / 10000) * 10000, hi = Math.ceil((Math.max(...vals) * 1.05) / 10000) * 10000;
  const X = (i: number) => 60 + i * ((760 - 60) / (n - 1));
  const Y = (v: number) => 250 - ((v - lo) / (hi - lo)) * 220;
  const full = n - 2; // index of last full week (W29); W30 is partial
  const pi = Math.max(0, Math.floor(p)), pf = Math.max(0, p - pi);
  const at = (i: number) => wk[Math.max(0, Math.min(i, n - 1))].sales.ty;
  const yAt = pi >= n - 1 ? Y(at(n - 1)) : Y(at(pi)) + (Y(at(pi + 1)) - Y(at(pi))) * pf; // drawing geometry only
  const solid: string[] = [];
  for (let i = 0; i <= Math.min(pi, full); i++) solid.push(`${X(i)},${Y(at(i))}`);
  let dash = "";
  if (p <= full) solid.push(`${X(p)},${yAt}`); else dash = `${X(full)},${Y(at(full))} ${X(p)},${yAt}`;
  const cur = wk[Math.max(0, Math.min(n - 1, Math.round(p)))];
  const events = D.timeline as any[];
  const evIdx = (e: any) => WEEKS.indexOf(e.wk);
  const sevColor = (s: string) => (s === "critical" ? C.crit : s === "warning" ? "#B98900" : C.charcoal);
  const hits = weekAI(cur.wk).counts.rule_hits;
  return (
    <section className="panel" style={{ padding: "22px 24px" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 16, flexWrap: "wrap" }}>
        <div style={{ flex: "1 1 260px" }}>
          <h2 className="cond" style={{ margin: 0, fontWeight: 800, fontSize: 26 }}>Season so far: weekly demand</h2>
          <div style={{ marginTop: 4, fontSize: 13, color: C.muted }}>Press play to replay W{FIRST_WEEK}→W{LAST_WEEK}, or drag the playhead. Where it stops is the selected week for the whole dashboard. Click a point to see that week's family contributions.</div>
        </div>
        <button onClick={play} style={{ display: "flex", alignItems: "center", gap: 8, padding: "9px 16px", border: 0, borderRadius: 6, background: C.sapphire, color: "#fff", fontSize: 14, fontWeight: 700 }}>
          {playing ? "❚❚ Pause" : p >= n - 1 ? "▶ Replay season" : "▶ Play"}
        </button>
      </div>
      <svg viewBox="0 0 800 290" width="100%" style={{ display: "block", overflow: "visible", marginTop: 14 }} role="img" aria-label="Weekly demand TY vs LY with alert events">
        {yTicks(lo, hi).map((v) => (
          <g key={v}><line x1={50} x2={770} y1={Y(v)} y2={Y(v)} stroke="rgba(52,64,85,.12)" /><text x={44} y={Y(v) + 4} textAnchor="end" fontFamily="Space Mono" fontSize={11} fill={C.muted}>${Math.round(v / 1000)}K</text></g>
        ))}
        {wk.map((r, i) => (
          <text key={r.wk} x={X(i)} y={282} textAnchor="middle" fontFamily="Space Mono" fontSize={11} fill={r.wk === cur.wk ? C.ink : C.muted} fontWeight={r.wk === cur.wk ? 700 : 400}>W{r.wk}{r.is_partial ? " ◔" : ""}</text>
        ))}
        {u.ly && (
          <g>
            <polyline points={wk.slice(0, full + 1).map((r, i) => `${X(i)},${Y(r.sales.ly)}`).join(" ")} fill="none" stroke={C.ly} strokeWidth={2} strokeOpacity={0.75} />
            <polyline points={`${X(full)},${Y(wk[full].sales.ly)} ${X(n - 1)},${Y(wk[n - 1].sales.ly)}`} fill="none" stroke={C.ly} strokeWidth={2} strokeOpacity={0.75} strokeDasharray="5 5" />
            <circle cx={X(n - 1)} cy={Y(D.meta.ly_w30_full_week_sales)} r={5} fill="#fff" stroke={C.ly} strokeWidth={1.5}><title>LY W{PARTIAL} full week (7 days, not like-for-like): {fmtMoney(D.meta.ly_w30_full_week_sales)}</title></circle>
            <text x={X(n - 1) + 9} y={Y(D.meta.ly_w30_full_week_sales) + 4} fontFamily="Space Mono" fontSize={10.5} fill={C.muted}>LY full wk</text>
            <text x={X(n - 1) + 9} y={Y(wk[n - 1].sales.ly) + 4} fontFamily="Space Mono" fontSize={11} fill={C.muted}>LY</text>
          </g>
        )}
        <polyline points={solid.join(" ")} fill="none" stroke={C.sapphire} strokeWidth={3.5} strokeLinejoin="round" strokeLinecap="round" />
        {dash && <polyline points={dash} fill="none" stroke={C.sapphire} strokeWidth={3.5} strokeDasharray="6 6" strokeLinecap="round" />}
        <line x1={X(p)} x2={X(p)} y1={14} y2={262} stroke={C.ink} strokeWidth={1.5} />
        <circle cx={X(p)} cy={yAt} r={6} fill={C.sapphire} stroke="#fff" strokeWidth={2} />
        {events.map((e, k) => {
          const i = evIdx(e);
          return (
            <g key={e.wk} style={{ transition: "opacity .25s ease", opacity: p >= i - 0.001 ? 1 : 0 }}>
              <circle cx={X(i)} cy={Y(at(i)) - 24} r={11} fill={sevColor(e.severity)} />
              <text x={X(i)} y={Y(at(i)) - 24} textAnchor="middle" dominantBaseline="central" fontFamily="Space Mono" fontSize={12} fontWeight={700} fill="#fff">{k + 1}</text>
            </g>
          );
        })}
        {wk.map((r, i) => (
          <circle key={r.wk} cx={X(i)} cy={Y(r.sales.ty)} r={12} fill="transparent" style={{ cursor: "pointer" }}
            onClick={() => { cancelAnimationFrame(raf.current); setPlaying(false); drillBus.weekMode = true; setUrl({ wk: r.wk, screen: "explore", tab: 2 }); }}>
            <title>W{r.wk}: {fmtMoney(r.sales.ty)} TY vs {fmtMoney(r.sales.ly)} LY ({fmtPct(r.sales.yoy_pct, true)}). Click for family contributions.</title>
          </circle>
        ))}
        {/* playhead handle: drag (or arrow keys) to scrub; a tap without dragging drills into that week like the points */}
        <rect x={X(p) - 14} y={14} width={28} height={248} fill="transparent" style={{ cursor: "ew-resize", touchAction: "none" }}
          tabIndex={0} role="slider" aria-label="Playhead week" aria-valuemin={WEEKS[0]} aria-valuemax={WEEKS[n - 1]} aria-valuenow={cur.wk} aria-valuetext={`W${cur.wk}`}
          onPointerDown={(e) => { e.currentTarget.setPointerCapture(e.pointerId); moved.current = false; }}
          onPointerMove={(e) => {
            if (!e.currentTarget.hasPointerCapture(e.pointerId)) return;
            moved.current = true;
            const r = e.currentTarget.ownerSVGElement!.getBoundingClientRect();
            seek(((e.clientX - r.left) * (800 / r.width) - 60) / ((760 - 60) / (n - 1))); // screen x -> viewBox x -> week index
          }}
          onClick={() => { if (!moved.current) { seek(Math.round(p)); drillBus.weekMode = true; setUrl({ screen: "explore", tab: 2 }); } }}
          onKeyDown={(e) => {
            const d = e.key === "ArrowRight" || e.key === "ArrowUp" ? 1 : e.key === "ArrowLeft" || e.key === "ArrowDown" ? -1 : 0;
            if (d) { e.preventDefault(); seek(Math.round(p) + d); }
            if (e.key === "Enter") { e.preventDefault(); drillBus.weekMode = true; setUrl({ screen: "explore", tab: 2 }); }
          }} />
        <text x={X(p) > 620 ? X(p) - 14 : X(p) + 12} y={yAt + (X(p) > 620 ? 22 : -12)} textAnchor={X(p) > 620 ? "end" : "start"} fontFamily="Space Mono" fontSize={12} fontWeight={700} fill={C.sapphireInk}>TY {fmtMoney(cur.sales.ty)}</text>
      </svg>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(170px,1fr))", gap: 8, marginTop: 16 }}>
        {events.map((e, k) => {
          const vis = p >= evIdx(e) - 0.001;
          return (
            <div key={e.wk} style={{ padding: "12px 14px", transition: "opacity .25s ease, transform .25s ease", background: vis ? C.page : "#FBFAFD", opacity: vis ? 1 : 0.25, transform: vis ? "none" : "translateY(4px)" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, fontFamily: MONO, fontSize: 11, fontWeight: 700 }}>
                <span style={{ flex: "none", width: 18, height: 18, borderRadius: "50%", display: "grid", placeItems: "center", color: "#fff", background: sevColor(e.severity) }}>{k + 1}</span>W{e.wk}
              </div>
              <div style={{ marginTop: 4, minHeight: 14, fontFamily: MONO, fontSize: 10.5, fontWeight: 700, color: e.severity === "critical" ? C.crit : C.warnText }}>
                {SEV[e.severity as keyof typeof SEV].icon} {e.tag || e.severity}
              </div>
              <div style={{ marginTop: 8, fontSize: 13, lineHeight: 1.4 }}>{e.message}</div>
              <div style={{ marginTop: 4, fontFamily: MONO, fontSize: 10.5, color: C.muted }}>{e.anomaly_id} · {e.rule_id}</div>
            </div>
          );
        })}
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginTop: 16, flexWrap: "wrap" }}>
        <span style={{ fontFamily: MONO, fontSize: 11, fontWeight: 700, whiteSpace: "nowrap" }}>RULES · W{cur.wk} · {weekAI(cur.wk).counts.n_alerts} ALERTS</span>
        <div style={{ display: "flex", gap: 3, flex: 1, minWidth: 280 }}>
          {D.rules.map((r: any) => {
            const off = cur.wk < 26 && WINDOWED.includes(r.id);
            const fired = (D.alerts_by_week[String(cur.wk)] || []).map((id: string) => D.anomalies.find((a: any) => a.id === id)).filter((a: any) => a.rule_id === r.id);
            const worst = fired.some((a: any) => a.severity === "critical") ? "critical" : fired.some((a: any) => a.severity === "warning") ? "warning" : "info";
            const bg = hits[r.id] ? SEV[worst].cell : off ? "repeating-linear-gradient(135deg,#E9E4EF 0 3px,#fff 3px 6px)" : C.lav3;
            return <div key={r.id} title={`${r.id}${hits[r.id] ? " · " + hits[r.id] : off ? " · off (truncated window)" : ""}`} style={{ flex: 1, height: 14, borderRadius: 2, transition: "background .2s ease", background: bg }} />;
          })}
        </div>
      </div>
    </section>
  );
}

function G1() {
  const u = useUrl();
  const b = trailing(u.wk, u.win);
  return (
    <>
      <Kpis items={[
        ["Demand", fmtMoney(b.sales.ty), b.sales], ["Transactions", fmtNum(b.txns.ty), b.txns], ["AOV", fmtMoney(b.aov.ty, false), b.aov],
        ["UPT", fmtNum(b.upt.ty, 2), b.upt], ["AUR", fmtMoney(b.aur.ty, false), b.aur], ["Customers", fmtNum(b.customers.ty), b.customers],
      ].map(([label, value, blk]: any) => ({ label: `${label} · ${u.win}`, value, delta: `${arrow(blk.yoy_pct)}${fmtPct(blk.yoy_pct, true)} YoY`, color: tone(blk.yoy_pct) }))} />
      <Playhead />
      <Table title="Weekly demand" note={`TY vs LY like-for-like. W${PARTIAL} is partial on both sides.`} initial={["wk", 1]} highlight={(r) => r.wk === u.wk}
        rows={D.weekly.map((r: any) => ({ ...r, alerts: weekAI(r.wk).counts.n_alerts }))}
        cols={[
          { key: "wk", label: "Week", sort: (r) => r.wk, cell: (r) => `W${r.wk}${r.is_partial ? " · partial" : ""}` },
          { key: "ty", label: "Demand TY", align: "r", sort: (r) => r.sales.ty, cell: (r) => fmtMoney(r.sales.ty) },
          ...(u.ly ? [{ key: "ly", label: "Demand LY", align: "r", sort: (r: any) => r.sales.ly, cell: (r: any) => fmtMoney(r.sales.ly), color: () => C.muted } as Col] : []),
          { key: "yoy", label: "YoY", align: "r", sort: (r) => r.sales.yoy_pct, cell: (r) => fmtPct(r.sales.yoy_pct, true), color: (r) => tone(r.sales.yoy_pct) },
          { key: "txn", label: "Txns YoY", align: "r", sort: (r) => r.txns.yoy_pct, cell: (r) => fmtPct(r.txns.yoy_pct, true), color: (r) => tone(r.txns.yoy_pct) },
          { key: "aov", label: "AOV YoY", align: "r", sort: (r) => r.aov.yoy_pct, cell: (r) => fmtPct(r.aov.yoy_pct, true), color: (r) => tone(r.aov.yoy_pct) },
          { key: "alerts", label: "Alerts", align: "r", sort: (r) => r.alerts, cell: (r) => r.alerts },
        ]} />
    </>
  );
}

// ---------- G2 ----------
function MorphShare() {
  const u = useUrl();
  const rm = useReducedMotion();
  const s = trailing(u.wk, "PTD").genz_share_of_new;
  const [state, setState] = useState<"LY" | "TY">(rm ? "TY" : "LY");
  const replay = () => { setState("LY"); setTimeout(() => setState("TY"), rm ? 0 : 450); };
  useEffect(replay, [u.wk]); // eslint-disable-line react-hooks/exhaustive-deps
  const val = state === "TY" ? s.ty : s.ly;
  return (
    <Panel title="Gen Z share of new · PTD" note={`${wkRange(FIRST_WEEK, u.wk)}. The bar moves from its LY value to TY when the comparison loads.`} style={{ flex: "1 1 300px" }}>
      <div style={{ marginTop: 24, overflow: "hidden" }}><span key={state} className="cond swap" style={{ fontWeight: 800, fontSize: 56, color: GOALS[1].ink, display: "inline-block" }}>{fmtPct(val)}</span></div>
      <div style={{ fontFamily: MONO, fontSize: 12, color: C.muted }}>{state === "TY" ? `TY · ${fmtPts(s.chg_pts)} vs LY` : "LY"}</div>
      <div style={{ position: "relative", height: 22, marginTop: 10, background: C.lav3 }}>
        <div style={{ position: "absolute", inset: "0 auto 0 0", transition: `width .45s ${EASE}`, background: GOALS[1].hue, width: `${val * 100}%` }} />
        <div style={{ position: "absolute", top: -6, bottom: -6, left: `${s.ly * 100}%`, borderLeft: `2px solid ${C.ink}` }} />
      </div>
      <div style={{ display: "flex", justifyContent: "space-between", marginTop: 8, fontFamily: MONO, fontSize: 11, color: C.muted }}><span>0%</span><span>LY {fmtPct(s.ly)}</span><span>100%</span></div>
      <button onClick={replay} className="btn-line" style={{ marginTop: 18 }}>Replay LY → TY</button>
      <p style={{ margin: "18px 0 0", fontSize: 12.5, lineHeight: 1.5, color: C.body }}>Retention figures on this tab are a proxy: CUST_ID does not link customers across years, so "returning" uses the brand's cohort status.</p>
    </Panel>
  );
}

function G2() {
  const u = useUrl();
  const b = trailing(u.wk, u.win);
  const ptd = trailing(u.wk, "PTD");
  const g = D.genz_weekly as any[];
  const X = (i: number) => 60 + i * (700 / (g.length - 1));
  const Y = (v: number) => 230 - (v / 0.6) * 210;
  const last = g.length - 1;
  return (
    <>
      <Kpis items={[
        { label: `Gen Z new · ${u.win}`, value: fmtNum(b.genz_new.ty), delta: `${arrow(b.genz_new.yoy_pct)}${fmtPct(b.genz_new.yoy_pct, true)} vs ${fmtNum(b.genz_new.ly)} LY`, color: tone(b.genz_new.yoy_pct) },
        { label: `Gen Z share of new · ${u.win}`, value: fmtPct(b.genz_share_of_new.ty), delta: `${fmtPts(b.genz_share_of_new.chg_pts)} vs ${fmtPct(b.genz_share_of_new.ly)} LY`, color: tone(b.genz_share_of_new.chg_pts) },
        { label: `Gen Z share of new · PTD`, value: fmtPct(ptd.genz_share_of_new.ty), delta: `${fmtPts(ptd.genz_share_of_new.chg_pts)} vs ${fmtPct(ptd.genz_share_of_new.ly)} LY`, color: tone(ptd.genz_share_of_new.chg_pts) },
        { label: `New Gen Z Insider attach · ${u.win}`, value: fmtPct(b.genz_new_insider_rate.ty), delta: `${fmtPts(b.genz_new_insider_rate.chg_pts)} vs ${fmtPct(b.genz_new_insider_rate.ly)} LY`, color: tone(b.genz_new_insider_rate.chg_pts) },
        { label: `Returning Gen Z · ${u.win} (proxy)`, value: fmtNum(b.genz_returning.ty), delta: `${fmtPct(b.genz_returning.yoy_pct, true)} vs ${fmtNum(b.genz_returning.ly)} LY`, color: tone(b.genz_returning.yoy_pct) },
      ]} />
      <div style={{ display: "flex", flexWrap: "wrap", gap: 18 }}>
        <Panel title="Gen Z share of new customers, by week" note={`TY above LY in every week. W${PARTIAL} is partial (dotted).`} style={{ flex: "999 1 520px" }}>
          <svg viewBox="0 0 800 270" width="100%" style={{ display: "block", marginTop: 12, overflow: "visible" }} role="img" aria-label="Gen Z share of new customers by week">
            {[0, 0.2, 0.4, 0.6].map((v) => <g key={v}><line x1={50} x2={770} y1={Y(v)} y2={Y(v)} stroke="rgba(52,64,85,.12)" /><text x={44} y={Y(v) + 4} textAnchor="end" fontFamily="Space Mono" fontSize={11} fill={C.muted}>{v * 100}%</text></g>)}
            <rect x={X(u.wk - WEEKS[0]) - 30} y={14} width={60} height={220} fill={GOALS[1].tint} opacity={0.6} />
            {g.map((r, i) => <text key={r.WK} x={X(i)} y={262} textAnchor="middle" fontFamily="Space Mono" fontSize={11} fill={C.muted}>W{r.WK}</text>)}
            {u.ly && <>
              <polyline points={g.slice(0, last).map((r, i) => `${X(i)},${Y(r.genz_share_of_new_LY)}`).join(" ")} fill="none" stroke={C.ly} strokeWidth={2} strokeOpacity={0.75} />
              <polyline points={`${X(last - 1)},${Y(g[last - 1].genz_share_of_new_LY)} ${X(last)},${Y(g[last].genz_share_of_new_LY)}`} fill="none" stroke={C.ly} strokeWidth={2} strokeDasharray="5 5" />
              <text x={X(last) + 10} y={Y(g[last].genz_share_of_new_LY) + 4} fontFamily="Space Mono" fontSize={12} fill={C.muted}>LY</text>
            </>}
            <polyline points={g.slice(0, last).map((r, i) => `${X(i)},${Y(r.genz_share_of_new_TY)}`).join(" ")} fill="none" stroke={GOALS[1].hue} strokeWidth={3.5} strokeLinejoin="round" />
            <polyline points={`${X(last - 1)},${Y(g[last - 1].genz_share_of_new_TY)} ${X(last)},${Y(g[last].genz_share_of_new_TY)}`} fill="none" stroke={GOALS[1].hue} strokeWidth={3.5} strokeDasharray="6 6" />
            {g.map((r, i) => <g key={r.WK}><circle cx={X(i)} cy={Y(r.genz_share_of_new_TY)} r={4} fill={GOALS[1].hue} /><text x={X(i)} y={Y(r.genz_share_of_new_TY) - 10} textAnchor="middle" fontFamily="Space Mono" fontSize={10.5} fill={GOALS[1].ink} fontWeight={r.WK === u.wk ? 700 : 400}>{fmtPct(r.genz_share_of_new_TY, false, 0)}</text></g>)}
          </svg>
        </Panel>
        <MorphShare />
      </div>
      <Table title="New-customer Insider attach by segment" note="TY, full period. Gen Z new vs other new customers; p from a two-proportion test." initial={["genz", 1]}
        rows={D.new_insider_by_segment}
        cols={[
          { key: "seg", label: "Segment", cell: (r) => SEGMENT_NAME[r.segment] || r.segment },
          { key: "dim", label: "Dimension", cell: (r) => r.dimension.replace("_", " ").toLowerCase(), color: () => C.muted },
          { key: "n", label: "Gen Z new n", align: "r", sort: (r) => r.genz_new_n, cell: (r) => r.genz_new_n },
          { key: "genz", label: "Gen Z new rate", align: "r", sort: (r) => r.genz_new_insider_rate, cell: (r) => fmtPct(r.genz_new_insider_rate), color: () => GOALS[1].ink, bold: true },
          { key: "other", label: "Other new rate", align: "r", sort: (r) => r.other_new_insider_rate, cell: (r) => fmtPct(r.other_new_insider_rate), color: () => C.muted },
          { key: "p", label: "p-value", align: "r", sort: (r) => r.p, cell: (r) => r.p.toFixed(3), color: (r) => (r.p < 0.05 ? C.down : C.muted) },
        ]} />
      <Table title="New vs returning customers by generation" note={`PTD ${PTD_RANGE}. Returning is a mix proxy (no customer key across years).`} initial={["new", -1]}
        rows={D.generation_ptd}
        cols={[
          { key: "g", label: "Generation", cell: (r) => r.generation, bold: true },
          { key: "new", label: "New TY", align: "r", sort: (r) => r.new_TY, cell: (r) => fmtNum(r.new_TY) },
          ...(u.ly ? [{ key: "newly", label: "New LY", align: "r", sort: (r: any) => r.new_LY, cell: (r: any) => fmtNum(r.new_LY), color: () => C.muted } as Col] : []),
          { key: "newyoy", label: "New YoY", align: "r", sort: (r) => r.new_yoy_pct, cell: (r) => fmtPct(r.new_yoy_pct, true), color: (r) => tone(r.new_yoy_pct) },
          { key: "ret", label: "Returning TY", align: "r", sort: (r) => r.returning_TY, cell: (r) => fmtNum(r.returning_TY) },
          { key: "retyoy", label: "Returning YoY", align: "r", sort: (r) => r.returning_yoy_pct, cell: (r) => fmtPct(r.returning_yoy_pct, true), color: (r) => tone(r.returning_yoy_pct) },
          { key: "share", label: "Share of all new", align: "r", sort: (r) => r.new_share_of_all_new_TY, cell: (r) => fmtPct(r.new_share_of_all_new_TY) },
        ]} />
    </>
  );
}

// ---------- G3: M3 growth drill-down ----------
type Block = { label: string; val: string; sub: string; w: number; next?: number | "styles"; family?: string; dark?: boolean };

function Drill() {
  const u = useUrl();
  const rm = useReducedMotion();
  const gd = D.growth_drill;
  const [weekMode, setWeekMode] = useState(drillBus.weekMode);
  const [level, setLevel] = useState(weekMode ? 2 : 0);
  const [family, setFamily] = useState("Tabby");
  const [zoom, setZoom] = useState<number | null>(null);
  useEffect(() => { drillBus.weekMode = false; }, []);
  const win = u.win === "PTD" ? "L1W" : u.win;
  const weekRows = useMemo(() => D.products_by_week.filter((r: any) => r.wk === u.wk && r.window === win), [u.wk, win]);
  let blocks: Block[] = [];
  let drags: { label: string; w: number }[] = [];
  let note = "";
  if (weekMode) {
    const gain = weekRows.filter((r: any) => r.contrib_pts > 0).sort((a: any, b: any) => b.contrib_pts - a.contrib_pts);
    blocks = gain.slice(0, 5).map((r: any) => ({ label: r.family, val: fmtPts(r.contrib_pts), sub: `demand ${fmtPct(r.sales_yoy_pct, true)}`, w: r.contrib_pts }));
    drags = weekRows.filter((r: any) => r.contrib_pts < 0).sort((a: any, b: any) => a.contrib_pts - b.contrib_pts).slice(0, 4).map((r: any) => ({ label: `${r.family} ${fmtPts(r.contrib_pts)}`, w: -r.contrib_pts }));
    note = `Contribution to YoY demand growth, ${win} ending W${u.wk}, in percentage points. Largest five gainers shown; the full list is in the table below.`;
  } else if (level === 0) {
    blocks = [{ label: `Demand · PTD ${PTD_RANGE}`, val: fmtPct(gd.total.yoy_pct, true), sub: `${fmtUsd0(gd.total.ty)} vs ${fmtUsd0(gd.total.ly)}`, w: 1, next: 1, dark: true }];
    note = "Full period, like-for-like (independent of the selected week). Click the bar to break demand growth into its drivers.";
  } else if (level === 1) {
    blocks = gd.drivers.map((d: any, i: number) => ({ label: d.label, val: fmtPct(d.share_of_growth, false, 0), sub: d.pct_chg != null ? `of growth · ${fmtPct(d.pct_chg, true)}` : "of growth", w: Math.max(d.share_of_growth, 0.04), next: i === 0 ? 2 : undefined, dark: i === 0 }));
    note = `Log decomposition of PTD growth (${PTD_RANGE}, like-for-like). Click 'More customers' to see which families carried it.`;
  } else if (level === 2) {
    const fam = (n: string) => gd.families.find((f: any) => f.family === n);
    blocks = [
      { label: "Tabby", val: fmtPct(fam("Tabby").share_of_growth, false, 0), sub: `demand ${fmtPct(fam("Tabby").sales_yoy_pct, true)}`, w: fam("Tabby").share_of_growth, next: "styles", family: "Tabby", dark: true },
      { label: "Pillow Tabby", val: fmtPct(fam("Pillow Tabby").share_of_growth, false, 0), sub: `demand ${fmtPct(fam("Pillow Tabby").sales_yoy_pct, true)}`, w: fam("Pillow Tabby").share_of_growth, next: "styles", family: "Pillow Tabby", dark: true },
      { label: "Other gaining families", val: fmtPct(gd.other_gainers_share_of_growth, false, 0), sub: "of growth", w: gd.other_gainers_share_of_growth },
    ];
    drags = gd.families.filter((f: any) => f.share_of_growth < 0).sort((a: any, b: any) => a.share_of_growth - b.share_of_growth).slice(0, 4)
      .map((f: any) => ({ label: `${f.family} ${fmtPct(f.share_of_growth, true, 0)}`, w: -f.share_of_growth }));
    note = `Share of PTD growth by family. Tabby and Pillow Tabby together: ${fmtPct(gd.hero_share_of_growth, false, 0)}. Declining families offset ${fmtPct(-gd.drags_share_of_growth, false, 0)}. Click Tabby or Pillow Tabby for styles.`;
  } else {
    const st = gd.styles[family];
    blocks = st.styles.map((s: any) => ({ label: s.style, val: fmtPct(s.share_of_growth, false, 0), sub: `style demand ${fmtPct(s.sales_yoy_pct, true)}`, w: s.share_of_growth }));
    if (Math.abs(st.other_styles_share_of_growth) >= 0.005) blocks.push({ label: `Other ${family} styles`, val: fmtPct(st.other_styles_share_of_growth, false, 0), sub: "below the volume threshold", w: Math.abs(st.other_styles_share_of_growth) });
    note = `${family} styles: share of total PTD growth (the family is ${fmtPct(st.family_share_of_growth, false, 0)}).`;
  }
  // Widths encode share of growth, but a tiny share would leave no room for its label: each block keeps a floor wide
  // enough to read, and a row that can't fit its blocks wraps (the zoom animation lifts the floor).
  const crumbs = weekMode ? [`Families · W${u.wk} (${win})`] : ["Demand", "Drivers", "Families", `${family} styles`].slice(0, level + 1);
  function click(b: Block, i: number) {
    if (weekMode || zoom != null || b.next == null) return;
    const go = () => { if (b.family) setFamily(b.family); setLevel(b.next === "styles" ? 3 : (b.next as number)); setZoom(null); };
    if (rm) { go(); return; }
    setZoom(i); setTimeout(go, 340);
  }
  return (
    <section className="panel" style={{ padding: "22px 24px" }}>
      <div style={{ display: "flex", alignItems: "flex-start", gap: 12, flexWrap: "wrap" }}>
        <h2 className="cond" style={{ margin: 0, fontWeight: 800, fontSize: 26, flex: "1 1 260px" }}>Where did the growth come from?</h2>
        <Seg opts={[["ptd", "PTD drill-down"], ["week", `W${u.wk} families`]]} value={weekMode ? "week" : "ptd"} onChange={(v) => { setWeekMode(v === "week"); setLevel(v === "week" ? 2 : 0); setZoom(null); }} />
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 6, marginTop: 10, fontFamily: MONO, fontSize: 12, flexWrap: "wrap" }}>
        {crumbs.map((c, i) => (
          <span key={c} style={{ display: "contents" }}>
            <button type="button" disabled={weekMode || i === crumbs.length - 1} aria-current={i === crumbs.length - 1 ? "step" : undefined} onClick={() => (setLevel(i), setZoom(null))} className="btn-plain" style={{ cursor: weekMode || i === crumbs.length - 1 ? "default" : "pointer", padding: "4px 8px", borderRadius: 4, background: i === crumbs.length - 1 ? C.charcoal : "transparent", color: i === crumbs.length - 1 ? "#fff" : C.sapphireInk, fontWeight: i === crumbs.length - 1 ? 700 : 400 }}>{c}</button>
            {i < crumbs.length - 1 && <span style={{ color: C.ly }}>›</span>}
          </span>
        ))}
      </div>
      <div style={{ marginTop: 6, fontSize: 13, color: C.muted }}>{note}</div>
      <div key={`${weekMode}${level}${family}${u.wk}`} className="fade-in" style={{ display: "flex", flexWrap: zoom == null ? "wrap" : "nowrap", gap: 3, marginTop: 16 }}>
        {blocks.map((b, i) => {
          const col = b.dark ? (i === 0 ? C.charcoal : "#5B6780") : i === 0 && weekMode ? C.charcoal : i === 1 ? "#5B6780" : "#C9CED9";
          const ink = col === "#C9CED9" ? C.ink : "#fff";
          // a block that drills in is a button (focusable, Enter/Space); the others are plain data blocks
          const drillable = b.next != null && !weekMode;
          const Block: any = drillable ? "button" : "div";
          return (
            <Block key={b.label} {...(drillable ? { type: "button", className: "btn-plain", onClick: () => click(b, i), title: "Click to drill in" } : {})}
              style={{ display: "flex", flexDirection: "column", justifyContent: "space-between", minWidth: zoom == null ? 136 : 0, minHeight: 132, overflow: "hidden", padding: 14, cursor: drillable ? "pointer" : "default", transition: `flex-grow .32s ${EASE}, opacity .2s ease`, flex: `${zoom == null ? b.w : zoom === i ? 100 : 0.0001} 1 0`, background: col, color: ink, opacity: zoom == null || zoom === i ? 1 : 0 }}>
              <span style={{ display: "block", fontSize: 14, fontWeight: 700, lineHeight: 1.2 }}>{b.label}{drillable ? " ↘" : ""}</span>
              <span style={{ display: "block" }}><span className="cond" style={{ display: "block", fontWeight: 800, fontSize: 34, whiteSpace: "nowrap" }}>{b.val}</span><span style={{ display: "block", fontFamily: MONO, fontSize: 11, lineHeight: 1.3 }}>{b.sub}</span></span>
            </Block>
          );
        })}
      </div>
      {drags.length > 0 && (
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginTop: 8, flexWrap: "wrap" }}>
          <span style={{ fontFamily: MONO, fontSize: 11, fontWeight: 700, whiteSpace: "nowrap" }}>DRAGS</span>
          <div style={{ flex: 1, display: "flex", flexWrap: "wrap", gap: 3, minWidth: 280, minHeight: 40 }}>
            {drags.map((d) => <div key={d.label} style={{ flex: `${d.w} 1 0`, minWidth: 136, display: "flex", alignItems: "center", padding: "0 10px", background: "repeating-linear-gradient(135deg,#E9E4EF 0 6px,#F6F3FA 6px 12px)", fontSize: 13, fontWeight: 700, lineHeight: 1.15 }}>{d.label}</div>)}
          </div>
        </div>
      )}
    </section>
  );
}

function G3() {
  const u = useUrl();
  const gd = D.growth_drill;
  const tabby = gd.families.find((f: any) => f.family === "Tabby");
  const drag = [...gd.families].sort((a: any, b: any) => a.share_of_growth - b.share_of_growth)[0];
  const isPtd = u.win === "PTD";
  const rows = isPtd ? D.products_ptd : D.products_by_week.filter((r: any) => r.wk === u.wk && r.window === u.win);
  const g = (r: any, ptdKey: string, wkKey: string) => (isPtd ? r[ptdKey] : r[wkKey]);
  return (
    <>
      <Kpis items={[
        { label: `Demand · PTD ${PTD_RANGE}`, value: fmtPct(gd.total.yoy_pct, true), delta: `${fmtMoney(gd.total.ty)} vs ${fmtMoney(gd.total.ly)}` },
        { label: `Tabby share of growth · PTD ${PTD_RANGE}`, value: fmtPct(tabby.share_of_growth, false, 0), delta: `demand ${fmtPct(tabby.sales_yoy_pct, true)}`, color: C.up },
        { label: "Tabby + Pillow Tabby", value: fmtPct(gd.hero_share_of_growth, false, 0), delta: "of PTD growth" },
        { label: "Biggest drag · PTD", value: drag.family, delta: `${fmtPct(drag.share_of_growth, true, 0)} of growth · demand ${fmtPct(drag.sales_yoy_pct, true)}`, color: C.down },
      ]} />
      <Drill />
      <Table title={`Family scorecard · ${isPtd ? `PTD ${PTD_RANGE}` : `${u.win} ending W${u.wk}`}`} note="Contribution = points of total YoY demand growth. Gen Z index: 100 = the family's average customer mix." initial={["contrib", -1]}
        rows={rows} highlight={(r) => ["Tabby", "Pillow Tabby"].includes(g(r, "STYLE_GROUP", "family"))}
        cols={[
          { key: "fam", label: "Family", cell: (r) => g(r, "STYLE_GROUP", "family") },
          { key: "ty", label: "Demand TY", align: "r", sort: (r) => g(r, "sales_TY", "sales_ty"), cell: (r) => fmtMoney(g(r, "sales_TY", "sales_ty")) },
          ...(u.ly ? [{ key: "ly", label: "Demand LY", align: "r", sort: (r: any) => g(r, "sales_LY", "sales_ly"), cell: (r: any) => fmtMoney(g(r, "sales_LY", "sales_ly")), color: () => C.muted } as Col] : []),
          { key: "yoy", label: "YoY", align: "r", sort: (r) => r.sales_yoy_pct, cell: (r) => fmtPct(r.sales_yoy_pct, true), color: (r) => tone(r.sales_yoy_pct) },
          { key: "contrib", label: "Contribution", align: "r", sort: (r) => (isPtd ? r.contrib_pts * 100 : r.contrib_pts), cell: (r) => fmtPts(isPtd ? r.contrib_pts * 100 : r.contrib_pts), bold: true },
          { key: "gz", label: "Gen Z index", align: "r", sort: (r) => g(r, "genz_index_TY", "genz_index_ty"), cell: (r) => fmtNum(g(r, "genz_index_TY", "genz_index_ty")) },
          ...(isPtd ? [{ key: "cls", label: "Class", cell: (r: any) => r.class, color: (r: any) => (r.class === "Winner" ? C.winInk : r.class === "Decliner" ? C.down : C.muted) } as Col] : []),
        ]} />
    </>
  );
}

// ---------- G4: M5 morphs ----------
function G4() {
  const u = useUrl();
  const rm = useReducedMotion();
  const [morph, setMorph] = useState<"LY" | "TY">(rm ? "TY" : "LY");
  useEffect(() => { if (!rm) { setMorph("LY"); const t = setTimeout(() => setMorph("TY"), 450); return () => clearTimeout(t); } }, [u.wk]); // eslint-disable-line react-hooks/exhaustive-deps
  const ty = morph === "TY";
  const sh = D.stock_demand_shares;
  const R1 = D.recommendations_sizing.R1, R2 = D.recommendations_sizing.R2;
  const tabbyPos = D.inventory_position.find((r: any) => r.STYLE_GROUP === "Tabby");
  const maxShare = Math.max(...sh.families.flatMap((f: any) => [f.stock_share_ly, f.demand_share_ly, f.stock_share_ty, f.demand_share_ty])) * 1.08;
  const LABEL = ["Tabby", "Pillow Tabby", "Knit Dress", "Trench", "Tailored Jacket"];
  const inv = D.inventory_by_week.filter((r: any) => r.year === "TY" && r.wk === u.wk).sort((a: any, b: any) => b.wos - a.wos);
  const lo = ruleThreshold("WOS_LOW")!, hi = ruleThreshold("WOS_HIGH")!;
  const off = u.wk < 26;
  const wmax = Math.max(...inv.flatMap((r: any) => [r.wos || 0, r.wos_ly_same_week || 0]));
  return (
    <>
      <Kpis items={[
        { label: "Demand at risk · next 4 weeks", value: fmtMoney(R1.demand_at_risk_usd_sample), delta: `${fmtPct(R1.demand_at_risk_pct_of_next_4wk_demand)} of demand (R1)`, color: C.down },
        { label: `Tabby replenishment cover · ${RECEIPT_WEEKS}`, value: fmtPct(tabbyPos.receipts_to_sales_TY, false, 0), delta: `▼ LY ${fmtPct(tabbyPos.receipts_to_sales_LY, false, 0)} of units sold`, color: C.down },
        { label: "Stock above median WOS", value: `${fmtNum(R2.excess_units)} units`, delta: `${fmtMoney(R2.excess_retail_value_usd_sample)} at retail (R2)` },
        { label: "Stock vs demand correlation", value: sh.corr_ty.toFixed(2), delta: `▼ LY ${sh.corr_ly.toFixed(2)}`, color: C.down },
      ]} />
      {off && <div style={{ padding: "12px 16px", background: C.lav1, fontSize: 13 }}>W{u.wk} has a truncated trailing window (fewer than 4 weeks), so weeks-of-supply rules are off and WOS readings are early signals.</div>}
      <div style={{ display: "flex", flexWrap: "wrap", gap: 18 }}>
        <section className="panel" style={{ flex: "1 1 420px", padding: "22px 24px" }}>
          <div style={{ display: "flex", alignItems: "flex-start", gap: 12, flexWrap: "wrap" }}>
            <div style={{ flex: "1 1 220px" }}>
              <h2 className="cond" style={{ margin: 0, fontWeight: 800, fontSize: 24 }}>Stock share vs demand share</h2>
              <div style={{ marginTop: 4, fontSize: 13, color: C.muted }}>On the diagonal, stock sits where demand is. Each dot is one family; it moves from LY to TY.</div>
            </div>
            <Seg opts={[["LY", "LY"], ["TY", "TY"]]} value={morph} onChange={(v) => setMorph(v as any)} />
          </div>
          <div style={{ position: "relative", margin: "18px 0 30px 30px", maxWidth: 420, aspectRatio: "1", boxShadow: `inset 1px -1px 0 ${C.ink}` }}>
            <svg viewBox="0 0 100 100" preserveAspectRatio="none" style={{ position: "absolute", inset: 0, width: "100%", height: "100%" }}><line x1={0} y1={100} x2={100} y2={0} stroke={C.ly} strokeDasharray="2 2" vectorEffect="non-scaling-stroke" /></svg>
            {sh.families.map((f: any) => {
              const x = (ty ? f.demand_share_ty : f.demand_share_ly) / maxShare, y = (ty ? f.stock_share_ty : f.stock_share_ly) / maxShare;
              const lab = LABEL.includes(f.family);
              const bg = f.family === "Tabby" || f.family === "Pillow Tabby" ? GOALS[3].hue : lab ? GOALS[3].ink : C.ly;
              return (
                <div key={f.family} title={`${f.family}: ${fmtPct(ty ? f.demand_share_ty : f.demand_share_ly)} of demand, ${fmtPct(ty ? f.stock_share_ty : f.stock_share_ly)} of stock (${morph})`}
                  style={{ position: "absolute", width: 14, height: 14, margin: "0 0 -7px -7px", borderRadius: "50%", transition: `left .5s ${EASE}, bottom .5s ${EASE}`, left: `${x * 100}%`, bottom: `${y * 100}%`, background: bg, boxShadow: "0 0 0 2px #fff" }}>
                  {lab && <span style={{ position: "absolute", ...(x > 0.55 ? { right: 18, textAlign: "right" as const } : { left: 18 }), top: -2, whiteSpace: "nowrap", fontFamily: MONO, fontSize: 11, fontWeight: 700 }}>{f.family}{f.family === "Tabby" && ty ? ` · ${fmtPct(f.demand_share_ty)} demand, ${fmtPct(f.stock_share_ty)} stock` : ""}</span>}
                </div>
              );
            })}
            <span style={{ position: "absolute", left: "50%", bottom: -24, transform: "translateX(-50%)", fontFamily: MONO, fontSize: 11, color: C.muted, whiteSpace: "nowrap" }}>demand share →</span>
            <span style={{ position: "absolute", left: -28, top: "50%", transform: "rotate(-90deg) translateX(50%)", transformOrigin: "left top", fontFamily: MONO, fontSize: 11, color: C.muted, whiteSpace: "nowrap" }}>stock share →</span>
          </div>
          <div style={{ fontFamily: MONO, fontSize: 12 }}>correlation <b key={morph} className="swap" style={{ fontSize: 16 }}>{(ty ? sh.corr_ty : sh.corr_ly).toFixed(2)}</b> · {ty ? "TY: families drift off the diagonal" : "LY: stock tracked demand"}</div>
          <div style={{ marginTop: 6, fontSize: 11.5, color: C.muted }}>{sh.basis}</div>
        </section>
        <section className="panel" style={{ flex: "1 1 420px", padding: "22px 24px" }}>
          <h2 className="cond" style={{ margin: 0, fontWeight: 800, fontSize: 24 }}>Weeks of supply by family · W{u.wk}</h2>
          <div style={{ marginTop: 4, fontSize: 13, color: C.muted }}>Bars move from LY same week to TY. Dashed lines = the low ({lo}) and high ({hi}) stock rules.</div>
          <div style={{ position: "relative", marginTop: 18, display: "flex", flexDirection: "column", gap: 6 }}>
            {inv.map((r: any) => {
              const v = ty ? r.wos : r.wos_ly_same_week;
              const flag = !off && ty && (r.wos < lo || r.wos > hi);
              return (
                <div key={r.family} style={{ display: "grid", gridTemplateColumns: "118px 1fr 46px", alignItems: "center", gap: 8, fontSize: 12.5 }}>
                  <b style={{ whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{r.family}</b>
                  <div style={{ position: "relative", height: 12 }}>
                    <div style={{ position: "absolute", inset: "0 auto 0 0", transition: `width .5s ${EASE}`, width: `${((v || 0) / wmax) * 100}%`, background: ty ? (flag ? (r.wos < lo ? C.crit : GOALS[3].hue) : "#D4B3CB") : "#C9C4D3" }} />
                  </div>
                  <span style={{ fontFamily: MONO, fontSize: 12, textAlign: "right" }}>{fmtWos(v)}</span>
                </div>
              );
            })}
            {[lo, hi].map((t) => <div key={t} style={{ position: "absolute", top: -6, bottom: -6, left: `calc(126px + (100% - 180px) * ${t / wmax})`, borderLeft: `1.5px dashed ${C.ink}` }} />)}
          </div>
        </section>
      </div>
      <Table title={`Weeks of supply · W${u.wk}`} note="End-of-week stock ÷ trailing (up to) 4-week average weekly units. Status uses the anomaly rule thresholds." initial={["wos", 1]}
        rows={inv} highlight={(r) => ["Tabby", "Pillow Tabby"].includes(r.family)}
        cols={[
          { key: "fam", label: "Family", cell: (r) => r.family },
          { key: "wos", label: "WOS TY", align: "r", sort: (r) => r.wos, cell: (r) => fmtWos(r.wos), bold: true },
          ...(u.ly ? [{ key: "ly", label: "WOS LY same week", align: "r", sort: (r: any) => r.wos_ly_same_week, cell: (r: any) => fmtWos(r.wos_ly_same_week), color: () => C.muted } as Col] : []),
          { key: "oh", label: "On hand", align: "r", sort: (r) => r.on_hand_eow, cell: (r) => fmtNum(r.on_hand_eow) },
          { key: "sold", label: "Units sold", align: "r", sort: (r) => r.units_sold, cell: (r) => fmtNum(r.units_sold) },
          { key: "st", label: "Status", sort: (r) => (off ? "" : r.wos < lo ? "a" : r.wos > hi ? "b" : "c"), cell: (r) => (off ? "rules off" : r.wos < lo ? "◆ Low" : r.wos > hi ? "▲ High" : "OK"), color: (r) => (off ? C.muted : r.wos < lo ? C.crit : r.wos > hi ? C.warnText : C.muted) },
        ]} />
    </>
  );
}

export default function Explore() {
  const u = useUrl();
  return (
    <main className="pad-x" style={{ padding: "28px 40px 56px", display: "flex", flexDirection: "column", gap: 18 }}>
      {u.tab === 0 && <G1 />}
      {u.tab === 1 && <G2 />}
      {u.tab === 2 && <G3 />}
      {u.tab === 3 && <G4 />}
      {u.wk === PARTIAL && <div style={{ fontSize: 12, color: C.muted }}>W{PARTIAL} is a partial week ({D.meta.partial_week_days}); LY is compared on the same days.</div>}
    </main>
  );
}
