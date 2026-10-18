"""Shared helpers: data loading, KPI rollups, simple stats, chart style.
All analysis scripts import from here so metric definitions live in ONE place (DECISIONS.md D4).
"""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data/processed"
TAB = ROOT / "outputs/tables"
FIG = ROOT / "outputs/figures"
TAB.mkdir(parents=True, exist_ok=True)
FIG.mkdir(parents=True, exist_ok=True)

GENS = ["Gen Z", "Millennial", "Gen X", "Boomer"]
LAST_FULL_WK = 29     # D10
L4W = [26, 27, 28, 29]  # D10
WTD_WK = 30


def load_lines():
    d = pd.read_csv(PROC / "lines.csv", parse_dates=["TXN_DT", "WK_START"])
    return d


def load_inventory():
    return pd.read_csv(PROC / "inventory.csv")


def ptd(d):
    """Period-to-date like-for-like basis (D3 option c): drop LY lines outside TY window."""
    return d[d.IN_TY_WINDOW]


def kpis(df):
    """Core KPI rollup (D4). line = transaction; customers = distinct CUST_ID."""
    sales = df.DEMAND_AMT.sum()
    units = df.UNIT_QTY.sum()
    txns = df.TXN_ID.nunique()
    cust = df.CUST_ID.nunique()
    return pd.Series({
        "sales": sales, "units": units, "txns": txns, "customers": cust,
        "aov": sales / txns if txns else np.nan,
        "upt": units / txns if txns else np.nan,
        "aur": sales / units if units else np.nan,
        "freq": txns / cust if cust else np.nan,
    })


def yoy_table(df, label=None):
    ty, ly = kpis(df[df.YEAR == "TY"]), kpis(df[df.YEAR == "LY"])
    t = pd.DataFrame({"TY": ty, "LY": ly})
    t["chg"] = t.TY - t.LY
    t["yoy_pct"] = t.TY / t.LY - 1
    if label:
        t.insert(0, "window", label)
    return t


def bootstrap_diff_mean(a, b, n=4000, seed=7):
    """95% CI for mean(a)-mean(b) and two-sided p (share of bootstrap diffs crossing 0)."""
    rng = np.random.default_rng(seed)
    a, b = np.asarray(a), np.asarray(b)
    diffs = rng.choice(a, (n, len(a))).mean(1) - rng.choice(b, (n, len(b))).mean(1)
    p = 2 * min((diffs <= 0).mean(), (diffs >= 0).mean())
    return a.mean() - b.mean(), np.percentile(diffs, 2.5), np.percentile(diffs, 97.5), min(p, 1.0)


def two_prop_z(x1, n1, x2, n2):
    """Two-proportion z-test; returns (p1, p2, diff, z, p_two_sided)."""
    from math import erf, sqrt
    p1, p2 = x1 / n1, x2 / n2
    p = (x1 + x2) / (n1 + n2)
    se = sqrt(p * (1 - p) * (1 / n1 + 1 / n2))
    z = (p1 - p2) / se if se else 0.0
    pval = 2 * (1 - 0.5 * (1 + erf(abs(z) / sqrt(2))))
    return p1, p2, p1 - p2, z, pval


def poisson_count_test(c_ty, c_ly):
    """Approximate test that two counts (equal exposure) differ: z = (a-b)/sqrt(a+b)."""
    from math import erf, sqrt
    z = (c_ty - c_ly) / sqrt(c_ty + c_ly) if (c_ty + c_ly) else 0.0
    return z, 2 * (1 - 0.5 * (1 + erf(abs(z) / sqrt(2))))


# ---------- chart style (dataviz skill reference palette, light mode) ----------
C = {
    "surface": "#fcfcfb", "ink": "#0b0b0b", "ink2": "#52514e", "muted": "#8a8984", "grid": "#e6e5e0",
    "ty": "#2a78d6",      # series slot 1 blue = This Year
    "ly": "#a9a8a2",      # neutral gray = Last Year (comparison, recessive)
    "genz": "#eb6834",    # slot 2 orange = Gen Z highlight
    "other": "#c9c8c2",
    "pos": "#2a78d6", "neg": "#e34948",  # diverging poles blue/red
    "good": "#0ca30c", "warning": "#fab219", "serious": "#ec835a", "critical": "#d03b3b",
}


def style():
    plt.rcParams.update({
        "figure.facecolor": C["surface"], "axes.facecolor": C["surface"], "savefig.facecolor": C["surface"],
        "axes.edgecolor": C["grid"], "axes.labelcolor": C["ink2"], "text.color": C["ink"],
        "xtick.color": C["ink2"], "ytick.color": C["ink2"], "axes.grid": True, "grid.color": C["grid"],
        "grid.linewidth": 0.8, "axes.spines.top": False, "axes.spines.right": False,
        "axes.spines.left": False, "font.size": 10, "axes.titlesize": 12, "axes.titleweight": "bold",
        "axes.titlelocation": "left", "legend.frameon": False, "lines.linewidth": 2,
        "figure.dpi": 110, "axes.axisbelow": True, "savefig.dpi": 160, "savefig.bbox": "tight",
    })


def save(fig, name):
    path = FIG / name
    fig.savefig(path)
    plt.close(fig)
    return path.relative_to(ROOT)


def fmt_pct(x, d=1):
    return f"{x*100:+.{d}f}%" if pd.notna(x) else "n/a"


def fixed(x, d=1):
    """Format like the dashboard's JavaScript Number.toFixed: on the exact binary value, ties away from zero.
    Python's own format() rounds exact ties to even (21.25 → "21.2"), which would disagree with the charts ("21.3")."""
    from decimal import ROUND_HALF_UP, Decimal
    return f"{Decimal(x).quantize(Decimal(1).scaleb(-d), rounding=ROUND_HALF_UP):.{d}f}"
