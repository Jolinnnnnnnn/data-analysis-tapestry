# TYLY take-home: analysis + weekly dashboard

Consumer Intelligence & Analytics exercise on `TYLY_data_sample.xlsx` (FY26 vs FY25, fiscal weeks W23–W30).

## Rebuild everything
```bash
./run_all.sh --clean
```
Creates `.venv` if needed, runs `scripts/01…14` (analysis → `metrics.json`, `anomalies.json`, findings audit) and `scripts/15…18` (AI pipeline: facts → Claude-worded texts → number validator → `web/src/data/app.json`), then the web parity check and production build. It fails if any AI-written number doesn't match its facts. The raw file in `data/raw/` is read-only.

## Dashboard
```bash
npm --prefix web install
npm --prefix web run dev
```
Static React app in `web/` (deploys to Vercel with Root Directory `web`; see `web/README.md`). Weekly AI briefing (headline, summary, 5 flagged items) with every number validated against `metrics.json`, rules and alerts, goal-by-goal Explore views with a season playhead, drill-down and LY→TY morphs, template-based Ask, and a "How it was built" page.

## Where things are
| What | Where |
|---|---|
| Working memory / assumptions | `NOTES.md` |
| Interpretation choices (D1–D13 analysis, D14–D24 dashboard) | `DECISIONS.md` |
| Verified findings (F1–F15) + ranked recommendations (R1–R3) | `FINDINGS.md` |
| Iteration log | `HISTORY.md` |
| AI prompts + verification | `PROMPTS.md` |
| Dashboard source of truth | `data/processed/metrics.json`, `anomalies.json`, `metrics_schema.md` |
| AI texts (written by Claude) + validator outputs | `ai/session_texts.json`, `data/dashboard/` |
| Web app | `web/` |
| Tables / charts | `outputs/tables/`, `outputs/figures/` |
| Data dictionary | `outputs/tables/data_dictionary.md` |
