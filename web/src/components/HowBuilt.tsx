import { BasisSwitch } from "./LikeForLike";
import { C, CHECK_INFO, D, DEMOS, GOALS, MONO, dateWords, fmtNum, fmtPct, setUrl } from "../lib/core";
import { VOCAB } from "../lib/validator.js";
import { TEMPLATES } from "../lib/ask/catalog";

export default function HowBuilt() {
  const b = D.build;
  const c = D.meta.counts;
  const dq = D.meta.data_quality;
  const sh = D.stock_demand_shares;
  const tabby = sh.families.find((f: any) => f.family === "Tabby");
  const stat = (v: string, l: string) => (
    <div style={{ flex: "1 1 170px", padding: "18px 20px", background: "#fff" }}>
      <div className="cond" style={{ fontWeight: 800, fontSize: 40 }}>{v}</div>
      <div style={{ fontSize: 13, color: C.muted }}>{l}</div>
    </div>
  );
  const tile = (n: string, k: string, t: string, d: string, bg: string, ink = "#fff", sub = C.onDarkMuted) => (
    <div style={{ padding: 16, background: bg, color: ink }}>
      <div style={{ fontFamily: MONO, fontSize: 11, fontWeight: 700 }}>{n} {k}</div>
      <div style={{ marginTop: 20, fontSize: 15, fontWeight: 700 }}>{t}</div>
      <div style={{ marginTop: 4, fontSize: 12, color: sub }}>{d}</div>
    </div>
  );
  const card = (t: string, d: string) => (
    <div className="panel" style={{ padding: "18px 20px" }}><b style={{ fontSize: 15 }}>{t}</b><p style={{ margin: "6px 0 0", fontSize: 13.5, lineHeight: 1.55, color: C.body }}>{d}</p></div>
  );
  return (
    <main className="pad-x" style={{ padding: "32px 40px 64px", display: "flex", flexDirection: "column", gap: 36 }}>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 1, background: C.hair, boxShadow: `0 0 0 1px ${C.hair}` }}>
        {stat(fmtNum(c.lines_total), "transaction lines")}
        {stat(fmtNum(c.inventory_snapshots), "stock snapshots")}
        {stat(String(D.rules.length), "monitoring rules")}
        {stat(`${b.texts_pass}/${b.texts_total}`, `AI texts passed all ${CHECK_INFO.length} checks · ${fmtNum(b.numbers_checked)} numbers`)}
        {stat(`${b.corpus_pass}/${b.corpus_total}`, "adversarial test cases give the expected verdict, in Python and in this page")}
        {stat(`${b.findings_audit_pass}/${b.findings_audit_total}`, "headline findings re-derived from metrics.json")}
      </div>

      <section>
        <h2 className="cond" style={{ margin: "0 0 14px", fontWeight: 800, fontSize: 30 }}>Pipeline</h2>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(150px,1fr))", gap: 4 }}>
          {tile("01", "DATA", "Transactions + stock snapshots", `FY26 vs FY25, W23–W30 · ${fmtNum(c.lines_total)} lines`, C.charcoal)}
          {tile("02", "METRICS", "metrics.json", "scripts 01–11 · ratios from totals", C.charcoal)}
          {tile("03", "RULES", "anomalies.json", `12_anomalies.py · ${D.rules.length} thresholds · ${D.anomaly_meta.n_anomalies} alerts`, C.thistle, C.ink, C.body)}
          {tile("04", "AI WRITES", "From the week's facts only", `${b.model} · no new math, no new numbers`, GOALS[1].hue, "#fff", "#EFE6FA")}
          {tile("05", "VALIDATOR", "Every number → the fact it cites", `${CHECK_INFO.length} checks · one miss = held back, build fails`, C.sapphire, "#fff", "#E2ECFB")}
          {tile("06", "UI", "Selects, formats, animates", "re-checks every text in the browser", C.chrome)}
        </div>
        <p style={{ margin: "12px 0 0", fontSize: 13.5, color: C.body, maxWidth: 820, lineHeight: 1.55 }}>
          The AI never types a figure. It writes a placeholder that names a fact and a format, the build renders it, and the validator then checks that each printed number is the fact it cites and that the words around it agree with that fact.
          The validator runs twice with two implementations: in Python at build time, and in this page before any AI text is shown. A parity check makes sure both agree on every text, every demo and the shared test corpus.
        </p>
        <p style={{ margin: "10px 0 0", fontSize: 13.5, color: C.body, maxWidth: 820, lineHeight: 1.55 }}>
          Ask follows the same rule. Claude only picks one of {TEMPLATES.length} query templates and fills its parameters, as structured output against a fixed schema; it never sees or writes a data value.
          Code then checks that choice (the week exists, any product or region named can actually be filtered, any change the question takes for granted is true) and writes the answer from metrics.json.
          If Claude is unavailable, a keyword parser picks the template and the same checks run. {" "}
          <span className="link" onClick={() => setUrl({ screen: "ask" }, true)} style={{ fontWeight: 700 }}>Try Ask →</span>
        </p>
      </section>

      <section>
        <h2 className="cond" style={{ margin: "0 0 6px", fontWeight: 800, fontSize: 30 }}>What the validator checks</h2>
        <p style={{ margin: "0 0 16px", fontSize: 14, color: C.body, maxWidth: 820, lineHeight: 1.55 }}>
          Words are matched to the nearest number in their clause. When a sentence is too loose to check, the validator holds it back and the wording is changed, never the rule.
        </p>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(250px,1fr))", gap: 12 }}>
          {CHECK_INFO.map((ck, i) => {
            const demo = DEMOS.find((d) => d.check === ck.id);
            return (
              <div key={ck.id} className="panel" style={{ display: "flex", flexDirection: "column", padding: "16px 18px" }}>
                <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", gap: 8 }}>
                  <b style={{ fontSize: 15 }}><span style={{ fontFamily: MONO, fontSize: 11, color: C.muted }}>{String(i + 1).padStart(2, "0")}</span> {ck.title}</b>
                  <span style={{ fontFamily: MONO, fontSize: 11, color: C.muted, whiteSpace: "nowrap" }}>{fmtNum(b.checks_run[ck.id])} runs</span>
                </div>
                <p style={{ flex: 1, margin: "6px 0 0", fontSize: 13.5, lineHeight: 1.55, color: C.body }}>{ck.text}</p>
                {demo && <span className="link" onClick={() => setUrl({ screen: "briefing", demo: demo.id }, true)} style={{ marginTop: 10, fontSize: 13, fontWeight: 700, color: C.crit }}>See it stop {demo.label.toLowerCase()} →</span>}
              </div>
            );
          })}
        </div>
        <div className="panel" style={{ marginTop: 12, padding: "16px 18px" }}>
          <b style={{ fontSize: 15 }}>What it does not check</b>
          <ul style={{ margin: "8px 0 0", paddingLeft: 18, fontSize: 13.5, lineHeight: 1.6, color: C.body }}>
            {VOCAB.unchecked.map((t: string) => <li key={t}>{t}</li>)}
          </ul>
        </div>
      </section>

      <section>
        <h2 className="cond" style={{ margin: "0 0 6px", fontWeight: 800, fontSize: 30 }}>What surprised us</h2>
        <p style={{ margin: "0 0 16px", fontSize: 14, color: C.body, maxWidth: 720 }}>
          The data stops on {dateWords(dq.ty_last_sale_date)}, so this year's W{D.meta.partial_week} only covers {D.meta.partial_week_days} days while last year's is a full week. Comparing them as-is shaves {D.meta.basis_alternatives.naive_gap_pts.toFixed(1)} points off the headline.
        </p>
        <div className="panel" style={{ padding: 24 }}><BasisSwitch /></div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(260px,1fr))", gap: 12, marginTop: 12 }}>
          {card("Stock stopped following demand.", `Family stock share and demand share correlated at ${sh.corr_ly.toFixed(2)} last year and ${sh.corr_ty.toFixed(2)} this year. Tabby is ${fmtPct(tabby.demand_share_ty)} of demand but ${fmtPct(tabby.stock_share_ty)} of stock.`)}
          {card("No cohorts are possible.", `Every transaction is one line, and ${fmtNum(c.cust_ids_total)} customer IDs on ${fmtNum(c.lines_total)} lines repeat about as often as random IDs would (${dq.cust_id_repeat_surplus_observed} repeats vs ≈${dq.cust_id_repeat_surplus_expected_random.toFixed(1)} expected), so retention is a labelled proxy.`)}
          {card("A snapshot from the future.", `TY sales stop on ${dateWords(dq.ty_last_sale_date)}, yet an end-of-week W${D.meta.partial_week} stock snapshot exists for every family. It's used as the latest position.`)}
        </div>
      </section>

      <section style={{ display: "flex", flexWrap: "wrap", gap: 24 }}>
        <div style={{ flex: "1 1 480px", minWidth: 0 }}>
          <h2 className="cond" style={{ margin: "0 0 14px", fontWeight: 800, fontSize: 30 }}>The AI's system prompts</h2>
          {(["summary", "headline", "card"] as const).map((k) => (
            <div key={k} style={{ marginBottom: 8 }}>
              <div style={{ fontFamily: MONO, fontSize: 11, fontWeight: 700, color: C.muted, marginBottom: 4 }}>{k.toUpperCase()}</div>
              <pre style={{ margin: 0, padding: 18, background: C.chrome, color: "#E6E9F0", font: `400 12.5px/1.65 ${MONO}`, whiteSpace: "pre-wrap" }}>{b.system_prompts[k]}</pre>
            </div>
          ))}
          <p style={{ fontSize: 12.5, color: C.muted, lineHeight: 1.5 }}>Texts on this page were written by {b.model} at build time from each week's facts file ({Object.entries(b.generated_by_counts).map(([k, v]) => `${v} ${k}`).join(", ")}). Set an API key and the build regenerates them live through the same validator.</p>
        </div>
        <div style={{ flex: "1 1 360px", minWidth: 0 }}>
          <h2 className="cond" style={{ margin: "0 0 14px", fontWeight: 800, fontSize: 30 }}>Definitions</h2>
          <dl style={{ margin: 0, fontSize: 13.5, lineHeight: 1.5 }}>
            {[["Like-for-like", D.meta.basis], ...Object.entries(D.meta.definitions), ["Ratios", D.meta.ratio_rule]].map(([t, d]: any) => (
              <div key={t} style={{ display: "grid", gridTemplateColumns: "140px 1fr", gap: 12, padding: "9px 0", borderBottom: `1px solid ${C.hair}` }}>
                <dt style={{ fontWeight: 700, fontFamily: MONO, fontSize: 12 }}>{t}</dt><dd style={{ margin: 0, color: C.body }}>{d}</dd>
              </div>
            ))}
          </dl>
        </div>
      </section>
    </main>
  );
}
