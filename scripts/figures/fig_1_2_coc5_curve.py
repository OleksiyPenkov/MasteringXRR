"""Figure 1-2: a measured XRR curve with its four features labeled.

The data are the Co/C multilayer curve CoC5 (record P2-05) from the fitting
procedure's data deposit (CC BY 4.0), read in place and never copied into the
book (CLAUDE.md: the outside sources are read-only). Raw counts against 2θ, as
exported by the instrument, with no processing.

Layout: the whole curve in the lower panel, and two magnified regions above
it, each marked on the whole curve by a box with its letter:
  A  the plateau and the critical edge;
  B  the Kiessig fringes between the first and second Bragg orders.

The Bragg-order labels are placed at the measured maximum inside a window
around each order. The windows were chosen from a peak search of this curve
(2026-09-23): orders at 2θ ≈ 1.83, 3.55, 5.32 and 7.06°.

Run:  python scripts/figures/fig_1_2_coc5_curve.py
Out:  public/figures/fig-1-2-coc5-curve.svg
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle

import local_paths

SRC = local_paths.deposit("curves", "CoC5.csv")
OUT = Path(__file__).resolve().parents[2] / "public" / "figures" / "fig-1-2-coc5-curve.svg"

# Light-theme figure tokens from src/styles/textbook.css.
STROKE = "#334155"
ACCENT = "#1a5276"
MUTED = "#94a3b8"

X_MAX = 8.0  # 2θ; past the fourth order the curve is background only
ORDER_WINDOWS = [(1.70, 2.00), (3.40, 3.70), (5.20, 5.45), (6.90, 7.20)]
EDGE_SPAN = (0.45, 0.75)

# The two magnified regions, as (2θ min, 2θ max, counts min, counts max).
REGION_A = (0.08, 1.0, 2e3, 3e6)     # plateau and critical edge
REGION_B = (1.95, 3.45, 5, 2e4)     # fringes between orders 1 and 2


def load():
    d = np.loadtxt(SRC, delimiter=",", skiprows=2)
    return d[:, 0], d[:, 1]


def peak_in(x, y, lo, hi):
    m = (x >= lo) & (x <= hi)
    i = np.argmax(y[m])
    return x[m][i], y[m][i]


def style(ax):
    ax.set_yscale("log")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def mark_region(ax, region, letter):
    x0, x1, y0, y1 = region
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False, ec=MUTED, lw=0.8, ls="--"))
    ax.text(x0, y1 * 1.3, letter, color=STROKE, fontsize=9, fontweight="bold", ha="left", va="bottom")


def main():
    x, y = load()
    keep = (x <= X_MAX) & (y > 0)  # zero counts have no place on a log axis
    xs, ys = x[keep], y[keep]

    plt.rcParams.update({
        "font.family": "sans-serif",
        # Drawn at the print column's width (136mm, figures bleed into the
        # padding), so it prints at 1:1 and no label falls under the PDF
        # gates' 7.9pt floor; tick labels included.
        "font.size": 9,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "svg.fonttype": "none",
        "axes.edgecolor": STROKE,
        "axes.labelcolor": STROKE,
        "xtick.color": STROKE,
        "ytick.color": STROKE,
    })
    fig = plt.figure(figsize=(136 / 25.4, 4.9))
    gs = fig.add_gridspec(2, 2, height_ratios=[1, 1.3], hspace=0.45, wspace=0.3)
    ax_a, ax_b, ax = fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1]), fig.add_subplot(gs[1, :])
    label = dict(color=STROKE, ha="center", fontsize=9)
    leader = dict(arrowstyle="-", color=MUTED)

    # ── The whole curve ─────────────────────────────────────────────────────
    style(ax)
    ax.plot(xs, ys, color=ACCENT, lw=0.8)
    ax.set_xlim(0, X_MAX)
    ax.set_ylim(0.5, 3e7)
    ax.set_xlabel("2θ (°)")
    ax.set_ylabel("Intensity (counts)")
    for m, (lo, hi) in enumerate(ORDER_WINDOWS, start=1):
        bx, by = peak_in(x, y, lo, hi)
        ax.annotate(f"m = {m}", (bx, by), (bx + 0.45, by * 4), arrowprops=leader, **label)
    ax.text(5.6, 1e5, "Bragg orders", **label)
    mark_region(ax, REGION_A, "A")
    mark_region(ax, REGION_B, "B")

    # ── A: plateau and critical edge ────────────────────────────────────────
    x0, x1, y0, y1 = REGION_A
    band = (x >= x0) & (x <= x1) & (y > 0)
    style(ax_a)
    ax_a.plot(x[band], y[band], color=ACCENT, lw=0.9)
    ax_a.set_xlim(x0, x1)
    ax_a.set_ylim(y0, y1)
    ax_a.set_xlabel("2θ (°)")
    ax_a.set_ylabel("Counts")
    ax_a.set_title("A", loc="left", fontsize=9, fontweight="bold", color=STROKE)
    px, py = peak_in(x, y, 0.2, 0.6)
    ax_a.annotate("plateau", (px, py), (px + 0.3, py * 1.8), arrowprops=leader, **label)
    ex = np.mean(EDGE_SPAN)
    ey = np.interp(ex, x, y)
    ax_a.annotate("critical edge", (ex, ey), (ex - 0.25, ey / 12), arrowprops=leader, **label)

    # ── B: Kiessig fringes between orders 1 and 2 ───────────────────────────
    x0, x1, y0, y1 = REGION_B
    band = (x >= x0) & (x <= x1) & (y > 0)
    style(ax_b)
    ax_b.plot(x[band], y[band], color=ACCENT, lw=0.9)
    ax_b.set_xlim(x0, x1)
    ax_b.set_ylim(y0, y1)
    ax_b.set_xlabel("2θ (°)")
    ax_b.set_title("B", loc="left", fontsize=9, fontweight="bold", color=STROKE)
    ax_b.text((x0 + x1) / 2, y1 / 2.2, "Kiessig fringes", va="top", **label)
    ax_b.text(x0 + 0.03, y0 * 1.6, "← m = 1", color=STROKE, fontsize=9, ha="left")
    ax_b.text(x1 - 0.03, y0 * 1.6, "m = 2 →", color=STROKE, fontsize=9, ha="right")

    fig.subplots_adjust(left=0.1, right=0.98, top=0.95, bottom=0.09)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, format="svg", metadata={
        "Title": "Figure 1-2: a measured XRR curve (Co/C multilayer CoC5)",
        "Description": f"Plotted from {SRC.name}, fitting-procedure data deposit, CC BY 4.0. "
                       "Script: scripts/figures/fig_1_2_coc5_curve.py",
    })
    print(f"wrote {OUT}")
    for m, (lo, hi) in enumerate(ORDER_WINDOWS, start=1):
        print(f"order {m}: 2θ = {peak_in(x, y, lo, hi)[0]:.3f}°")
    print(f"plateau maximum: 2θ = {px:.4f}°, {py:.0f} counts")


if __name__ == "__main__":
    main()
