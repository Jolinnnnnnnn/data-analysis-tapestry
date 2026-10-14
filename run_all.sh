#!/usr/bin/env bash
# Rebuild the whole project: analysis → dashboard pipeline → deck. Usage: ./run_all.sh [--clean]
# Each stage runs only if it exists; dashboard/ and deck/ start as handoff prompts (PROMPT.md).
set -euo pipefail
cd "$(dirname "$0")"
export PY="$(pwd)/.venv/bin/python"
if [ ! -x "$PY" ]; then
  python3 -m venv .venv && .venv/bin/pip install -q pandas openpyxl matplotlib numpy tabulate
fi

analysis/run_all.sh "$@"

for stage in dashboard deck; do
  if [ -x "$stage/run_all.sh" ]; then
    "$stage/run_all.sh" "$@"
  elif compgen -G "$stage/scripts/[0-9][0-9]_*.py" > /dev/null; then
    for s in "$stage"/scripts/[0-9][0-9]_*.py; do
      echo "== $s"
      "$PY" -W ignore "$s" > /dev/null
    done
  else
    echo "-- $stage: not built yet (see $stage/PROMPT.md)"
  fi
done
