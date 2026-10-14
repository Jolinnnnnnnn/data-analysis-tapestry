#!/usr/bin/env bash
# Rebuild everything: analysis (metrics.json, anomalies.json) then the dashboard pipeline
# (facts -> AI-worded summaries/cards -> number validator). Usage: ./run_all.sh [--clean]
# Fails (non-zero exit) if any script fails, including a FLAGGED summary in the validator.
set -euo pipefail
cd "$(dirname "$0")"
PY=".venv/bin/python"
if [ ! -x "$PY" ]; then
  python3 -m venv .venv
fi
# pip is invoked via the interpreter (the venv's pip shebang can go stale if the repo moves).
if ! "$PY" -c "import pandas, openpyxl, matplotlib, numpy, tabulate, streamlit, plotly" 2>/dev/null; then
  "$PY" -m pip install -q pandas openpyxl matplotlib numpy tabulate streamlit plotly
fi
export PY="$(pwd)/$PY"
./analysis/run_all.sh "$@"
if [ -x dashboard/run_all.sh ]; then
  ./dashboard/run_all.sh "$@"
else
  if [ "${1:-}" = "--clean" ]; then
    rm -rf dashboard/facts/* dashboard/summaries.json dashboard/briefing.json dashboard/build_stats.json
  fi
  mkdir -p dashboard/facts
  for s in dashboard/scripts/[0-9][0-9]_*.py; do
    echo "== $s"
    "$PY" -W ignore "$s"
  done
fi
echo "OK: run_all complete. Launch: .venv/bin/streamlit run dashboard/app.py"
