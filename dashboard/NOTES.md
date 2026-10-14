# NOTES: dashboard working memory (rewrite freely)

## What exists
- `app.py`: single-file Streamlit app (Signal design). Pages: Briefing (AI summary + 5 rule-driven cards + "What I'm watching" rail), Explore = Classic dashboard (G1 Performance, G2 Gen Z, G3 Products, G4 Inventory), Ask (template Q&A), How it was built. URL query params mirror the state (`page, wk, win, ly, theme, tab`); `?inject_error=1` demos the validator block.
- Pipeline: `scripts/15_build_facts.py` → `facts/W<wk>.json`, `facts/W<wk>_cards.json`; `scripts/16_generate_summaries.py` → `summaries.json`, `briefing.json`; `scripts/17_validate_summaries.py` → validation + `build_stats.json` (exit 1 on any FLAGGED number).
- `pregenerated/session_texts.json`: the Claude-written texts (summaries + cards), md5-stamped against their facts.
- `tests/`: `smoke_test.py` (140 headless runs + 40 Ask prefills; part of run_all), `trace_numbers.py` (number → facts → metrics.json trace), `tile_spotcheck.py` (tiles vs analysis outputs).
- `verification/`: number_trace.md (W28–W30), tile_spotcheck.md. `screenshots/`: app views + reference views.

## Inputs the app reads
`analysis/data/processed/metrics.json`, `anomalies.json`; `dashboard/summaries.json`, `briefing.json`, `build_stats.json`, `facts/*.json`. Nothing else.

## Gotchas
- Python 3.9: no nested same-quote f-strings (`f'{x["k"]}'` inside `f"..."`), no `match`, no `X | Y` types.
- `st.html` drops `<style>`-only content, so the CSS is injected with `st.markdown(..., unsafe_allow_html=True)`.
- `st.cache_data` ignores parameters that start with `_`; the loader keys on `mtime` (not `_mtime`).
- Widget keys that live on one page (tabs, sort, family) are mirrored into persistent session keys; sidebar widgets own `wk`, `win`, `ly`.
- After editing a pregenerated text: run `16_generate_summaries.py --stamp` only after `17` passes on it. Stamping asserts "written from these facts".
- After changing `15_build_facts.py`, the facts md5s change, so the pregenerated texts go stale (template used) until they are re-validated and re-stamped. That is intended.
- The theme switch uses `streamlit.config.set_option` (process-wide): two viewers on different themes would fight. That's acceptable for a local single-user tool.

## Current state
- DONE (2026-10-13). 48/48 texts PASS (491 numbers); trace 491/491; tiles 10/10; smoke 140 runs / 0 exceptions; clean rebuild byte-identical. See HISTORY Iteration 8 for what's open.
