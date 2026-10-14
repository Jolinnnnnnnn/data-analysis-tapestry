"""TYLY weekly dashboard: Signal design (design/DESIGN_SIGNAL.md), Streamlit + Plotly.

Run from the repo root:  .venv/bin/streamlit run dashboard/app.py

Reads ONLY files derived from the analysis layer:
  analysis/data/processed/metrics.json, anomalies.json     (the single source of truth)
  dashboard/summaries.json, briefing.json, build_stats.json (AI-worded texts + validator results, built from the two above)
  dashboard/facts/*.json                                   (the exact facts each AI text was written from)
The app does NO ad-hoc math: it selects and formats precomputed fields. The only arithmetic is drawing
geometry (bar widths in the HTML micro-charts) and display unit formatting (0.128 → +12.8%, 71311 → $71.3K).
Every AI text is re-validated here with the same function the build uses; an unverified number blocks the text.
"""
import html
import importlib.util
import json
import os
import re
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "analysis/data/processed"
DASH = ROOT / "dashboard"

# =====================================================================================================
# THEME: tokens from design/DESIGN_SIGNAL.md §2. CSS and Plotly both read these.
# =====================================================================================================
THEMES = {
    "light": dict(bg="#f7f8fa", surface="#ffffff", surface2="#f1f3f6", surface3="#e5e8ed", border="#e2e6eb",
                  border2="#cdd3db", text="#0f1318", muted="#58616d", faint="#868e9b", accent="#2d54d3",
                  accent_soft="#e9f0ff", accent_ink="#2346bc", on_accent="#ffffff", green="#329d5a",
                  green_soft="#e0f7e5", green_ink="#126635", amber="#e4a339", amber_soft="#fff0d1",
                  amber_ink="#8d5406", red="#db423c", red_soft="#ffebe9", red_ink="#b02b27"),
    "dark": dict(bg="#0c0e11", surface="#13161a", surface2="#1a1e23", surface3="#252a31", border="#242a31",
                 border2="#363d47", text="#e6e9ed", muted="#9aa3ae", faint="#6d7682", accent="#7099ff",
                 accent_soft="#18274b", accent_ink="#a7c3ff", on_accent="#0c0e11", green="#4fb772",
                 green_soft="#16321f", green_ink="#89dea1", amber="#e9b452", amber_soft="#3f2c10",
                 amber_ink="#f5cf7d", red="#ef6661", red_soft="#451e1c", red_ink="#ffaaa2"),
}
SANS = "Geist, -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"
SERIF = "'Instrument Serif', Georgia, 'Times New Roman', serif"
MONO = "'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, monospace"
FONTS_URL = ("https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600&family=Instrument+Serif:ital@0;1"
             "&family=JetBrains+Mono:wght@400;500&display=swap")

st.set_page_config(page_title="TYLY Signal · weekly briefing", page_icon="◼", layout="wide",
                   initial_sidebar_state="expanded")


# =====================================================================================================
# DATA (cached on file mtime) + validator (the same module the build runs)
# =====================================================================================================
@st.cache_data(show_spinner=False)
def _load(path_str, mtime):  # mtime is part of the cache key, so a rebuilt file is re-read
    return json.loads(Path(path_str).read_text())


def load(path):
    return _load(str(path), path.stat().st_mtime)


@st.cache_resource(show_spinner=False)
def _module(name, file):
    spec = importlib.util.spec_from_file_location(name, DASH / "scripts" / file)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


V = _module("validator", "17_validate_summaries.py")
WRITER = _module("writer", "16_generate_summaries.py")
M = load(PROC / "metrics.json")
A = load(PROC / "anomalies.json")
SUMM = load(DASH / "summaries.json")
BRIEF = load(DASH / "briefing.json")
BSTATS = load(DASH / "build_stats.json")
META = M["meta"]
WEEKS = META["weeks"]
AN = {a["id"]: a for a in A["anomalies"]}
RULES = {r["id"]: r for r in A["rules"]}
FAMILIES = [r["STYLE_GROUP"] for r in M["products_ptd"]]

# Plain-word labels for rules and findings (no figures here: thresholds come from anomalies.json, numbers from metrics.json)
RULE_LABEL = {
    "SALES_YOY_NEG": "Weekly demand below LY", "SALES_YOY_DROP": "Weekly demand sharply below LY",
    "SALES_YOY_SPIKE": "Weekly demand far above LY", "SALES_WOW_SWING": "Big week-on-week swing",
    "TXNS_YOY_NEG": "Transactions below LY", "AOV_YOY_SWING": "Basket (AOV) swing vs LY",
    "GENZ_NEW_YOY_NEG": "Gen Z new customers below LY", "GENZ_NEW_WOW_DROP": "Gen Z new customers drop WoW",
    "GENZ_SHARE_BELOW_LY": "Gen Z share of new below LY", "GENZ_NEW_INSIDER_LOW": "New Gen Z Insider attach low",
    "RETURNING_YOY_FLAT": "Returning customers flat", "GENZ_RETURNING_YOY_NEG": "Returning Gen Z below LY",
    "FAMILY_L4W_DECLINE": "Family demand in steep decline", "WOS_LOW": "Weeks of supply low",
    "WOS_HIGH": "Weeks of supply high", "WOS_COLLAPSE_VS_LY": "Weeks of supply collapsed vs LY",
    "RECEIPTS_BELOW_SALES": "Replenishment below sales", "PARTIAL_WEEK": "Partial week",
}
FINDINGS = [  # id, goal, short title (numberless), Explore tab
    ("F1", "G1", "Growth comes from more customers, not bigger baskets", "G1"),
    ("F2", "G1", "A naive full-week comparison understates growth", "G1"),
    ("F3", "G1", "The W29 week-on-week drop is a basket normalisation", "G1"),
    ("F4", "G2", "Gen Z new-customer acquisition more than doubled", "G2"),
    ("F5", "G2", "Gen Z share of new customers is accelerating", "G2"),
    ("F6", "G2", "Retention proxy is weak: returning customers flat", "G2"),
    ("F7", "G2", "New Gen Z have the lowest Insider attach", "G2"),
    ("F8", "G2", "New Gen Z buy the Tabby franchise first, at full price", "G2"),
    ("F9", "G3", "The Tabby franchise drives most of the growth", "G3"),
    ("F10", "G3", "Halo apparel and Rogue are the drag", "G3"),
    ("F11", "G4", "Winners are nearly out of stock; apparel is overstocked", "G4"),
    ("F12", "G4", "Replenishment stopped following demand", "G4"),
    ("F13", "G4", "TY W30 stock snapshot is dated after the last sale", "G4"),
    ("F14", "All", "CUST_ID behaves like a random number: no cohort retention", "G2"),
    ("F15", "G3", "Mens Bag is the next Gen Z over-indexer (watch)", "G3"),
]
FIND_TITLE = {f[0]: f[2] for f in FINDINGS}
TABS = {"G1": "G1 Performance", "G2": "G2 Gen Z", "G3": "G3 Products", "G4": "G4 Inventory"}
PAGES = ["briefing", "explore", "ask", "build"]
WINDOWS = ["L1W", "L4W", "PTD"]
E = html.escape


# =====================================================================================================
# STATE (mirrored to the URL so views are linkable)
# =====================================================================================================
ss = st.session_state
if "init" not in ss:
    qp = st.query_params
    ss.page = qp.get("page") if qp.get("page") in PAGES else "briefing"
    ss.wk = int(qp["wk"]) if qp.get("wk", "").isdigit() and int(qp["wk"]) in WEEKS else META["last_full_week"]
    ss.win = qp.get("win") if qp.get("win") in WINDOWS else "L4W"
    ss.ly = qp.get("ly", "1") != "0"
    ss.theme = qp.get("theme") if qp.get("theme") in THEMES else "light"
    ss.tab = qp.get("tab") if qp.get("tab") in TABS else "G1"
    ss.banner = True
    ss.chat = []
    ss.family = "Tabby"
    ss.sort3 = "contrib_pts"
    ss.init = True
if ss.get("win") is None:  # segmented control can be deselected; keep the last valid window
    ss.win = ss.get("_win_last", "L4W")
ss._win_last = ss.win
T = THEMES[ss.theme]
INJECT = st.query_params.get("inject_error") == "1"  # validator self-test in the UI (dashboard/HISTORY.md)


def go_page(page, tab=None, prefill=None, family=None):
    ss.page = page
    if tab:
        ss.tab = tab
    if prefill:
        ss.pending_q = prefill
    if family:
        ss.family = family
    ss.q = ""


def toggle_theme():
    ss.theme = "dark" if ss.theme == "light" else "light"


def _set_streamlit_theme(t):
    """Keep Streamlit's own widget theme in step with the token set (best effort, private API)."""
    try:
        from streamlit import config as _cfg
        for k, v in {"theme.base": ss.theme, "theme.primaryColor": t["accent"], "theme.backgroundColor": t["bg"],
                     "theme.secondaryBackgroundColor": t["surface2"], "theme.textColor": t["text"]}.items():
            _cfg.set_option(k, v)
    except Exception:
        pass


_set_streamlit_theme(T)


# =====================================================================================================
# FORMATTING (display only)
# =====================================================================================================
def money(x, compact=True):
    if x is None:
        return "—"
    if compact and abs(x) >= 1000:
        return f"${x / 1000:,.1f}K"
    return f"${x:,.2f}" if abs(x) < 1000 else f"${x:,.0f}"


def pct(x, signed=False, dp=1):
    if x is None:
        return "—"
    v = x * 100
    if abs(v) >= 100:
        return f"{v:+.0f}%" if signed else f"{v:.0f}%"
    return f"{v:+.{dp}f}%" if signed else f"{v:.{dp}f}%"


def pts(x):
    return "—" if x is None else f"{x:+.1f} pts"


def num(x, dp=0):
    return "—" if x is None else f"{x:,.{dp}f}"


def wosf(x):
    return "—" if x is None else f"{x:.1f}"


def ratio2(x):
    return "—" if x is None else f"{x:.2f}"


def td(text):
    return f'<td class="r mono">{E(text)}</td>'


def txn_cell(r):
    return num(r["txns_ty"]) + (" / " + num(r["txns_ly"]) if SHOW_LY else "")


def gap_cls(x, risk):
    """Stock share minus demand share: understock risk in red ink, overstock risk in amber ink (status colours only)."""
    return "down" if "Under" in risk else "warn" if "Over" in risk else "flat"


def tone(x):
    return "flat" if x is None or x == 0 else ("up" if x > 0 else "down")


def arrow(x):
    return "" if x is None or x == 0 else ("▲ " if x > 0 else "▼ ")


def week_label(w):
    return f"W{w} · partial" if w == META["partial_week"] else f"W{w}"


def date_words(iso):
    import datetime as _dt
    d = _dt.date.fromisoformat(iso)
    return d.strftime("%a %b ") + str(d.day)


SEV_ICON = {"critical": ("▲", "Critical"), "warning": ("◆", "Warning"), "info": ("●", "Info")}


# =====================================================================================================
# CSS: one global block (fonts, tokens, Streamlit chrome hidden, widgets restyled)
# =====================================================================================================
def css(t):
    v = "\n".join(f"  --{k.replace('_', '-')}: {val};" for k, val in t.items())
    return f"""
<style>
@import url('{FONTS_URL}');
:root {{
{v}
  --sans: {SANS}; --serif: {SERIF}; --mono: {MONO};
}}
html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {{ background: var(--bg) !important; color: var(--text); font-family: var(--sans); }}
.stApp, .stApp p, .stApp span, .stApp div, .stApp button, .stApp input, .stApp label, .stApp li, .stApp td, .stApp th {{ font-family: var(--sans); }}
.stApp [data-testid="stIconMaterial"], .stApp span[class*="material-symbols"], .stApp [data-testid="stExpanderIcon"] {{ font-family: "Material Symbols Rounded" !important; }}
.stApp code, .stApp pre, .stApp .mono, .stApp .mono * {{ font-family: var(--mono) !important; }}
header[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"], footer, #MainMenu,
[data-testid="stStatusWidget"] {{ display: none !important; }}
[data-testid="stMainBlockContainer"], .block-container {{ padding: 18px 32px 110px 32px !important; max-width: 1480px; }}
[data-testid="stVerticalBlock"] {{ gap: 0.75rem; }}
p, li {{ color: var(--text); }}
.stale-element, [data-stale="true"] {{ opacity: 1 !important; transition: none !important; }}
a {{ color: var(--accent-ink); }}
/* ---------- sidebar ---------- */
section[data-testid="stSidebar"] {{ background: var(--bg) !important; border-right: 1px solid var(--border); width: 252px !important; min-width: 252px !important; }}
section[data-testid="stSidebar"] > div {{ background: var(--bg) !important; }}
[data-testid="stSidebarHeader"] {{ height: 8px; min-height: 8px; padding: 0 !important; }}
[data-testid="stSidebarCollapseButton"] {{ display: none !important; }}
[data-testid="stSidebarUserContent"] {{ padding: 6px 12px 16px 12px !important; }}
[data-testid="stSidebarUserContent"] [data-testid="stVerticalBlock"] {{ gap: 2px; }}
.logo {{ display: flex; align-items: center; gap: 10px; padding: 6px 8px 18px 8px; }}
.logo .mark {{ width: 22px; height: 22px; border-radius: 6px; background: var(--accent); position: relative; flex: none; }}
.logo .mark::after {{ content: ""; position: absolute; inset: 7px; border-radius: 2px; background: var(--on-accent); }}
.logo .word {{ font-family: var(--serif) !important; font-size: 28px; line-height: 1; letter-spacing: -0.01em; color: var(--text); }}
.logo .sub {{ font-family: var(--mono) !important; font-size: 10.5px; color: var(--faint); letter-spacing: .06em; margin-top: 3px; }}
div[class*="st-key-nav_"] button {{ width: 100%; justify-content: flex-start !important; gap: 10px; background: transparent !important;
  border: 0 !important; box-shadow: none !important; border-radius: 6px !important; padding: 7px 10px !important; min-height: 33px !important;
  color: var(--muted) !important; font-size: 13px !important; }}
div[class*="st-key-nav_"] button:hover {{ background: var(--surface2) !important; color: var(--text) !important; }}
div[class*="st-key-nav_"] button p {{ font-size: 13px !important; margin: 0; }}
div[class*="st-key-nav_"] button::before {{ font-family: var(--mono); font-size: 12px; width: 16px; text-align: center; color: var(--muted); }}
div[class*="st-key-nav_"] button::after {{ margin-left: auto; font-family: var(--mono); font-size: 11px; color: var(--faint); }}
.st-key-nav_briefing button::before {{ content: "⊙"; }}
.st-key-nav_explore button::before {{ content: "☰"; }}
.st-key-nav_ask button::before {{ content: "▢"; }}
.st-key-nav_build button::before {{ content: "</>"; font-size: 10px; }}
.side-h {{ font-family: var(--mono) !important; font-size: 10.5px; letter-spacing: .08em; color: var(--faint); text-transform: uppercase; margin: 22px 8px 6px 8px; }}
.side-lbl {{ font-size: 12px; color: var(--muted); margin: 10px 8px 4px 8px; }}
.watching {{ margin: 26px 8px 0 8px; padding-top: 14px; border-top: 1px solid var(--border); font-size: 12px; color: var(--muted); line-height: 1.55; }}
.watching b {{ color: var(--text); font-weight: 500; font-size: 12.5px; }}
.watching .dot {{ display: inline-block; width: 7px; height: 7px; border-radius: 50%; background: var(--accent); margin-right: 7px; vertical-align: 1px; animation: pulse 2.4s ease-in-out infinite; }}
@keyframes pulse {{ 0%,100% {{ opacity: 1; }} 50% {{ opacity: .35; }} }}
.side-foot {{ margin: 14px 8px 0 8px; font-size: 11px; color: var(--faint); }}
/* ---------- widgets ---------- */
[data-testid="stWidgetLabel"] p, [data-testid="stWidgetLabel"] {{ font-size: 12px !important; color: var(--muted) !important; }}
[data-baseweb="select"] > div, [data-baseweb="input"], [data-baseweb="base-input"], .stTextInput input, [data-baseweb="textarea"] {{
  background: var(--surface) !important; border-color: var(--border) !important; color: var(--text) !important; border-radius: 8px !important; }}
[data-baseweb="select"] > div {{ min-height: 32px; font-size: 13px; }}
[data-baseweb="select"] svg {{ color: var(--muted); fill: var(--muted); }}
[data-baseweb="select"] span, [data-baseweb="select"] div {{ color: var(--text); }}
[data-baseweb="input"] input, .stTextInput input {{ color: var(--text) !important; font-size: 13px !important; caret-color: var(--accent); }}
input::placeholder {{ color: var(--faint) !important; }}
[data-baseweb="popover"] ul, [data-baseweb="popover"] [role="listbox"], [data-baseweb="menu"] {{ background: var(--surface) !important; border: 1px solid var(--border); }}
[data-baseweb="popover"] li {{ color: var(--text) !important; background: var(--surface) !important; font-size: 13px; }}
[data-baseweb="popover"] li:hover, [data-baseweb="popover"] li[aria-selected="true"] {{ background: var(--surface2) !important; }}
[data-testid="stButtonGroup"] {{ background: var(--surface); border: 1px solid var(--border); border-radius: 9px; padding: 3px; gap: 2px !important; width: fit-content; flex-wrap: nowrap !important; }}
[data-testid="stButtonGroup"] button {{ white-space: nowrap; }}
[data-testid="stButtonGroup"] button {{ border: 0 !important; background: transparent !important; color: var(--muted) !important; height: 30px; min-height: 30px !important;
  padding: 0 11px !important; border-radius: 6px !important; font-weight: 500; box-shadow: none !important; }}
[data-testid="stButtonGroup"] button p {{ font-size: 12.5px !important; }}
[data-testid="stButtonGroup"] button[data-testid$="Active"], [data-testid="stButtonGroup"] button[kind$="Active"] {{ background: var(--text) !important; color: var(--bg) !important; }}
[data-testid="stButtonGroup"] button[data-testid$="Active"] p, [data-testid="stButtonGroup"] button[kind$="Active"] p {{ color: var(--bg) !important; }}
[data-testid="stCheckbox"] label p, .stToggle label p {{ font-size: 12.5px !important; color: var(--text) !important; }}
.stButton > button, .stFormSubmitButton > button {{ font-size: 13px; border-radius: 8px; min-height: 32px; height: 32px; padding: 0 12px; font-weight: 500;
  background: transparent; border: 1px solid var(--border2); color: var(--text); box-shadow: none; }}
.stButton > button:hover {{ border-color: var(--text); color: var(--text); background: var(--surface); }}
.stButton > button p {{ font-size: 13px; }}
.stButton > button[kind="primary"] {{ background: var(--text) !important; color: var(--bg) !important; border: 0 !important; font-weight: 600; }}
.stButton > button[kind="primary"] p {{ color: var(--bg) !important; font-weight: 600; }}
.stButton > button[kind="primary"]:hover {{ opacity: .88; }}
div[class*="st-key-ask_"] button, .st-key-ask_send button, .stFormSubmitButton > button {{ background: var(--accent) !important; color: var(--on-accent) !important; border: 0 !important; }}
div[class*="st-key-ask_"] button p, .stFormSubmitButton > button p {{ color: var(--on-accent) !important; }}
div[class*="st-key-ask_"] button p::before {{ content: "● "; font-size: 9px; vertical-align: 2px; }}
[data-testid="stExpander"] details {{ border: 1px solid var(--border) !important; border-radius: 8px !important; background: var(--surface) !important; }}
[data-testid="stExpander"] summary {{ font-size: 12.5px; color: var(--muted); padding: 8px 12px !important; }}
[data-testid="stExpander"] summary p {{ font-size: 12.5px !important; color: var(--muted) !important; }}
[data-testid="stExpander"] summary:hover p {{ color: var(--text) !important; }}
[data-testid="stExpander"] svg {{ fill: var(--muted); color: var(--muted); }}
.stCode pre, [data-testid="stCode"] pre {{ background: var(--surface2) !important; border-radius: 8px; font-size: 11.5px !important; }}
.stCode code, [data-testid="stCode"] code {{ color: var(--text) !important; background: transparent !important; }}
[data-testid="stRadio"] [role="radiogroup"] {{ gap: 0 !important; border-bottom: 1px solid var(--border); width: 100%; flex-wrap: wrap; }}
[data-testid="stRadio"] label {{ padding: 8px 14px 9px 14px !important; margin: 0 !important; border-bottom: 2px solid transparent; cursor: pointer; }}
[data-testid="stRadio"] label > div:first-child {{ display: none !important; }}
[data-testid="stRadio"] label p {{ font-size: 13px !important; color: var(--muted) !important; font-weight: 500; }}
[data-testid="stRadio"] label:has(input:checked) {{ border-bottom-color: var(--text); }}
[data-testid="stRadio"] label:has(input:checked) p {{ color: var(--text) !important; }}
[data-testid="stAlert"] {{ background: var(--amber-soft) !important; color: var(--amber-ink) !important; border-radius: 8px; }}
/* ---------- top bar ---------- */
.st-key-topbar {{ border-bottom: 1px solid var(--border); padding-bottom: 12px; margin-bottom: 4px; }}
.st-key-search input {{ padding-left: 30px !important; }}
.st-key-search {{ position: relative; max-width: 380px; }}
.st-key-search::before {{ content: "○"; position: absolute; left: 11px; top: 7px; z-index: 2; color: var(--faint); font-size: 12px; }}
.st-key-search::after {{ content: "/"; position: absolute; right: 9px; top: 6px; z-index: 2; font-family: var(--mono); font-size: 11px; color: var(--faint);
  border: 1px solid var(--border); border-radius: 4px; padding: 0 6px; line-height: 18px; }}
.st-key-theme_btn {{ display: flex; justify-content: flex-end; }}
.st-key-theme_btn button {{ background: var(--surface) !important; border: 1px solid var(--border) !important; white-space: nowrap; min-width: 84px; }}
.st-key-theme_btn button p {{ white-space: nowrap; }}
.st-key-banner {{ background: var(--accent-soft); border-radius: 8px; padding: 9px 10px 9px 14px; }}
.st-key-banner [data-testid="stHorizontalBlock"] {{ align-items: center; }}
.banner {{ font-size: 13px; color: var(--text); line-height: 1.45; }}
.banner .dot {{ color: var(--accent); margin-right: 8px; font-size: 9px; vertical-align: 2px; }}
.st-key-banner_x button {{ border: 0 !important; background: transparent !important; color: var(--muted) !important; min-height: 24px !important; height: 24px !important; padding: 0 6px !important; }}
.st-key-results {{ background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 10px 12px; }}
div[class*="st-key-res_"] button {{ border: 0 !important; justify-content: flex-start; width: 100%; background: transparent !important; }}
div[class*="st-key-res_"] button:hover {{ background: var(--surface2) !important; }}
/* ---------- page type ---------- */
.eyebrow {{ font-family: var(--mono) !important; font-size: 11.5px; letter-spacing: .08em; color: var(--muted); text-transform: uppercase; display: flex; align-items: center; gap: 8px; }}
.eyebrow .dot {{ width: 6px; height: 6px; border-radius: 50%; background: var(--accent); display: inline-block; }}
h1.serif, .serif-h1 {{ font-family: var(--serif) !important; font-weight: 400 !important; font-size: 60px !important; line-height: 1 !important; letter-spacing: -0.02em; margin: 14px 0 0 0 !important; padding: 0 !important; color: var(--text) !important; text-wrap: balance; }}
.serif-h1 em {{ font-family: var(--serif) !important; color: var(--muted); }}
.lead {{ font-size: 15px; line-height: 1.5; color: var(--muted); max-width: 640px; margin-top: 12px; text-wrap: pretty; }}
.h2 {{ font-family: var(--serif) !important; font-size: 32px; line-height: 1.1; letter-spacing: -0.01em; color: var(--text); margin: 4px 0 6px 0; }}
.secnum {{ font-family: var(--mono) !important; font-size: 11.5px; color: var(--faint); margin-top: 34px; }}
.muted {{ color: var(--muted); }}
/* ---------- briefing cards ---------- */
div[class*="st-key-card_"] {{ border-bottom: 1px solid var(--border); padding: 8px 0 30px 0; gap: 14px !important; }}
.cardtop {{ display: flex; flex-direction: column; gap: 14px; }}
.pillrow {{ display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }}
.pill {{ border-radius: 999px; padding: 2px 9px; font-size: 12px; font-weight: 500; line-height: 16px; white-space: nowrap; }}
.pill.today, .pill.needs {{ background: var(--red-soft); color: var(--red-ink); }}
.pill.pattern {{ background: var(--amber-soft); color: var(--amber-ink); }}
.pill.win {{ background: var(--green-soft); color: var(--green-ink); }}
.pill.watch {{ background: var(--surface2); color: var(--muted); }}
.pill.winner {{ background: var(--green-soft); color: var(--green-ink); }}
.pill.decliner {{ background: var(--red-soft); color: var(--red-ink); }}
.pill.steady {{ background: var(--surface2); color: var(--muted); }}
.pill.under {{ background: var(--red-soft); color: var(--red-ink); }}
.pill.over {{ background: var(--amber-soft); color: var(--amber-ink); }}
.meta {{ font-size: 12px; color: var(--muted); }}
.headline {{ font-family: var(--serif) !important; font-size: 30px; line-height: 1.08; letter-spacing: -0.01em; color: var(--text); text-wrap: balance; max-width: 820px; }}
@media (min-width: 1280px) {{ .headline {{ font-size: 42px; }} }}
.body {{ font-size: 14px; line-height: 1.625; color: var(--muted); max-width: 660px; text-wrap: pretty; }}
.n {{ border-bottom: 1px dotted transparent; cursor: help; font-family: inherit !important; }}
.headline *, .q *, .quote *, .serif-h1 *, .h2 * {{ font-family: var(--serif) !important; }}
.pillrow .trust {{ margin-left: auto; }}
.n:hover {{ border-bottom-color: var(--accent); }}
.n.bad {{ background: var(--red-soft); color: var(--red-ink); border-bottom: 1px solid var(--red); }}
.bars {{ display: flex; flex-direction: column; gap: 7px; max-width: 640px; }}
.bars .row {{ display: flex; align-items: center; gap: 14px; }}
.bars .lab {{ flex: none; width: 190px; font-size: 12.5px; color: var(--muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
.bars .track {{ flex: 1; height: 8px; border-radius: 4px; background: var(--surface3); overflow: hidden; }}
.bars .fill {{ height: 100%; border-radius: 4px; }}
.bars .val {{ width: 64px; text-align: right; font-family: var(--mono) !important; font-size: 12px; color: var(--muted); }}
.bars .unit {{ font-size: 11.5px; color: var(--faint); margin-top: 2px; }}
.f-red {{ background: var(--red); }} .f-amber {{ background: var(--amber); }} .f-accent {{ background: var(--accent); }}
.f-ly {{ background: var(--border2); }} .f-neutral {{ background: var(--faint); opacity: .55; }} .f-green {{ background: var(--green); }}
.cols {{ display: flex; align-items: flex-end; gap: 6px; max-width: 640px; height: 124px; }}
.cols .c {{ flex: 1; max-width: 84px; display: flex; flex-direction: column; align-items: center; justify-content: flex-end; height: 100%; gap: 4px; }}
.cols .v {{ font-family: var(--mono) !important; font-size: 10.5px; color: var(--muted); }}
.cols .b {{ width: 100%; flex: none; background: var(--surface3); border-radius: 3px 3px 0 0; }}
.cols .b.last {{ background: var(--amber); }}
.cols .b.partial {{ background-image: repeating-linear-gradient(135deg, transparent 0 4px, rgba(255,255,255,.35) 4px 7px); }}
.cols .l {{ font-family: var(--mono) !important; font-size: 10.5px; color: var(--faint); }}
.chips {{ display: flex; gap: 6px; flex-wrap: wrap; justify-content: flex-end; }}
.chip {{ font-family: var(--mono) !important; font-size: 11.5px; border: 1px solid var(--border); border-radius: 4px; padding: 1px 7px; color: var(--muted); white-space: nowrap; cursor: help; }}
.trust {{ font-size: 12px; display: inline-flex; align-items: center; gap: 6px; color: var(--muted); }}
.trust .ok {{ color: var(--green-ink); font-weight: 600; }}
.trust .no {{ color: var(--red-ink); font-weight: 600; }}
div[class*="st-key-act_"] {{ align-items: center; }}
div[class*="st-key-act_"] .stButton > button {{ height: 32px; }}
.st-key-summary {{ background: var(--surface); border: 1px solid var(--border); border-radius: 10px; padding: 18px 20px 14px 20px; }}
.sumhead {{ display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap; }}
.sumtext {{ font-size: 15px; line-height: 1.65; color: var(--text); margin: 10px 0 2px 0; text-wrap: pretty; }}
.sumfoot {{ font-family: var(--mono) !important; font-size: 11px; color: var(--faint); }}
.blocked {{ background: var(--red-soft); color: var(--red-ink); border-radius: 8px; padding: 10px 12px; font-size: 13px; }}
/* ---------- right rail ---------- */
.rail {{ border-top: 1px solid var(--text); padding-top: 14px; }}
.rail .head {{ display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 8px; }}
.rail .head b {{ font-weight: 600; font-size: 13px; color: var(--text); }}
.rail .head span {{ font-size: 12px; color: var(--faint); }}
.rule {{ display: flex; align-items: center; gap: 9px; padding: 5px 0; font-size: 12.5px; color: var(--muted); }}
.rule .d {{ width: 6px; height: 6px; border-radius: 50%; background: var(--border2); flex: none; }}
.rule .d.critical {{ background: var(--red); }} .rule .d.warning {{ background: var(--amber); }} .rule .d.info {{ background: var(--accent); }}
.rule.hit {{ color: var(--text); }}
.rule .t {{ margin-left: auto; font-family: var(--mono) !important; font-size: 10.5px; color: var(--faint); white-space: nowrap; }}
.rule .k {{ margin-left: auto; font-family: var(--mono) !important; font-size: 11.5px; min-width: 18px; text-align: right; color: var(--muted); }}
.rule:not(.hit) .k {{ color: var(--faint); }}
.alerts {{ margin-top: 18px; border-top: 1px solid var(--border); padding-top: 12px; }}
.alert {{ display: grid; grid-template-columns: 74px 1fr; gap: 2px 8px; padding: 7px 0; border-bottom: 1px solid var(--border); font-size: 12.5px; }}
.alert .sev {{ font-size: 11.5px; font-weight: 600; white-space: nowrap; }}
.alert .sev.critical {{ color: var(--red-ink); }} .alert .sev.warning {{ color: var(--amber-ink); }} .alert .sev.info {{ color: var(--accent-ink); }}
.alert .msg {{ color: var(--text); line-height: 1.45; }}
.alert .id {{ grid-column: 2; font-family: var(--mono) !important; font-size: 10.5px; color: var(--faint); }}
/* responsive: rail below cards under 1280px */
@media (max-width: 1279px) {{
  .st-key-brief_grid > div > [data-testid="stHorizontalBlock"] {{ flex-wrap: wrap !important; }}
  .st-key-brief_grid > div > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {{ flex: 1 1 100% !important; width: 100% !important; min-width: 100% !important; }}
  h1.serif, .serif-h1 {{ font-size: 46px !important; }}
}}
@media (max-width: 1100px) {{
  .st-key-hdr [data-testid="stHorizontalBlock"] {{ flex-wrap: wrap !important; }}
  .st-key-hdr [data-testid="stColumn"], .st-key-xbody [data-testid="stColumn"] {{ flex: 1 1 100% !important; width: 100% !important; min-width: 100% !important; }}
  .st-key-xbody [data-testid="stHorizontalBlock"] {{ flex-wrap: wrap !important; }}
}}
/* ---------- explore ---------- */
.kpis {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; }}
.kpi {{ background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 13px 16px; }}
.kpi .l {{ font-size: 12px; color: var(--muted); }}
.kpi .v {{ font-size: 26px; font-weight: 600; margin-top: 2px; color: var(--text); letter-spacing: -0.01em; }}
.kpi .s {{ font-family: var(--mono) !important; font-size: 11.5px; color: var(--faint); margin-top: 2px; display: flex; gap: 8px; flex-wrap: wrap; }}
.up {{ color: var(--green-ink) !important; }} .warn {{ color: var(--amber-ink) !important; }} .down {{ color: var(--red-ink) !important; }} .flat {{ color: var(--muted) !important; }}
.ccard {{ background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 13px 16px 4px 16px; }}
.ctitle {{ display: flex; justify-content: space-between; align-items: baseline; gap: 10px; flex-wrap: wrap; }}
.ctitle b {{ font-size: 12.5px; font-weight: 500; color: var(--text); }}
.ctitle span {{ font-size: 11.5px; color: var(--faint); }}
div[class*="st-key-cc_"] {{ background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 13px 14px 6px 16px; gap: 4px !important; }}
.tbl {{ width: 100%; border-collapse: collapse; font-size: 12.5px; }}
.tbl th {{ text-align: left; font-weight: 500; color: var(--muted); font-size: 11.5px; padding: 7px 8px; border-bottom: 1px solid var(--border); white-space: nowrap; }}
.tbl td {{ padding: 7px 8px; border-bottom: 1px solid var(--border); color: var(--text); white-space: nowrap; }}
.tbl td.r, .tbl th.r {{ text-align: right; }}
.tbl td.mono {{ font-family: var(--mono) !important; font-size: 12px; }}
.tbl tr:hover td {{ background: var(--surface2); }}
.tbl tr.hl td {{ background: var(--accent-soft); }}
.tblwrap {{ overflow-x: auto; }}
.mbar {{ display: inline-block; height: 7px; border-radius: 3px; vertical-align: middle; }}
.callout {{ border-left: 2px solid var(--amber); background: var(--amber-soft); color: var(--amber-ink); padding: 10px 14px; border-radius: 0 8px 8px 0; font-size: 13px; line-height: 1.5; }}
.callout b {{ color: var(--amber-ink); }}
.note {{ font-size: 12px; color: var(--faint); }}
/* ---------- ask ---------- */
.askhead {{ display: flex; justify-content: space-between; align-items: center; }}
.askhead b {{ font-size: 18px; font-weight: 600; }} .askhead span {{ font-size: 12px; color: var(--faint); margin-left: 8px; }}
.askhero {{ text-align: center; margin: 46px 0 22px 0; }}
.askhero .t {{ font-size: 20px; font-weight: 600; color: var(--text); }}
.askhero .s {{ font-size: 13px; color: var(--muted); margin-top: 6px; }}
div[class*="st-key-sugg_"] button {{ width: 100%; min-height: 58px !important; height: auto !important; justify-content: flex-start; text-align: left;
  background: var(--surface) !important; border: 1px solid var(--border) !important; padding: 10px 14px !important; }}
div[class*="st-key-sugg_"] button p {{ text-align: left; font-weight: 400; }}
div[class*="st-key-sugg_"] button:hover {{ border-color: var(--border2) !important; }}
.q {{ font-family: var(--serif) !important; font-size: 26px; line-height: 1.15; color: var(--text); margin-top: 8px; }}
.ans {{ background: var(--surface); border: 1px solid var(--border); border-radius: 10px; padding: 16px 18px; margin-top: 10px; }}
.ans .a {{ font-size: 14.5px; line-height: 1.6; color: var(--text); }}
.steps {{ margin-top: 12px; display: flex; flex-direction: column; gap: 4px; }}
.steps div {{ font-family: var(--mono) !important; font-size: 11.5px; color: var(--muted); }}
.steps div b {{ color: var(--accent-ink); font-weight: 500; }}
.st-key-askform [data-testid="stForm"] {{ border: 1px solid var(--border); background: var(--surface); border-radius: 10px; padding: 6px 6px 6px 12px; }}
.st-key-askform [data-testid="stForm"] [data-baseweb="input"] {{ border: 0 !important; background: transparent !important; }}
.st-key-askform [data-testid="stHorizontalBlock"] {{ align-items: center; flex-wrap: nowrap !important; }}
.st-key-askform [data-testid="stColumn"]:last-child {{ flex: 0 0 84px !important; min-width: 84px !important; }}
.stFormSubmitButton > button {{ white-space: nowrap; min-width: 72px; }}
/* ---------- build ---------- */
.stats {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 28px; margin-top: 30px; }}
.stat {{ border-top: 1px solid var(--border2); padding-top: 14px; }}
.stat .v {{ font-family: var(--serif) !important; font-size: 46px; line-height: 1; color: var(--text); }}
.stat .c {{ font-size: 12px; color: var(--muted); margin-top: 8px; }}
.flow {{ background: var(--surface); border: 1px solid var(--border); border-radius: 10px; padding: 26px 22px; display: flex; align-items: stretch; gap: 0; overflow-x: auto; }}
.node {{ flex: 1; min-width: 118px; border: 1px solid var(--border2); border-radius: 8px; padding: 12px 12px; background: var(--surface); }}
.node .k {{ font-family: var(--mono) !important; font-size: 10.5px; color: var(--faint); letter-spacing: .06em; text-transform: uppercase; }}
.node .t {{ font-size: 14px; font-weight: 600; color: var(--text); margin-top: 4px; }}
.node .d {{ font-size: 11.5px; color: var(--muted); margin-top: 4px; line-height: 1.4; }}
.node.claude {{ background: var(--accent-soft); border-color: var(--accent); }}
.node.claude .t {{ color: var(--accent-ink); }}
.node.check {{ border-color: var(--green); }}
.arr {{ flex: none; width: 26px; display: flex; align-items: center; justify-content: center; color: var(--accent); font-size: 15px; }}
.four {{ display: grid; grid-template-columns: 1.15fr 24px 1fr 24px 1fr 24px 1fr; align-items: stretch; }}
.four .arr {{ width: auto; }}
.box {{ border: 1px solid var(--border); background: var(--surface); border-radius: 10px; padding: 14px 16px; font-size: 12.5px; }}
.box .k {{ font-family: var(--mono) !important; font-size: 10.5px; color: var(--faint); letter-spacing: .06em; text-transform: uppercase; margin-bottom: 8px; }}
.box.prompt {{ background: var(--accent-soft); border-color: var(--accent); }}
.box.prompt .k {{ color: var(--accent-ink); }}
.box .quote {{ font-family: var(--serif) !important; font-size: 19px; line-height: 1.2; color: var(--text); }}
.box pre {{ font-family: var(--mono) !important; font-size: 11px; line-height: 1.55; margin: 0; white-space: pre-wrap; color: var(--text); background: transparent; }}
.tag {{ font-family: var(--mono) !important; font-size: 11px; background: var(--accent-soft); color: var(--accent-ink); border-radius: 4px; padding: 2px 7px; }}
.okchip {{ font-family: var(--mono) !important; font-size: 11.5px; background: var(--green-soft); color: var(--green-ink); border-radius: 4px; padding: 2px 7px; margin-right: 4px; display: inline-block; margin-bottom: 4px; }}
.badchip {{ font-family: var(--mono) !important; font-size: 11.5px; background: var(--red-soft); color: var(--red-ink); border-radius: 4px; padding: 2px 7px; display: inline-block; }}
.defs {{ display: grid; grid-template-columns: 140px 1fr; gap: 0; font-size: 13px; }}
.defs div {{ padding: 7px 0; border-bottom: 1px solid var(--border); }}
.defs .k {{ font-family: var(--mono) !important; font-size: 12px; color: var(--muted); }}
.plain {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 12px; }}
.plain .box b {{ font-size: 13px; }}
.plain .box p {{ font-size: 13px; color: var(--muted); line-height: 1.55; margin: 6px 0 0 0; }}
/* floating ask pill */
.st-key-fab {{ position: fixed; right: 22px; bottom: 20px; z-index: 1000; width: auto !important; }}
.st-key-fab button {{ height: 44px !important; min-height: 44px !important; border-radius: 22px !important; background: var(--accent) !important; color: var(--on-accent) !important;
  border: 0 !important; padding: 0 16px 0 14px !important; box-shadow: 0 6px 20px rgba(20,40,120,.22) !important; }}
.st-key-fab button p {{ color: var(--on-accent) !important; font-weight: 500; }}
[data-testid="stPlotlyChart"] {{ background: transparent; }}
@media (max-width: 900px) {{
  [data-testid="stMainBlockContainer"], .block-container {{ padding: 14px 16px 100px 16px !important; }}
  h1.serif, .serif-h1 {{ font-size: 40px !important; }}
  .headline {{ font-size: 26px; }}
  .bars .lab {{ width: 130px; }}
  .stats {{ grid-template-columns: 1fr; }}
  .four {{ grid-template-columns: 1fr; }} .four .arr {{ transform: rotate(90deg); height: 22px; }}
}}
</style>"""


st.markdown(css(T), unsafe_allow_html=True)
# dynamic bits of CSS: active nav item + badges/counters (values read from briefing.json / metrics.json)
B = BRIEF[str(ss.wk)]
n_crit = B["n_critical_alerts"]
nav_active = "explore" if ss.page == "explore" else ss.page
st.markdown(f"""<style>
.st-key-nav_{nav_active} button {{ background: var(--surface2) !important; color: var(--text) !important; font-weight: 500 !important; }}
.st-key-nav_{nav_active} button p {{ font-weight: 500 !important; }}
.st-key-nav_briefing button::after {{ content: "{n_crit if n_crit else ''}"; {'background: var(--accent); color: var(--on-accent) !important; border-radius: 9px; min-width: 18px; height: 18px; line-height: 18px; text-align: center; font-family: var(--sans) !important; font-weight: 600; padding: 0 5px; box-sizing: border-box;' if n_crit else ''} }}
.st-key-nav_explore button::after {{ content: "G1–G4"; }}
.st-key-nav_ask button::after {{ content: "{len(ss.chat) or ''}"; }}
</style>""", unsafe_allow_html=True)


# =====================================================================================================
# PLOTLY HELPERS (tokens → chart style: no top/right spines, faint grid, Geist ticks, mono labels)
# =====================================================================================================
def fig_base(height=260, l=8, r=8, t=10, b=8):
    f = go.Figure()
    f.update_layout(height=height, margin=dict(l=l, r=r, t=t, b=b), paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)", showlegend=False, font=dict(family=SANS, size=12, color=T["muted"]),
                    hoverlabel=dict(bgcolor=T["surface"], bordercolor=T["border2"], font=dict(family=SANS, size=12, color=T["text"])),
                    bargap=0.32, bargroupgap=0.08, dragmode=False)
    f.update_xaxes(showgrid=False, zeroline=False, linecolor=T["border"], tickcolor=T["border"], ticks="", automargin=True,
                   tickfont=dict(family=SANS, size=11.5, color=T["muted"]), fixedrange=True)
    f.update_yaxes(showgrid=True, gridcolor=T["border"], gridwidth=1, zeroline=False, showline=False, ticks="", automargin=True,
                   tickfont=dict(family=SANS, size=11.5, color=T["muted"]), fixedrange=True)
    return f


def show(fig):
    st.plotly_chart(fig, use_container_width=True, theme=None, config={"displayModeBar": False, "staticPlot": False})


def chart_card(key, title, note=""):
    c = st.container(key=f"cc_{key}")
    c.html(f'<div class="ctitle"><b>{E(title)}</b><span>{E(note)}</span></div>')
    return c


# =====================================================================================================
# SIDEBAR
# =====================================================================================================
with st.sidebar:
    st.html('<div class="logo"><div class="mark"></div><div><div class="word">Signal</div>'
            '<div class="sub">TYLY · WEEKLY AGENT</div></div></div>')
    st.button("Briefing", key="nav_briefing", on_click=go_page, args=("briefing",))
    st.button("Explore", key="nav_explore", on_click=go_page, args=("explore",))
    st.button("Ask", key="nav_ask", on_click=go_page, args=("ask",))
    st.button("How it was built", key="nav_build", on_click=go_page, args=("build",))
    st.html('<div class="side-h">Controls</div>')
    st.selectbox("Fiscal week", WEEKS, key="wk", format_func=week_label)
    st.html('<div class="side-lbl">Window</div>')
    st.segmented_control("Window", WINDOWS, key="win", label_visibility="collapsed", selection_mode="single")
    st.html('<div style="height:6px"></div>')
    st.toggle("Show LY comparison", key="ly")
    c = META["counts"]
    st.html(f"""<div class="watching"><div><span class="dot"></span><b>Agent watching</b></div>
      <div>{num(c['lines_total'])} transaction lines · {num(c['inventory_snapshots'])} stock snapshots</div>
      <div>{B['n_rules']} rules · {B['n_alerts']} alerts in W{ss.wk}</div>
      <div>Data as of {E(date_words(META['as_of_date']))} · {E(META['ty_label'])} vs {E(META['ly_label'])}</div></div>
      <div class="side-foot">Sample extract · built with Claude Code</div>""")

W, WIN, SHOW_LY = ss.wk, ss.win, ss.ly
TR = M["trailing"][str(W)]


# =====================================================================================================
# TOP BAR + BANNER + SEARCH
# =====================================================================================================
with st.container(key="topbar"):
    c1, c2 = st.columns([6, 1], vertical_alignment="center")
    with c1:
        st.text_input("Search", key="q", placeholder="Jump to a family, finding or rule", label_visibility="collapsed")
    with c2:
        with st.container(key="theme_btn"):
            st.button("◐ Light" if ss.theme == "light" else "◑ Dark", key="theme_toggle", on_click=toggle_theme)

if ss.banner:
    with st.container(key="banner"):
        b1, b2 = st.columns([30, 1], vertical_alignment="center")
        b1.html(f'<div class="banner"><span class="dot">●</span>Like-for-like basis: {E(META["basis"])} '
                f'W{META["partial_week"]} is {E(META["partial_week_days"])}, so LY uses the same days. '
                f'Shares and ratios are the robust read.</div>')
        b2.button("×", key="banner_x", on_click=lambda: ss.update(banner=False))

q = (ss.get("q") or "").strip().lower()
if q:
    with st.container(key="results"):
        fams = [f for f in FAMILIES if q in f.lower()]
        fnds = [f for f in FINDINGS if q in f[0].lower() or q in f[2].lower() or q in f[1].lower()]
        rls = [r for r in A["rules"] if q in r["id"].lower() or q in RULE_LABEL[r["id"]].lower()]
        if not (fams or fnds or rls):
            st.html('<div class="note">No family, finding or rule matches. Try “tabby”, “insider”, “F12” or “wos”.</div>')
        for f in fams[:6]:
            st.button(f"◼ {f}  ·  products (G3) and stock (G4)", key=f"res_f_{f}", on_click=go_page,
                      args=("explore", "G4" if "stock" in q else "G3"), kwargs={"family": f})
        for f in fnds[:6]:
            st.button(f"{f[0]} · {f[2]}  →  {TABS[f[3]]}", key=f"res_x_{f[0]}", on_click=go_page, args=("explore", f[3]))
        for r in rls[:4]:
            st.button(f"Rule · {RULE_LABEL[r['id']]} ({r['rule']})  →  Briefing", key=f"res_r_{r['id']}", on_click=go_page,
                      args=("briefing",))


# =====================================================================================================
# SHARED RENDERERS
# =====================================================================================================
def numbered_html(text, facts, sources=None, metrics_prefix=""):
    """Escape text; wrap every number with its source (hover) or mark it unverified."""
    segs, res = V.annotate(text, facts)
    out = []
    for s in segs:
        if not s["num"]:
            out.append(E(s["text"]))
            continue
        f = s.get("fact")
        if f is None:
            out.append(f'<span class="n bad" title="Not found in the facts JSON">{E(s["text"])}</span>')
        else:
            src = (sources or {}).get(f.split("[")[0].split(".")[0]) or f"{metrics_prefix}{f}"
            out.append(f'<span class="n" title="{E(src)}">{E(s["text"])}</span>')
    return "".join(out), res


def trust_badge(status, n=None):
    if status == "PASS":
        return f'<span class="trust"><span class="ok">✓</span>Worded by Claude; every number checked{f" ({n})" if n else ""}</span>'
    return '<span class="trust"><span class="no">✕</span>Blocked: unverified number</span>'


def facts_table_html(values):
    rows = "".join(f'<tr><td class="mono">{E(k)}</td><td class="r mono">{E(json.dumps(v))}</td></tr>' for k, v in values.items()
                   if not isinstance(v, (list, dict)))
    return f'<div class="tblwrap"><table class="tbl"><tr><th>fact</th><th class="r">value</th></tr>{rows}</table></div>'


def bars_html(chart):
    vals = [r["value"] for r in chart["rows"] if r["value"] is not None]
    mx = max(vals) if vals else 1
    rows = []
    for r in chart["rows"]:
        v = r["value"]
        w = 0 if v is None or mx == 0 else max(2, v / mx * 100)  # drawing geometry only
        lab = {"wos": lambda x: f"{wosf(x)} wk", "pct": lambda x: pct(x), "int": lambda x: num(x)}[r["fmt"]](v)
        if r["tone"] == "ly" and not SHOW_LY:
            continue
        rows.append(f'<div class="row"><div class="lab" title="{E(r["label"])}">{E(r["label"])}</div><div class="track">'
                    f'<div class="fill f-{r["tone"]}" style="width:{w:.1f}%"></div></div><div class="val">{E(lab)}</div></div>')
    return f'<div class="bars">{"".join(rows)}<div class="unit">{E(chart["unit"])}</div></div>'


def cols_html(chart):
    vals = [c["value"] for c in chart["cols"]]
    mx = max(vals) if vals else 1
    out = []
    for i, c in enumerate(chart["cols"]):
        h = c["value"] / mx * 78 if mx else 0  # drawing geometry only
        cls = "b" + (" last" if i == len(chart["cols"]) - 1 else "") + (" partial" if c["partial"] else "")
        out.append(f'<div class="c"><div class="v">{pct(c["value"], dp=0)}</div><div class="{cls}" style="height:{h:.0f}px"></div>'
                   f'<div class="l">{E(c["label"])}{"·p" if c["partial"] else ""}</div></div>')
    return f'<div class="cols">{"".join(out)}</div><div class="bars"><div class="unit">{E(chart["unit"])}</div></div>'


PILL_CLASS = {"Needs you today": "today", "Needs you": "needs", "Pattern": "pattern", "Win": "win", "Watch": "watch"}


def render_card(card, card_facts):
    valid_text = f"{card['headline']} {card['body']}"
    head_html, res = numbered_html(card["headline"], card_facts["values"], card_facts["sources"])
    body_html, res_b = numbered_html(card["body"], card_facts["values"], card_facts["sources"])
    status = "PASS" if V.validate_text(valid_text, card_facts["values"])["status"] == "PASS" else "FLAGGED"
    with st.container(key=f"card_{card['card_id']}"):
        chart = bars_html(card["chart"]) if card["chart"]["type"] == "bars" else cols_html(card["chart"])
        if status == "PASS":
            text = f'<div class="headline">{head_html}</div><div class="body">{body_html}</div>'
        else:
            text = (f'<div class="headline">{E(card["title"])}</div><div class="blocked">✕ Blocked: this card’s wording contained a number '
                    f'that is not in its facts, so it is hidden. The facts it may cite:</div>{facts_table_html(card_facts["values"])}')
        st.html(f"""<div class="cardtop"><div class="pillrow"><span class="pill {PILL_CLASS[card['pill']]}">{E(card['pill'])}</span>
            <span class="meta">{E(card['meta'])}</span>{trust_badge(status)}</div>{text}{chart}</div>""")
        with st.container(horizontal=True, key=f"act_{card['card_id']}", vertical_alignment="center", gap="small"):
            st.button("Open in Explore", key=f"open_{card['card_id']}", type="primary", on_click=go_page,
                      args=("explore", card["explore_tab"]))
            st.button("Ask why", key=f"ask_{card['card_id']}", on_click=go_page, args=("ask",),
                      kwargs={"prefill": card["ask_prefill"]})
            chips = "".join(f'<span class="chip" title="{E(FIND_TITLE.get(i, ""))}">{E(i)}</span>' for i in card["findings"])
            chips += "".join(f'<span class="chip" title="{E(AN[i]["message"])}">{E(i)}</span>' for i in card["anomaly_ids"][:4])
            more = len(card["anomaly_ids"]) - 4
            if more > 0:
                chips += f'<span class="chip" title="more rule hits in the rail">+{more}</span>'
            st.html(f'<div style="flex:1"></div>')
            st.html(f'<div class="chips">{chips}</div>')


def rail_html():
    rows = []
    for r in A["rules"]:
        k = B["rule_hits"][r["id"]]
        cls = r["severity"] if k else ""
        rows.append(f'<div class="rule {"hit" if k else ""}" title="{E(r["metric"])}: {E(r["rule"])} ({E(r["severity"])})"><span class="d {cls}"></span>'
                    f'<span>{E(RULE_LABEL[r["id"]])}</span><span class="k">{k}</span></div>')
    alerts = []
    for aid in sorted(A["by_week"][str(W)], key=lambda i: ({"critical": 0, "warning": 1, "info": 2}[AN[i]["severity"]], i)):
        a = AN[aid]
        ic, lab = SEV_ICON[a["severity"]]
        alerts.append(f'<div class="alert"><span class="sev {a["severity"]}">{ic} {lab}</span><span class="msg">{E(a["message"])}</span>'
                      f'<span class="id">{E(a["id"])} · {E(a["rule_id"])}</span></div>')
    sev = B["n_alerts_by_severity"]
    return (f'<div class="rail"><div class="head"><b>What I’m watching</b><span>{B["n_rules"]} rules</span></div>{"".join(rows)}'
            f'<div class="alerts"><div class="head"><b>Alerts · W{W}</b><span>{sev["critical"]} critical · {sev["warning"]} warning · '
            f'{sev["info"]} info</span></div>{"".join(alerts) or "<div class=note>No rule fired this week.</div>"}</div></div>')


def header(eyebrow, h1_html, lead, view):
    left, right = st.container(key="hdr").columns([3, 1.15], vertical_alignment="bottom")
    left.html(f'<div class="eyebrow"><span class="dot"></span>{E(eyebrow)}</div><h1 class="serif-h1">{h1_html}</h1>'
              f'<div class="lead">{lead}</div>')
    with right:
        sel = st.segmented_control("View", ["Agent briefing", "Classic dashboard"], key=f"view_{view}",
                                   default="Agent briefing" if view == "briefing" else "Classic dashboard",
                                   label_visibility="collapsed")
        if sel and sel != ("Agent briefing" if view == "briefing" else "Classic dashboard"):
            ss.page = "explore" if sel == "Classic dashboard" else "briefing"
            ss.pop(f"view_{view}", None)
            st.rerun()


def eyebrow_date():
    d = META["week_dates_ty"][str(W)]
    if W == META["partial_week"]:
        return f"AGENT BRIEFING · W{W} · AS OF {date_words(d['last_sale']).upper()} (PARTIAL WEEK)"
    return f"AGENT BRIEFING · W{W} · WEEK ENDING {date_words(d['end']).upper()}"


NUMWORD = {0: "Nothing needs", 1: "One thing needs", 2: "Two things need", 3: "Three things need", 4: "Four things need", 5: "Five things need"}


# =====================================================================================================
# PAGE: BRIEFING (the AI feature)
# =====================================================================================================
def page_briefing():
    k = B["n_needs_you"]
    so_far = " so far" if W == META["partial_week"] else ""
    c = META["counts"]
    sev = B["n_alerts_by_severity"]
    lead = (f"I checked {num(c['lines_total'])} transaction lines and {num(c['inventory_snapshots'])} stock snapshots against "
            f"{B['n_rules']} rules: {sev['critical']} critical and {sev['warning']} warning alerts fired for W{W}. "
            f"{k} need a decision from you, {B['n_fyi']} are worth knowing about.")
    header(eyebrow_date(), f"{NUMWORD.get(k, f'{k} things need')} you this week{so_far}.", E(lead), "briefing")
    st.html('<div style="height:10px"></div>')
    with st.container(key="brief_grid"):
        main, rail = st.columns([1, 0.36], gap="large")
        with main:
            # ---- This week in one paragraph (AI summary) ----
            s = SUMM[str(W)]
            facts = load(ROOT / s["facts_file"])
            text = V.inject_error(s["text"]) if INJECT else s["text"]
            body, res = numbered_html(text, facts, metrics_prefix=f"metrics.json → weekly_facts.{W}.")
            with st.container(key="summary"):
                src = {"pregenerated": "worded by Claude at build time", "template": "deterministic template"}.get(
                    s["generated_by"], s["generated_by"].replace("live:", "worded live by "))
                cnt = f"{res['n_matched']}/{res['n_numbers']}" if res["status"] == "PASS" else None
                st.html(f'<div class="sumhead"><span class="eyebrow">This week in one paragraph</span>'
                        f'{trust_badge(res["status"], cnt)}</div>')
                if res["status"] == "PASS":
                    st.html(f'<div class="sumtext">{body}</div>'
                            f'<div class="sumfoot">{res["n_matched"]}/{res["n_numbers"]} numbers traced to metrics.json · {E(src)} · hover a number for its source</div>')
                else:
                    st.html(f'<div class="blocked">✕ Blocked: unverified number {E(", ".join(res["unmatched"]))}. '
                            f'The summary is hidden and the facts it was given are shown instead.</div>')
                    rows = {k2: v for k2, v in facts.items() if k2 != "anomalies"}
                    st.html(facts_table_html(rows))
                with st.expander(f"Facts used · {s['facts_file']}"):
                    st.code(json.dumps(facts, indent=1, ensure_ascii=False), language="json")
            st.html('<div style="height:8px"></div>')
            cf = {x["card_id"]: x for x in load(ROOT / B["cards_file"])["cards"]}
            for card in B["cards"]:
                render_card(card, cf[card["card_id"]])
        with rail:
            st.html(rail_html())


# =====================================================================================================
# PAGE: EXPLORE (classic dashboard, G1–G4)
# =====================================================================================================
def kpi_tile(label, blk, fmt, is_share=False):
    ty, ly = blk["ty"], blk["ly"]
    if is_share:
        d, dtxt = blk.get("chg_pts"), pts(blk.get("chg_pts"))
    else:
        d, dtxt = blk.get("yoy_pct"), pct(blk.get("yoy_pct"), signed=True)
    ly_txt = f"<span>LY {E(fmt(ly))}</span>" if SHOW_LY else ""
    return (f'<div class="kpi"><div class="l">{E(label)}</div><div class="v">{E(fmt(ty))}</div>'
            f'<div class="s">{ly_txt}<span class="{tone(d)}">{arrow(d)}{E(dtxt)}{"" if is_share else " YoY"}</span></div></div>')


def window_note(blk):
    wks = blk["weeks"]
    rng = f"W{wks[0]}–W{wks[-1]}" if len(wks) > 1 else f"W{wks[0]}"
    extra = " · truncated (fewer than four weeks of history)" if blk.get("truncated") else ""
    extra += " · includes partial W30" if META["partial_week"] in wks else ""
    return f"{WIN} = {rng}{extra}"


def tab_g1():
    blk = TR[WIN]
    st.html(f'<div class="note">{E(window_note(blk))} · TY vs LY like-for-like</div>')
    st.html('<div class="kpis">' + "".join([
        kpi_tile("Demand", blk["sales"], money), kpi_tile("Transactions", blk["txns"], num),
        kpi_tile("AOV", blk["aov"], lambda x: money(x, compact=False)), kpi_tile("UPT", blk["upt"], lambda x: num(x, 2)),
        kpi_tile("AUR", blk["aur"], lambda x: money(x, compact=False)), kpi_tile("Customers", blk["customers"], num)]) + "</div>")
    if WIN == "L1W" and TR["L1W"].get("wow"):
        wv = TR["L1W"]["wow"]
        st.html(f'<div class="note">Week-on-week (TY W{W} vs W{W - 1}): demand <b class="{tone(wv["sales"])}">{pct(wv["sales"], True)}</b>, '
                f'transactions <b class="{tone(wv["txns"])}">{pct(wv["txns"], True)}</b>, AOV <b class="{tone(wv["aov"])}">{pct(wv["aov"], True)}</b>.</div>')
    a, b = st.columns([1.55, 1], gap="medium")
    with a:
        with chart_card("g1w", "Weekly demand, TY vs LY", f"W{META['partial_week']} is {META['partial_week_days']}; LY on the same days"):
            wk = M["weekly"]
            xs = [f"W{r['wk']}" for r in wk]
            full = [r for r in wk if not r["is_partial"]]
            f = fig_base(290, l=46, r=70, b=24)
            last_full = f"W{full[-1]['wk']}"
            f.add_vrect(x0=xs.index(f"W{W}") - 0.45, x1=xs.index(f"W{W}") + 0.45, fillcolor=T["accent_soft"], opacity=0.7, line_width=0, layer="below")
            if SHOW_LY:
                f.add_scatter(x=[f"W{r['wk']}" for r in full], y=[r["sales"]["ly"] for r in full], mode="lines+markers",
                              line=dict(color=T["border2"], width=2), marker=dict(size=6, color=T["border2"]),
                              hovertemplate="%{x} LY $%{y:,.0f}<extra></extra>")
                f.add_scatter(x=[last_full, xs[-1]], y=[full[-1]["sales"]["ly"], wk[-1]["sales"]["ly"]], mode="lines+markers",
                              line=dict(color=T["border2"], width=2, dash="dot"), marker=dict(size=6, color=T["border2"]),
                              hovertemplate="%{x} LY (same days) $%{y:,.0f}<extra></extra>")
                f.add_scatter(x=[xs[-1]], y=[META["ly_w30_full_week_sales"]], mode="markers",
                              marker=dict(size=9, color="rgba(0,0,0,0)", line=dict(color=T["muted"], width=1.5)),
                              hovertemplate="LY full W30 (7 days, not like-for-like) $%{y:,.0f}<extra></extra>")
                f.add_annotation(x=xs[-1], y=META["ly_w30_full_week_sales"], text="LY full week", showarrow=False, xanchor="left",
                                 xshift=8, font=dict(family=MONO, size=10.5, color=T["faint"]))
                f.add_annotation(x=xs[0], y=full[0]["sales"]["ly"], text="LY", showarrow=False, xanchor="right", xshift=-10,
                                 font=dict(family=SANS, size=12, color=T["muted"]))
            f.add_scatter(x=[f"W{r['wk']}" for r in full], y=[r["sales"]["ty"] for r in full], mode="lines+markers",
                          line=dict(color=T["accent"], width=2.5), marker=dict(size=7, color=T["accent"]),
                          hovertemplate="%{x} TY $%{y:,.0f}<extra></extra>")
            f.add_scatter(x=[last_full, xs[-1]], y=[full[-1]["sales"]["ty"], wk[-1]["sales"]["ty"]], mode="lines+markers",
                          line=dict(color=T["accent"], width=2.5, dash="dot"),
                          marker=dict(size=[7, 9], color=[T["accent"], T["surface"]], line=dict(color=T["accent"], width=2)),
                          hovertemplate="%{x} TY $%{y:,.0f}<extra></extra>")
            f.add_annotation(x=xs[0], y=full[0]["sales"]["ty"], text="TY", showarrow=False, xanchor="right", xshift=-10,
                             font=dict(family=SANS, size=12, color=T["accent"]))
            f.add_annotation(x=xs[-1], y=wk[-1]["sales"]["ty"], text="partial", showarrow=False, yshift=-16,
                             font=dict(family=MONO, size=10.5, color=T["faint"]))
            f.update_yaxes(tickprefix="$", tickformat="~s")
            show(f)
    with b:
        with chart_card("g1d", "What drove PTD demand growth", "log decomposition · W23–W30, like-for-like"):
            rows = M["decomposition_ptd"]
            f = fig_base(290, l=8, r=8)
            names = [r["factor"] for r in rows][::-1]
            vals = [r["share_of_growth"] for r in rows][::-1]
            cols = [T["accent"] if r["factor"] == "customers" else T["surface3"] for r in rows][::-1]
            f.add_bar(y=names, x=vals, orientation="h", marker=dict(color=cols), cliponaxis=False,
                      text=[f"{pct(r['share_of_growth'])} of growth · {pct(r['pct_chg'], True)}" for r in rows][::-1],
                      textposition="outside", textfont=dict(family=MONO, size=11, color=T["muted"]),
                      hovertemplate="%{y}: %{x:.1%} of growth<extra></extra>")
            f.update_xaxes(visible=False, range=[0, max(vals) * 2.4])
            f.update_yaxes(showgrid=False)
            show(f)
    st.html('<div class="note">Read: growth is a customer-count (traffic) story; UPT and frequency add nothing because every '
            'transaction is a single line and CUST_ID does not link purchases (F1, F14).</div>')


def tab_g2():
    blk = TR[WIN]
    st.html(f'<div class="note">{E(window_note(blk))}</div>')
    st.html('<div class="kpis">' + "".join([
        kpi_tile("Gen Z new customers", blk["genz_new"], num),
        kpi_tile("Gen Z share of new", blk["genz_share_of_new"], pct, is_share=True),
        kpi_tile("All new customers", blk["new_customers"], num),
        kpi_tile("Returning customers", blk["returning_customers"], num),
        kpi_tile("Returning Gen Z", blk["genz_returning"], num),
        kpi_tile("New Gen Z Insider attach", blk["genz_new_insider_rate"], pct, is_share=True)]) + "</div>")
    a, b = st.columns([1.4, 1], gap="medium")
    with a:
        with chart_card("g2s", "Gen Z share of new customers by week", "TY vs LY · W30 partial"):
            g = M["genz_weekly"]
            xs = [f"W{r['WK']}" for r in g]
            f = fig_base(280, l=40, r=40)
            f.add_vrect(x0=xs.index(f"W{W}") - 0.45, x1=xs.index(f"W{W}") + 0.45, fillcolor=T["accent_soft"], opacity=0.7, line_width=0, layer="below")
            if SHOW_LY:
                f.add_scatter(x=xs, y=[r["genz_share_of_new_LY"] for r in g], mode="lines+markers", line=dict(color=T["border2"], width=2),
                              marker=dict(size=6, color=T["border2"]), hovertemplate="%{x} LY %{y:.1%}<extra></extra>")
                f.add_annotation(x=xs[-1], y=g[-1]["genz_share_of_new_LY"], text="LY", showarrow=False, xanchor="left", xshift=8,
                                 font=dict(size=12, color=T["muted"]))
            f.add_scatter(x=xs, y=[r["genz_share_of_new_TY"] for r in g], mode="lines+markers+text", line=dict(color=T["accent"], width=2.5),
                          marker=dict(size=7, color=T["accent"]), text=[pct(r["genz_share_of_new_TY"], dp=0) for r in g],
                          textposition="top center", textfont=dict(family=MONO, size=10.5, color=T["accent_ink"]),
                          hovertemplate="%{x} TY %{y:.1%}<extra></extra>")
            f.add_annotation(x=xs[-1], y=g[-1]["genz_share_of_new_TY"], text="TY", showarrow=False, xanchor="left", xshift=10,
                             font=dict(size=12, color=T["accent"]))
            f.update_yaxes(tickformat=".0%", rangemode="tozero")
            show(f)
    with b:
        with chart_card("g2g", "New customers by generation", "PTD W23–W30 · counts (sample)"):
            gp = [r for r in M["generation_ptd"] if r["generation"] != "All"]
            f = fig_base(280, l=8, r=8)
            ys = [r["generation"] for r in gp][::-1]
            if SHOW_LY:
                f.add_bar(y=ys, x=[r["new_LY"] for r in gp][::-1], orientation="h", name="LY", marker_color=T["border2"],
                          text=[num(r["new_LY"]) for r in gp][::-1], textposition="outside", cliponaxis=False,
                          textfont=dict(family=MONO, size=10.5, color=T["faint"]), hovertemplate="%{y} LY %{x}<extra></extra>")
            f.add_bar(y=ys, x=[r["new_TY"] for r in gp][::-1], orientation="h", name="TY",
                      marker_color=[T["accent"] if r["generation"] == "Gen Z" else T["text"] if False else T["faint"] for r in gp][::-1],
                      text=[f"{num(r['new_TY'])}  {pct(r['new_yoy_pct'], True)}" for r in gp][::-1], textposition="outside",
                      cliponaxis=False, textfont=dict(family=MONO, size=10.5, color=T["muted"]), hovertemplate="%{y} TY %{x}<extra></extra>")
            f.update_layout(barmode="group")
            f.update_xaxes(visible=False, range=[0, max(r["new_TY"] for r in gp) * 1.45])
            f.update_yaxes(showgrid=False)
            show(f)
    a, b, c = st.columns([1, 1, 1], gap="medium")
    with a:
        with chart_card("g2r", "Returning customers YoY by generation", "PTD · mix proxy (D8)"):
            gp = M["generation_ptd"]
            f = fig_base(240, l=8, r=8)
            ys = [r["generation"] for r in gp][::-1]
            xv = [r["returning_yoy_pct"] for r in gp][::-1]
            f.add_bar(y=ys, x=xv, orientation="h",
                      marker_color=[T["accent"] if r["generation"] == "Gen Z" else T["surface3"] for r in gp][::-1],
                      text=[pct(x, True) for x in xv], textposition="outside", cliponaxis=False,
                      textfont=dict(family=MONO, size=10.5, color=T["muted"]), hovertemplate="%{y} %{x:+.1%}<extra></extra>")
            lim = max(abs(x) for x in xv) * 1.8
            f.update_xaxes(visible=False, range=[-lim, lim])
            f.update_yaxes(showgrid=False)
            f.add_vline(x=0, line_color=T["border2"], line_width=1)
            show(f)
    with b:
        with chart_card("g2m", "First purchase of new Gen Z, by family", "TY · share of first purchases · top 8"):
            mix = [r for r in M["first_purchase_mix"] if r["dimension"] == "STYLE_GROUP" and r["YEAR"] == "TY"]
            mix = sorted(mix, key=lambda r: r["genz_new_share"], reverse=True)[:8][::-1]
            f = fig_base(240, l=8, r=8)
            f.add_bar(y=[r["segment"] for r in mix], x=[r["other_new_share"] for r in mix], orientation="h", marker_color=T["surface3"],
                      hovertemplate="%{y} other new %{x:.1%}<extra></extra>")
            f.add_bar(y=[r["segment"] for r in mix], x=[r["genz_new_share"] for r in mix], orientation="h",
                      marker_color=T["accent"], text=[f"{pct(r['genz_new_share'])} · idx {num(r['index_vs_other_new'])}" for r in mix],
                      textposition="outside", cliponaxis=False, textfont=dict(family=MONO, size=10.5, color=T["muted"]),
                      hovertemplate="%{y} Gen Z new %{x:.1%}<extra></extra>")
            f.update_layout(barmode="group")
            f.update_xaxes(visible=False, range=[0, max(r["genz_new_share"] for r in mix) * 1.9])
            f.update_yaxes(showgrid=False)
            show(f)
            st.html('<div class="note"><span style="color:var(--accent)">■</span> new Gen Z · <span style="color:var(--faint)">■</span> other new</div>')
    with c:
        with chart_card("g2i", "Insider attach of new customers", "TY · Gen Z vs other new, by segment"):
            seg = M["new_insider_by_segment"][::-1]
            labs = [f"{r['segment'].title() if r['segment'].isupper() else r['segment']}" for r in seg]
            f = fig_base(240, l=8, r=8)
            f.add_bar(y=labs, x=[r["other_new_insider_rate"] for r in seg], orientation="h", marker_color=T["surface3"],
                      hovertemplate="%{y} other new %{x:.1%}<extra></extra>")
            f.add_bar(y=labs, x=[r["genz_new_insider_rate"] for r in seg], orientation="h", marker_color=T["accent"],
                      text=[pct(r["genz_new_insider_rate"]) for r in seg], textposition="outside", cliponaxis=False,
                      textfont=dict(family=MONO, size=10.5, color=T["muted"]), hovertemplate="%{y} Gen Z new %{x:.1%}<extra></extra>")
            f.update_layout(barmode="group")
            f.update_xaxes(visible=False, range=[0, max(r["other_new_insider_rate"] for r in seg) * 1.35])
            f.update_yaxes(showgrid=False)
            show(f)
    st.html('<div class="callout"><b>Retention is a proxy here (D8).</b> CUST_ID does not link a customer across purchases (F14), so '
            'there is no cohort repeat rate. “Returning” = transactions whose COHORT_STATUS is Retained or Reactivated, and Insider '
            'attach of new customers is the leading indicator. Read these as mix measures, not “x% came back”.</div>')


def tab_g3():
    if WIN == "PTD":
        st.html('<div class="note">The weekly family table exists for L1W and L4W; PTD uses the family scorecard below.</div>')
    win3 = WIN if WIN in ("L1W", "L4W") else "L4W"
    rows = [r for r in M["products_by_week"] if r["wk"] == W and r["window"] == win3]
    c1, c2 = st.columns([3, 1], vertical_alignment="bottom")
    c1.html(f'<div class="ctitle" style="margin-top:6px"><b>Families · {win3} ending W{W}</b>'
            f'<span>contribution = percentage points of total YoY growth</span></div>')
    sort_opts = {"contrib_pts": "Contribution (pts)", "sales_yoy_pct": "Demand YoY", "genz_index_ty": "Gen Z index"}
    c2.selectbox("Sort by", list(sort_opts), key="sort3", format_func=sort_opts.get)
    key = ss.sort3
    rows = sorted(rows, key=lambda r: (r[key] is None, -(r[key] or 0)))
    mx = max(abs(r["contrib_pts"]) for r in rows) or 1
    trs = []
    for r in rows:
        w = abs(r["contrib_pts"]) / mx * 70  # drawing geometry only
        bar = (f'<span class="mbar" style="width:{w:.0f}px;background:var(--{"accent" if r["contrib_pts"] >= 0 else "red"})"></span>')
        ly_cells = (f'<td class="r mono">{money(r["sales_ly"])}</td>' if SHOW_LY else "")
        trs.append(f'<tr class="{"hl" if r["family"] == ss.family else ""}"><td>{E(r["family"])}</td><td class="r mono">{money(r["sales_ty"])}</td>{ly_cells}'
                   f'<td class="r mono {tone(r["sales_yoy_pct"])}">{pct(r["sales_yoy_pct"], True)}</td>'
                   f'<td class="r mono">{pts(r["contrib_pts"])}</td><td>{bar}</td>'
                   f'<td class="r mono">{num(r["genz_index_ty"])}</td><td class="r mono">{txn_cell(r)}</td></tr>')
    st.html(f'<div class="ccard tblwrap"><table class="tbl"><tr><th>Family</th><th class="r">Demand TY</th>{"<th class=r>Demand LY</th>" if SHOW_LY else ""}'
            f'<th class="r">YoY</th><th class="r">Contribution</th><th></th><th class="r">Gen Z index</th>'
            f'<th class="r">Txns TY{" / LY" if SHOW_LY else ""}</th></tr>{"".join(trs)}</table></div>')
    a, b = st.columns([1.2, 1], gap="medium")
    with a:
        with chart_card("g3s", "Growth vs Gen Z over-index", "PTD · bubble = TY demand · Hero families highlighted"):
            pp = M["products_ptd"]
            f = fig_base(330, l=46, r=16)
            mxs = max(r["sales_TY"] for r in pp)
            for hero in (False, True):
                sub = [r for r in pp if (r["PROD_TYPE"] == "Hero") == hero]
                f.add_scatter(x=[r["sales_yoy_pct"] for r in sub], y=[r["genz_index_TY"] for r in sub], mode="markers+text",
                              marker=dict(size=[8 + 26 * (r["sales_TY"] / mxs) ** 0.5 for r in sub],  # drawing geometry only
                                          color=T["accent"] if hero else T["surface3"], line=dict(color=T["accent"] if hero else T["border2"], width=1),
                                          opacity=0.9),
                              text=[r["STYLE_GROUP"] if (hero or r["class"] != "Steady" or r["genz_index_TY"] > 130) else "" for r in sub],
                              textposition="top center", textfont=dict(size=11, color=T["accent_ink"] if hero else T["muted"]),
                              customdata=[[r["STYLE_GROUP"], r["class"]] for r in sub],
                              hovertemplate="%{customdata[0]} (%{customdata[1]})<br>YoY %{x:+.1%} · Gen Z index %{y:.0f}<extra></extra>")
            f.add_hline(y=100, line_color=T["border2"], line_dash="dot", line_width=1)
            f.add_vline(x=0, line_color=T["border2"], line_dash="dot", line_width=1)
            f.update_xaxes(tickformat="+.0%", showgrid=True, gridcolor=T["border"], title=dict(text="Demand YoY (PTD)", font=dict(size=11.5)))
            f.update_yaxes(title=dict(text="Gen Z index (100 = average)", font=dict(size=11.5)))
            show(f)
    with b:
        pp = sorted(M["products_ptd"], key=lambda r: -r["contrib_pts"])
        trs = "".join(
            f'<tr class="{"hl" if r["STYLE_GROUP"] == ss.family else ""}"><td>{E(r["STYLE_GROUP"])}</td><td><span class="pill {r["class"].lower()}">{E(r["class"])}</span></td>'
            f'<td class="r mono {tone(r["sales_yoy_pct"])}">{pct(r["sales_yoy_pct"], True)}</td><td class="r mono">{pts(r["contrib_pts"] * 100)}</td>'
            f'<td class="r mono">{pct(r["share_of_growth"])}</td></tr>' for r in pp)
        st.html(f'<div class="ccard tblwrap" style="max-height:372px;overflow-y:auto"><div class="ctitle"><b>PTD scorecard</b><span>W23–W30 like-for-like</span></div>'
                f'<table class="tbl"><tr><th>Family</th><th>Class</th><th class="r">YoY</th><th class="r">Contribution</th>'
                f'<th class="r">Share of growth</th></tr>{trs}</table></div>')
    c1, c2 = st.columns([1, 3], vertical_alignment="bottom")
    if ss.family not in FAMILIES:
        ss.family = "Tabby"
    c1.selectbox("Style drill-down · family", FAMILIES, key="family")
    sty = [r for r in M["styles_ptd"] if r["STYLE_GROUP"] == ss.family]
    trs = "".join(f'<tr><td>{E(r["STYLE_DESC"])}</td><td class="r mono">{money(r["sales_TY"])}</td>'
                  f'{td(money(r["sales_LY"])) if SHOW_LY else ""}'
                  f'<td class="r mono {tone(r["sales_yoy_pct"])}">{pct(r["sales_yoy_pct"], True)}</td>'
                  f'<td class="r mono">{num(r["genz_index_TY"])}</td><td class="r mono">{num(r["txns_TY"])}</td></tr>' for r in sty)
    st.html(f'<div class="ccard tblwrap"><table class="tbl"><tr><th>Style · {E(ss.family)} · PTD</th><th class="r">Demand TY</th>'
            f'{"<th class=r>Demand LY</th>" if SHOW_LY else ""}<th class="r">YoY</th><th class="r">Gen Z index</th><th class="r">Txns TY</th></tr>'
            f'{trs or "<tr><td colspan=6 class=note>No style passes the minimum-volume rule for this family (D12).</td></tr>"}</table></div>')


def _rule_threshold(rule_id):
    m = re.search(r"([\d.]+)", RULES[rule_id]["rule"])
    return float(m.group(1)) if m else None


def tab_g4():
    inv = sorted([r for r in M["inventory_by_week"] if r["year"] == "TY" and r["wk"] == W], key=lambda r: r["wos"] or 0)
    lo, hi = _rule_threshold("WOS_LOW"), _rule_threshold("WOS_HIGH")
    truncated = inv and inv[0]["wos_window_weeks"] < 4
    a, b = st.columns([1.15, 1], gap="medium")
    with a:
        with chart_card("g4w", f"Weeks of supply by family · W{W}",
                        "TY bars · LY same week ◆ · values TY / LY · dotted lines = stock rules" + (" · window truncated: rules off" if truncated else "")):
            f = fig_base(560, l=8, r=40)
            ys = [r["family"] for r in inv]
            col = [T["red"] if r["wos"] is not None and r["wos"] < lo else T["amber"] if r["wos"] is not None and r["wos"] > hi else T["surface3"] for r in inv]
            xr = max(max(r["wos"] or 0 for r in inv), max(r["wos_ly_same_week"] or 0 for r in inv) if SHOW_LY else 0)
            f.add_bar(y=ys, x=[r["wos"] for r in inv], orientation="h", marker_color=col,
                      customdata=[[r["on_hand_eow"], r["units_sold"]] for r in inv],
                      hovertemplate="%{y}: %{x:.1f} weeks · %{customdata[0]} on hand · %{customdata[1]} sold this week<extra></extra>")
            if SHOW_LY:
                f.add_scatter(y=ys, x=[r["wos_ly_same_week"] for r in inv], mode="markers",
                              marker=dict(symbol="diamond", size=8, color=T["text"], line=dict(color=T["surface"], width=1)),
                              hovertemplate="%{y}: LY %{x:.1f} weeks<extra></extra>")
            # aligned value column at the right edge (position = drawing geometry): "TY / LY"
            f.add_scatter(y=ys, x=[xr * 1.5] * len(inv), mode="text", textposition="middle left", hoverinfo="skip",
                          text=[wosf(r["wos"]) + (f"  /  {wosf(r['wos_ly_same_week'])}" if SHOW_LY else "") for r in inv],
                          textfont=dict(family=MONO, size=10.5, color=T["muted"]))
            f.update_xaxes(range=[0, xr * 1.51])
            for x, lab in ((lo, "low-stock rule"), (hi, "high-stock rule")):
                f.add_vline(x=x, line_color=T["border2"], line_dash="dot", line_width=1)
                f.add_annotation(x=x, y=1.0, yref="paper", text=RULES['WOS_LOW' if x == lo else 'WOS_HIGH']['rule'].replace(" weeks", " wk"),
                                 showarrow=False, xanchor="left", xshift=3, yshift=8, font=dict(family=MONO, size=10, color=T["faint"]),
                                 hovertext=lab)
            f.update_xaxes(showgrid=True, gridcolor=T["border"], title=dict(text="weeks of supply", font=dict(size=11)))
            f.update_yaxes(showgrid=False, autorange=True)
            f.update_layout(margin=dict(t=26))
            show(f)
    with b:
        for fam in ("Tabby", "Pillow Tabby"):
            with chart_card(f"g4t_{fam}", f"{fam}: stock vs demand by week", "units · TY on hand (line) vs units sold (bars)"):
                ty = [r for r in M["inventory_by_week"] if r["family"] == fam and r["year"] == "TY"]
                ly = [r for r in M["inventory_by_week"] if r["family"] == fam and r["year"] == "LY"]
                xs = [f"W{r['wk']}" for r in ty]
                f = fig_base(232, l=36, r=40)
                f.add_bar(x=xs, y=[r["units_sold"] for r in ty], marker_color=T["surface3"],
                          hovertemplate="%{x} sold %{y}<extra></extra>")
                if SHOW_LY:
                    f.add_scatter(x=xs, y=[r["on_hand_eow"] for r in ly], mode="lines", line=dict(color=T["border2"], width=2, dash="dot"),
                                  hovertemplate="%{x} LY on hand %{y}<extra></extra>")
                    f.add_annotation(x=xs[-1], y=ly[-1]["on_hand_eow"], text="LY", xanchor="left", xshift=6, showarrow=False,
                                     font=dict(size=11, color=T["muted"]))
                f.add_scatter(x=xs, y=[r["on_hand_eow"] for r in ty], mode="lines+markers", line=dict(color=T["accent"], width=2.5),
                              marker=dict(size=6, color=T["accent"]), hovertemplate="%{x} TY on hand %{y}<extra></extra>")
                f.add_annotation(x=xs[-1], y=ty[-1]["on_hand_eow"], text="TY", xanchor="left", xshift=6, showarrow=False,
                                 font=dict(size=11, color=T["accent"]))
                f.add_vrect(x0=xs.index(f"W{W}") - 0.45, x1=xs.index(f"W{W}") + 0.45, fillcolor=T["accent_soft"], opacity=0.6, line_width=0, layer="below")
                show(f)
    pos = sorted(M["inventory_position"], key=lambda r: r["stock_minus_demand_share_pts"])
    trs = "".join(
        f'<tr class="{"hl" if r["STYLE_GROUP"] == ss.family else ""}"><td>{E(r["STYLE_GROUP"])}</td>'
        f'<td><span class="pill {"under" if "Under" in r["risk"] else "over" if "Over" in r["risk"] else "steady"}">{E(r["risk"])}</span></td>'
        f'<td class="r mono">{wosf(r["wos_W29_TY"])}</td>{td(wosf(r["wos_W29_LY"])) if SHOW_LY else ""}'
        f'<td class="r mono">{wosf(r["wos_W30_TY_latest"])}</td>'
        f'{td(ratio2(r["receipts_to_sales_TY"]))}'
        f'{td(ratio2(r["receipts_to_sales_LY"])) if SHOW_LY else ""}'
        f'<td class="r mono {gap_cls(r["stock_minus_demand_share_pts"], r["risk"])}">{pts(r["stock_minus_demand_share_pts"])}</td>'
        f'<td>{E(r["g3_class"] or "")}</td></tr>' for r in pos)
    st.html(f'<div class="ccard tblwrap"><div class="ctitle"><b>Stock risk by family · latest position</b>'
            f'<span>WOS at W29 (full week) and W30 snapshot · receipts ÷ units sold W24–W29 · stock share minus demand share</span></div>'
            f'<table class="tbl"><tr><th>Family</th><th>Risk</th><th class="r">WOS W29 TY</th>{"<th class=r>WOS W29 LY</th>" if SHOW_LY else ""}'
            f'<th class="r">WOS latest</th><th class="r">Receipts/sales TY</th>{"<th class=r>Receipts/sales LY</th>" if SHOW_LY else ""}'
            f'<th class="r">Stock − demand share</th><th>G3 class</th></tr>{trs}</table></div>')
    st.html('<div class="callout"><b>Data caveat (F13).</b> The TY W30 stock snapshot is labelled end-of-week but TY sales stop on '
            f'{E(date_words(META["data_quality"]["ty_last_sale_date"]))}; it is used as the latest position with a full-week (W26–W29) demand denominator.</div>')


def page_explore():
    header(f"CLASSIC DASHBOARD · W{W} · {WIN}", "Everything is here. <em>You find the story.</em>",
           "The goal-by-goal view: KPI tiles, trends and tables for the selected week and window. Every number is a "
           "precomputed field from metrics.json; the briefing is where the agent ranks what changed.", "explore")
    st.html('<div style="height:6px"></div>')
    ss.tab_w = ss.tab
    st.radio("Goal", list(TABS), key="tab_w", format_func=TABS.get, horizontal=True, label_visibility="collapsed",
             on_change=lambda: ss.update(tab=ss.tab_w))
    with st.container(key="xbody"):
        {"G1": tab_g1, "G2": tab_g2, "G3": tab_g3, "G4": tab_g4}[ss.tab]()


# =====================================================================================================
# PAGE: ASK (fixed query templates; the model may only pick a template + parameters)
# =====================================================================================================
TEMPLATES = {
    "wos_threshold": "Which families have WOS below/above {x} in week {w}?",
    "genz_new": "Gen Z new customers in {window} ending week {w}?",
    "top_contrib": "Top/bottom {n} families by contribution in {window} for week {w}",
    "sales_kpi": "How did sales do in {window} ending week {w}?",
    "why_flagged": "Why is {entity} flagged in week {w}?",
    "genz_share_trend": "Gen Z share of new customers by week up to week {w}?",
    "insider_segments": "Where is the Insider gap for new Gen Z?",
    "winners": "Which families are winners / decliners?",
}
RETENTION_RULES = {"RETURNING_YOY_FLAT", "GENZ_RETURNING_YOY_NEG", "GENZ_NEW_INSIDER_LOW"}
SUGGESTED = ["Why is Tabby flagged in week 29?", "Which families have WOS below 3 in week 30?",
             "Top 3 families by contribution in L4W for week 29", "Gen Z new customers in L4W ending week 29?",
             "How did sales do in L1W ending week 28?", "Where is the Insider gap for new Gen Z?"]


def parse_question(qtext):
    """Deterministic template picker (offline default). Returns (template_id, params) or (None, None)."""
    t = qtext.lower()
    p = {}
    m = re.search(r"\b(?:w|wk|week)\s*(\d{2})\b", t)
    p["w"] = int(m.group(1)) if m and int(m.group(1)) in WEEKS else W
    m = re.search(r"\b(l1w|l4w|ptd)\b", t)
    p["window"] = m.group(1).upper() if m else ("L1W" if "last week" in t else "PTD" if "period" in t or "to date" in t else WIN)
    fam = next((f for f in sorted(FAMILIES, key=len, reverse=True) if f.lower() in t), None)
    if "why" in t and ("flag" in t or "alert" in t or "why is" in t):
        ent = fam or ("retention" if "retention" in t or "returning" in t else "genz" if "gen z" in t or "genz" in t else "total")
        return "why_flagged", {"entity": ent, "w": p["w"]}
    if "wos" in t or "weeks of supply" in t or ("stock" in t and re.search(r"below|under|above|over", t)):
        m = re.search(r"(below|under|less than|<|above|over|more than|>)\s*(\d+(?:\.\d+)?)", t)
        if m:
            return "wos_threshold", {"op": "above" if m.group(1) in ("above", "over", "more than", ">") else "below",
                                     "x": float(m.group(2)), "w": p["w"]}
    m = re.search(r"\b(top|bottom)\s*(\d+)?", t)
    if m and ("contribut" in t or "famil" in t or "growth" in t):
        return "top_contrib", {"dir": m.group(1), "n": int(m.group(2) or 5), "window": p["window"], "w": p["w"]}
    if "insider" in t:
        return "insider_segments", {}
    if ("gen z" in t or "genz" in t) and "share" in t:
        return "genz_share_trend", {"w": p["w"]}
    if ("gen z" in t or "genz" in t) and "new" in t:
        return "genz_new", {"window": p["window"], "w": p["w"]}
    if "winner" in t or "decliner" in t or "winning" in t:
        return "winners", {}
    if re.search(r"sales|demand|perform|how did|revenue|aov|transactions", t):
        return "sales_kpi", {"window": p["window"], "w": p["w"]}
    return None, None


# === LIVE MODEL PLUG-IN POINT (Ask) ===
def pick_template(qtext):
    """With ANTHROPIC_API_KEY set, Claude picks the template + params (JSON only; it never sees or writes numbers
    from the data). Any invalid choice falls back to the deterministic parser. The answer is always rendered by code."""
    if os.environ.get("ANTHROPIC_API_KEY"):
        try:
            import anthropic
            client = anthropic.Anthropic()
            resp = client.messages.create(
                model="claude-opus-5-5", max_tokens=2000,
                system=("Map the user's question to exactly one query template and its parameters. Reply with JSON only: "
                        '{"template": <id or null>, "params": {...}}. Templates: ' + json.dumps(TEMPLATES) +
                        f". Valid weeks: {WEEKS}. Valid windows: {WINDOWS}. Valid entities: {FAMILIES + ['retention', 'genz', 'total']}. "
                        f"Default week {W}, default window {WIN}."),
                messages=[{"role": "user", "content": qtext}],
                extra_headers={"anthropic-beta": "server-side-fallback-2026-07-01"},
                extra_body={"fallbacks": "default", "output_config": {"effort": "low"}},
            )
            if resp.stop_reason != "refusal":
                out = json.loads("".join(b.text for b in resp.content if getattr(b, "type", "") == "text"))
                if out.get("template") in TEMPLATES:
                    return out["template"], out.get("params") or {}, "live:claude-opus-5-5"
        except Exception:
            pass
    tid, params = parse_question(qtext)
    return tid, params, "rule-based parser"
# === END LIVE MODEL PLUG-IN POINT ===


def answer(tid, p):
    """Render an answer from metrics.json / anomalies.json by code. Returns dict(a, table, steps)."""
    w = int(p.get("w", W)) if str(p.get("w", W)).isdigit() else W
    win = p.get("window", WIN) if p.get("window") in WINDOWS else WIN
    if tid == "wos_threshold":
        x, op = float(p.get("x", 3)), p.get("op", "below")
        rows = [r for r in M["inventory_by_week"] if r["year"] == "TY" and r["wk"] == w and r["wos"] is not None
                and (r["wos"] < x if op == "below" else r["wos"] > x)]
        rows.sort(key=lambda r: r["wos"], reverse=op == "above")
        trunc = rows and rows[0]["wos_window_weeks"] < 4
        a = (f"{len(rows)} famil{'y has' if len(rows) == 1 else 'ies have'} weeks of supply {op} {x:g} in W{w}"
             + (": " + ", ".join(f"{r['family']} {wosf(r['wos'])}" for r in rows) if rows else ".")
             + (" Note: the WOS window is truncated before W26, so the rules don't use these readings." if trunc else ""))
        table = [{"Family": r["family"], "WOS TY": wosf(r["wos"]), "WOS LY same week": wosf(r["wos_ly_same_week"]),
                  "On hand": num(r["on_hand_eow"]), "Units sold": num(r["units_sold"])} for r in rows]
        return a, table, f"inventory_by_week where year=TY, wk={w}, wos {'<' if op == 'below' else '>'} {x:g}"
    if tid == "genz_new":
        b = M["trailing"][str(w)][win]
        g, s = b["genz_new"], b["genz_share_of_new"]
        a = (f"Gen Z new customers, {win} ending W{w} ({window_note(b).split('= ')[1]}): {num(g['ty'])} vs {num(g['ly'])} LY "
             f"({pct(g['yoy_pct'], True)}). That is {pct(s['ty'])} of all new customers vs {pct(s['ly'])} LY ({pts(s['chg_pts'])}).")
        return a, [], f"trailing.{w}.{win}.genz_new, .genz_share_of_new"
    if tid == "top_contrib":
        n, d = int(p.get("n", 5)), p.get("dir", "top")
        if win == "PTD":
            rows = sorted(M["products_ptd"], key=lambda r: r["contrib_pts"], reverse=d == "top")[:n]
            table = [{"Family": r["STYLE_GROUP"], "Contribution": pts(r["contrib_pts"] * 100), "YoY": pct(r["sales_yoy_pct"], True),
                      "Class": r["class"]} for r in rows]
            a = f"{d.title()} {n} families by contribution to PTD growth: " + ", ".join(f"{r['STYLE_GROUP']} ({pts(r['contrib_pts'] * 100)})" for r in rows) + "."
            return a, table, "products_ptd sorted by contrib_pts"
        rows = sorted([r for r in M["products_by_week"] if r["wk"] == w and r["window"] == win], key=lambda r: r["contrib_pts"],
                      reverse=d == "top")[:n]
        table = [{"Family": r["family"], "Contribution": pts(r["contrib_pts"]), "YoY": pct(r["sales_yoy_pct"], True),
                  "Demand TY": money(r["sales_ty"]), "Gen Z index": num(r["genz_index_ty"])} for r in rows]
        a = f"{d.title()} {n} families by contribution, {win} ending W{w}: " + ", ".join(f"{r['family']} ({pts(r['contrib_pts'])})" for r in rows) + "."
        return a, table, f"products_by_week where wk={w}, window={win}, sorted by contrib_pts"
    if tid == "sales_kpi":
        b = M["trailing"][str(w)][win]
        a = (f"{win} ending W{w} ({window_note(b).split('= ')[1]}): demand {money(b['sales']['ty'])} vs {money(b['sales']['ly'])} LY "
             f"({pct(b['sales']['yoy_pct'], True)}); transactions {pct(b['txns']['yoy_pct'], True)}; AOV {money(b['aov']['ty'], False)} "
             f"({pct(b['aov']['yoy_pct'], True)}).")
        if win == "L1W" and b.get("wow"):
            a += f" Week-on-week: demand {pct(b['wow']['sales'], True)}, transactions {pct(b['wow']['txns'], True)}, AOV {pct(b['wow']['aov'], True)}."
        return a, [], f"trailing.{w}.{win}.sales / txns / aov"
    if tid == "why_flagged":
        ent = p.get("entity", "total")
        ent_l = {"gen z": "genz"}.get(str(ent).lower(), ent)
        # "retention" means the retention card's rule set (two retention rules + the new Gen Z Insider-attach rule)
        match = (lambda a: a["rule_id"] in RETENTION_RULES) if str(ent_l).lower() == "retention" else \
            (lambda a: a["entity"].lower() == str(ent_l).lower())
        hits = [AN[i] for i in A["by_week"][str(w)] if match(AN[i])]
        if not hits:
            return (f"No rule fired for {ent} in W{w}. Try another week, or open the rail on the Briefing page for that week's alerts.",
                    [], f"anomalies.json by_week[{w}] filtered to entity={ent}")
        a = f"{len(hits)} rule{'s' if len(hits) > 1 else ''} fired for {ent} in W{w}: " + " ".join(h["message"] for h in hits)
        cards = [c for c in BRIEF[str(w)]["cards"] if set(c["anomaly_ids"]) & {h["id"] for h in hits}]
        if cards and cards[0]["validation"]["status"] == "PASS":
            a += f" Agent’s read: {cards[0]['headline']}"
        table = [{"Alert": h["id"], "Severity": SEV_ICON[h["severity"]][1], "Rule": RULE_LABEL[h["rule_id"]],
                  "Threshold": RULES[h["rule_id"]]["rule"]} for h in hits]
        return a, table, f"anomalies.json by_week[{w}] where entity={ent}; card text from briefing.json (validated)"
    if tid == "genz_share_trend":
        rows = [r for r in M["genz_weekly"] if r["WK"] <= w]
        table = [{"Week": f"W{r['WK']}", "TY share": pct(r["genz_share_of_new_TY"]), "LY share": pct(r["genz_share_of_new_LY"]),
                  "Gen Z new TY": num(r["genz_new_TY"]), "Gen Z new LY": num(r["genz_new_LY"])} for r in rows]
        a = (f"Gen Z share of new customers went from {pct(rows[0]['genz_share_of_new_TY'])} in W{rows[0]['WK']} to "
             f"{pct(rows[-1]['genz_share_of_new_TY'])} in W{rows[-1]['WK']} (LY that week {pct(rows[-1]['genz_share_of_new_LY'])}).")
        return a, table, f"genz_weekly where WK <= {w}"
    if tid == "insider_segments":
        rows = sorted(M["new_insider_by_segment"], key=lambda r: r["genz_new_insider_rate"])
        table = [{"Segment": r["segment"], "Gen Z new": pct(r["genz_new_insider_rate"]), "Other new": pct(r["other_new_insider_rate"]),
                  "n Gen Z": num(r["genz_new_n"]), "p-value": f"{r['p']:.3f}"} for r in rows]
        a = ("TY Insider attach of new Gen Z vs other new customers, lowest first. The gap is significant where p < 0.05: "
             + ", ".join(f"{r['segment']} {pct(r['genz_new_insider_rate'])} vs {pct(r['other_new_insider_rate'])}" for r in rows if r["p"] < 0.05) + ".")
        return a, table, "new_insider_by_segment sorted by genz_new_insider_rate"
    if tid == "winners":
        rows = [r for r in M["products_ptd"] if r["class"] in ("Winner", "Decliner")]
        rows.sort(key=lambda r: (r["class"] != "Winner", -r["sales_yoy_pct"]))
        table = [{"Family": r["STYLE_GROUP"], "Class": r["class"], "YoY": pct(r["sales_yoy_pct"], True),
                  "Contribution": pts(r["contrib_pts"] * 100), "Gen Z index": num(r["genz_index_TY"])} for r in rows]
        a = ("Winners: " + ", ".join(r["STYLE_GROUP"] for r in rows if r["class"] == "Winner") + ". Decliners: "
             + ", ".join(r["STYLE_GROUP"] for r in rows if r["class"] == "Decliner") + " (PTD, minimum-volume rule D12).")
        return a, table, "products_ptd where class in (Winner, Decliner)"
    return None, [], ""


def table_html(rows):
    if not rows:
        return ""
    cols = list(rows[0])
    head = "".join(f"<th>{E(c)}</th>" for c in cols)
    body = "".join("<tr>" + "".join(f'<td class="{"mono" if i else ""}">{E(str(r[c]))}</td>' for i, c in enumerate(cols)) + "</tr>" for r in rows)
    return f'<div class="tblwrap" style="margin-top:10px"><table class="tbl"><tr>{head}</tr>{body}</table></div>'


def run_question(qtext):
    tid, params, picker = pick_template(qtext)
    if tid is None:
        ss.chat.append({"q": qtext, "a": "I can only answer questions that map to one of my fixed query templates, so I don't guess. "
                        "Try one of these: " + " · ".join(TEMPLATES.values()), "table": [], "steps": [f"<b>1</b> · {picker}: no template matched"]})
        return
    a, table, src = answer(tid, params)
    ss.chat.append({"q": qtext, "a": a, "table": table, "steps": [
        f"<b>1 · pick</b> {E(picker)} → template <b>{E(tid)}</b> · params {E(json.dumps(params))}",
        f"<b>2 · read</b> metrics.json / anomalies.json → {E(src)}",
        f"<b>3 · render</b> numbers formatted by code; nothing written by a model"]})


def page_ask():
    if ss.get("pending_q"):
        run_question(ss.pop("pending_q"))
    hl, hr = st.columns([5, 1], vertical_alignment="center")
    hl.html('<div class="askhead"><div><b>Ask</b><span>template Q&amp;A over metrics.json</span></div></div>')
    with hr:
        st.button("New chat", key="newchat", on_click=lambda: ss.update(chat=[]))
    _, mid, _ = st.columns([1, 3.2, 1])
    with mid:
        if not ss.chat:
            st.html('<div class="askhero"><div class="t">Ask about any family, week or metric</div>'
                    '<div class="s">I map your question to a fixed query template, read metrics.json, and show my steps. '
                    'A model may pick the template; it never writes the numbers.</div></div>')
            g1, g2 = st.columns(2)
            for i, s in enumerate(SUGGESTED):
                (g1 if i % 2 == 0 else g2).button(s, key=f"sugg_{i}", on_click=lambda s=s: run_question(s), use_container_width=True)
        for m in ss.chat:
            st.html(f'<div class="q">{E(m["q"])}</div><div class="ans"><div class="a">{E(m["a"])}</div>{table_html(m["table"])}'
                    f'<div class="steps">{"".join(f"<div>{s}</div>" for s in m["steps"])}</div></div>')
        st.html('<div style="height:14px"></div>')
        with st.container(key="askform"):
            with st.form("ask_form", clear_on_submit=True, border=False):
                c1, c2 = st.columns([6, 1], vertical_alignment="center")
                qtext = c1.text_input("Question", placeholder="Ask about a family, week or metric", label_visibility="collapsed")
                sent = c2.form_submit_button("Send", use_container_width=True)
            if sent and qtext.strip():
                run_question(qtext.strip())
                st.rerun()
        st.html('<div class="note" style="text-align:center;margin-top:8px">Templates: ' + " · ".join(E(t) for t in TEMPLATES.values()) + '</div>')


# =====================================================================================================
# PAGE: HOW IT WAS BUILT
# =====================================================================================================
def page_build():
    bs = BSTATS
    c = META["counts"]
    st.html(f"""<h1 class="serif-h1" style="margin-top:22px !important">How this dashboard was built</h1>
    <div class="stats">
      <div class="stat"><div class="v">{bs['findings_audit_pass']}/{bs['findings_audit_total']}</div><div class="c">headline numbers in FINDINGS.md re-derived from metrics.json (14_findings_audit.md)</div></div>
      <div class="stat"><div class="v">{bs['texts_pass']}/{bs['texts_total']}</div><div class="c">AI-worded texts passed the number check · {num(bs['numbers_checked'])} numbers traced</div></div>
      <div class="stat"><div class="v">{bs['n_scripts']}</div><div class="c">numbered scripts from the raw xlsx to this page · one command: ./run_all.sh --clean</div></div>
    </div>""")
    n_sections = len(M)
    st.html(f"""<div class="secnum">01</div><div class="h2">Same data, every number traced</div>
    <div class="lead" style="margin-bottom:16px">Rules decide what is unusual. Claude only words what the rules and metrics already say, and a validator checks every number before it reaches the screen.</div>
    <div class="flow">
      <div class="node"><div class="k">source</div><div class="t">Raw xlsx</div><div class="d">{num(c['lines_total'])} lines · {num(c['inventory_snapshots'])} stock snapshots · read-only</div></div><div class="arr">→</div>
      <div class="node"><div class="k">python · 01–11</div><div class="t">metrics.json</div><div class="d">{n_sections} sections indexed by week · like-for-like basis</div></div><div class="arr">→</div>
      <div class="node"><div class="k">python · 12</div><div class="t">Rules</div><div class="d">anomalies.json · {len(A['rules'])} rules · {A['meta']['n_anomalies']} alerts</div></div><div class="arr">→</div>
      <div class="node claude"><div class="k">claude · facts only</div><div class="t">✦ Claude</div><div class="d">words the summary and {bs['cards_total']} cards from a per-week facts JSON</div></div><div class="arr">→</div>
      <div class="node check"><div class="k">python · 17</div><div class="t">Validator</div><div class="d">{num(bs['numbers_checked'])} numbers checked · a miss blocks the text and fails the build</div></div><div class="arr">→</div>
      <div class="node"><div class="k">streamlit</div><div class="t">This UI</div><div class="d">selects and formats fields · re-checks every text at render</div></div>
    </div>""")
    s29 = SUMM[str(META["last_full_week"])]
    f29 = load(ROOT / s29["facts_file"])
    snippet = "\n".join(f"{k}: {json.dumps(v)}" for k, v in list(f29.items())[3:11])
    first = s29["text"].split(". ")[0] + "."
    v29 = s29["validation"]
    st_ = bs["selftest_injected"]
    chips = "".join(f'<span class="okchip">{E(m["text"])} ✓</span>' for m in v29["matches"][:8])
    st.html(f"""<div class="secnum">02</div><div class="h2">How Claude is used</div>
    <div style="margin:8px 0 14px 0"><span class="tag">claude-opus-5-5</span> <span class="note">writes the weekly summary and briefing cards · offline at build time (live when ANTHROPIC_API_KEY is set)</span></div>
    <div class="four">
      <div class="box"><div class="k">1 · facts for W{META['last_full_week']}</div><pre>{E(snippet)}\n…</pre></div><div class="arr">→</div>
      <div class="box prompt"><div class="k">2 · system prompt</div><div class="quote">“{E(WRITER.SYSTEM_SUMMARY.split('. ')[1])}. {E(WRITER.SYSTEM_SUMMARY.split('. ')[2])}.”</div></div><div class="arr">→</div>
      <div class="box"><div class="k">3 · Claude writes</div><div class="quote">{E(first)}</div></div><div class="arr">→</div>
      <div class="box"><div class="k">4 · number check</div>{chips}<div class="note" style="margin-top:6px">{v29['n_matched']}/{v29['n_numbers']} found in the facts → shown.<br>
        Self-test: injected <span class="badchip">{E(', '.join(st_['unmatched']))}</span> → {E(st_['injected_status'])} → blocked, facts table instead.</div></div>
    </div>""")
    with st.expander("Full system prompts (summary and cards)"):
        st.code(WRITER.SYSTEM_SUMMARY + "\n\n" + WRITER.SYSTEM_CARD, language=None)
    defs = "".join(f'<div class="k">{E(k)}</div><div>{E(v)}</div>' for k, v in META["definitions"].items())
    st.html(f'<div class="secnum">03</div><div class="h2">Definitions</div><div class="note" style="margin-bottom:10px">{E(META["basis"])} '
            f'{E(META["ratio_rule"])}</div><div class="ccard"><div class="defs">{defs}</div></div>')
    ba = META["basis_alternatives"]
    dq = META["data_quality"]
    g = {r["WK"]: r for r in M["genz_weekly"]}
    tabby = next(r for r in M["inventory_position"] if r["STYLE_GROUP"] == "Tabby")
    plain = [
        ("D3 · Like-for-like days", f"TY's last week has only {E(META['partial_week_days'])}, so LY is cut to the same days. Comparing all rows would show "
                                    f"{pct(ba['naive_all_rows_sales_yoy_pct'], True)} instead of {pct(ba['like_for_like_sales_yoy_pct'], True)}."),
        ("D5 · CUST_ID is not a key", f"{num(c['cust_ids_total'])} IDs on {num(c['lines_total'])} lines; repeats look like random collisions, so customers are counted per period and never linked."),
        ("D8 · Retention is a proxy", "Returning = Retained or Reactivated status from the brand's full history; Insider attach of new customers is the leading indicator. No cohort repeat rate."),
        ("D9 · Weeks of supply", "End-of-week stock ÷ average weekly units over the trailing (up to) four full weeks. Snapshots are never summed across weeks."),
        ("D10 · Trailing windows", "L1W = the selected week; L4W = it and the three before (truncated before W26); PTD = W23 through the selected week."),
    ]
    surprises = [
        ("F2 · The headline depends on the days", f"Naive all-rows YoY is {pct(ba['naive_all_rows_sales_yoy_pct'], True)}; like-for-like is {pct(ba['like_for_like_sales_yoy_pct'], True)}; full weeks only {pct(ba['full_weeks_only_sales_yoy_pct'], True)}."),
        ("F5 · Gen Z is accelerating", f"Gen Z share of new customers: {pct(g[23]['genz_share_of_new_TY'], dp=0)} in W23 → {pct(g[29]['genz_share_of_new_TY'], dp=0)} in W29 → {pct(g[30]['genz_share_of_new_TY'], dp=0)} in W30 (partial)."),
        ("F12 · Replenishment stopped following demand", f"Tabby receipts covered {tabby['receipts_to_sales_TY']:.2f} of units sold over W24–W29 vs {tabby['receipts_to_sales_LY']:.2f} LY."),
        ("F13 · A snapshot from the future", f"TY sales stop on {E(date_words(dq['ty_last_sale_date']))}, yet a TY W30 end-of-week stock snapshot exists for every family."),
        ("F14 · No cohorts possible", f"Every transaction is one line ({dq['lines_per_txn']:.2f} lines per transaction) and repeat CUST_IDs ({dq['cust_id_repeat_surplus_observed']}) "
                                      f"match random collisions (≈{dq['cust_id_repeat_surplus_expected_random']:.1f} expected)."),
    ]
    st.html('<div class="secnum">04</div><div class="h2">Decisions, in plain words</div><div class="plain">'
            + "".join(f'<div class="box"><b>{E(t)}</b><p>{d}</p></div>' for t, d in plain) + "</div>")
    st.html('<div class="secnum">05</div><div class="h2">What surprised me</div><div class="plain">'
            + "".join(f'<div class="box"><b>{E(t)}</b><p>{d}</p></div>' for t, d in surprises) + "</div>")
    gen = ", ".join(f"{k}: {v}" for k, v in bs["generated_by_counts"].items())
    st.html(f'<div class="note" style="margin-top:22px">Writers used for the texts on screen: {E(gen)}. Scripts: {E(" · ".join(bs["scripts"]))}.</div>')


# =====================================================================================================
# ROUTER + floating Ask pill + URL sync
# =====================================================================================================
{"briefing": page_briefing, "explore": page_explore, "ask": page_ask, "build": page_build}[ss.page]()
if ss.page != "ask":
    st.button(f"●  Ask   {n_crit}" if n_crit else "●  Ask", key="fab", on_click=go_page, args=("ask",))
want = {"page": ss.page, "wk": str(ss.wk), "win": ss.win, "ly": "1" if ss.ly else "0", "theme": ss.theme, "tab": ss.tab}
if INJECT:
    want["inject_error"] = "1"
if {k: st.query_params.get(k) for k in want} != want:
    st.query_params.from_dict(want)
