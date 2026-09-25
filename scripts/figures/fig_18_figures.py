"""Figures 18-2 to 18-4 of Chapter 18.

  Figure 18-2  the order ratios (calculated / measured peak, at the chart's
               scale) of the fits Chapter 17 ended with: CoC4 Polynomial
               order 1, CoC5 one period with the period free, the demo at
               order 1 and order 3; five runs each; the band 0.75-1.25 shaded
  Figure 18-3  the orders that fail, in counts: CoC4 orders 7 and 8 against
               the order-1 fit, CoC5 order 4 against the one-period fit (best
               runs), the model divided by its solved scale as the chart draws
               it, with the floor
  Figure 18-4  the residual by band of the demo, order 1 against order 3 (best
               runs), with the warning level ±0.1

ch18_engine_data.chart() puts the fit reports on the chart's scale.

Run:  python scripts/figures/fig_18_figures.py   (after ch18_engine_data.py)
Out:  public/figures/fig-18-2-order-ratios.svg, fig-18-3-weak-orders.svg,
      fig-18-4-demo-bands.svg
"""
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ch18_engine_data import chart  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
S17 = ROOT / "figures-src" / "ch17"
S18 = ROOT / "figures-src" / "ch18"
OUT = ROOT / "public" / "figures"

STROKE = "#334155"
ACCENT = "#1a5276"
MUTED = "#94a3b8"
ORANGE = "#b9770e"
GREEN = "#1e8449"
BAND = "#d5e8d4"


def setup():
    plt.rcParams.update({
        "font.family": "sans-serif", "font.size": 9, "xtick.labelsize": 9, "ytick.labelsize": 9,
        "svg.fonttype": "none", "axes.edgecolor": STROKE, "axes.labelcolor": STROKE,
        "xtick.color": STROKE, "ytick.color": STROKE,
    })


def clean(ax):
    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)


def load(p):
    return json.loads(p.read_text(encoding="utf-8"))


def runs_of(p, mode):
    rs = sorted((r for r in load(p)["runs"] if r["mode"] == mode), key=lambda r: r["chi2"])
    return [(r, chart(r)[0]) for r in rs]


def ratio_panel(ax, groups, title):
    ax.axhspan(0.75, 1.25, color=BAND, lw=0)
    ax.axhline(1.0, color=MUTED, lw=0.6)
    nmax = 1
    for (label, col, off, runs) in groups:
        for i, (r, orders) in enumerate(runs):
            vis = [o for o in orders if o["visible"]]
            n = np.array([o["n"] for o in vis]) + off
            v = [o["ratio_chart"] for o in vis]
            nmax = max(nmax, max(o["n"] for o in vis))
            ax.plot(n, v, "o", ms=4.5 if i == 0 else 3, color=col,
                    alpha=1 if i == 0 else 0.45, mec="none",
                    label=label if i == 0 else None)
    ax.set_xticks(range(1, nmax + 1))
    ax.set_xlim(0.5, nmax + 0.5)
    ax.set_ylim(0, 1.5)
    ax.set_title(title, fontsize=9, color=STROKE, loc="left")
    ax.set_xlabel("order")
    clean(ax)


def figure_18_1():
    fig, axes = plt.subplots(1, 3, figsize=(5.35, 2.7), gridspec_kw={"width_ratios": [8, 4, 5]})
    ratio_panel(axes[0], [("five runs", ACCENT, 0,
                           runs_of(S17 / "coc4-final.json", "poly1"))], "CoC4")
    ratio_panel(axes[1], [("five runs", ACCENT, 0,
                           runs_of(S18 / "coc5-free.json", "periodic_free"))], "CoC5")
    ratio_panel(axes[2], [("order 1", ACCENT, -0.15, runs_of(S17 / "demo.json", "poly1")),
                          ("order 3", ORANGE, 0.15, runs_of(S17 / "demo.json", "poly3"))],
                "the demo")
    axes[0].set_ylabel("calculated / measured")
    fig.legend(*axes[2].get_legend_handles_labels(), frameon=False, fontsize=8, loc="upper right",
               ncol=2, title="the demo:", title_fontsize=8, alignment="left")
    fig.tight_layout(rect=(0, 0, 1, 0.84))
    fig.savefig(OUT / "fig-18-2-order-ratios.svg", format="svg", metadata={
        "Title": "Figure 18-2: the order table of three fits",
        "Description": "Fits by the X-Ray Calc 3.9.4.1250 engine; measured CoC4 and CoC5 from the "
                       "fitting procedure's deposit (CC BY 4.0). Script: scripts/figures/fig_18_figures.py"})


def read_curves(p):
    head, calc, meas, cur = None, [], [], None
    for ln in p.read_text(encoding="utf-8").splitlines():
        if ln.startswith("# coc"):
            head = ln
        elif ln.startswith("# section calc"):
            cur = calc
        elif ln.startswith("# section measured"):
            cur = meas
        elif ln and not ln[0].isalpha() and not ln.startswith("#") and cur is not None:
            a, b = ln.split()[:2]
            cur.append((float(a), float(b)))
    sr = float(head.split("scale_ratio")[1].split(",")[0])
    rmin = float(head.split("r_min")[1])
    return np.array(calc), np.array(meas), sr, rmin


def high_order_panel(ax, curves, run_orders, orders, xlim, title, one_count):
    calc, meas, sr, rmin = read_curves(curves)
    m = (2 * meas[:, 0] > xlim[0]) & (2 * meas[:, 0] < xlim[1])
    c = (2 * calc[:, 0] > xlim[0]) & (2 * calc[:, 0] < xlim[1])
    ax.plot(2 * meas[m, 0], meas[m, 1] / one_count, color=MUTED, lw=0.9, label="measured")
    ax.plot(2 * calc[c, 0], calc[c, 1] / sr / one_count, color=ORANGE, lw=1.3, label="fit, best run")
    ax.axhline(rmin / sr / one_count, color=STROKE, lw=0.7, ls="--", label="the floor, R min")
    for o in run_orders:
        if o["n"] in orders:
            x = 2 * o["theta_meas_deg"]
            y = o["i_meas"] / one_count
            ax.annotate(f"order {o['n']}: {o['ratio_chart']:.2f}", (x, y), xytext=(0, 6),
                        textcoords="offset points", ha="center", fontsize=8, color=STROKE)
            print(f"{title} order {o['n']}: 2θ {x:.3f}, measured {y:.1f} counts, "
                  f"model {o['r_chart'] / one_count:.2f} counts, ratio {o['ratio_chart']:.3f}")
    ax.set_xlim(*xlim)
    ax.set_title(title, fontsize=9, color=STROKE, loc="left")
    ax.set_xlabel("2θ (°)")
    clean(ax)
    return sr, rmin


def figure_18_2():
    fig, axes = plt.subplots(1, 2, figsize=(5.35, 2.9), gridspec_kw={"width_ratios": [3, 2]})
    best4 = runs_of(S17 / "coc4-final.json", "poly1")[0][1]
    sr4, one4 = high_order_panel(axes[0], S18 / "coc4-poly1-curves.dat", best4, (7, 8), (10.9, 13.3),
                                 "CoC4, order 1: orders 7 and 8", 1.383e-06)
    best5 = runs_of(S18 / "coc5-free.json", "periodic_free")[0][1]
    sr5, one5 = high_order_panel(axes[1], S18 / "coc5-free-curves.dat", best5, (4,), (6.6, 7.5),
                                 "CoC5, one period: order 4", 8.01145e-07)
    axes[0].set_ylim(0, 8)
    axes[1].set_ylim(0, 22)
    axes[0].set_ylabel("counts")
    fig.legend(*axes[0].get_legend_handles_labels(), frameon=False, fontsize=8, loc="upper center",
               ncol=3, bbox_to_anchor=(0.5, 1.0))
    fig.tight_layout(rect=(0, 0, 1, 0.9))
    fig.savefig(OUT / "fig-18-3-weak-orders.svg", format="svg", metadata={
        "Title": "Figure 18-3: the orders that fail, in counts",
        "Description": "Measured CoC4 and CoC5 from the fitting procedure's deposit (CC BY 4.0); fits by "
                       "the X-Ray Calc 3.9.4.1250 engine. Script: scripts/figures/fig_18_figures.py"})
    print(f"Figure 18-3: CoC4 scale ratio {sr4}, floor {one4 / sr4:.4e}; CoC5 scale ratio {sr5}")


def figure_18_3():
    fig, ax = plt.subplots(figsize=(5.35, 2.5))
    k = np.arange(1, 9)
    for mode, col, off, lab in (("poly1", ACCENT, -0.18, "order 1"), ("poly3", ORANGE, 0.18, "order 3")):
        r = min((x for x in load(S17 / "demo.json")["runs"] if x["mode"] == mode), key=lambda x: x["chi2"])
        b = [x["mean_chart"] for x in chart(r)[2]]
        ax.bar(k + off, b, width=0.34, color=col, label=f"{lab}, best run (χ² = {r['chi2']:.3g})")
        print(lab, [round(x, 3) for x in b])
    for y in (0.1, -0.1):
        ax.axhline(y, color=STROKE, lw=0.7, ls="--")
    ax.axhline(0, color=MUTED, lw=0.6)
    ax.set_xticks(k)
    ax.set_xlabel("band (1 = start of the range)")
    ax.set_ylabel("mean log10(calc / meas)")
    ax.set_ylim(-0.2, 0.2)
    ax.legend(frameon=False, fontsize=8, loc="lower left", ncol=2)
    clean(ax)
    fig.tight_layout()
    fig.savefig(OUT / "fig-18-4-demo-bands.svg", format="svg", metadata={
        "Title": "Figure 18-4: the residual by band of the demo",
        "Description": "Fits of the Chapter 3 demo by the X-Ray Calc 3.9.4.1250 engine. "
                       "Script: scripts/figures/fig_18_figures.py"})


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    setup()
    OUT.mkdir(parents=True, exist_ok=True)
    figure_18_1()
    figure_18_2()
    figure_18_3()
