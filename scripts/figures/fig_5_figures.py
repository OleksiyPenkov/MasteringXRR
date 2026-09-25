"""Figures 5-2 to 5-4 and the numbers of Chapter 5.

  Figure 5-2  the measured carbon film C1 (fitting-procedure data deposit,
              CC BY 4.0, read in place), with its fringe maxima numbered
  Figure 5-3  200 Å films on Si: C at 2.266 and 1.8 g/cm³, and Mo (engine)
  Figure 5-4  200 Å Mo on Si: smooth, 5 Å on top, 5 Å at the interface (engine)

The C1 maxima are found on a five-point running mean of the counts, as the
largest value within ±8 points (±0.024° in 2θ), between 2θ = 0.5° and 2.4°;
a second point less than 0.1° after a maximum (a flat, noisy top) is dropped.
Past 2.4° the fringes sink into the counting noise. Positions are read from
the raw 2θ grid (step 0.003°).

Thickness from the maxima, printed for the text:
  * from each pair of neighbors, H = λ / Δ(2θ), with Δ(2θ) in radians;
  * from all seven with refraction: θ_j² = a²(j + m₀)² + b, least squares
    over a, m₀ and b; H = λ / 2a and θc = √b.

Run:  python scripts/figures/fig_5_figures.py
Out:  public/figures/fig-5-2-c1-fringes.svg, fig-5-3-density.svg, fig-5-4-roughness.svg
"""
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import least_squares

import local_paths

ROOT = Path(__file__).resolve().parents[2]
C1 = local_paths.deposit("curves", "C1.csv")
SRC = ROOT / "figures-src" / "ch5"
OUT = ROOT / "public" / "figures"
LAMBDA_C1 = 1.540598  # Å, K-alpha1 as recorded in the C1 file (C1.meta.json)

STROKE = "#334155"
ACCENT = "#1a5276"
MUTED = "#94a3b8"
ORANGE = "#b9770e"
PURPLE = "#7d3c98"


def setup():
    plt.rcParams.update({
        "font.family": "sans-serif",
        # Drawn at the print column's width (136 mm), printed at 1:1.
        "font.size": 9, "xtick.labelsize": 9, "ytick.labelsize": 9,
        "svg.fonttype": "none",
        "axes.edgecolor": STROKE, "axes.labelcolor": STROKE,
        "xtick.color": STROKE, "ytick.color": STROKE,
    })


def log_axes(fig, ylabel, x_max, top_theta=True):
    ax = fig.add_subplot(111)
    ax.set_yscale("log")
    ax.spines["right"].set_visible(False)
    ax.set_xlim(0, x_max)
    ax.set_xlabel("2θ (°)")
    ax.set_ylabel(ylabel)
    if top_theta:
        top = ax.secondary_xaxis("top", functions=(lambda x: x / 2, lambda t: 2 * t))
        top.set_xlabel("θ (°)")
    else:
        ax.spines["top"].set_visible(False)
    return ax


def save(fig, name, title, source):
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / name, format="svg", metadata={
        "Title": title, "Description": f"{source} Script: scripts/figures/fig_5_figures.py"})
    print(f"wrote {OUT / name}")


# ── C1, the measured film ───────────────────────────────────────────────────
def c1_maxima():
    d = np.loadtxt(C1, delimiter=",", skiprows=2)
    x, y = d[:, 0], d[:, 1]
    ys = np.convolve(y, np.ones(5) / 5, mode="same")
    idx = []
    for i in range(8, len(ys) - 8):
        if ys[i] == ys[i - 8:i + 9].max() and 0.5 < x[i] < 2.4:
            if idx and x[i] - x[idx[-1]] < 0.1:  # a flat, noisy top gives two points; keep the first
                continue
            idx.append(i)
    return x, y, np.array(idx)


def fig_5_2():
    x, y, idx = c1_maxima()
    fig = plt.figure(figsize=(136 / 25.4, 3.3))
    ax = log_axes(fig, "Intensity (counts)", 3.0, top_theta=False)
    keep = (x <= 3.0) & (y > 0)
    ax.plot(x[keep], y[keep], color=ACCENT, lw=0.8)
    for k, i in enumerate(idx, start=1):
        ax.annotate(str(k), (x[i], y[i]), (x[i], y[i] * 4), ha="center", color=STROKE, fontsize=8,
                    arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.6))
    ax.set_ylim(0.5, 3e6)
    fig.subplots_adjust(left=0.11, right=0.97, top=0.95, bottom=0.14)
    save(fig, "fig-5-2-c1-fringes.svg", "Figure 5-2: the fringes of a measured carbon film",
         f"Plotted from {C1.name}, fitting-procedure data deposit, CC BY 4.0.")


def c1_report():
    x, _, idx = c1_maxima()
    tt = x[idx]
    print("\nC1 maxima (2θ, °) and pair thicknesses H = λ/Δ(2θ):")
    for k in range(len(tt)):
        line = f"  {k + 1}: 2θ = {tt[k]:.3f}"
        if k:
            d = tt[k] - tt[k - 1]
            line += f"   Δ(2θ) = {d:.3f}°   H = {LAMBDA_C1 / math.radians(d):.0f} Å"
        print(line)
    th = np.radians(tt / 2)
    j = np.arange(len(th))
    fit = least_squares(lambda p: p[0] ** 2 * (j + p[1]) ** 2 + p[2] - th ** 2, [LAMBDA_C1 / 600, 2, 1e-5])
    a, m0, b = fit.x
    print(f"  refraction fit: H = {LAMBDA_C1 / (2 * a):.1f} Å, m0 = {m0:.2f}, "
          f"θc = {math.degrees(math.sqrt(b)):.3f}° (2θc = {2 * math.degrees(math.sqrt(b)):.3f}°)")


# ── calculated films ────────────────────────────────────────────────────────
def curve(case):
    d = np.loadtxt(SRC / f"curve-{case}.dat", skiprows=1)
    return d[:, 0], d[:, 1]


def contrast_near(case, theta0):
    """Ratio of the fringe maximum nearest θ0 to the minimum that follows it."""
    t, r = curve(case)
    mx = [i for i in range(1, len(r) - 1) if r[i] > r[i - 1] and r[i] > r[i + 1] and t[i] > 0.3]
    mn = [i for i in range(1, len(r) - 1) if r[i] < r[i - 1] and r[i] < r[i + 1] and t[i] > 0.3]
    if not mx:
        return None
    i = min(mx, key=lambda k: abs(t[k] - theta0))
    after = [k for k in mn if k > i]
    return (t[i], r[i] / r[after[0]]) if after else None


def fig_5_3():
    fig = plt.figure(figsize=(136 / 25.4, 3.3))
    ax = log_axes(fig, "Reflectivity R", 4.0)
    for case, color, label in [("Mo", PURPLE, "Mo, 10.22 g/cm³"), ("C-1.8", ORANGE, "C, 1.8 g/cm³"),
                               ("C-bulk", ACCENT, "C, 2.266 g/cm³ (bulk)")]:
        t, r = curve(case)
        ax.plot(2 * t, r, color=color, lw=1.0, label=label)
    ax.set_ylim(1e-7, 2)
    ax.legend(loc="upper right", frameon=False)
    fig.subplots_adjust(left=0.11, right=0.97, top=0.84, bottom=0.14)
    save(fig, "fig-5-3-density.svg", "Figure 5-3: film density and fringe contrast",
         "Reflectivity calculated by the X-Ray Calc 3.9.4.1250 engine (figures-src/ch5/).")


def fig_5_4():
    fig = plt.figure(figsize=(136 / 25.4, 3.3))
    ax = log_axes(fig, "Reflectivity R", 6.0)
    for case, color, label, lw in [("Mo", MUTED, "smooth", 1.6), ("Mo-top5", ORANGE, "σ = 5 Å on top", 1.0),
                                   ("Mo-int5", ACCENT, "σ = 5 Å at the interface", 1.0)]:
        t, r = curve(case)
        ax.plot(2 * t, r, color=color, lw=lw, label=label)
    ax.set_ylim(1e-8, 2)
    ax.legend(loc="upper right", frameon=False)
    fig.subplots_adjust(left=0.11, right=0.97, top=0.84, bottom=0.14)
    save(fig, "fig-5-4-roughness.svg", "Figure 5-4: roughness and fringe contrast",
         "Reflectivity calculated by the X-Ray Calc 3.9.4.1250 engine (figures-src/ch5/).")


def engine_report():
    print("\nFringe contrast (max / next min) of the calculated films:")
    for case in ["C-bulk", "C-1.8", "Mo", "Mo-top5", "Mo-int5"]:
        cells = []
        for th0 in (0.5, 1.0, 2.0, 2.8):
            c = contrast_near(case, th0)
            cells.append(f"θ≈{th0}: " + ("none" if c is None else f"{c[1]:.2f} at θ = {c[0]:.3f}°"))
        print(f"  {case:8s} " + " | ".join(cells))
    for case in ["Mo", "Mo-top5", "Mo-int5"]:
        t, r = curve(case)
        print(f"  {case}: R at θ = 1° {np.interp(1.0, t, r):.3g}, at 2° {np.interp(2.0, t, r):.3g}, "
              f"at 2.8° {np.interp(2.8, t, r):.3g}")
    t, r = curve("Mo")
    print(f"  Mo: R at θ = 0.40° {np.interp(0.40, t, r):.3f}, at 0.45° {np.interp(0.45, t, r):.3f}")


def main():
    setup()
    fig_5_2()
    fig_5_3()
    fig_5_4()
    c1_report()
    engine_report()


if __name__ == "__main__":
    main()
