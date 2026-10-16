#!/usr/bin/env bash
# Rebuild everything from data/raw (read-only). Usage: ./run_all.sh [--clean]
#   scripts/01–14  analysis → data/processed/metrics.json, anomalies.json, findings audit
# Exits non-zero on any failure (scripts assert their own reconciliations).
set -euo pipefail
cd "$(dirname "$0")"
PY=".venv/bin/python"
if [ ! -x "$PY" ]; then
  python3 -m venv .venv
fi
# pip via the interpreter: the venv's pip shebang goes stale if the repo folder moves
if ! "$PY" -c "import pandas, openpyxl, matplotlib, numpy, tabulate" 2>/dev/null; then
  "$PY" -m pip install -q pandas openpyxl matplotlib numpy tabulate
fi
if [ "${1:-}" = "--clean" ]; then
  rm -rf data/processed/* outputs/tables/* outputs/figures/*
fi
mkdir -p data/processed outputs/tables outputs/figures
for s in scripts/[0-9][0-9]_*.py; do
  echo "== $s"
  "$PY" -W ignore "$s" | tail -1
done
echo "OK analysis: $(ls outputs/tables | wc -l | tr -d ' ') tables, $(ls outputs/figures | wc -l | tr -d ' ') figures"
