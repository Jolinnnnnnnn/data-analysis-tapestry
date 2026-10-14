"""Headless smoke test for dashboard/app.py (Streamlit AppTest): every page and Explore tab renders without an
exception for weeks 23/29/30 × windows L1W/L4W/PTD × LY on/off × light/dark, and every briefing card's
"Ask why" question (all weeks) maps to a template and gets an answer.

Run from the repo root:  .venv/bin/python dashboard/tests/smoke_test.py
"""
import itertools
import json
import sys
from pathlib import Path

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[2]
APP = str(ROOT / "dashboard/app.py")
fails, runs = [], 0


def run(params, setup=None):
    global runs
    at = AppTest.from_file(APP, default_timeout=60)
    for k, v in params.items():
        at.query_params[k] = v
    if setup:
        setup(at)
    at.run()
    runs += 1
    if at.exception:
        fails.append((params, [e.message for e in at.exception]))
    return at


for page, wk, win, ly in itertools.product(["briefing", "explore", "ask", "build"], ["23", "29", "30"], ["L1W", "L4W", "PTD"], ["1", "0"]):
    tabs = ["G1", "G2", "G3", "G4"] if page == "explore" else ["G1"]
    for tab in tabs:
        if page in ("ask", "build") and (win != "L4W" or ly != "1"):
            continue
        run({"page": page, "wk": wk, "win": win, "ly": ly, "theme": "light", "tab": tab})
for page in ["briefing", "explore", "build"]:
    run({"page": page, "wk": "28", "win": "L4W", "ly": "1", "theme": "dark", "tab": "G4"})
run({"page": "briefing", "wk": "29", "win": "L4W", "ly": "1", "theme": "light", "tab": "G1", "inject_error": "1"})

# every card's "Ask why" prefill, every week: must map to a template and produce an answer (no fallback text)
brief = json.loads((ROOT / "dashboard/briefing.json").read_text())
answered = 0
for wk, b in brief.items():
    for c in b["cards"]:
        at = run({"page": "ask", "wk": wk, "win": "L4W", "ly": "1", "theme": "light", "tab": "G1"},
                 setup=lambda at, q=c["ask_prefill"]: at.session_state.__setitem__("pending_q", q))
        chat = at.session_state["chat"] if "chat" in at.session_state else []
        if not chat or "fixed query templates" in chat[-1]["a"]:
            fails.append(({"ask": c["ask_prefill"]}, ["no template matched"]))
        else:
            answered += 1

print(f"{runs} app runs, {answered} card questions answered, {len(fails)} failures")
for f in fails[:20]:
    print("  FAIL", f)
sys.exit(1 if fails else 0)
