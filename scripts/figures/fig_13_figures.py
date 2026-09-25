"""Figure 13-1, Table 13-1 and the numbers of Chapter 13.

  Table 13-1   the sensitivity map of the CoC4 starting model: for each variant
               of the fitting procedure v5 §3.1, how far the order positions
               move, how the order heights change (log10 of variant / base,
               orders 1-6), how the level between the orders changes (mean
               log10 R in the valleys between orders 1-2, 2-3 and 3-4), and how
               far the critical edge moves (2θ where R falls to half of the
               plateau maximum)
  Figure 13-1  six panels: the base against the two extreme steps of the
               period, the layer ratio, σ of Co, ρ of Co, the surface layer and N

Run:  python scripts/figures/fig_13_figures.py   (after ch13_engine_data.py)
Out:  public/figures/fig-13-1-sensitivity.svg, figures-src/ch13/numbers.txt (via tee)
"""
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "figures-src" / "ch13"
MEAS = ROOT / "figures-src" / "ch11" / "curve-measured.dat"
OUT = ROOT / "public" / "figures"
LAMBDA = 1.541874
D_BASE, TWO_DELTA = 54.70, 2.116e-5     # the seed of Chapter 11, to find the orders

STROKE = "#334155"
ACCENT = "#2e86c1"
ORANGE = "#b9770e"
MUTED = "#94a3b8"

# Table 13-1: the procedure's variants (label, curve key, period of the variant)
VARIANTS = [("period +2 %", "period-+2", 1.02), ("period −2 %", "period--2", 0.98),
            ("Co +2 Å, C −2 Å", "ratio-+2", 1), ("Co −2 Å, C +2 Å", "ratio--2", 1),
            ("σ of C = 1 Å", "sigC-1", 1), ("σ of C = 8 Å", "sigC-8", 1),
            ("σ of Co = 1 Å", "sigCo-1", 1), ("σ of Co = 8 Å", "sigCo-8", 1),
            ("ρ of C +15 %", "rhoC-+15", 1), ("ρ of C −15 %", "rhoC--15", 1),
            ("ρ of Co +15 %", "rhoCo-+15", 1), ("ρ of Co −15 %", "rhoCo--15", 1),
            ("surface layer 20 Å, 1.2 g/cm³", "top-20", 1), ("no surface layer", "top-none", 1),
            ("N = 10", "N-10", 1), ("N = 40", "N-40", 1)]


def setup():
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.size": 8.5, "xtick.labelsize": 8.5, "ytick.labelsize": 8.5,
        "svg.fonttype": "none",
        "axes.edgecolor": STROKE, "axes.labelcolor": STROKE,
        "xtick.color": STROKE, "ytick.color": STROKE,
    })


def curve(key):
    d = np.loadtxt(SRC / f"curve-{key}.dat", skiprows=1)
    return d[:, 0], d[:, 1]


def orders(t, r, d=D_BASE, mmax=6):
    out = []
    for m in range(1, mmax + 1):
        c = math.degrees(math.asin(math.sqrt((m * LAMBDA / (2 * d)) ** 2 + TWO_DELTA)))
        s = (t > c - 0.07) & (t < c + 0.07)
        i = int(np.argmax(r[s]))
        out.append((float(t[s][i]), float(r[s][i])))
    return out


def edge(t, r, level=0.5):
    i0 = int(np.argmax(np.where((t > 0.05) & (t < 0.25), r, 0)))
    return 2 * float(t[i0 + int(np.argmax(r[i0:] < level * r[i0]))])


def valley(t, r, a, b):
    s = (t > a) & (t < b)
    return float(np.mean(np.log10(r[s])))


def table():
    tb, rb = curve("base")
    pb = orders(tb, rb)
    wins = [(pb[k][0] + 0.12, pb[k + 1][0] - 0.12) for k in range(3)]
    print("Table 13-1: variant | max |Δ2θ| of orders 1-6 (°) | log10(height / base), orders 1-6 | "
          "Δ mean log10 R between orders 1-2, 2-3, 3-4 | Δ edge 2θ (°)")
    for label, key, f in VARIANTS:
        t, r = curve(key)
        p = orders(t, r, d=D_BASE * f)
        dpos = max(abs(2 * (p[k][0] - pb[k][0])) for k in range(6))
        hr = [math.log10(p[k][1] / pb[k][1]) for k in range(6)]
        lv = [valley(t, r, *w) - valley(tb, rb, *w) for w in wins]
        print(f"  {label:30s} {dpos:6.3f} | " + " ".join(f"{h:+5.2f}" for h in hr) + " | "
              + " ".join(f"{x:+5.2f}" for x in lv) + f" | {edge(t, r) - edge(tb, rb):+.4f}")
    print(f"base: orders at 2θ = {', '.join(f'{2 * x[0]:.3f}' for x in pb)}°; edge (half plateau) at 2θ = {edge(tb, rb):.4f}°")


PANELS = [("period ±2 %", "period--2", "period-+2", "−2 %", "+2 %", (1.0, 10.5)),
          ("layer ratio: Co ±2 Å, same period", "ratio--2", "ratio-+2", "Co −2 Å", "Co +2 Å", (1.0, 10.5)),
          ("σ of Co: 1 and 8 Å", "sigCo-1", "sigCo-8", "1 Å", "8 Å", (1.0, 10.5)),
          ("ρ of Co ±15 %", "rhoCo--15", "rhoCo-+15", "−15 %", "+15 %", (0.3, 2.2)),
          ("surface layer: none and 20 Å", "top-none", "top-20", "none", "20 Å, 1.2", (1.0, 5.5)),
          ("N: 10 and 40", "N-10", "N-40", "10", "40", (1.0, 10.5))]


def figure():
    tb, rb = curve("base")
    tm, rm = np.loadtxt(MEAS, skiprows=1).T
    fig, axes = plt.subplots(3, 2, figsize=(5.35, 6.6))
    for ax, (title, lo, hi, llo, lhi, (x0, x1)) in zip(axes.flat, PANELS):
        ax.plot(tm * 2, rm, color=MUTED, lw=0.5, alpha=0.8)
        ax.plot(tb * 2, rb, color="#111111", lw=0.7, label="starting model")
        t, r = curve(lo)
        ax.plot(t * 2, r, color=ACCENT, lw=0.8, label=llo)
        t, r = curve(hi)
        ax.plot(t * 2, r, color=ORANGE, lw=0.8, label=lhi)
        ax.set_yscale("log")
        ax.set_xlim(x0, x1)
        ax.set_ylim(1e-8 if x1 > 6 else (1e-7 if x1 > 3 else 1e-3), 2)
        ax.set_title(title, fontsize=8.5, color=STROKE, loc="left")
        ax.legend(frameon=False, fontsize=8, loc="upper right", handlelength=1.2)
        ax.spines["right"].set_visible(False)
        ax.spines["top"].set_visible(False)
    for ax in axes[-1]:
        ax.set_xlabel("2θ (°)")
    for ax in axes[:, 0]:
        ax.set_ylabel("R")
    fig.tight_layout()
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / "fig-13-1-sensitivity.svg", format="svg", metadata={
        "Title": "Figure 13-1: what each parameter moves",
        "Description": "Measured CoC4 (deposit, CC BY 4.0). Model reflectivity calculated by the X-Ray Calc "
                       "3.9.4.1250 engine (figures-src/ch13/). Script: scripts/figures/fig_13_figures.py"})


def main():
    setup()
    table()
    figure()


if __name__ == "__main__":
    main()
