# NOTES — working memory (rewrite freely)

## Data understanding
- 3 sheets, clean headers (row 1). Data: 3,609 lines (TY FY26 1,829 / LY FY25 1,780), W23–W30, long format with FISCAL_YR flag. Inventory: 21 families × 8 wks × 2 yrs = 336 snapshots; family names match exactly.
- Fiscal weeks Sun–Sat, 364-day aligned. **TY W30 partial (Sun–Wed, as-of 2026-08-19)**; last full TY week = W29.
- 1 line = 1 TXN_ID. CUST_ID non-durable (random-collision pattern), so no behavioural retention. COHORT_STATUS uses full history outside the extract.
- Hero = Tabby + Pillow Tabby only. Halo = Rogue, Sculpted Sandal, Knit Dress, Tailored Jacket, Trench, Jewelry.

## Assumptions (full detail in DECISIONS.md)
- A1 YoY basis = PTD like-for-like (LY W30 Thu–Sat excluded, 90 lines) [D3]
- A2 line = txn; customers = distinct CUST_ID per period; frequency ≈ 1 [D4, D5]
- A3 New = COHORT_STATUS 'New'; alt = New+Reactivated [D6]
- A4 Gen Z = CUST_AGE_GROUP label [D7]
- A5 Retention proxies = returning share/count, Insider attach of new [D8]
- A6 WOS = EOH / trailing ≤4 full-week avg units; scale check passed (implied receipts never <0) [D9]
- A7 L1W = W29, L4W = W26–29, WTD = W30 Sun–Wed [D10]
- A8 Equal sampling rate TY/LY [D11]; significance testing on all key comparisons [D12]

## Data quality issues
- TY W30 partial; W30 inventory snapshot dated after last sale (F13).
- CUST_ID unusable as a key (F14). No returns/discount fields; DEMAND_AMT net.

## Current state
- ANALYSIS SESSION COMPLETE (13 iterations). FINDINGS F1–F15 + R1–R3; metrics.json / anomalies.json / metrics_schema.md built; findings audit 30/30; run_all reproducible.
- DASHBOARD BUILT as a static web app (web/, React + Vite, Vercel) from the Claude Design file; AI pipeline scripts 15–18; see DECISIONS D14–D24, HISTORY 14–16. handoff/PROMPT_C (Streamlit) is superseded; PROMPT_D (deck) still open.
- ASK IS LIVE-ROUTED (D26, Iteration 18): Claude picks one of 12 templates via `web/api/ask.ts` (needs `ANTHROPIC_API_KEY` in the Vercel project), code checks and answers; keyword parser fallback. handoff/PROMPT_E (semantic validator) is open and reserves D25 / Iteration 17 / P20.

## Gotchas
- Use `.venv/bin/python -W ignore`. `./run_all.sh --clean` rebuilds analysis + AI texts + web data, then runs the JS parity check and `vite build`.
- After editing a text in ai/session_texts.json: validate (scripts/17), then `scripts/16_generate_summaries.py --stamp`. Any facts change makes texts stale → template until re-stamped.
- Local dev: `npm --prefix web run dev` (port 5199). For live Ask locally, put `ANTHROPIC_API_KEY=...` in `web/.env.local` (git-ignored); `npm --prefix web run ask-live` prints live routes (spends credits).
- Never sum ON_HAND_UNITS across weeks (summing across families within a week is fine).
- Ratio metrics (AOV, UPT, AUR) must be recomputed from totals, never averaged across weeks.
- 08 depends on 07 output (g3 scorecard); 10 depends on 08.
