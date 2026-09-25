"""Figures 16-1 and 16-2, Tables 16-2 and 16-3 and the numbers of Chapter 16.

  Figure 16-1  χ² against Δθ on CoC4: one run at each Δθ from 0.009 to 0.020°
               (the procedure's scan uses the first seed), the five runs at each
               Δθ of the laboratory's window 0.012-0.015°, each marked by the σ
               valley it ended in, and the window shaded
  Figure 16-2  the Kiessig fringes between orders 1 and 2: measured CoC4 after
               Normalize (Auto), and the best run at Δθ = 0.012° and 0.014°
               (each divided by its solved scale, so that it sits on the
               anchored curve the program draws); the mean fringe contrasts
               are the ones the engine reports
  Table 16-2   population × iterations, five runs each at Δθ = 0.012°
  Table 16-3   the five runs at Δθ = 0.014°, the value the scan picks

Valleys: Chapter 9's two σ minima. A run is in valley "C smaller" when
σ(C) < σ(Co) (σ(C) ≈ 2.5 Å, σ(Co) ≈ 4.2 Å) and in "C larger" otherwise
(σ(C) ≈ 4.3 Å, σ(Co) ≈ 2.6 Å).

Run:  python scripts/figures/fig_16_figures.py   (after ch16_engine_data.py)
Out:  public/figures/fig-16-1-resolution-scan.svg, fig-16-2-fringe-contrast.svg,
      figures-src/ch16/numbers.txt
"""
import json
import statistics as st
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "figures-src" / "ch16"
OUT = ROOT / "public" / "figures"

STROKE = "#334155"
ACCENT = "#1a5276"
MUTED = "#94a3b8"
ORANGE = "#b9770e"
BAND = "#e8eef4"

lines = []


def out(s=""):
    print(s)
    lines.append(s)


def setup():
    plt.rcParams.update({
        "font.family": "sans-serif", "font.size": 9, "xtick.labelsize": 9, "ytick.labelsize": 9,
        "svg.fonttype": "none", "axes.edgecolor": STROKE, "axes.labelcolor": STROKE,
        "xtick.color": STROKE, "ytick.color": STROKE,
    })


def clean(ax):
    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)


def load(name):
    return json.loads((SRC / name).read_text(encoding="utf-8"))


def c_smaller(r):
    return r["C"]["sigma"] < r["Co"]["sigma"]


def ms(xs, nd):
    return f"{st.mean(xs):.{nd}f} ± {st.stdev(xs):.{nd}f}"


RES = load("resolution.json")
POP = load("population.json")["runs"]
WINDOW = [0.012, 0.013, 0.014, 0.015]


def at(dt):
    return [r for r in RES["scan"] if r["resolution"] == dt] + \
           [r for r in RES["window"] if r["resolution"] == dt]


def figure_16_1():
    scan = RES["scan"]
    out("Figure 16-1: the scan (first seed)")
    for r in scan:
        out(f"  Δθ {r['resolution']:.3f}°  χ² {r['chi2']:.4f}  σ(C) {r['C']['sigma']:.2f}  "
            f"σ(Co) {r['Co']['sigma']:.2f}  {'C smaller' if c_smaller(r) else 'C larger'}")
    pick = min((r for r in scan if 0.012 <= r["resolution"] <= 0.015), key=lambda r: r["chi2"])
    out(f"  lowest χ² in the window: Δθ {pick['resolution']}° ({pick['chi2']:.4f})")
    low = min(scan, key=lambda r: r["chi2"])
    out(f"  lowest χ² of the whole scan: Δθ {low['resolution']}° ({low['chi2']:.4f})")

    fig, ax = plt.subplots(figsize=(5.35, 2.9))
    ax.axvspan(0.0115, 0.0155, color=BAND, lw=0)
    ax.text(0.0135, 1.425, "the laboratory's\nwindow", color=ACCENT, fontsize=8, ha="center")
    x = [r["resolution"] for r in scan]
    y = [r["chi2"] for r in scan]
    ax.plot(x, y, color=MUTED, lw=0.8, zorder=1)
    for r in scan:
        ax.plot(r["resolution"], r["chi2"], "o", ms=6, zorder=3,
                color=ACCENT if c_smaller(r) else ORANGE)
    for dt in WINDOW:
        for r in at(dt)[1:]:
            ax.plot(dt + 0.00018, r["chi2"], "o", ms=3.2, zorder=2, mfc="white",
                    color=ACCENT if c_smaller(r) else ORANGE)
    ax.plot([], [], "o", color=ACCENT, ms=6, label="σ(C) 2.5 Å, σ(Co) 4.2 Å")
    ax.plot([], [], "o", color=ORANGE, ms=6, label="σ(C) 4.3 Å, σ(Co) 2.6 Å")
    ax.plot([], [], "o", color=STROKE, mfc="white", ms=3.2, label="the other four runs")
    ax.legend(frameon=False, fontsize=8, loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=3,
              handletextpad=0.3, columnspacing=1.0)
    ax.set_ylim(1.21, 1.47)
    ax.set_xlabel("Δθ (°)")
    ax.set_ylabel("χ²")
    ax.set_xlim(0.0085, 0.0205)
    ax.set_xticks([0.009 + 0.001 * i for i in range(12)])
    ax.set_xticklabels([f"{0.009 + 0.001 * i:.3f}" for i in range(12)], rotation=45)
    clean(ax)
    fig.tight_layout()
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / "fig-16-1-resolution-scan.svg", format="svg", metadata={
        "Title": "Figure 16-1: χ² against Δθ for CoC4",
        "Description": "Fits of measured CoC4 (deposit, CC BY 4.0) by the X-Ray Calc 3.9.4.1250 "
                       "engine. Script: scripts/figures/fig_16_figures.py"})


def contrast(r):
    f = r["fringes"]
    return f["measured"]["mean_contrast"], f["calculated"]["mean_contrast"]


def figure_16_2():
    out("\nFigure 16-2 and the fringe check (mean contrast between orders 1 and 2)")
    for r in RES["scan"]:
        m, c = contrast(r)
        out(f"  Δθ {r['resolution']:.3f}°: measured {m:.2f}, model {c:.2f}, "
            f"fringes {r['fringes']['count']}, θ {r['fringes']['between_deg']}")
    anchor = json.loads((ROOT / "figures-src" / "ch14" / "anchor.json").read_text(encoding="utf-8"))
    d = np.loadtxt(ROOT / "figures-src" / "ch11" / "curve-measured.dat", skiprows=1)
    t, rn = d[:, 0], d[:, 1] * anchor["scale"]
    lo, hi = 0.84875, 1.63475                      # the engine's band between orders 1 and 2 (θ)
    fig, axes = plt.subplots(1, 2, figsize=(5.35, 2.9), gridspec_kw={"width_ratios": [1.5, 1]})
    m = contrast(RES["scan"][0])[0]
    models = []
    for dt in (0.012, 0.014):
        best = min(at(dt), key=lambda r: r["chi2"])
        c = np.loadtxt(SRC / f"fringes-{dt:.3f}.dat", comments="#", skiprows=2)
        models.append((dt, best, c))
        out(f"  best run at {dt}: seed {best['seed']}, χ² {best['chi2']:.4f}, scale {best['scale_ratio']}, "
            f"contrast {contrast(best)[1]:.3f}")
    for ax, (a, b) in ((axes[0], (lo, hi)), (axes[1], (1.20, 1.36))):
        s = (t >= a) & (t <= b)
        ax.plot(2 * t[s], rn[s], color=MUTED, lw=1.4, label=f"measured (mean contrast {m:.2f})")
        for (dt, best, c), col, ls in zip(models, (ACCENT, ORANGE), ("-", "--")):
            k = (c[:, 0] >= a) & (c[:, 0] <= b)
            ax.plot(2 * c[k, 0], c[k, 1] / best["scale_ratio"], color=col, lw=0.9, ls=ls,
                    label=f"model, Δθ = {dt:.3f}° (mean contrast {contrast(best)[1]:.2f})")
        ax.set_yscale("log")
        ax.set_xlim(2 * a, 2 * b)
        ax.set_xlabel("2θ (°)")
        clean(ax)
    axes[0].axvspan(2.40, 2.72, color=BAND, lw=0, zorder=0)
    axes[0].set_title("orders 1 to 2", fontsize=9, color=STROKE, loc="left")
    axes[1].set_title("enlarged", fontsize=9, color=STROKE, loc="left")
    axes[0].set_ylabel("R")
    fig.legend(*axes[0].get_legend_handles_labels(), frameon=False, fontsize=8, loc="upper center",
               ncol=1, bbox_to_anchor=(0.5, 1.0))
    fig.tight_layout(rect=(0, 0, 1, 0.8))
    fig.savefig(OUT / "fig-16-2-fringe-contrast.svg", format="svg", metadata={
        "Title": "Figure 16-2: the fringes between orders 1 and 2 of CoC4",
        "Description": "Measured CoC4 (deposit, CC BY 4.0) after Normalize (Auto); models of the "
                       "X-Ray Calc 3.9.4.1250 engine. Script: scripts/figures/fig_16_figures.py"})


def table_16_2():
    out("\nTable 16-2: population × iterations, five runs each, Δθ = 0.012°")
    keys = []
    for r in POP:
        k = (r["population"], r["iterations"])
        if k not in keys:
            keys.append(k)
    for k in keys:
        g = [r for r in POP if (r["population"], r["iterations"]) == k]
        a = [r for r in g if c_smaller(r)]
        out(f"  {k[0]} × {k[1]}: {len(a)} of 5 in 'C smaller'; χ² {[round(r['chi2'], 4) for r in g]}; "
            f"best {min(r['chi2'] for r in g):.4f}; σ(C) {ms([r['C']['sigma'] for r in g], 2)}; "
            f"σ(Co) {ms([r['Co']['sigma'] for r in g], 2)}; ρ(Co) {ms([r['Co']['density'] for r in g], 3)}; "
            f"top H {ms([r['top']['thickness'] for r in g], 2)}; "
            f"time {st.mean(r['elapsed_s'] for r in g):.1f} s on {g[0]['device']}")
        other = [r for r in g if not c_smaller(r)]
        if other:
            out(f"     other valley: χ² {[round(r['chi2'], 4) for r in other]}")


def table_16_3():
    out("\nTable 16-3 and the window: the five runs at each Δθ")
    for dt in WINDOW:
        g = at(dt)
        out(f"  Δθ {dt}: χ² {ms([r['chi2'] for r in g], 4)}; best {min(r['chi2'] for r in g):.4f}; "
            f"{sum(c_smaller(r) for r in g)} of 5 in 'C smaller'")
    g = at(0.014)
    best = min(g, key=lambda r: r["chi2"])
    out(f"\n  Δθ 0.014 runs:")
    for r in g:
        out(f"    seed {r['seed']}: χ² {r['chi2']:.4f}  C H {r['C']['thickness']:.2f} σ {r['C']['sigma']:.2f} "
            f"ρ {r['C']['density']:.3f} | Co H {r['Co']['thickness']:.2f} σ {r['Co']['sigma']:.2f} "
            f"ρ {r['Co']['density']:.3f} | top H {r['top']['thickness']:.2f} σ {r['top']['sigma']:.3f} "
            f"ρ {r['top']['density']:.3f} | scale {r['scale_ratio']}")
    out(f"  best run: seed {best['seed']}, χ² {best['chi2']:.4f}")
    for lay in ("C", "Co", "top"):
        for q, nd in (("thickness", 2), ("sigma", 2), ("density", 3)):
            xs = [r[lay][q] for r in g]
            out(f"    {lay} {q}: best {best[lay][q]:.{nd}f}, sd {st.stdev(xs):.{nd}f}, "
                f"range {min(xs):.{nd}f}–{max(xs):.{nd}f}")
    out(f"    χ²: best {best['chi2']:.4f}, sd {st.stdev([r['chi2'] for r in g]):.4f}")
    out(f"    period C + Co: {[round(r['C']['thickness'] + r['Co']['thickness'], 3) for r in g]}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    setup()
    figure_16_1()
    figure_16_2()
    table_16_2()
    table_16_3()
    (SRC / "numbers.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\nwrote figures-src/ch16/numbers.txt")
