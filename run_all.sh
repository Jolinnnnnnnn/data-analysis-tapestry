#!/usr/bin/env bash
# Rebuild everything from data/raw (read-only). Usage: ./run_all.sh [--clean]
#   scripts/01–14  analysis → data/processed/metrics.json, anomalies.json, findings audit
#   scripts/15–18  AI pipeline → facts, Claude-worded texts, number validator, web/src/data/app.json
#   web/           parity check (browser validator == Python validator) + production build
# Exits non-zero on any failure, including an AI-written number that doesn't match its facts.
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
  rm -rf data/processed/* outputs/tables/* outputs/figures/* data/dashboard/*
fi
mkdir -p data/processed outputs/tables outputs/figures data/dashboard/facts
for s in scripts/[0-9][0-9]_*.py; do
  echo "== $s"
  "$PY" -W ignore "$s" | tail -1
done
echo "OK analysis: $(ls outputs/tables | wc -l | tr -d ' ') tables, $(ls outputs/figures | wc -l | tr -d ' ') figures"
if command -v npm >/dev/null 2>&1; then
  [ -d web/node_modules ] || npm --prefix web ci --no-audit --no-fund --silent
  echo "== web: validator parity"
  npm --prefix web run --silent verify
  echo "== web: production build"
  npm --prefix web run --silent build > /dev/null
  echo "OK web: web/dist built"
else
  echo "npm not found: skipped the web parity check and build"
fi
