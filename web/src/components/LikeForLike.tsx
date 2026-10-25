import { useEffect, useState } from "react";
import { C, D, MONO, fmtMoney, fmtPct, fmtUsd0 } from "../lib/core";

/** M6: Naive ↔ like-for-like. Every number is a stored value; the headline swaps between the two real values. */
export function BasisSwitch({ big = 72 }: { big?: number }) {
  const [naive, setNaive] = useState(false);
  const ba = D.meta.basis_alternatives;
  const days = D.w30_daily as { day: string; ty: number | null; ly: number; ly_in_like_for_like: boolean }[];
  const w30 = D.weekly[D.weekly.length - 1];
  const head = naive ? ba.naive_all_rows_sales_yoy_pct : ba.like_for_like_sales_yoy_pct;
  const ly = naive ? ba.naive_ly_sales : D.headline_ptd.sales.ly;
  const lyW30 = naive ? D.meta.ly_w30_full_week_sales : w30.sales.ly;
  const extra = days.filter((d) => !d.ly_in_like_for_like);
  return (
    <div>
      <div style={{ display: "flex", alignItems: "flex-end", gap: 20, flexWrap: "wrap" }}>
        <div style={{ flex: "1 1 280px" }}>
          <div style={{ fontFamily: MONO, fontSize: 11, fontWeight: 700, color: C.muted }}>DEMAND PTD · TY VS LY</div>
          <div style={{ display: "flex", alignItems: "baseline", gap: 14, flexWrap: "wrap", overflow: "hidden" }}>
            <span key={String(naive)} className="cond swap" style={{ fontWeight: 800, fontSize: big, lineHeight: 1.05, color: C.sapphireInk }}>{fmtPct(head, true)}</span>
            {naive && (
              <span className="fade-in" style={{ padding: "4px 8px", background: C.warn, color: C.warnInk, fontFamily: MONO, fontSize: 12, fontWeight: 700 }}>
                ≈{ba.naive_gap_pts.toFixed(1)} pts lost to {extra.length} extra days ({fmtMoney(ba.ly_extra_days_sales)})
              </span>
            )}
          </div>
          <div style={{ marginTop: 6, fontFamily: MONO, fontSize: 13 }}>TY {fmtUsd0(D.headline_ptd.sales.ty)} vs LY <span key={String(naive)} className="swap">{fmtUsd0(ly)}</span></div>
        </div>
        <div className="seg" style={{ background: C.lav2 }} role="radiogroup" aria-label="Comparison basis">
          {([["Naive", true], ["Like-for-like", false]] as const).map(([l, v]) => (
            <button type="button" key={l} role="radio" aria-checked={naive === v} className="btn-plain" onClick={() => setNaive(v)} style={{ background: naive === v ? C.charcoal : "transparent", color: naive === v ? "#fff" : C.ink, fontWeight: 700 }}>{l}</button>
          ))}
        </div>
      </div>
      <div style={{ marginTop: 22, display: "grid", gridTemplateColumns: "96px repeat(7,minmax(0,1fr))", gap: 4, fontSize: 12 }}>
        <div style={{ display: "flex", flexDirection: "column", justifyContent: "center", fontFamily: MONO, fontSize: 11, fontWeight: 700 }}>LY W{D.meta.partial_week}<span key={String(naive)} className="swap" style={{ fontWeight: 400 }}>{fmtMoney(lyW30)}</span></div>
        {days.map((d, i) => {
          const isExtra = !d.ly_in_like_for_like;
          const filled = !isExtra || naive;
          const k = isExtra ? i - 4 : 0;
          return (
            <div key={d.day} style={{ height: 58, padding: 8, display: "flex", flexDirection: "column", justifyContent: "space-between", transition: "background .15s ease, color .15s ease", transitionDelay: isExtra ? `${naive ? k * 120 : (2 - k) * 120}ms` : "0ms", background: filled ? C.ly : "transparent", color: filled ? "#fff" : C.muted, boxShadow: filled ? "none" : `inset 0 0 0 1.5px ${C.ly}` }}>
              <span style={{ fontFamily: MONO, fontSize: 11, fontWeight: 700 }}>{d.day}</span>
              <span style={{ fontFamily: MONO, fontSize: 11 }}>{fmtMoney(d.ly)}</span>
            </div>
          );
        })}
        <div style={{ display: "flex", flexDirection: "column", justifyContent: "center", fontFamily: MONO, fontSize: 11, fontWeight: 700 }}>TY W{D.meta.partial_week}<span style={{ fontWeight: 400 }}>{fmtMoney(w30.sales.ty)}</span></div>
        {days.map((d) => (
          <div key={d.day} style={{ height: 58, padding: 8, display: "flex", flexDirection: "column", justifyContent: "space-between", background: d.ty != null ? C.sapphire : "transparent", color: "#fff" }}>
            {d.ty != null && <><span style={{ fontFamily: MONO, fontSize: 11, fontWeight: 700 }}>{d.day}</span><span style={{ fontFamily: MONO, fontSize: 11 }}>{fmtMoney(d.ty)}</span></>}
          </div>
        ))}
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "96px repeat(7,minmax(0,1fr))", gap: 4, marginTop: 6 }}>
        <div />
        <div style={{ gridColumn: "6 / span 3", fontSize: 12, fontWeight: 600, color: C.muted, transition: "opacity .2s ease", opacity: naive ? 0 : 1 }}>↑ days this year hasn't had yet</div>
      </div>
      <p style={{ margin: "16px 0 0", fontSize: 14, fontWeight: 700 }}>Same weeks, same weekdays: that's like-for-like.</p>
    </div>
  );
}

export function LikeForLikeStrip() {
  const [open, setOpen] = useState(false);
  useEffect(() => {
    const k = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    window.addEventListener("keydown", k);
    return () => window.removeEventListener("keydown", k);
  }, []);
  return (
    <>
      <div className="pad-x" style={{ display: "flex", alignItems: "center", gap: 12, padding: "11px 40px", background: C.thistle, color: C.ink, fontSize: 13, fontWeight: 500, flexWrap: "wrap" }}>
        <b style={{ whiteSpace: "nowrap", fontFamily: MONO, fontSize: 11 }}>LIKE-FOR-LIKE</b>
        <span>W{D.meta.partial_week} is partial: {D.meta.partial_week_days}. LY W{D.meta.partial_week} is cut to the same days. Counts are sample-scale; read shares and ratios.</span>
        <div style={{ flex: 1 }} />
        <button type="button" className="btn-plain link" onClick={() => setOpen(true)} style={{ whiteSpace: "nowrap", fontWeight: 700 }}>Naive vs like-for-like →</button>
      </div>
      {open && (
        <div onClick={() => setOpen(false)} style={{ position: "fixed", inset: 0, zIndex: 50, background: "rgba(31,38,54,.45)", display: "flex", alignItems: "flex-start", justifyContent: "center", padding: "80px 20px", overflow: "auto" }}>
          <div className="fade-in" role="dialog" aria-modal="true" aria-label="Naive vs like-for-like" onClick={(e) => e.stopPropagation()} style={{ width: 780, maxWidth: "100%", padding: 24, background: "#fff", boxShadow: "0 30px 80px rgba(0,0,0,.35)" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 12 }}>
              <b style={{ fontFamily: MONO, fontSize: 11 }}>LIKE-FOR-LIKE</b><div style={{ flex: 1 }} />
              <button type="button" onClick={() => setOpen(false)} className="btn-plain" aria-label="Close" autoFocus style={{ fontSize: 20, lineHeight: 1 }}>×</button>
            </div>
            <BasisSwitch big={60} />
          </div>
        </div>
      )}
    </>
  );
}
