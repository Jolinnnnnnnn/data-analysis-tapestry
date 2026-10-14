# TYLY take-home: data structure & analysis

Consumer Intelligence & Analytics exercise on `TYLY_data_sample.xlsx` (FY26 vs FY25, fiscal weeks W23–W30).

## Rebuild everything
```bash
./run_all.sh --clean
```
This creates `.venv` if needed (pandas, openpyxl, matplotlib, numpy, tabulate), then runs `scripts/01…14` in order. The raw file in `data/raw/` is read-only.

## Where things are
| What | Where |
|---|---|
| Working memory / assumptions | `NOTES.md` |
| Interpretation choices (D1–D13) | `DECISIONS.md` |
| Verified findings (F1–F15) + ranked recommendations (R1–R3) | `FINDINGS.md` |
| Iteration log | `HISTORY.md` |
| AI prompts + verification | `PROMPTS.md` |
| Dashboard source of truth | `data/processed/metrics.json`, `anomalies.json`, `metrics_schema.md` |
| Tables / charts | `outputs/tables/`, `outputs/figures/` |
| Data dictionary | `outputs/tables/data_dictionary.md` |
| Next-session prompts | `handoff/PROMPT_C_dashboard.md`, `handoff/PROMPT_D_deck.md` |
