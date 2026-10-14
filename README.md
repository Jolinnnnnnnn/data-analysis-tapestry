# TYLY take-home: analysis → dashboard → deck

Consumer Intelligence & Analytics exercise on `TYLY_data_sample.xlsx` (FY26 vs FY25 sales at transaction-line grain, fiscal weeks W23–W30, plus weekly stock by product family).

| Folder | What | Status |
|---|---|---|
| [`analysis/`](analysis/) | Data structure decisions, analysis scripts, findings (F1–F15), recommendations (R1–R3), and the dashboard source of truth (`analysis/data/processed/metrics.json`, `anomalies.json`) | Done |
| [`dashboard/`](dashboard/) | D1: Streamlit weekly dashboard with an accuracy-guarded AI briefing | To build: run [`dashboard/PROMPT.md`](dashboard/PROMPT.md) |
| [`deck/`](deck/) | D2: 5–8 slide findings deck | To build after the dashboard: run [`deck/PROMPT.md`](deck/PROMPT.md) |
| [`design/`](design/) | Shared visual spec (Signal style) for dashboard and deck | [`design/DESIGN_SIGNAL.md`](design/DESIGN_SIGNAL.md) |

`TYLY_data_sample.xlsx` at the root is the original input and is never modified; the analysis works on its read-only copy in `analysis/data/raw/`.

## Rebuild everything
```bash
./run_all.sh --clean
```
Creates `.venv` if needed, runs `analysis/run_all.sh`, then the dashboard and deck stages once they exist.

Start with [`analysis/FINDINGS.md`](analysis/FINDINGS.md) for the story and [`analysis/DECISIONS.md`](analysis/DECISIONS.md) for the definition choices.
