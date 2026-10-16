# TYLY take-home: data analysis

Consumer Intelligence & Analytics exercise on `TYLY_data_sample.xlsx` (FY26 vs FY25, fiscal weeks W23–W30).

## Rebuild everything
```bash
./run_all.sh --clean
```
Creates `.venv` if needed and runs `scripts/01…14` (cleaning → G1–G4 analysis → challenge and sizing → `metrics.json`, `anomalies.json`, findings audit). The raw file in `data/raw/` is read-only.

## Dashboard and deck
Not built yet: starting over from a clean slate. The first dashboard (React web app + AI briefing pipeline) and the deck handoff prompt are archived at git tag `archive/dashboard-v1` (`git checkout archive/dashboard-v1` to see it). `data/processed/metrics.json`, `anomalies.json` and `metrics_schema.md` are the data source for the new one.

## Where things are
| What | Where |
|---|---|
| Working memory / assumptions | `NOTES.md` |
| Interpretation choices (D1–D13, D16) | `DECISIONS.md` |
| Verified findings (F1–F15) + ranked recommendations (R1–R3) | `FINDINGS.md` |
| Iteration log | `HISTORY.md` |
| AI prompts + verification | `PROMPTS.md` |
| Hypothesis backlog | `QUESTIONS.md` |
| Metrics (dashboard source of truth) | `data/processed/metrics.json`, `anomalies.json`, `metrics_schema.md` |
| Tables / charts | `outputs/tables/`, `outputs/figures/` |
| Data dictionary | `outputs/tables/data_dictionary.md` |
