import { useEffect, useRef, useState } from "react";
import { annotate } from "../lib/validator.js";
import {
  checkTitle,
  C, D, GOALS, MONO, PARTIAL, WEEKS, arrow, dateWords, fmtMoney, fmtNum, fmtPct, setUrl, tone, trailing, useUrl, weekAI,
} from "../lib/core";

// Findings for search (titles written without figures; numbers live in the data, not in UI copy)
export const FINDINGS: [string, string, number][] = [
  ["F1", "Growth comes from more customers, not bigger baskets", 0], ["F2", "A naive full-week comparison understates growth", 0],
  ["F3", "The W29 drop vs the previous week is basket, not traffic", 0], ["F4", "Gen Z new-customer acquisition more than doubled", 1],
  ["F5", "Gen Z share of new customers is accelerating", 1], ["F6", "Retention proxy is weak: returning customers flat", 1],
  ["F7", "New Gen Z have the lowest Insider attach", 1], ["F8", "New Gen Z buy the Tabby franchise first, at full price", 1],
  ["F9", "The Tabby franchise drives most of the growth", 2], ["F10", "Halo apparel and Rogue are the drag", 2],
  ["F11", "Winners nearly out of stock; apparel overstocked", 3], ["F12", "Replenishment stopped following demand", 3],
  ["F13", "TY W30 stock snapshot is dated after the last sale", 3], ["F14", "CUST_ID behaves like a random number", 1],
  ["F15", "Mens Bag is the next Gen Z over-indexer (watch)", 2],
];

function Search() {
  const [q, setQ] = useState("");
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLInputElement>(null);
  useEffect(() => {
    const k = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") { e.preventDefault(); ref.current?.focus(); }
      if (e.key === "Escape") setOpen(false);
    };
    window.addEventListener("keydown", k);
    return () => window.removeEventListener("keydown", k);
  }, []);
  const qq = q.trim().toLowerCase();
  const idx = [
    ...D.products_ptd.map((p: any) => ({ kind: "FAMILY", label: p.STYLE_GROUP, dest: "Explore · G3", go: () => setUrl({ screen: "explore", tab: 2 }, true) })),
    ...FINDINGS.map(([id, t, g]) => ({ kind: "FINDING", label: `${id} · ${t}`, dest: `Explore · ${GOALS[g].id}`, go: () => setUrl({ screen: "explore", tab: g }, true) })),
    ...D.rules.map((r: any) => ({ kind: "RULE", label: r.id, dest: "Briefing · rules", go: () => setUrl({ screen: "briefing" }, true) })),
  ];
  const results = qq ? idx.filter((r) => r.label.toLowerCase().includes(qq)).slice(0, 8) : [];
  return (
    <div style={{ position: "relative", width: 300, maxWidth: "100%" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10, padding: "8px 12px", borderRadius: 6, background: "rgba(255,255,255,.08)", fontSize: 13, color: C.onDarkMuted }}>
        <span>⌕</span>
        <input ref={ref} value={q} onChange={(e) => { setQ(e.target.value); setOpen(true); }} onFocus={() => setOpen(true)}
          onBlur={() => setTimeout(() => setOpen(false), 150)} placeholder="Search families, findings, rules"
          aria-label="Search families, findings and rules"
          style={{ flex: 1, minWidth: 0, background: "transparent", border: 0, outline: "none", color: "#fff", font: "inherit" }} />
        <span style={{ fontFamily: MONO, fontSize: 11 }}>⌘K</span>
      </div>
      {open && results.length > 0 && (
        <div style={{ position: "absolute", zIndex: 30, top: "calc(100% + 6px)", left: 0, right: 0, padding: 6, borderRadius: 8, background: "#fff", color: C.ink, boxShadow: "0 16px 40px rgba(31,38,54,.28)" }}>
          {results.map((r, i) => (
            <div key={i} className="hov-lav" onMouseDown={() => { r.go(); setQ(""); }}
              style={{ display: "flex", alignItems: "center", gap: 10, padding: "8px 10px", borderRadius: 6, cursor: "pointer", fontSize: 13 }}>
              <span style={{ fontFamily: MONO, fontSize: 10, fontWeight: 700, color: C.muted, width: 58 }}>{r.kind}</span>
              <span style={{ flex: 1 }}>{r.label}</span>
              <span style={{ fontSize: 11, color: C.muted }}>{r.dest}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function WeekStrip() {
  const u = useUrl();
  const max = weekAI(WEEKS[0]).counts.n_alerts_all_weeks_max;
  return (
    <div style={{ display: "flex", gap: 2, alignItems: "flex-end", fontFamily: MONO, fontSize: 12, flexWrap: "wrap" }} role="radiogroup" aria-label="Fiscal week">
      {WEEKS.map((w) => {
        const on = w === u.wk;
        const n = weekAI(w).counts.n_alerts;
        return (
          <span key={w} role="radio" aria-checked={on} tabIndex={0} onClick={() => setUrl({ wk: w })} onKeyDown={(e) => e.key === "Enter" && setUrl({ wk: w })}
            title={`${n} alerts fired in W${w}${w === PARTIAL ? " (partial week)" : ""}`}
            style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 4, padding: "6px 9px", borderRadius: 5, cursor: "pointer", whiteSpace: "nowrap", transition: "background .2s ease", background: on ? C.sapphire : "transparent", color: on ? "#fff" : C.onDarkFaint, fontWeight: on ? 700 : 400 }}>
            <span style={{ width: 12, borderRadius: 2, transition: "height .25s ease", height: Math.round((n / max) * 22) + 2, background: on ? "#fff" : w === PARTIAL ? "repeating-linear-gradient(0deg,rgba(255,255,255,.35) 0 2px,transparent 2px 4px)" : "rgba(255,255,255,.28)" }} />
            W{w}{w === PARTIAL ? " ◔" : ""}
          </span>
        );
      })}
    </div>
  );
}

export function KpiBand({ dark = true }: { dark?: boolean }) {
  const u = useUrl();
  const b = trailing(u.wk, u.win);
  const k = [
    ["Demand", b.sales, (x: number) => fmtMoney(x)], ["Transactions", b.txns, fmtNum], ["AOV", b.aov, (x: number) => fmtMoney(x, false)],
    ["UPT", b.upt, (x: number) => fmtNum(x, 2)], ["AUR", b.aur, (x: number) => fmtMoney(x, false)], ["Customers", b.customers, fmtNum],
  ] as const;
  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(140px,1fr))", background: dark ? C.band : "#fff", borderTop: dark ? "1px solid rgba(255,255,255,.08)" : undefined, boxShadow: dark ? undefined : `inset 0 0 0 1px ${C.hair}` }}>
      {k.map(([label, blk, f]) => (
        <div key={label} style={{ padding: "18px 20px", boxShadow: dark ? "inset 1px 0 0 rgba(255,255,255,.1)" : `1px 1px 0 ${C.hair}` }}>
          <div style={{ fontSize: 12, fontWeight: 600, color: dark ? C.onDarkMuted : C.muted }}>{label}</div>
          <div key={`${u.wk}${u.win}`} className="swap cond" style={{ marginTop: 6, fontWeight: 700, fontSize: 28, fontStretch: "80%" }}>{f(blk.ty as number)}</div>
          <div style={{ fontFamily: MONO, fontSize: 12, color: tone(blk.yoy_pct, dark), display: "flex", gap: 8, flexWrap: "wrap" }}>
            <span>{arrow(blk.yoy_pct)}{fmtPct(Math.abs(blk.yoy_pct))}</span>
            {u.ly && <span style={{ color: dark ? C.onDarkFaint : C.muted }}>LY {f(blk.ly as number)}</span>}
          </div>
        </div>
      ))}
    </div>
  );
}

function Headline({ wk }: { wk: number }) {
  const w = weekAI(wk);
  const { segs, res } = annotate(w.headline, w.facts, w.headline_citations);
  if (res.status !== "PASS") return <>Headline held back: it failed the {checkTitle(res.failures[0].check).toLowerCase()} check.</>;
  return <>{segs.map((s: any, i: number) => (s.num ? <span key={i} style={{ color: C.sapphireLight }}>{s.text}</span> : <span key={i}>{s.text}</span>))}</>;
}

export default function Header() {
  const u = useUrl();
  const w = weekAI(u.wk);
  const dates = D.meta.week_dates_ty[String(u.wk)];
  const sev = w.counts.n_alerts_by_severity;
  const nav: [typeof u.screen, string][] = [["briefing", "Briefing"], ["explore", "Explore"], ["ask", "Ask"], ["how", "How it was built"]];
  const eyebrow = u.wk === PARTIAL
    ? `FY26 W${u.wk} · as of ${dateWords(dates.last_sale)} · partial: ${D.meta.partial_week_days} · window ${u.win}`
    : `FY26 W${u.wk} · week ending ${dateWords(dates.end)} · window ${u.win}`;
  const hero = { padding: "28px 40px 30px", borderTop: "1px solid rgba(255,255,255,.1)" };
  return (
    <header style={{ background: C.chrome, color: "#fff" }}>
      <div className="pad-x" style={{ display: "flex", alignItems: "center", gap: 24, padding: "0 40px", minHeight: 60, flexWrap: "wrap" }}>
        <span className="cond" style={{ fontWeight: 900, fontSize: 20 }}>TY/LY</span>
        <nav style={{ display: "flex", alignSelf: "stretch", fontSize: 14, fontWeight: 600 }}>
          {nav.map(([k, l]) => (
            <span key={k} onClick={() => setUrl({ screen: k }, true)} className="clickable"
              style={{ display: "flex", alignItems: "center", padding: "0 14px", whiteSpace: "nowrap", color: u.screen === k ? "#fff" : C.onDarkMuted, boxShadow: u.screen === k ? `inset 0 -3px 0 ${C.thistle}` : "none", minHeight: 60 }}>{l}</span>
          ))}
        </nav>
        <div style={{ flex: 1 }} />
        <Search />
      </div>
      <div className="pad-x" style={{ display: "flex", alignItems: "center", gap: 20, padding: "8px 40px 10px", borderTop: "1px solid rgba(255,255,255,.1)", flexWrap: "wrap" }}>
        <WeekStrip />
        <span className="hide-narrow" style={{ fontSize: 11, lineHeight: 1.3, color: C.onDarkFaint, maxWidth: 92 }}>Bar height = alerts fired that week</span>
        <div style={{ flex: 1 }} />
        <div className="seg" style={{ background: "rgba(255,255,255,.08)" }}>
          {["L1W", "L4W", "PTD"].map((o) => (
            <span key={o} onClick={() => setUrl({ win: o })} style={{ background: u.win === o ? C.thistle : "transparent", color: u.win === o ? C.ink : "#fff", fontWeight: u.win === o ? 700 : 400 }}>{o}</span>
          ))}
        </div>
        <div onClick={() => setUrl({ ly: !u.ly })} role="switch" aria-checked={u.ly} className="clickable" style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13, fontWeight: 600 }}>
          <div style={{ width: 32, height: 18, borderRadius: 999, position: "relative", transition: "background .2s ease", background: u.ly ? C.sapphire : "rgba(255,255,255,.2)" }}>
            <div style={{ position: "absolute", top: 2, width: 14, height: 14, borderRadius: "50%", background: "#fff", transition: "left .2s ease", left: u.ly ? 16 : 2 }} />
          </div>
          Show LY
        </div>
      </div>

      {u.screen === "briefing" && (
        <>
          <div className="pad-x" style={{ padding: "34px 40px 38px", borderTop: "1px solid rgba(255,255,255,.1)", display: "flex", flexWrap: "wrap", gap: 32, alignItems: "flex-end" }}>
            <div style={{ flex: "999 1 560px", minWidth: 0 }}>
              <span style={{ fontFamily: MONO, fontSize: 12, color: C.onDarkMuted }}>{eyebrow}</span>
              <h1 key={u.wk} className="cond h1-hero fade-in" style={{ margin: "16px 0 0", fontWeight: 800, fontSize: 56, lineHeight: 1, maxWidth: 900, textWrap: "pretty" as any }}><Headline wk={u.wk} /></h1>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "8px 20px", marginTop: 16, fontFamily: MONO, fontSize: 12, color: C.onDarkMuted }}>
                <span>{fmtNum(D.meta.counts.lines_total)} transaction lines</span><span>{fmtNum(D.meta.counts.inventory_snapshots)} stock snapshots</span>
                <span>{w.counts.n_rules} rules</span>
                <b style={{ color: C.downOnDark }}>◆ {sev.critical} critical</b><b style={{ color: C.warn }}>▲ {sev.warning} warning</b>
                {sev.info > 0 && <b style={{ color: C.onDarkMuted }}>● {sev.info} info</b>}
              </div>
            </div>
            <div style={{ flex: "1 1 260px", maxWidth: 320, display: "grid", gridTemplateColumns: "1fr 1fr", gap: 4 }}>
              {GOALS.map((g, i) => (
                <div key={g.id} className="hov-bright clickable" onClick={() => setUrl({ screen: "explore", tab: i }, true)} style={{ padding: 12, background: g.key, color: i === 3 ? C.ink : "#fff" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", gap: 6, whiteSpace: "nowrap", fontFamily: MONO, fontSize: 10, fontWeight: 700 }}><span>{g.id}</span><span>Explore →</span></div>
                  <div style={{ marginTop: 14, fontSize: 13, fontWeight: 700 }}>{g.name}</div>
                </div>
              ))}
            </div>
          </div>
          <KpiBand />
        </>
      )}
      {u.screen === "explore" && (
        <div className="pad-x" style={{ padding: "28px 40px 0", borderTop: "1px solid rgba(255,255,255,.1)" }}>
          <span style={{ fontFamily: MONO, fontSize: 12, color: C.onDarkMuted }}>Explore · FY26 W{u.wk} · window {u.win}</span>
          <h1 className="cond h1-hero" style={{ margin: "10px 0 22px", fontWeight: 800, fontSize: 44, lineHeight: 1 }}>{GOALS[u.tab].id} {GOALS[u.tab].name}</h1>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(170px,1fr))", gap: 4 }}>
            {GOALS.map((g, i) => (
              <div key={g.id} onClick={() => setUrl({ tab: i })} className="clickable" role="tab" aria-selected={i === u.tab}
                style={{ padding: "12px 14px 14px", transition: "background .2s ease", background: i === u.tab ? g.key : "rgba(255,255,255,.06)", color: i === u.tab && i === 3 ? C.ink : "#fff" }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8, fontFamily: MONO, fontSize: 11, fontWeight: 700 }}>
                  <span style={{ width: 8, height: 8, borderRadius: 2, background: i === u.tab ? (i === 3 ? C.ink : "#fff") : g.key }} />{g.id}
                </div>
                <div style={{ marginTop: 12, fontSize: 15, fontWeight: 700 }}>{g.name}</div>
              </div>
            ))}
          </div>
        </div>
      )}
      {u.screen === "ask" && (
        <div className="pad-x" style={hero}>
          <span style={{ fontFamily: MONO, fontSize: 12, color: C.onDarkMuted }}>Ask · Claude picks a query template, code answers from metrics.json</span>
          <h1 className="cond h1-hero" style={{ margin: "10px 0 0", fontWeight: 800, fontSize: 44, lineHeight: 1 }}>Ask the data</h1>
        </div>
      )}
      {u.screen === "how" && (
        <div className="pad-x" style={hero}>
          <span style={{ fontFamily: MONO, fontSize: 12, color: C.onDarkMuted }}>How it was built</span>
          <h1 className="cond h1-hero" style={{ margin: "10px 0 0", fontWeight: 800, fontSize: 44, lineHeight: 1.02, maxWidth: 900 }}>Rules decide what's unusual. The AI only words the facts, and code checks every number.</h1>
        </div>
      )}
    </header>
  );
}
