# TYLY take-home: analysis + weekly dashboard

Consumer Intelligence & Analytics exercise on `TYLY_data_sample.xlsx` (FY26 vs FY25, fiscal weeks W23–W30).

## Rebuild and run
```bash
./run_all.sh --clean
```
```bash
.venv/bin/streamlit run dashboard/app.py
```
`run_all.sh` creates `.venv` if needed, rebuilds the analysis (`analysis/scripts/01…14` → `metrics.json`, `anomalies.json`, findings audit), then the dashboard pipeline (`dashboard/scripts/15…17`: facts → AI-worded texts → number validator) and a headless app smoke test. It exits non-zero if any AI-written number can't be traced to the facts. The raw file in `analysis/data/raw/` is read-only.

## Where things are
| What | Where |
|---|---|
| Analysis (data understanding, D1–D13, findings F1–F15, R1–R3) | `analysis/` (see `analysis/README.md`) |
| Dashboard source of truth | `analysis/data/processed/metrics.json`, `anomalies.json`, `metrics_schema.md` |
| Dashboard app (D1) | `dashboard/app.py` (see `dashboard/README.md`) |
| AI pipeline + validator | `dashboard/scripts/15_build_facts.py`, `16_generate_summaries.py`, `17_validate_summaries.py` |
| Dashboard decisions / log / prompts | `dashboard/DECISIONS.md` (D14+), `dashboard/HISTORY.md`, `dashboard/PROMPTS.md` (P17+) |
| Verification evidence | `dashboard/verification/`, `dashboard/screenshots/`, `analysis/outputs/tables/14_findings_audit.md` |
| Visual design spec | `design/DESIGN_SIGNAL.md` |
