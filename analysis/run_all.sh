#!/usr/bin/env bash
# Rebuild the analysis from analysis/data/raw (read-only). Usage: analysis/run_all.sh [--clean]
set -euo pipefail
cd "$(dirname "$0")"
REPO="$(cd .. && pwd)"
PY="${PY:-$REPO/.venv/bin/python}"
if [ ! -x "$PY" ]; then
  python3 -m venv "$REPO/.venv" && "$REPO/.venv/bin/pip" install -q pandas openpyxl matplotlib numpy tabulate
  PY="$REPO/.venv/bin/python"
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
