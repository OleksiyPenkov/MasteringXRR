"""Figures 4-2 and 4-3, and the numbers of Table 4-1.

Reads what scripts/figures/ch4_engine_data.py saved from the X-Ray Calc engine
(figures-src/ch4/). Nothing here computes a reflectivity: the curves are the
engine's. The only arithmetic is θc = √(2δ) from the engine's δ, and the
(θc/2θ)⁴ line of Figure 4-3, which is the chapter's own approximation drawn for
comparison.

  Figure 4-2  bare, smooth Si, Mo and W substrates at λ = 1.5406 Å, θc marked
  Figure 4-3  bare Si with the (θc/2θ)⁴ line

Both plots have 2θ on the bottom axis, as on the X-Ray Calc chart, and θ on
the top axis, as in the formulas (author, 2026-09-24).

Run:  python scripts/figures/fig_4_curves.py
Out:  public/figures/fig-4-2-three-substrates.svg, public/figures/fig-4-3-fall-off.svg
"""
import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "figures-src" / "ch4"
OUT = ROOT / "public" / "figures"

# Light-theme figure tokens from src/styles/textbook.css, plus two darker
# series colors for the curves that are not the accent.
STROKE = "#334155"
ACCENT = "#1a5276"
MUTED = "#94a3b8"
SERIES = {"Si": ACCENT, "Mo": "#b9770e", "W": "#7d3c98"}
TABLE_ORDER = ["C", "B4C", "Si", "SiO2", "Co", "Mo", "Ru", "W"]


def load_constants():
    data = json.loads((SRC / "optical-constants.json").read_text(encoding="utf-8"))
    by_name = {c["material"].lower(): c for c in data["materials"]}
    return {m: by_name[m.lower()] for m in TABLE_ORDER}


def theta_c_deg(delta):
    return math.degrees(math.sqrt(2 * delta))


def load_curve(material):
    d = np.loadtxt(SRC / f"curve-{material}.dat", skiprows=1)
    return d[:, 0], d[:, 1]  # θ (degrees), R


def setup():
    plt.rcParams.update({
        "font.family": "sans-serif",
        # Drawn at the print column's width (136 mm), so it prints at 1:1 and
        # no label falls under the PDF gates' 7.9 pt floor.
        "font.size": 9, "xtick.labelsize": 9, "ytick.labelsize": 9,
        "svg.fonttype": "none",
        "axes.edgecolor": STROKE, "axes.labelcolor": STROKE,
        "xtick.color": STROKE, "ytick.color": STROKE,
    })


def axes(fig, x_max):
    ax = fig.add_subplot(111)
    ax.set_yscale("log")
    ax.spines["right"].set_visible(False)
    ax.set_xlim(0, x_max)
    ax.set_xlabel("2θ (°)")
    ax.set_ylabel("Reflectivity R")
    top = ax.secondary_xaxis("top", functions=(lambda x: x / 2, lambda t: 2 * t))
    top.set_xlabel("θ (°)")
    return ax


def save(fig, name, title):
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / name, format="svg", metadata={
        "Title": title,
        "Description": "Reflectivity calculated by the X-Ray Calc 3.9.4.1250 engine "
                       "(figures-src/ch4/). Script: scripts/figures/fig_4_curves.py",
    })
    print(f"wrote {OUT / name}")


def fig_4_2(constants):
    fig = plt.figure(figsize=(136 / 25.4, 3.3))
    ax = axes(fig, 2.4)
    ax.set_ylim(1e-4, 2)
    for m in ["Si", "Mo", "W"]:
        t, r = load_curve(m)
        tc = theta_c_deg(constants[m]["delta"])
        ax.plot(2 * t, r, color=SERIES[m], lw=1.2, label=f"{m}, 2θc = {2 * tc:.3f}°")
        ax.axvline(2 * tc, color=SERIES[m], lw=0.7, ls=":")
    ax.text(0.12, 0.45, "plateau", color=STROKE, fontsize=9, ha="left")
    ax.legend(loc="upper right", frameon=False)
    fig.subplots_adjust(left=0.11, right=0.97, top=0.84, bottom=0.14)
    save(fig, "fig-4-2-three-substrates.svg", "Figure 4-2: reflectivity of bare Si, Mo and W")


def fig_4_3(constants):
    fig = plt.figure(figsize=(136 / 25.4, 3.3))
    ax = axes(fig, 6.0)
    ax.set_ylim(1e-6, 2)
    t, r = load_curve("Si")
    tc = theta_c_deg(constants["Si"]["delta"])
    ax.plot(2 * t, r, color=ACCENT, lw=1.3, label="Si, calculated by X-Ray Calc")
    tt = np.linspace(1.6 * tc, 3.0, 200)
    ax.plot(2 * tt, (tc / (2 * tt)) ** 4, color=STROKE, lw=0.9, ls="--", label="(θc / 2θ)⁴")
    for x2 in (2.0, 4.0):  # 2θ values marked on the curve
        ri = np.interp(x2 / 2, t, r)
        ax.plot([x2], [ri], "o", color=ACCENT, ms=4)
        ax.annotate(f"2θ = {x2:g}°", (x2, ri), (x2 + 0.25, ri * 6),
                    color=STROKE, fontsize=8, arrowprops=dict(arrowstyle="-", color=MUTED))
    ax.legend(loc="upper right", frameon=False)
    fig.subplots_adjust(left=0.11, right=0.97, top=0.84, bottom=0.14)
    save(fig, "fig-4-3-fall-off.svg", "Figure 4-3: the fall of the Si reflectivity above the critical angle")


def report(constants):
    print("\nTable 4-1 (λ = 1.5406 Å, bulk density from the program's Henke table)")
    print("material | ρ | δ×10⁶ | β×10⁶ | δ/β | θc | 2θc")
    for m, c in constants.items():
        tc = theta_c_deg(c["delta"])
        print(f"{m} | {c['density_used']} | {c['delta'] * 1e6:.2f} | {c['beta'] * 1e6:.3g} | "
              f"{c['delta'] / c['beta']:.3g} | {tc:.3f} | {2 * tc:.3f}")
    print("\nCurve values used in the text")
    for m in ["Si", "Mo", "W"]:
        t, r = load_curve(m)
        tc = theta_c_deg(constants[m]["delta"])
        print(f"{m}: θc = {tc:.4f}°, R(0.5 θc) = {np.interp(0.5 * tc, t, r):.3f}, "
              f"R(0.9 θc) = {np.interp(0.9 * tc, t, r):.3f}, R(θc) = {np.interp(tc, t, r):.3f}")
    t, r = load_curve("MoSi-multilayer")
    dbar = (25 * constants["Si"]["delta"] + 15 * constants["Mo"]["delta"]) / 40
    print(f"Mo/Si multilayer: δ̄ = {dbar:.4g}, √(2δ̄) = {theta_c_deg(dbar):.3f}°; R at θ = "
          + ", ".join(f"{th}°: {np.interp(th, t, r):.2f}" for th in (0.20, 0.29, 0.30, 0.31, 0.32, 0.33)))
    t, r = load_curve("Si")
    tc = theta_c_deg(constants["Si"]["delta"])
    for th in (1.0, 2.0):
        print(f"Si θ = {th}°: engine R = {np.interp(th, t, r):.4g}, (θc/2θ)⁴ = {(tc / (2 * th)) ** 4:.4g}")


def main():
    setup()
    constants = load_constants()
    fig_4_2(constants)
    fig_4_3(constants)
    report(constants)


if __name__ == "__main__":
    main()
