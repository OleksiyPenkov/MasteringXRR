"""Figure 12-2 and the numbers of Chapter 12.

  Figure 12-2  the CoC4 starting model against the measured curve: the whole
               curve, and the order positions and heights compared

The measured curve is the Chapter 11 import (θ, normalised to 1 at the
maximum). The model is plotted as calculated, without a scale: the chapter
checks positions, and Chapter 14 sets the scale.

Run:  python scripts/figures/fig_12_figures.py   (after ch11_engine_data.py and ch12_engine_data.py)
Out:  public/figures/fig-12-2-starting-model.svg
"""
import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SRC11 = ROOT / "figures-src" / "ch11"
SRC = ROOT / "figures-src" / "ch12"
OUT = ROOT / "public" / "figures"

STROKE = "#334155"
ACCENT = "#1a5276"
MUTED = "#94a3b8"


def setup():
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.size": 9, "xtick.labelsize": 9, "ytick.labelsize": 9,
        "svg.fonttype": "none",
        "axes.edgecolor": STROKE, "axes.labelcolor": STROKE,
        "xtick.color": STROKE, "ytick.color": STROKE,
    })


def curve(path):
    d = np.loadtxt(path, skiprows=1)
    return d[:, 0], d[:, 1]


def peak(t, r, centre, half=0.04):
    s = (t > centre - half) & (t < centre + half)
    i = int(np.argmax(r[s]))
    return float(t[s][i]), float(r[s][i])


def main():
    setup()
    orders = json.loads((SRC11 / "orders.json").read_text(encoding="utf-8"))
    count = json.loads((SRC11 / "assess-design.json").read_text(encoding="utf-8"))["checks"]["counting"]
    one = 1 / (count["peak_rate_cps"] * count["counting_time_s"])
    tm, rm = curve(SRC11 / "curve-measured.dat")
    ts, rs = curve(SRC / "curve-start.dat")
    tb, rb = curve(SRC / "curve-start-bare.dat")
    meas = orders["seed_orders"] + orders["weak_orders"]

    print("orders: 2θ measured, 2θ start model, difference; R measured, R model, model / measured")
    for o in meas:
        tmod, rmod = peak(ts, rs, o["theta"])
        print(f"  {o['m']}  {2 * o['theta']:.4f}  {2 * tmod:.4f}  {2 * (tmod - o['theta']):+.4f}   "
              f"{o['R']:.3e}  {rmod:.3e}  {rmod / o['R']:.2f}")
    # The first order against the plateau, model and measurement.
    m1 = meas[0]
    _, r1 = peak(ts, rs, m1["theta"])
    i0 = int(np.argmax(np.where(ts < 0.25, rs, 0)))
    print(f"start model: plateau max {rs[i0]:.3f} at 2θ = {2 * ts[i0]:.4f}°, first order {r1:.3f}, "
          f"ratio {r1 / rs[i0]:.3f} (measured 0.574)")
    # Between the orders: the level at the minimum between orders 2 and 3, with and without the top layer.
    lo, hi = meas[1]["theta"] + 0.1, meas[2]["theta"] - 0.1
    for lab, t, r in (("measured", tm, rm), ("start", ts, rs), ("start, no top layer", tb, rb)):
        s = (t > lo) & (t < hi)
        print(f"  mean log10 R between orders 2 and 3 ({lab}): {np.mean(np.log10(r[s])):.3f}")

    fig, ax = plt.subplots(figsize=(5.35, 3.0))
    ax.plot(tm * 2, rm, color=MUTED, lw=0.7, label="measured CoC4")
    ax.plot(ts * 2, rs, color=ACCENT, lw=0.9, label="starting model")
    ax.set_yscale("log")
    ax.set_ylim(3e-8, 3)
    ax.set_xlim(0, 14)
    ax.set_xlabel("2θ (°)")
    ax.set_ylabel("R")
    for o in meas:
        ax.text(2 * o["theta"], o["R"] * 3, str(o["m"]), color=STROKE, fontsize=8, ha="center")
    ax.legend(frameon=False, fontsize=8.5, loc="upper right")
    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)
    fig.tight_layout()
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / "fig-12-2-starting-model.svg", format="svg", metadata={
        "Title": "Figure 12-2: the CoC4 starting model against the measurement",
        "Description": "Measured CoC4 (deposit, CC BY 4.0). Model reflectivity calculated by the "
                       "X-Ray Calc 3.9.4.1250 engine (figures-src/ch12/). Script: scripts/figures/fig_12_figures.py"})
    print(f"one count = {one:.3e}")


if __name__ == "__main__":
    main()
