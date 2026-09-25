"""Figures 8-2 and 8-3, Table 8-1 and the numbers of Chapter 8.

  Figure 8-2  the CoC5 model at Δθ = 0, 0.01° and 0.03° (engine)
  Figure 8-3  the CoC5 model calculated at 150 points against 9000 (engine)
  Table 8-1   s against sp for the CoC5 model, with (1 − cos²2θ)/2 (engine)

An order is the largest R within ±0.15° (θ) of the Bragg law with refraction.
The fringe contrast is the mean of each fringe maximum over the minimum that
follows it, between 0.1° (θ) past the 1st order and 0.1° before the 2nd.

Run:  python scripts/figures/fig_8_figures.py   (after ch8_engine_data.py)
Out:  public/figures/fig-8-2-resolution.svg, fig-8-3-sampling.svg
"""
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "figures-src" / "ch8"
OUT = ROOT / "public" / "figures"
LAMBDA = 1.5406
D = 50.0318  # the CoC5 expert period, Å

STROKE = "#334155"
ACCENT = "#1a5276"
MUTED = "#94a3b8"
ORANGE = "#b9770e"
PURPLE = "#7d3c98"
ENGINE = "Reflectivity calculated by the X-Ray Calc 3.9.4.1250 engine (figures-src/ch8/)."


def setup():
    plt.rcParams.update({
        "font.family": "sans-serif",
        # Drawn at the print column's width (136 mm), printed at 1:1.
        "font.size": 9, "xtick.labelsize": 9, "ytick.labelsize": 9,
        "svg.fonttype": "none",
        "axes.edgecolor": STROKE, "axes.labelcolor": STROKE,
        "xtick.color": STROKE, "ytick.color": STROKE,
    })


def save(fig, name, title):
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / name, format="svg", metadata={
        "Title": title, "Description": f"{ENGINE} Script: scripts/figures/fig_8_figures.py"})
    print(f"wrote {OUT / name}")


def curve(case):
    d = np.loadtxt(SRC / f"curve-{case}.dat", skiprows=1)
    return d[:, 0], d[:, 1]


def log_axes(ax):
    ax.set_yscale("log")
    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)


def orders(case, n=4):
    t, r = curve(case)
    out = []
    for m in range(1, n + 1):
        tp = math.degrees(math.asin(math.sqrt((m * LAMBDA / (2 * D)) ** 2 + 2.1e-5)))
        w = (t > tp - 0.15) & (t < tp + 0.15)
        i = np.argmax(r[w])
        out.append((t[w][i], r[w][i]))
    return out


def fringe_contrast(case):
    t, r = curve(case)
    o = orders(case, 2)
    s = (t > o[0][0] + 0.1) & (t < o[1][0] - 0.1)
    rr = r[s]
    mx = [i for i in range(1, len(rr) - 1) if rr[i] > rr[i - 1] and rr[i] >= rr[i + 1]]
    mn = [i for i in range(1, len(rr) - 1) if rr[i] < rr[i - 1] and rr[i] <= rr[i + 1]]
    ratios = [rr[i] / rr[[j for j in mn if j > i][0]] for i in mx if any(j > i for j in mn)]
    return len(mx), float(np.mean(ratios))


RES = [("dt0", MUTED, 1.4, "Δθ = 0"), ("dt0.01", ACCENT, 0.8, "Δθ = 0.01°"), ("dt0.03", ORANGE, 1.0, "Δθ = 0.03°")]


def fig_8_2():
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(136 / 25.4, 3.3), gridspec_kw={"width_ratios": [1.3, 1]})
    for case, color, lw, label in RES:
        t, r = curve(case)
        for ax, lo, hi in [(a1, 0, 8), (a2, 2.1, 3.3)]:
            s = (2 * t >= lo) & (2 * t <= hi)
            ax.plot(2 * t[s], r[s], color=color, lw=lw, label=label)
    for ax, lo, hi in [(a1, 0, 8), (a2, 2.1, 3.3)]:
        log_axes(ax)
        ax.set_xlim(lo, hi)
        ax.set_xlabel("2θ (°)")
    a1.set_ylim(1e-9, 3)
    a1.set_ylabel("Reflectivity R")
    a1.axvspan(2.1, 3.3, color=MUTED, alpha=0.18, lw=0)
    a1.legend(loc="upper right", frameon=False, fontsize=8)
    fig.subplots_adjust(left=0.11, right=0.98, top=0.97, bottom=0.15, wspace=0.28)
    save(fig, "fig-8-2-resolution.svg", "Figure 8-2: the resolution blurs the calculated curve")
    print("\nFigure 8-2, orders (2θ, R, fraction of Δθ = 0) and fringe contrast between orders 1 and 2:")
    base = orders("dt0")
    for case, _, _, label in RES:
        o = orders(case)
        n, c = fringe_contrast(case)
        cells = "  ".join(f"{2 * t:.3f}° {r:.3g} ({r / b[1]:.2f})" for (t, r), b in zip(o, base))
        print(f"  {label:10s} {cells}   fringes {n}, mean max/min {c:.2f}")


def fig_8_3():
    tf, rf = curve("dt0")
    tc, rc = curve("coarse")
    fig = plt.figure(figsize=(136 / 25.4, 3.0))
    ax = fig.add_subplot(111)
    log_axes(ax)
    s = (2 * tf >= 1.5) & (2 * tf <= 4.0)
    ax.plot(2 * tf[s], rf[s], color=MUTED, lw=1.2, label="9000 points")
    s = (2 * tc >= 1.5) & (2 * tc <= 4.0)
    ax.plot(2 * tc[s], rc[s], color=ACCENT, lw=0.9, marker="o", ms=2.5, label="150 points")
    ax.set_xlim(1.5, 4.0)
    ax.set_xlabel("2θ (°)")
    ax.set_ylabel("Reflectivity R")
    ax.legend(loc="upper right", frameon=False)
    fig.subplots_adjust(left=0.11, right=0.97, top=0.97, bottom=0.16)
    save(fig, "fig-8-3-sampling.svg", "Figure 8-3: too few calculated points")
    step = 2 * (tc[1] - tc[0])
    spacing = math.degrees(LAMBDA / (20 * D))  # Δ(2θ) ≈ λ/H for the whole stack, H = N·D (Chapter 5)
    print(f"\nFigure 8-3: coarse step {step:.4f}° in 2θ; fringe spacing λ/(N·D) = {spacing:.4f}° in 2θ; "
          f"{spacing / step:.2f} points per fringe")


def table_8_1():
    t, rs = curve("pol-s")
    _, rsp = curve("pol-sp")
    print("\nTable 8-1, s against sp (CoC5 model):")
    for th in (0.5, 1, 2, 3, 4):
        i = np.argmin(abs(t - th))
        f = (1 - math.cos(math.radians(2 * th)) ** 2) / 2
        print(f"  θ = {th}° (2θ = {2 * th}°): Rs {rs[i]:.3g}, sp/s {rsp[i] / rs[i]:.4f}, "
              f"sp lower by {(1 - rsp[i] / rs[i]) * 100:.2f} %, (1 − cos²2θ)/2 = {f * 100:.2f} %")


def main():
    setup()
    fig_8_2()
    fig_8_3()
    table_8_1()


if __name__ == "__main__":
    main()
