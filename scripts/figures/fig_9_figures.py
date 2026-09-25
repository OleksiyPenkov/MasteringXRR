"""Figures 9-1 and 9-2, Tables 9-1 and 9-2 and the numbers of Chapter 9.

  Figure 9-1  χ² of the CoC5 model against the period D, 20–110 Å (engine)
  Figure 9-2  χ² over the two roughnesses of the CoC5 period (engine)
  Table 9-1   the CoC5 model under six χ² settings (engine)
  Table 9-2   five Polynomial fits of CoC5 that differ only in the seed (engine)

The engine works in θ, so its TW weights θ² and 1/θ² are taken on θ. With the
2θ box ticked the GUI takes them on 2θ (Help, Fitting: "θ here is the value on
the chart axis"), which multiplies the whole sum by 4 and by 1/4. The solved
scale is the same, because it depends only on ratios of the weighted sums.
Table 9-1 prints the 2θ values.

A local minimum of a scan is a point lower than both neighbors. The valley of
the global minimum runs to the nearest local maximum on each side.

Run:  python scripts/figures/fig_9_figures.py   (after ch9_engine_data.py)
Out:  public/figures/fig-9-1-period-scan.svg, fig-9-2-sigma-map.svg
"""
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "figures-src" / "ch9"
OUT = ROOT / "public" / "figures"

STROKE = "#334155"
ACCENT = "#1a5276"
MUTED = "#94a3b8"
ORANGE = "#b9770e"
ENGINE = "χ² calculated by the X-Ray Calc 3.9.4.1250 engine (figures-src/ch9/)."
EXPERT_SIGMA = (4.3254, 5.7386)  # σ_C, σ_Co of the CoC5 expert model, Å


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
        "Title": title, "Description": f"{ENGINE} Script: scripts/figures/fig_9_figures.py"})
    print(f"wrote {OUT / name}")


def load(name):
    return json.loads((SRC / name).read_text(encoding="utf-8"))


def local_minima(y):
    return [i for i in range(1, len(y) - 1) if y[i] < y[i - 1] and y[i] < y[i + 1]]


# ── Table 9-1 ────────────────────────────────────────────────────────────────
def table_9_1():
    print("\nTable 9-1 (2θ axis):")
    for row in load("scores.json"):
        tw = row["settings"].get("chi2", {}).get("theta_weight", 0)
        factor = {1: 4, 4: 0.25}.get(tw, 1)
        print(f"  {row['case']:34s} χ² {row['chi2'] * factor:.4g} (θ axis {row['chi2']:.6g})"
              f"  plain {row['chi2_plain']:.4g}  scale {row['scale_ratio']:.3f}")


# ── Figure 9-1 ───────────────────────────────────────────────────────────────
def figure_9_1():
    rows = load("scan-D.json")
    d = np.array([r["D"] for r in rows])
    y = np.array([r["chi2"] for r in rows])
    g = int(y.argmin())
    a = g
    while a > 0 and y[a - 1] > y[a]:
        a -= 1
    b = g
    while b < len(y) - 1 and y[b + 1] > y[b]:
        b += 1
    mins = local_minima(y)
    second = sorted((i for i in mins if i != g), key=lambda i: y[i])[0]
    print(f"\nFigure 9-1: {len(mins)} local minima over D = {d[0]:.0f}–{d[-1]:.0f} Å;"
          f" global D = {d[g]:.1f} Å, χ² {y[g]:.3f}; valley {d[a]:.1f}–{d[b]:.1f} Å;"
          f" next lowest D = {d[second]:.1f} Å, χ² {y[second]:.2f}")
    print(f"  max χ² {y.max():.0f}; χ² at the valley edges {y[a]:.0f}, {y[b]:.0f}")

    fig, ax = plt.subplots(figsize=(5.35, 2.9))
    ax.axvspan(d[a], d[b], color=MUTED, alpha=0.18, lw=0)
    ax.plot(d, y, color=ACCENT, lw=1.2)
    ax.plot([d[i] for i in mins if i != g], [y[i] for i in mins if i != g], "o", ms=3.5,
            mfc="white", mec=ORANGE, mew=1.1, label="local minima")
    ax.plot(d[g], y[g], "o", ms=5, color=ACCENT, label="global minimum")
    ax.annotate(f"D = {d[g]:.1f} Å\nχ² = {y[g]:.2f}", (d[g], y[g]), xytext=(d[g] + 6, y[g] * 1.4),
                color=STROKE, fontsize=8.5, arrowprops={"arrowstyle": "-", "color": STROKE, "lw": 0.6})
    ax.annotate(f"D = {d[second]:.1f} Å\nχ² = {y[second]:.1f}", (d[second], y[second]),
                xytext=(d[second] + 4, y[second] / 4), color=STROKE, fontsize=8.5,
                arrowprops={"arrowstyle": "-", "color": STROKE, "lw": 0.6})
    ax.set_yscale("log")
    ax.set_xlim(d[0], d[-1])
    ax.set_xlabel("Period D (Å)")
    ax.set_ylabel("χ²")
    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)
    ax.legend(frameon=False, fontsize=8.5, loc="lower right")
    fig.tight_layout()
    save(fig, "fig-9-1-period-scan.svg", "Figure 9-1: χ² of the CoC5 model against the period")


# ── Figure 9-2 ───────────────────────────────────────────────────────────────
def figure_9_2():
    rows = load("map-sigma.json")
    sc = np.array(sorted({r["sigma_C"] for r in rows}))
    sco = np.array(sorted({r["sigma_Co"] for r in rows}))
    z = np.full((len(sco), len(sc)), np.nan)
    for r in rows:
        z[np.searchsorted(sco, r["sigma_Co"]), np.searchsorted(sc, r["sigma_C"])] = r["chi2"]
    mins = []
    for i in range(len(sco)):
        for j in range(len(sc)):
            nb = z[max(0, i - 1):i + 2, max(0, j - 1):j + 2]
            if z[i, j] <= nb.min() and (nb == z[i, j]).sum() == 1:
                mins.append((z[i, j], sc[j], sco[i]))
    mins.sort()
    print("\nFigure 9-2: local minima of the σ map (χ², σ_C, σ_Co):")
    for m in mins:
        print(f"  χ² {m[0]:.4f} at σ_C = {m[1]:.1f}, σ_Co = {m[2]:.1f} Å")
    print(f"  range χ² {np.nanmin(z):.3f}–{np.nanmax(z):.2f}")

    fig, ax = plt.subplots(figsize=(4.6, 3.7))
    # Fine levels near the two minima, coarse ones far from them; the valleys are light.
    lo = np.nanmin(z)
    levels = lo + (np.nanmax(z) - lo) * np.linspace(0, 1, 17) ** 3
    levels[0] = lo - 1e-6
    cs = ax.contourf(sc, sco, z, levels=levels, cmap="Blues")
    ax.contour(sc, sco, z, levels=levels, colors=STROKE, linewidths=0.3)
    offsets = [(-58, -16), (8, 6)]
    for k, (v, x, yv) in enumerate(mins):
        ax.plot(x, yv, "o", ms=5.5, mfc=ORANGE, mec=STROKE, mew=0.8)
        ax.annotate(f"χ² = {v:.3f}", (x, yv), xytext=offsets[k % 2], textcoords="offset points",
                    color=STROKE, fontsize=8.5,
                    bbox={"boxstyle": "round,pad=0.2", "fc": "white", "ec": "none", "alpha": 0.85})
    ax.plot(*EXPERT_SIGMA, "+", ms=8, color=STROKE, mew=1.2)
    ax.set_xlabel("σ of the C layer (Å)")
    ax.set_ylabel("σ of the Co layer (Å)")
    cb = fig.colorbar(cs, ax=ax, format="%.3g", ticks=levels[::2])
    cb.set_label("χ²")
    fig.tight_layout()
    save(fig, "fig-9-2-sigma-map.svg", "Figure 9-2: χ² over the two roughnesses of the CoC5 period")


# ── Table 9-2 and the Periodic runs ──────────────────────────────────────────
def table_9_2():
    poly = load("seeds-poly.json")
    print(f"\nTable 9-2 (Polynomial, start D = {poly['start_D']} Å):")
    for r in poly["runs"]:
        c, co = r["C"], r["Co"]
        flag = " scale at bound" if r["scale_clamped"] else ""
        near = " near bound: " + ", ".join(f"layer {n['layer']} {n['parameter']} = {n['value']}"
                                          for n in r["near_bounds"]) if r["near_bounds"] else ""
        print(f"  seed {r['seed']}: χ² {r['chi2']:.3f}  D {r['D']:.2f} (top {r['D_top']:.2f},"
              f" bottom {r['D_bottom']:.2f})  C {c['thickness']:.2f} σ {c['sigma']:.2f} ρ {c['density']:.3f}"
              f"  Co {co['thickness']:.2f} σ {co['sigma']:.2f} ρ {co['density']:.3f}"
              f"  scale {r['scale_ratio']:.3f}{flag}{near}  {r['elapsed_s']:.2f} s")
    per = load("seeds-periodic.json")
    chi = [r["chi2"] for r in per["runs"]]
    s_c = [r["C"]["sigma"] for r in per["runs"]]
    s_co = [r["Co"]["sigma"] for r in per["runs"]]
    print(f"\nPeriodic, {len(chi)} seeds: χ² {min(chi):.4f}–{max(chi):.4f}, σ_C {min(s_c):.3f}–{max(s_c):.3f},"
          f" σ_Co {min(s_co):.3f}–{max(s_co):.3f}, D {per['runs'][0]['D']:.3f}")
    t = [r["elapsed_s"] for r in poly["runs"] + per["runs"]]
    print(f"fit times {min(t):.2f}–{max(t):.2f} s on {poly['runs'][0]['device']}")


def main():
    setup()
    table_9_1()
    figure_9_1()
    if (SRC / "map-sigma.json").exists():
        figure_9_2()
    table_9_2()


if __name__ == "__main__":
    main()
