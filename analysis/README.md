# Analysis: data structure & findings

Consumer Intelligence & Analytics exercise on `TYLY_data_sample.xlsx` (FY26 vs FY25, fiscal weeks W23–W30). This folder holds the finished analysis; the dashboard and deck are built from its outputs.

## Rebuild
```bash
analysis/run_all.sh --clean     # analysis only
./run_all.sh --clean            # from the repo root: analysis → dashboard → deck
```
Uses the repo-root `.venv` (created if missing: pandas, openpyxl, matplotlib, numpy, tabulate) and runs `scripts/01…14` in order. The raw copy in `data/raw/` is read-only.

## Where things are (paths relative to `analysis/`)
| What | Where |
|---|---|
| Working memory / assumptions | `NOTES.md` |
| Interpretation choices (D1–D13) | `DECISIONS.md` |
| Verified findings (F1–F15) + ranked recommendations (R1–R3) | `FINDINGS.md` |
| Iteration log | `HISTORY.md` |
| AI prompts + verification | `PROMPTS.md` |
| Hypothesis backlog | `QUESTIONS.md` |
| Dashboard source of truth | `data/processed/metrics.json`, `anomalies.json`, `metrics_schema.md` |
| Tables / charts | `outputs/tables/`, `outputs/figures/` |
| Data dictionary | `outputs/tables/data_dictionary.md` |
| Next builds | `../dashboard/PROMPT.md`, `../deck/PROMPT.md` (both follow `../design/DESIGN_SIGNAL.md`) |
