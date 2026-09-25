"""Figures 7-2 to 7-5 and the numbers of Chapter 7.

  Figure 7-2  a rough Mo surface against a graded one with the same average
              profile, and the smooth surface (engine)
  Figure 7-3  Co/C with a CoC interlayer on one interface or the other (engine)
  Figure 7-4  the measured Co/C multilayer CoC4 fitted without and with a carbon
              contamination layer (fitting-procedure data deposit, CC BY 4.0,
              jobs/figure-data/fig7-CoC4-*, read in place)
  Figure 7-5  the Chapter 3 demo's drifting stack against a uniform one (engine)

The deposit files are in θ and hold the measured curve already multiplied by
the fit's scale. They are plotted against 2θ, the program's axis.

Run:  python scripts/figures/fig_7_figures.py   (after ch7_engine_data.py)
Out:  public/figures/fig-7-2-rough-graded.svg, fig-7-3-interlayer.svg,
      fig-7-4-contamination.svg, fig-7-5-drift.svg
"""
import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import local_paths

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "figures-src" / "ch7"
OUT = ROOT / "public" / "figures"
DEPOSIT = local_paths.deposit("jobs")
FIG7 = DEPOSIT / "figure-data"
STUDY = DEPOSIT / "seed-and-surface-study"
LAMBDA = 1.5406

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


def save(fig, name, title, source):
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / name, format="svg", metadata={
        "Title": title, "Description": f"{source} Script: scripts/figures/fig_7_figures.py"})
    print(f"wrote {OUT / name}")


def curve(case):
    d = np.loadtxt(SRC / f"curve-{case}.dat", skiprows=1)
    return d[:, 0], d[:, 1]


def log_axes(ax):
    ax.set_yscale("log")
    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)


ENGINE = "Reflectivity calculated by the X-Ray Calc 3.9.4.1250 engine (figures-src/ch7/)."


# ── Figure 7-2: rough against graded ────────────────────────────────────────
def fig_7_2():
    t, rs = curve("Mo-smooth")
    _, rr = curve("Mo-rough")
    _, rg = curve("Mo-graded")
    fig = plt.figure(figsize=(136 / 25.4, 3.2))
    ax = fig.add_subplot(111)
    log_axes(ax)
    ax.plot(2 * t, rs, color=MUTED, lw=1.4, label="smooth, σ = 0")
    ax.plot(2 * t, rg, color=ORANGE, lw=2.6, label="graded transition, σ = 0")
    ax.plot(2 * t, rr, color=ACCENT, lw=0.9, ls=(0, (4, 2)), label="rough, σ = 5 Å")
    ax.set_xlim(0, 6)
    ax.set_ylim(1e-7, 2)
    ax.set_xlabel("2θ (°)")
    ax.set_ylabel("Reflectivity R")
    ax.legend(loc="upper right", frameon=False)
    fig.subplots_adjust(left=0.11, right=0.97, top=0.97, bottom=0.14)
    save(fig, "fig-7-2-rough-graded.svg", "Figure 7-2: roughness and a graded transition", ENGINE)
    print("\nFigure 7-2, bare Mo:")
    for th in (0.3, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0):
        i = np.argmin(abs(t - th))
        q = 4 * math.pi * math.sin(math.radians(th)) / LAMBDA
        print(f"  θ = {th}: rough/smooth {rr[i] / rs[i]:.3f}, graded/smooth {rg[i] / rs[i]:.3f}, "
              f"rough/graded {rr[i] / rg[i]:.3f}, exp(−q²σ²) {math.exp(-(q * 5) ** 2):.3f}")
    s = t >= 0.45
    dev = np.abs(rr[s] / rg[s] - 1)
    print(f"  from θ = 0.45° to 3°: rough and graded differ by at most {dev.max() * 100:.1f} %")


# ── Figure 7-3: the side of an interlayer ───────────────────────────────────
def orders(case, d=50.0, dbar=1.3e-5, n=5):
    t, r = curve(case)
    out = []
    for m in range(1, n + 1):
        tp = math.degrees(math.asin(math.sqrt((m * LAMBDA / (2 * d)) ** 2 + 2 * dbar)))
        w = (t > tp - 0.15) & (t < tp + 0.15)
        i = np.argmax(r[w])
        out.append((2 * t[w][i], r[w][i]))
    return out


def fig_7_3():
    fig = plt.figure(figsize=(136 / 25.4, 3.4))
    ax = fig.add_subplot(111)
    log_axes(ax)
    t, r = curve("CoC-none")
    ax.plot(2 * t, r, color=MUTED, lw=1.4, label="no interlayer")
    t, r = curve("CoC-upper")
    ax.plot(2 * t, r, color=ACCENT, lw=0.8, label="interlayer under C (C grown on Co)")
    t, r = curve("CoC-lower")
    ax.plot(2 * t, r, color=ORANGE, lw=0.8, ls=(0, (3, 1.5)), label="interlayer under Co (Co grown on C)")
    ax.set_xlim(0, 9)
    ax.set_ylim(1e-9, 5)
    ax.set_xlabel("2θ (°)")
    ax.set_ylabel("Reflectivity R")
    ax.legend(loc="upper right", frameon=False, fontsize=8)
    fig.subplots_adjust(left=0.11, right=0.97, top=0.97, bottom=0.13)
    save(fig, "fig-7-3-interlayer.svg", "Figure 7-3: an interlayer on one side or the other", ENGINE)
    print("\nFigure 7-3, order heights:")
    base = orders("CoC-none")
    up = orders("CoC-upper")
    lo = orders("CoC-lower")
    for m in range(5):
        print(f"  m={m + 1}: none {base[m][1]:.3g}, upper {up[m][1]:.3g}, lower {lo[m][1]:.3g}, "
              f"lower/upper {lo[m][1] / up[m][1]:.2f}, upper/none {up[m][1] / base[m][1]:.2f}")
    t, ru = curve("CoC-upper")
    _, rl = curve("CoC-lower")
    s = t > 0.4
    d = np.abs(np.log10(ru[s] / rl[s]))
    print(f"  upper against lower, θ > 0.4°: median |log10 ratio| {np.median(d):.3f} "
          f"(factor {10 ** np.median(d):.2f})")


# ── Figure 7-4: the contamination layer on CoC4 ─────────────────────────────
def deposit(kind, name):
    d = np.loadtxt(FIG7 / f"fig7-CoC4-{kind}" / f"{name}.dat", skiprows=1)
    return d[:, 0], d[:, 1]


def fig_7_4():
    tm, im = deposit("surface", "measured")
    tn, rn = deposit("no-surface", "calc")
    ts, rsu = deposit("surface", "calc")
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(136 / 25.4, 3.3), gridspec_kw={"width_ratios": [1.25, 1]})
    for ax, lo, hi in [(a1, 0.4, 11.2), (a2, 3.5, 4.8)]:
        log_axes(ax)
        s = (2 * tm >= lo) & (2 * tm <= hi)
        ax.plot(2 * tm[s], im[s], color=MUTED, lw=1.8, label="measured × scale")
        ax.plot(2 * tn[s], rn[s], color=ORANGE, lw=0.9, label="fit without the layer")
        ax.plot(2 * ts[s], rsu[s], color=ACCENT, lw=0.9, label="fit with the layer")
        ax.set_xlim(lo, hi)
        ax.set_xlabel("2θ (°)")
    a1.set_ylabel("Reflectivity R")
    a1.axvspan(3.5, 4.8, color=MUTED, alpha=0.18, lw=0)
    a2.set_ylim(1e-6, 3e-4)
    a1.legend(loc="upper right", frameon=False, fontsize=8)
    fig.subplots_adjust(left=0.11, right=0.98, top=0.97, bottom=0.15, wspace=0.28)
    save(fig, "fig-7-4-contamination.svg", "Figure 7-4: a contamination layer on a measured curve",
         "Measured CoC4 and two fits, fitting-procedure data deposit (CC BY 4.0), jobs/figure-data/fig7-CoC4-*.")
    print("\nFigure 7-4, CoC4:")
    for kind, job in [("no-layer", "fit-20260919-061017-879e"), ("with-layer", "fit-20260919-061017-4587")]:
        rep = json.loads((STUDY / f"CoC4-{kind}-start-agent-sigma" / job / "report.json").read_text(encoding="utf-8"))
        band = rep["bands"][2]
        print(f"  {kind}: χ² {rep['chi2']}, band θ {band['theta_deg']}: mean log10 residual {band['mean']:+.3f}")


# ── Figure 7-5: drift ───────────────────────────────────────────────────────
def demo_orders(case, n=5):
    t, r = curve(case)
    out = []
    for m in range(1, n + 1):
        tp = math.degrees(math.asin(math.sqrt((m * LAMBDA / (2 * 42.30)) ** 2 + 2 * 1.55e-5)))
        w = (t > tp - 0.2) & (t < tp + 0.2)
        tt, rr = t[w], r[w]
        i = np.argmax(rr)
        above = tt[rr >= rr[i] / 2]
        out.append((2 * tt[i], rr[i], 2 * (above.max() - above.min())))
    return out


def fig_7_5():
    fig = plt.figure(figsize=(136 / 25.4, 3.3))
    ax = fig.add_subplot(111)
    log_axes(ax)
    t, r = curve("uniform")
    ax.plot(2 * t, r, color=MUTED, lw=1.4, label="uniform, D = 42.30 Å")
    t, r = curve("drift")
    ax.plot(2 * t, r, color=ACCENT, lw=0.8, label="drifting, D = 40.00–43.60 Å")
    ax.set_xlim(0, 11.5)
    ax.set_ylim(1e-9, 5)
    ax.set_xlabel("2θ (°)")
    ax.set_ylabel("Reflectivity R")
    ax.legend(loc="upper right", frameon=False)
    fig.subplots_adjust(left=0.11, right=0.97, top=0.97, bottom=0.14)
    save(fig, "fig-7-5-drift.svg", "Figure 7-5: a stack that drifts", ENGINE)
    print("\nFigure 7-5, orders (2θ, R, full width at half maximum in 2θ):")
    u = demo_orders("uniform")
    g = demo_orders("drift")
    for m in range(5):
        print(f"  m={m + 1}: uniform {u[m][0]:.3f}° {u[m][1]:.3g} w {u[m][2]:.3f}; "
              f"drift {g[m][0]:.3f}° {g[m][1]:.3g} w {g[m][2]:.3f}; height ratio {g[m][1] / u[m][1]:.2f}")


def main():
    setup()
    fig_7_2()
    fig_7_3()
    fig_7_4()
    fig_7_5()


if __name__ == "__main__":
    main()
