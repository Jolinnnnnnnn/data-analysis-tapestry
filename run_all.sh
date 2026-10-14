#!/usr/bin/env bash
# Rebuild everything from data/raw (read-only). Usage: ./run_all.sh [--clean]
set -euo pipefail
cd "$(dirname "$0")"
PY=".venv/bin/python"
if [ ! -x "$PY" ]; then
  python3 -m venv .venv && .venv/bin/pip install -q pandas openpyxl matplotlib numpy tabulate
fi
if [ "${1:-}" = "--clean" ]; then
  rm -rf data/processed/* outputs/tables/* outputs/figures/*
fi
mkdir -p data/processed outputs/tables outputs/figures
for s in scripts/[0-9][0-9]_*.py; do
  echo "== $s"
  "$PY" -W ignore "$s" > /dev/null
done
echo "OK: $(ls outputs/tables | wc -l | tr -d ' ') tables, $(ls outputs/figures | wc -l | tr -d ' ') figures, processed: $(ls data/processed | tr '\n' ' ')"
