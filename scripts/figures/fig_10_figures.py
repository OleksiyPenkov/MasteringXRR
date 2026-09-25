"""Figure 10-1, Table 10-1 and the numbers of Chapter 10.

  Figure 10-1  the CoC5 measurement on its own axis and misread as θ, against
               the CoC5 model (engine)
  Table 10-1   the eight checks of the assessment, with and without the design

The measured curve is the one the import leaves (θ, normalised to 1 at the
maximum, zero counts floored; figures-src/ch10/curve-measured.dat). "Misread
as θ" plots it the way a two-column file in 2θ is drawn when the 2θ box is
unticked: the file's 2θ numbers are taken as θ, so on a 2θ axis every point
sits at twice its angle.

One count on the normalised scale is 1 / (peak rate × counting time), both
from the file's header (procedure v5 §1 rule 5).

Run:  python scripts/figures/fig_10_figures.py   (after ch10_engine_data.py)
Out:  public/figures/fig-10-1-two-theta-misread.svg
"""
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "figures-src" / "ch10"
OUT = ROOT / "public" / "figures"

STROKE = "#334155"
ACCENT = "#1a5276"
MUTED = "#94a3b8"
ORANGE = "#b9770e"
ENGINE = "Model reflectivity calculated by the X-Ray Calc 3.9.4.1250 engine (figures-src/ch10/)."


def setup():
    plt.rcParams.update({
        "font.family": "sans-serif",
        # Drawn at the print column's width (136 mm), printed at 1:1.
        "font.size": 9, "xtick.labelsize": 9, "ytick.labelsize": 9,
        "svg.fonttype": "none",
        "axes.edgecolor": STROKE, "axes.labelcolor": STROKE,
        "xtick.color": STROKE, "ytick.color": STROKE,
    })


def load(name):
    return json.loads((SRC / name).read_text(encoding="utf-8"))


def curve(name):
    d = np.loadtxt(SRC / name, skiprows=1)
    return d[:, 0], d[:, 1]


def numbers():
    a = load("assess-design.json")["checks"]
    n = load("assess-none.json")["checks"]
    count = a["counting"]
    one = 1 / (count["peak_rate_cps"] * count["counting_time_s"])
    print(f"one count = 1 / ({count['peak_rate_cps']:.0f} × {count['counting_time_s']}) = {one:.3e}"
          f"; background {a['orders_visible']['background']:.3e} = {a['orders_visible']['background'] / one:.2f} counts")
    print("\nTable 10-1 (design / none):")
    for k in a:
        print(f"  {k:24s} {a[k]['verdict']:8s} value {a[k]['value']}  threshold {a[k]['threshold']}   |  none: {n[k]['verdict']}")
    print("\norders (2θ Bragg, 2θ measured, I measured in counts, model scaled in counts, visible, expected):")
    for o in a["orders_visible"]["orders"]:
        print(f"  {o['n']}  {o['theta_bragg_two_theta_deg']:.3f}  {o['theta_meas_two_theta_deg']:.4f}"
              f"  {o['i_meas'] / one:10.1f}  {o['i_model_scaled'] / one:10.1f}  {o['visible']}  {o['expected_visible']}")
    z = a["zeros"]
    print(f"\nzeros: {z['value']} ({z['fraction'] * 100:.1f} %), first at 2θ = {z['first_two_theta_deg']}°")
    r = a["range_below_background"]
    print(f"below background from 2θ = {r['first_at_background_two_theta_deg']}°, last above at {r['last_above_background_two_theta_deg']}°")
    s = a["sampling"]
    print(f"sampling {s['points_per_fringe']:.1f} per fringe (fringe {s['fringe_period_theta_deg'] * 2:.4f}° 2θ), "
          f"{s['points_per_order']:.0f} per order, total thickness {s['total_thickness_A']:.1f} Å")
    p = a["plateau_vs_first_order"]
    print(f"plateau vs first order {p['value']:.3f} against the design's {p['model_ratio']:.3f}")


def figure_10_1():
    tm, rm = curve("curve-measured.dat")      # θ
    tc, rc = curve("curve-model.dat")         # θ
    fig, axes = plt.subplots(2, 1, figsize=(5.35, 4.6), sharex=True)
    for ax, factor, title in [(axes[0], 2, "Read as 2θ (right)"), (axes[1], 4, "The same file read as θ (wrong)")]:
        ax.plot(tc * 2, rc, color=ACCENT, lw=1.0, label="the Co/C model")
        ax.plot(tm * factor, rm, color=MUTED, lw=0.8, label="the measured curve")
        ax.set_yscale("log")
        ax.set_ylim(3e-7, 2)
        ax.set_xlim(0, 9)
        ax.set_ylabel("R")
        ax.set_title(title, fontsize=9, color=STROKE, loc="left")
        ax.spines["right"].set_visible(False)
        ax.spines["top"].set_visible(False)
    axes[0].legend(frameon=False, fontsize=8.5, loc="upper right")
    # The misread first order lands where the model has its second.
    i1 = np.argmax(np.where((tm > 0.85) & (tm < 1.0), rm, 0))
    axes[1].annotate(f"1st order, now at 2θ = {tm[i1] * 4:.2f}°", (tm[i1] * 4, rm[i1]),
                     xytext=(tm[i1] * 4 + 0.6, rm[i1] * 3), color=STROKE, fontsize=8.5,
                     arrowprops={"arrowstyle": "-", "color": STROKE, "lw": 0.6})
    axes[1].set_xlabel("2θ (°)")
    fig.tight_layout()
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / "fig-10-1-two-theta-misread.svg", format="svg", metadata={
        "Title": "Figure 10-1: a 2θ file read as θ",
        "Description": f"Measured CoC5 (deposit, CC BY 4.0). {ENGINE} Script: scripts/figures/fig_10_figures.py"})
    print(f"\nFigure 10-1: misread 1st order at 2θ = {tm[i1] * 4:.4f}° (right: {tm[i1] * 2:.4f}°)")


def main():
    setup()
    numbers()
    figure_10_1()


if __name__ == "__main__":
    main()
