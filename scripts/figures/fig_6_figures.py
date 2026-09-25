"""Figures 6-2 to 6-4, Table 6-1 and the numbers of Chapter 6.

  Table 6-1   the Bragg orders of the measured Co/C multilayer CoC5
              (fitting-procedure data deposit, CC BY 4.0, read in place)
  Figure 6-2  Co/C, D = 100 Å: evenly spaced orders against the Bragg law
              with refraction (engine)
  Figure 6-3  Co/C, D = 50 Å, at three layer ratios Γ (engine)
  Figure 6-4  the CoC5 expert model against σ + 2 Å and against a changed
              ratio at the same period (engine)

The CoC5 orders are the largest raw count inside the same windows as
Figure 1-2 (fig_1_2_coc5_curve.py), on the file's 2θ grid (step 0.003°).
The period is fitted to them with sin²θm = (mλ/2D)² + 2δ̄, linear least
squares in m², at λ = 1.541874 Å, the wavelength the CoC5 .xrdml implies.

On an engine curve an order is the largest R within ±0.2 of the order
spacing around the position the Bragg law with refraction predicts, with δ̄
the thickness-weighted mean of the layers' δ (Spiller Eq. 7.8).

Run:  python scripts/figures/fig_6_figures.py   (after ch6_engine_data.py)
Out:  public/figures/fig-6-2-even-spacing.svg, fig-6-3-layer-ratio.svg,
      fig-6-4-high-orders.svg
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
COC5 = local_paths.deposit("curves", "CoC5.csv")
SRC = ROOT / "figures-src" / "ch6"
OUT = ROOT / "public" / "figures"
LAMBDA = 1.5406       # Å, the engine curves
LAMBDA_COC5 = 1.541874  # Å, the wavelength the .xrdml implies (Kα doublet, ratio 0.5; Chapter 10)
ORDER_WINDOWS = [(1.70, 2.00), (3.40, 3.70), (5.20, 5.45), (6.90, 7.20)]  # 2θ, as Figure 1-2

STROKE = "#334155"
ACCENT = "#1a5276"
MUTED = "#94a3b8"
ORANGE = "#b9770e"
PURPLE = "#7d3c98"

CONST = {c["material"]: c for c in json.loads((SRC / "optical-constants.json").read_text(encoding="utf-8"))["materials"]}
D_C, D_CO = CONST["C"]["delta"], CONST["Co"]["delta"]
RHO_C, RHO_CO = CONST["C"]["density_used"], CONST["Co"]["density_used"]


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
        "Title": title, "Description": f"{source} Script: scripts/figures/fig_6_figures.py"})
    print(f"wrote {OUT / name}")


def curve(case):
    d = np.loadtxt(SRC / f"curve-{case}.dat", skiprows=1)
    return d[:, 0], d[:, 1]


def bragg_theta(m, d, dbar, lam=LAMBDA):
    """θ of order m in degrees, from sin²θm = (mλ/2D)² + 2δ̄."""
    return math.degrees(math.asin(math.sqrt((m * lam / (2 * d)) ** 2 + 2 * dbar)))


def dbar_coc(ratio, rho_c=RHO_C, rho_co=RHO_CO):
    """Thickness-weighted mean δ of a Co/C period; δ scales with density."""
    return ratio * D_CO * rho_co / RHO_CO + (1 - ratio) * D_C * rho_c / RHO_C


def engine_orders(case, d, dbar, mmax):
    t, r = curve(case)
    half = 0.2 * math.degrees(LAMBDA / (2 * d))
    out = []
    for m in range(1, mmax + 1):
        tp = bragg_theta(m, d, dbar)
        w = (t > tp - half) & (t < tp + half)
        i = np.argmax(r[w])
        out.append((m, tp, t[w][i], r[w][i]))
    return out


# ── Table 6-1: the measured CoC5 orders ─────────────────────────────────────
def coc5_orders():
    d = np.loadtxt(COC5, delimiter=",", skiprows=2)
    x, y = d[:, 0], d[:, 1]
    out = []
    for a, b in ORDER_WINDOWS:
        s = (x >= a) & (x <= b)
        i = np.argmax(y[s])
        out.append((x[s][i], y[s][i]))
    return out


def coc5_report():
    pk = coc5_orders()
    tt = np.array([p[0] for p in pk])
    th = np.radians(tt / 2)
    m = np.arange(1, len(tt) + 1)
    a, b = np.linalg.lstsq(np.vstack([m ** 2, np.ones_like(m)]).T, np.sin(th) ** 2, rcond=None)[0]
    d_fit = LAMBDA_COC5 / (2 * math.sqrt(a))
    print("\nTable 6-1, CoC5 (λ = 1.541874 Å):")
    print("  m  2θ meas.  counts   D plain (Å)  2θ even  diff    2θ refr.")
    for k in range(len(tt)):
        d_plain = m[k] * LAMBDA_COC5 / (2 * math.sin(th[k]))
        even = m[k] * tt[0]
        refr = 2 * bragg_theta(m[k], d_fit, b / 2, LAMBDA_COC5)
        print(f"  {m[k]}  {tt[k]:.4f}  {pk[k][1]:8.0f}  {d_plain:6.2f}      {even:.4f}  {tt[k] - even:+.3f}  {refr:.3f}")
    print(f"  refraction fit: D = {d_fit:.2f} Å, 2δ̄ = {b:.3g}, δ̄ = {b / 2:.3g}")
    sp = np.mean(np.diff(tt))
    print(f"  mean order spacing Δ(2θ) = {sp:.3f}°; 4th-order error {tt[3] - 4 * tt[0]:+.3f}° "
          f"= {abs(tt[3] - 4 * tt[0]) / sp * 100:.0f} % of it")
    # Spiller pp. 272–273: D_m² against 1/sin²θm is a straight line, intercept D², slope −2δ̄D².
    dm2 = (m * LAMBDA_COC5 / (2 * np.sin(th))) ** 2
    slope, icpt = np.polyfit(1 / np.sin(th) ** 2, dm2, 1)
    print(f"  straight line D_m² vs 1/sin²θ: D = {math.sqrt(icpt):.2f} Å, δ̄ = {-slope / icpt / 2:.3g}")
    h_c, h_co = 31.2135, 18.8183
    print(f"  expert fit: D = {h_c + h_co:.2f} Å, Γ = {h_co / (h_c + h_co):.3f}")


# ── Figure 6-2: evenly spaced orders against refraction ─────────────────────
def fig_6_2():
    t, r = curve("D100")
    dbar = dbar_coc(0.3)
    orders = engine_orders("D100", 100, dbar, 8)
    t1 = orders[0][2]
    fig = plt.figure(figsize=(136 / 25.4, 3.4))
    ax = fig.add_subplot(111)
    ax.set_yscale("log")
    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)
    ax.plot(2 * t, r, color=ACCENT, lw=0.7)
    ax.set_xlim(0, 7.6)
    ax.set_ylim(1e-8, 1e3)
    ax.set_xlabel("2θ (°)")
    ax.set_ylabel("Reflectivity R")
    ax.set_yticks([1e-8, 1e-6, 1e-4, 1e-2, 1])
    y_refr, y_even = 12, 180
    for m, tp, te, _ in orders:
        ax.plot([2 * tp], [y_refr], marker="v", color=PURPLE, ms=5)
        ax.text(2 * tp, y_refr * 2.3, str(m), ha="center", color=PURPLE, fontsize=8)
        xe = 2 * m * t1
        if xe < 7.6:
            ax.plot([xe], [y_even], marker="v", color=ORANGE, ms=5)
            ax.text(xe, y_even * 2.3, str(m), ha="center", color=ORANGE, fontsize=8)
    handles = [plt.Line2D([], [], ls="none", marker="v", color=ORANGE, ms=5, label="evenly spaced, m × 2θ₁"),
               plt.Line2D([], [], ls="none", marker="v", color=PURPLE, ms=5, label="Bragg law with refraction")]
    ax.legend(handles=handles, loc="lower left", frameon=False, fontsize=8)
    fig.subplots_adjust(left=0.11, right=0.97, top=0.97, bottom=0.14)
    save(fig, "fig-6-2-even-spacing.svg", "Figure 6-2: evenly spaced orders against refraction",
         "Reflectivity calculated by the X-Ray Calc 3.9.4.1250 engine (figures-src/ch6/).")
    print("\nFigure 6-2, Co/C D = 100 Å, Γ = 0.3, N = 20:")
    print(f"  δ̄ = {dbar:.4g}")
    for m, tp, te, rr in orders:
        near = min(orders, key=lambda o: abs(2 * o[2] - 2 * m * t1))[0]
        print(f"  m={m}: engine 2θ {2 * te:.3f}, law {2 * tp:.3f} (diff {2 * (tp - te):+.3f}), "
              f"even {2 * m * t1:.3f} → nearest order {near}")


# ── Figure 6-3: the layer ratio ─────────────────────────────────────────────
RATIOS = [("G0.5", 0.5, "Γ = 0.5"), ("G0.333", 1 / 3, "Γ = 1/3"), ("G0.376", 0.376, "Γ = 0.376")]


def fig_6_3():
    fig, axes = plt.subplots(3, 1, figsize=(136 / 25.4, 5.6), sharex=True)
    for ax, (case, g, label) in zip(axes, RATIOS):
        t, r = curve(case)
        ax.set_yscale("log")
        ax.spines["right"].set_visible(False)
        ax.spines["top"].set_visible(False)
        ax.plot(2 * t, r, color=ACCENT, lw=0.6)
        ax.set_ylim(1e-9, 1e2)
        ax.set_yticks([1e-8, 1e-5, 1e-2])
        ax.set_ylabel("R")
        ax.text(11.9, 3, label, ha="right", va="center", color=STROKE, fontsize=9)
        for m, tp, te, rr in engine_orders(case, 50, dbar_coc(g), 6):
            ax.text(2 * te, rr * 4, str(m), ha="center", color=PURPLE, fontsize=8)
    axes[-1].set_xlim(0, 12)
    axes[-1].set_xlabel("2θ (°)")
    fig.subplots_adjust(left=0.11, right=0.97, top=0.98, bottom=0.08, hspace=0.12)
    save(fig, "fig-6-3-layer-ratio.svg", "Figure 6-3: the layer ratio and the order heights",
         "Reflectivity calculated by the X-Ray Calc 3.9.4.1250 engine (figures-src/ch6/).")
    print("\nFigure 6-3, order heights R and sin²(mπΓ):")
    for case, g, label in RATIOS:
        cells = [f"{m}: {rr:.2g} ({math.sin(m * math.pi * g) ** 2:.2f})"
                 for m, tp, te, rr in engine_orders(case, 50, dbar_coc(g), 6)]
        print(f"  {label:10s} " + "  ".join(cells))
    for case, n in [("G0.376", 20), ("G0.376-N10", 10)]:
        t, r = curve(case)
        o = engine_orders(case, 50, dbar_coc(0.376), 2)
        s = (t > o[0][2]) & (t < o[1][2])
        rr = r[s]
        count = sum(1 for i in range(1, len(rr) - 1) if rr[i] > rr[i - 1] and rr[i] > rr[i + 1])
        print(f"  N = {n}: {count} fringe maxima between orders 1 and 2")


# ── Figure 6-4: the high orders carry the details ───────────────────────────
def fig_6_4():
    tb, rb = curve("CoC5")
    fig, axes = plt.subplots(2, 1, figsize=(136 / 25.4, 4.4), sharex=True)
    for ax, (case, color, label) in zip(axes, [("CoC5-sigma", ORANGE, "σ + 2 Å in both layers"),
                                               ("CoC5-ratio", PURPLE, "2 Å moved from C to Co")]):
        t, r = curve(case)
        ax.set_yscale("log")
        ax.spines["right"].set_visible(False)
        ax.spines["top"].set_visible(False)
        ax.plot(2 * tb, rb, color=MUTED, lw=1.4, label="expert fit")
        ax.plot(2 * t, r, color=color, lw=0.7, label=label)
        ax.set_ylim(1e-9, 5)
        ax.set_yticks([1e-8, 1e-6, 1e-4, 1e-2, 1])
        ax.set_ylabel("R")
        ax.legend(loc="upper right", frameon=False)
    axes[-1].set_xlim(0, 8)
    axes[-1].set_xlabel("2θ (°)")
    fig.subplots_adjust(left=0.11, right=0.97, top=0.98, bottom=0.1, hspace=0.12)
    save(fig, "fig-6-4-high-orders.svg", "Figure 6-4: what the high orders carry",
         "Reflectivity calculated by the X-Ray Calc 3.9.4.1250 engine (figures-src/ch6/).")
    dbar = dbar_coc(18.8183 / 50.0318, rho_c=2.0621, rho_co=6.2509)
    base = engine_orders("CoC5", 50.0318, dbar, 4)
    print("\nFigure 6-4, order heights relative to the expert model:")
    for case in ["CoC5-sigma", "CoC5-ratio"]:
        var = engine_orders(case, 50.0318, dbar, 4)
        print(f"  {case:11s} " + "  ".join(f"{m}: ×{v[3] / b[3]:.2g}" for m, b, v in
                                           zip(range(1, 5), base, var)))


def main():
    setup()
    fig_6_2()
    fig_6_3()
    fig_6_4()
    coc5_report()


if __name__ == "__main__":
    main()
