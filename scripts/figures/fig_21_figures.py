"""Figures 21-1 to 21-3 of Chapter 21.

  Figure 21-1  C1 (single carbon film) at the critical edge: the measured curve
               and the one-layer fits made with the range from θ_max (the edge
               included) and from θ = 0.3° (the single-film start), best runs;
               the start of each range marked
  Figure 21-2  the Co film P2-08: the measured curve and the three models (Co;
               Co + contamination layer; Co + CoO + contamination layer), best
               runs, each pair shifted down by two decades so they don't overlap
  Figure 21-3  the Co film P2-08: log10(calculated / measured) against 2θ for the
               three models, best runs, as a moving average over 61 points
               (0.18° in 2θ), so that the level of each stretch shows

The measured curve is drawn at the anchored scale and each model divided by its
solved scale ratio, as the chart of the program draws them.

Run:  python scripts/figures/fig_21_figures.py   (after ch21_engine_data.py)
Out:  public/figures/fig-21-1-c1-edge.svg, fig-21-2-co-curve.svg, fig-21-3-co-residual.svg
"""
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ch21_engine_data import curve  # noqa: E402
from fig_18_figures import ACCENT, GREEN, MUTED, ORANGE, STROKE, clean, setup  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
S21 = ROOT / "figures-src" / "ch21"
OUT = ROOT / "public" / "figures"


def load(p):
    return json.loads(p.read_text(encoding="utf-8"))


def measured(name, c):
    """The measured curve at the anchored scale, as the chart draws it."""
    m = np.array(curve(name))
    return m[:, 0], m[:, 1] * c["scale"]


def model(c):
    """The model divided by its solved scale ratio, as the chart draws it."""
    a = np.array(c["calc"])
    return a[:, 0], a[:, 1] / c["scale_ratio"]


def figure_1():
    cv = load(S21 / "curves.json")
    fits = load(S21 / "fits.json")
    fig, ax = plt.subplots(figsize=(5.35, 3.1))
    t, r = measured("c1", cv["c1-film"])
    sel = t < 0.45
    ax.plot(2 * t[sel], r[sel], ".", ms=2.5, color=MUTED, label="measured C1")
    for key, col, lab in (("c1-edge", ORANGE, "one layer, range from θ_max"),
                          ("c1-film", ACCENT, "one layer, range from θ = 0.3°")):
        mt, mr = model(cv[key])
        s = mt < 0.45
        ax.plot(2 * mt[s], mr[s], "-", lw=1.2, color=col, label=f"{lab} (χ² {cv[key]['chi2']:.3f})")
        start = fits[key]["request"]["theta_range"]["min"]
        ax.axvline(2 * start, color=col, lw=0.8, ls=":")
    ax.set_yscale("log")
    ax.set_xlim(0.25, 0.9)
    ax.set_ylim(1e-2, 1.3)
    ax.set_xlabel("2θ (°)")
    ax.set_ylabel("reflectivity")
    ax.legend(frameon=False, fontsize=8, loc="upper right")
    clean(ax)
    fig.tight_layout()
    fig.savefig(OUT / "fig-21-1-c1-edge.svg", format="svg", metadata={
        "Title": "Figure 21-1: the critical edge of a single carbon film",
        "Description": "Fits by the X-Ray Calc 3.9.4.1270 engine; measured C1 from the fitting procedure's "
                       "deposit (CC BY 4.0). Script: scripts/figures/fig_21_figures.py"})


CO_MODELS = (("co-bare", ORANGE, "Co"), ("co-c", ACCENT, "Co + contamination layer"),
             ("co-coo", GREEN, "Co + CoO + contamination layer"))


def figure_2():
    cv = load(S21 / "curves.json")
    fits = load(S21 / "fits.json")
    fig, ax = plt.subplots(figsize=(5.35, 3.6))
    for i, (key, col, lab) in enumerate(CO_MODELS):
        shift = 10.0 ** (-2 * i)
        c = cv[key]
        t, r = measured("co", c)
        ax.plot(2 * t, r * shift, ".", ms=1.2, color=MUTED,
                label="measured P2-08" if i == 0 else None)
        mt, mr = model(c)
        rng = fits[key]["request"]["theta_range"]
        s = (mt >= rng["min"]) & (mt <= rng["max"])
        tag = "" if i == 0 else f", ×10⁻{2 * i}".replace("10⁻2", "10⁻²").replace("10⁻4", "10⁻⁴")
        ax.plot(2 * mt[s], mr[s] * shift, "-", lw=0.9, color=col,
                label=f"{lab} (χ² {c['chi2']:.3f}){tag}")
    rng = fits["co-coo"]["request"]["theta_range"]
    for lim in (rng["min"], rng["max"]):
        ax.axvline(2 * lim, color=MUTED, lw=0.6, ls=":")
    ax.set_yscale("log")
    ax.set_xlim(0, 5.6)
    ax.set_ylim(1e-11, 3)
    ax.set_xlabel("2θ (°)")
    ax.set_ylabel("reflectivity (shifted)")
    ax.legend(frameon=False, fontsize=8, loc="upper right", markerscale=4)
    clean(ax)
    fig.tight_layout()
    fig.savefig(OUT / "fig-21-2-co-curve.svg", format="svg", metadata={
        "Title": "Figure 21-2: the measured curve of a cobalt film and three models",
        "Description": "Fits by the X-Ray Calc 3.9.4.1270 engine; measured Co film P2-08 (the author's "
                       "measurement). Script: scripts/figures/fig_21_figures.py"})


def moving(y, n=61):
    k = np.ones(n) / n
    return np.convolve(y, k, mode="same")


def figure_3():
    cv = load(S21 / "curves.json")
    fits = load(S21 / "fits.json")
    fig, ax = plt.subplots(figsize=(5.35, 2.9))
    ax.axhline(0, color=MUTED, lw=0.6)
    for lim in (0.1, -0.1):
        ax.axhline(lim, color=MUTED, lw=0.5, ls=":")
    for key, col, lab in CO_MODELS:
        c = cv[key]
        t, r = measured("co", c)
        rng = fits[key]["request"]["theta_range"]
        sel = (t >= rng["min"]) & (t <= rng["max"])
        mt, mr = model(c)
        rc = np.interp(t[sel], mt, mr)
        res = np.log10(rc / r[sel])
        ax.plot(2 * t[sel], moving(res), "-", lw=1.1, color=col, label=f"{lab} (χ² {c['chi2']:.3f})")
    ax.set_xlabel("2θ (°)")
    ax.set_ylabel("log₁₀(calculated / measured)")
    ax.set_ylim(-0.6, 0.6)
    ax.legend(frameon=False, fontsize=8, loc="lower left")
    clean(ax)
    fig.tight_layout()
    fig.savefig(OUT / "fig-21-3-co-residual.svg", format="svg", metadata={
        "Title": "Figure 21-3: the residual of three models of a cobalt film",
        "Description": "Fits by the X-Ray Calc 3.9.4.1270 engine; measured Co film P2-08 (the author's "
                       "measurement). Script: scripts/figures/fig_21_figures.py"})


if __name__ == "__main__":
    setup()
    figure_1()
    figure_2()
    figure_3()
