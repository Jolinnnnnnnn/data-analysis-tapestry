#!/usr/bin/env bash
# Rebuild the analysis from data/raw (read-only). Usage: ./run_all.sh [--clean]
# Uses the repo-root virtualenv (../.venv); the root ./run_all.sh creates it if missing.
set -euo pipefail
cd "$(dirname "$0")"
PY="${PY:-../.venv/bin/python}"
if [ ! -x "$PY" ]; then
  python3 -m venv ../.venv && ../.venv/bin/python -m pip install -q pandas openpyxl matplotlib numpy tabulate streamlit plotly
fi
if [ "${1:-}" = "--clean" ]; then
  rm -rf data/processed/* outputs/tables/* outputs/figures/*
fi
mkdir -p data/processed outputs/tables outputs/figures
for s in scripts/[0-9][0-9]_*.py; do
  echo "== analysis/$s"
  "$PY" -W ignore "$s" > /dev/null
done
echo "OK analysis: $(ls outputs/tables | wc -l | tr -d ' ') tables, $(ls outputs/figures | wc -l | tr -d ' ') figures, processed: $(ls data/processed | tr '\n' ' ')"
