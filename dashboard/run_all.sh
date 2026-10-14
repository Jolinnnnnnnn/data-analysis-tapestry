#!/usr/bin/env bash
# Dashboard pipeline: facts (15) → AI-worded summaries + cards (16) → number validator (17) → app smoke test,
# KPI tile spot-check and the W28–W30 number trace (verification/).
# Called by the repo-root ./run_all.sh after analysis/run_all.sh. Usage: ./run_all.sh [--clean]
# Exits non-zero if the validator FLAGS any number (or its self-test fails) or the app raises in any view.
set -euo pipefail
cd "$(dirname "$0")"
PY="${PY:-../.venv/bin/python}"
if [ "${1:-}" = "--clean" ]; then
  rm -rf facts/* summaries.json briefing.json build_stats.json
fi
mkdir -p facts
for s in scripts/[0-9][0-9]_*.py; do
  echo "== dashboard/$s"
  "$PY" -W ignore "$s" | tail -1
done
for t in smoke_test tile_spotcheck; do
  echo "== dashboard/tests/$t.py"
  "$PY" -W ignore tests/$t.py 2>/dev/null | tail -1
done
echo "== dashboard/tests/trace_numbers.py (W28 W29 W30)"
"$PY" -W ignore tests/trace_numbers.py 28 29 30
echo "OK dashboard: $(ls facts | wc -l | tr -d ' ') facts files, summaries.json, briefing.json, build_stats.json"
