"""Figures of Chapter 22.

  Figure 22-1  three measured curves, one above the other: a periodic Mo/Si
               mirror (sharp orders), the W/BN mirror whose period changes with
               depth (lopsided orders), and the Sb/B4C supermirror (a band)
  Figure 22-2  W/BN (N = 36): the measured curve against the best uniform fit
               and the best fit of order 2; the whole range and orders 2 and 4
  Figure 22-3  W/BN: the period against its number (1 at the surface) for the
               five order-2 runs of N = 36 and of N = 60
  Figure 22-4  Sb/B4C: the period of each of the 50 periods for the five
               Irregular runs from the stack values (Smooth off) and the author's
               fit; left in depth order, right sorted by size
  Figure 22-5  Sb/B4C: the measured curve against the best run with Smooth off
               and the best with Smooth on

The curves are the ones stored in the X-Ray Calc 3 paper's project files
(figures-src/ch22/*.xrcx), drawn as stored.

Run:  python scripts/figures/fig_22_figures.py
Out:  public/figures/fig-22-1-three-curves.svg, fig-22-2-wbn-fit.svg, fig-22-3-wbn-period.svg,
      fig-22-4-sb-periods.svg, fig-22-5-sb-fit.svg
"""
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import json

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ch22_engine_data import curve  # noqa: E402
from fig_18_figures import ACCENT, GREEN, ORANGE, clean, setup  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "public" / "figures"
S22 = ROOT / "figures-src" / "ch22"
MUTED = "#94a3b8"


def load(name):
    return json.loads((S22 / name).read_text(encoding="utf-8"))


def figure_1():
    fig, axs = plt.subplots(3, 1, figsize=(5.35, 5.6), sharex=True)
    for ax, (project, col, lab) in zip(axs, (
            ("Mo-Si_240204E_Fitted_best.xrcx", ACCENT, "Mo/Si, 12 periods: sharp orders"),
            ("W-BN(221101A)_BF.xrcx", ORANGE, "W/BN: the period changes with depth"),
            ("Sb-B4C_120925_Fitted_Best.xrcx", GREEN, "Sb/B4C supermirror: a band"))):
        a = np.array(curve(project))
        ax.semilogy(2 * a[:, 0], a[:, 1], "-", lw=0.8, color=col)
        ax.set_ylim(3e-7, 3)
        ax.set_ylabel("reflectivity")
        ax.text(0.98, 0.9, lab, transform=ax.transAxes, ha="right", va="top", fontsize=8, color=col)
        clean(ax)
    axs[-1].set_xlabel("2θ (°)")
    axs[-1].set_xlim(0, 12)
    fig.tight_layout()
    fig.savefig(OUT / "fig-22-1-three-curves.svg", format="svg", metadata={
        "Title": "Figure 22-1: sharp orders, lopsided orders and a band",
        "Description": "Measured curves from the X-Ray Calc 3 paper's project files. "
                       "Script: scripts/figures/fig_22_figures.py"})


def figure_2():
    cv = load("wbn-curves.json")
    m = np.array(curve("W-BN(221101A)_BF.xrcx"))
    fig = plt.figure(figsize=(5.35, 4.6))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.3, 1])
    axes = [fig.add_subplot(gs[0, :]), fig.add_subplot(gs[1, 0]), fig.add_subplot(gs[1, 1])]
    cases = (("36-uniform", ORANGE, "one period"), ("36-poly2", ACCENT, "order 2"))
    for ax, (lo, hi) in zip(axes, ((0, 12), (3.9, 4.8), (8.2, 9.3))):
        sel = (2 * m[:, 0] >= lo) & (2 * m[:, 0] <= hi)
        k = cv["36-poly2"]["scale"]
        ax.semilogy(2 * m[sel, 0], m[sel, 1] * k, ".", ms=1.6, color=MUTED, label="measured")
        for key, col, lab in cases:
            a = np.array(cv[key]["calc"])
            s_ = (2 * a[:, 0] >= lo) & (2 * a[:, 0] <= hi)
            ax.semilogy(2 * a[s_, 0], a[s_, 1] / cv[key]["scale_ratio"], "-", lw=0.9, color=col,
                        label=f"{lab} (χ² {cv[key]['chi2']:.2f})")
        ax.set_xlim(lo, hi)
        clean(ax)
    axes[0].set_ylim(3e-7, 3)
    axes[0].legend(frameon=False, fontsize=8, loc="upper right", markerscale=4)
    axes[0].set_ylabel("reflectivity")
    axes[1].set_ylabel("reflectivity")
    for ax in axes[1:]:
        ax.set_xlabel("2θ (°)")
    axes[1].set_title("order 2", fontsize=8)
    axes[2].set_title("order 4", fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT / "fig-22-2-wbn-fit.svg", format="svg", metadata={
        "Title": "Figure 22-2: W/BN, one period against a period that changes with depth",
        "Description": "Fits by the X-Ray Calc 3.9.4.1110 engine; measured W/BN(221101A) from the X-Ray Calc 3 "
                       "paper's project. Script: scripts/figures/fig_22_figures.py"})


def figure_3():
    d = load("wbn.json")
    fig, ax = plt.subplots(figsize=(5.35, 2.9))
    for n, col in (("60", ORANGE), ("36", ACCENT)):
        runs = [r for r in d[n]["runs"] if r["mode"] == "poly2"]
        best = min(r["chi2"] for r in runs)
        for i, r in enumerate(x for x in runs if x["chi2"] < 2 * best):
            dd = np.array(r["W"]["thickness_profile"]) + np.array(r["BN"]["thickness_profile"])
            ax.plot(np.arange(1, len(dd) + 1), dd, "-", lw=0.9, color=col, alpha=0.8,
                    label=f"N = {n} (five runs, χ² {best:.2f} best)" if i == 0 else None)
    ax.set_xlabel("period (1 at the surface)")
    ax.set_ylabel("period D (Å)")
    ax.set_xlim(0, 61)
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    clean(ax)
    fig.tight_layout()
    fig.savefig(OUT / "fig-22-3-wbn-period.svg", format="svg", metadata={
        "Title": "Figure 22-3: W/BN, the period through the stack",
        "Description": "Fits by the X-Ray Calc 3.9.4.1110 engine. Script: scripts/figures/fig_22_figures.py"})


def periods(r):
    t = r["thickness"]
    return np.array(t["Sb2B4C"]) + np.array(t["Sb"]) + np.array(t["B4C"])


def figure_4():
    d = load("sb.json")
    runs = load("sb-engine.json")["off"]["runs"]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(5.35, 2.9), sharey=True, gridspec_kw={"width_ratios": [1.6, 1]})
    k = np.arange(1, 51)
    for i, r in enumerate(runs):
        a1.plot(k, periods(r), "-", lw=0.7, color=ACCENT, alpha=0.55, label="five runs" if i == 0 else None)
        a2.plot(k, np.sort(periods(r)), "-", lw=0.8, color=ACCENT, alpha=0.7)
    a = periods(d["author"])
    a1.plot(k, a, "--", lw=0.9, color=ORANGE, label="the author's fit")
    a2.plot(k, np.sort(a), "--", lw=0.9, color=ORANGE)
    a1.set_xlabel("period (1 at the surface)")
    a2.set_xlabel("periods sorted by size")
    a1.set_ylabel("period D (Å)")
    a1.legend(frameon=False, fontsize=8, loc="upper right", ncol=2)
    for ax in (a1, a2):
        ax.set_xlim(0, 51)
        clean(ax)
    a1.set_ylim(28, 82)
    fig.tight_layout()
    fig.savefig(OUT / "fig-22-4-sb-periods.svg", format="svg", metadata={
        "Title": "Figure 22-4: Sb/B4C, the periods found by five Irregular fits",
        "Description": "Irregular fits by the X-Ray Calc engine (a build after 3.9.4.1130); the author's fit from "
                       "the X-Ray Calc 3 paper's project. "
                       "Script: scripts/figures/fig_22_figures.py"})


def figure_5():
    cv = load("sb-engine-curves.json")
    m = np.array(curve("Sb-B4C_120925_Fitted_Best.xrcx"))
    fig, ax = plt.subplots(figsize=(5.35, 3.1))
    k = cv["smooth-off"]["scale"]
    ax.semilogy(2 * m[:, 0], m[:, 1] * k, ".", ms=1.4, color=MUTED, label="measured")
    for key, col, lab, shift in (("smooth-off", ACCENT, "Smooth off", 1.0), ("smooth-on", ORANGE, "Smooth on", 1e-2)):
        a = np.array(cv[key]["calc"])
        s_ = (2 * a[:, 0] >= 0.3) & (2 * a[:, 0] <= 7.5)
        if shift != 1.0:
            ax.semilogy(2 * m[:, 0], m[:, 1] * k * shift, ".", ms=1.4, color=MUTED)
        ax.semilogy(2 * a[s_, 0], a[s_, 1] / cv[key]["scale_ratio"] * shift, "-", lw=0.8, color=col,
                    label=f"{lab} (χ² {cv[key]['chi2']:.1f})" + (", ×10⁻²" if shift != 1.0 else ""))
    ax.set_xlim(0, 7.6)
    ax.set_ylim(3e-9, 3)
    ax.set_xlabel("2θ (°)")
    ax.set_ylabel("reflectivity")
    ax.legend(frameon=False, fontsize=8, loc="upper right", markerscale=4)
    clean(ax)
    fig.tight_layout()
    fig.savefig(OUT / "fig-22-5-sb-fit.svg", format="svg", metadata={
        "Title": "Figure 22-5: Sb/B4C, Irregular fits with Smooth off and on",
        "Description": "Irregular fits by the X-Ray Calc engine (a build after 3.9.4.1130). "
                       "Script: scripts/figures/fig_22_figures.py"})


if __name__ == "__main__":
    setup()
    figure_1()
    figure_2()
    figure_3()
    figure_4()
    figure_5()
