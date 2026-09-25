"""Figures 17-2, 17-4 and 17-5, Tables 17-1 and 17-2 and the numbers of Chapter 17.

  Figure 17-2  the Chapter 3 demo (Data 1.dat, calculated from a stack whose Si
               thickness drifts) against the best one-period fit with the
               period free (every box ticked), on 2θ; the order ratios are the
               engine's order table
  Figure 17-4  the demo's period through the stack: the true one (Target's
               gradient), five runs of order 1 and five of order 3
  Figure 17-5  CoC4 and CoC5: the period through the stack, five runs of order 1
               and five of order 3, with the one-period fit's period
  Table 17-1   CoC4 and CoC5: the period held, the period free, order 1 and 3
  Table 17-2   the drift test of the procedure (§9.7) and the order test (§9.8)

The period of period k is the sum of the C and Co (Si and Mo) thicknesses in
period k; k = 1 is the top period. The drift is the bottom period minus the
top period (substrate end minus surface end).

Run:  python scripts/figures/fig_17_figures.py   (after ch17_engine_data.py)
Out:  public/figures/fig-17-2-demo-orders.svg, fig-17-4-demo-drift.svg,
      fig-17-5-coc-drift.svg, figures-src/ch17/numbers.txt
"""
import json
import statistics as st
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import local_paths

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "figures-src" / "ch17"
OUT = ROOT / "public" / "figures"

STROKE = "#334155"
ACCENT = "#1a5276"
MUTED = "#94a3b8"
ORANGE = "#b9770e"
GREEN = "#1e8449"

MODE_NAME = {"periodic": "Periodic, period held", "pairedall": "every box ticked (period free)",
             "poly1": "Polynomial, order 1", "poly3": "Polynomial, order 3"}

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


def sd(xs):
    return st.stdev(xs) if len(xs) > 1 else 0.0


def periods(r, n):
    c = np.array(r["C"].get("thickness_profile", [r["C"]["thickness"]] * n))
    co = np.array(r["Co"].get("thickness_profile", [r["Co"]["thickness"]] * n))
    return c + co


def truth_demo():
    k = np.arange(1, 31)
    si = 25 + 0.14 * (k - 1) + 0.012 * (k - 1) ** 2 - 0.0005 * (k - 1) ** 3
    return k, si + 15.0


def summary(label, runs, n):
    out(f"\n{label}")
    for mode in ("periodic", "pairedall", "poly1", "poly3"):
        g = [r for r in runs if r["mode"] == mode]
        if not g:
            continue
        best = min(g, key=lambda r: r["chi2"])
        ch = [r["chi2"] for r in g]
        dr = [r["drift"] for r in g]
        out(f"  {MODE_NAME[mode]}: χ² {[round(x, 4) for x in ch]}  best {best['chi2']:.4f} (seed {best['seed']})"
            f"  χ² sd {sd(ch):.4f}")
        out(f"     D mean over the stack {[round(r['D'], 3) for r in g]}")
        if mode.startswith("poly"):
            out(f"     drift {[round(x, 3) for x in dr]}  best-run drift {best['drift']:+.3f}  sd {sd(dr):.3f}"
                f"  2 sd {2 * sd(dr):.3f}  → {'drift reported' if abs(best['drift']) > 2 * sd(dr) else 'uniform'}")
            p = periods(best, n)
            out(f"     best run: top D {p[0]:.3f}, bottom D {p[-1]:.3f}, min {p.min():.3f}, max {p.max():.3f}")
        for r in g:
            out(f"     seed {r['seed']}: χ² {r['chi2']:.4f}  C H {r['C']['thickness']:.2f} σ {r['C']['sigma']:.2f} "
                f"ρ {r['C']['density']:.3f} | Co H {r['Co']['thickness']:.2f} σ {r['Co']['sigma']:.2f} "
                f"ρ {r['Co']['density']:.3f} | top H {r['top']['thickness']:.2f} σ {r['top']['sigma']:.2f} "
                f"ρ {r['top']['density']:.3f} | nb {[(x['stack'], x['layer'], x['parameter'], x['bound'], round(x['margin_fraction'], 3)) for x in (r['near_bounds'] or [])]}")
        out(f"     order ratios (best run) {[(o['n'], round(o['ratio'], 2)) for o in (best['orders'] or []) if o.get('visible')]}")
    p1 = [r for r in runs if r["mode"] == "poly1"]
    p3 = [r for r in runs if r["mode"] == "poly3"]
    if p1 and p3:
        b1, b3 = min(r["chi2"] for r in p1), min(r["chi2"] for r in p3)
        m = 2 * sd([r["chi2"] for r in p1])
        out(f"  order test (§9.8): order-1 best {b1:.4f} − order-3 best {b3:.4f} = {b1 - b3:.4f}"
            f" against 2 × order-1 χ² sd = {m:.4f} → {'order 3 passes the χ² margin' if b1 - b3 > m else 'order 1 stays'}")


def figure_17_2(demo):
    d = np.loadtxt(ROOT / "figures-src" / "ch17" / "demo-curves.dat", comments="#", skiprows=2)
    best = min((r for r in demo["runs"] if r["mode"] == "pairedall"), key=lambda r: r["chi2"])
    import zipfile
    z = zipfile.ZipFile(local_paths.deploy("Examples", "ML(30x2)P3_Best.xrcx"))
    name = next(n for n in z.namelist() if n.startswith("data_"))
    rows = [ln.split("\t") for ln in z.read(name).decode("utf-8-sig").splitlines()[2:] if ln.strip()]
    m = np.array([[float(a), float(b)] for a, b in rows])
    fig, ax = plt.subplots(figsize=(5.35, 2.9))
    ax.plot(m[:, 0], m[:, 1], color=MUTED, lw=1.4, label="demo curve (Data 1.dat)")
    ax.plot(2 * d[:, 0], d[:, 1] / best["scale_ratio"], color=ORANGE, lw=0.8,
            label=f"one-period fit, D = {best['D']:.2f} Å")
    for o in best["orders"]:
        if o.get("visible"):
            x = 2 * o["theta_calc_deg"]
            ax.annotate(f"{o['ratio']:.2f}", (x, o["r_calc"]), xytext=(0, 5), textcoords="offset points",
                        ha="center", fontsize=8, color=ORANGE)
    ax.set_yscale("log")
    ax.set_xlim(0, 12)
    ax.set_ylim(1e-8, 2)
    ax.set_xlabel("2θ (°)")
    ax.set_ylabel("R")
    ax.legend(frameon=False, fontsize=8, loc="upper right")
    clean(ax)
    fig.tight_layout()
    fig.savefig(OUT / "fig-17-2-demo-orders.svg", format="svg", metadata={
        "Title": "Figure 17-2: the demo curve against a one-period fit",
        "Description": "Chapter 3 demo (X-Ray Calc example project) and a fit by the X-Ray Calc "
                       "3.9.4.1250 engine. Script: scripts/figures/fig_17_figures.py"})
    out(f"\nFigure 17-2: one-period fit seed {best['seed']}, χ² {best['chi2']:.4f}, D {best['D']:.3f}, "
        f"scale ratio {best['scale_ratio']}")


def profile_panel(ax, runs, n, title, extra=None):
    k = np.arange(1, n + 1)
    for mode, col, lab in (("poly1", ACCENT, "order 1"), ("poly3", ORANGE, "order 3")):
        g = sorted((r for r in runs if r["mode"] == mode), key=lambda r: r["chi2"])
        for i, r in enumerate(g):
            ax.plot(k, periods(r, n), color=col, lw=1.6 if i == 0 else 0.7, alpha=1 if i == 0 else 0.55,
                    label=f"{lab}, five runs" if i == 0 else None)
    g = [r for r in runs if r["mode"] == "pairedall"]
    if g:
        b = min(g, key=lambda r: r["chi2"])
        ax.axhline(b["D"], color=MUTED, lw=1.0, ls="--", label="one period, period free")
    if extra is not None:
        ax.plot(*extra, color=GREEN, lw=2.2, ls=":", label="the true period")
    ax.set_title(title, fontsize=9, color=STROKE, loc="left")
    ax.set_xlabel("period (1 = top)")
    ax.set_xlim(1, n)
    clean(ax)


def figure_17_3(demo):
    fig, ax = plt.subplots(figsize=(5.35, 2.9))
    profile_panel(ax, demo["runs"], 30, "the Chapter 3 demo", truth_demo())
    ax.set_ylabel("period D (Å)")
    ax.legend(frameon=False, fontsize=8, loc="lower center")
    fig.tight_layout()
    fig.savefig(OUT / "fig-17-4-demo-drift.svg", format="svg", metadata={
        "Title": "Figure 17-4: the period of the demo stack, period by period",
        "Description": "Fits by the X-Ray Calc 3.9.4.1250 engine. Script: scripts/figures/fig_17_figures.py"})


def figure_17_4(c4, c5):
    fig, axes = plt.subplots(1, 2, figsize=(5.35, 3.1), sharey=False)
    profile_panel(axes[0], c4["runs"], 20, "CoC4")
    profile_panel(axes[1], c5["runs"], 20, "CoC5")
    axes[0].set_ylabel("period D (Å)")
    fig.legend(*axes[0].get_legend_handles_labels(), frameon=False, fontsize=8, loc="upper center",
               ncol=3, bbox_to_anchor=(0.5, 1.0))
    fig.tight_layout(rect=(0, 0, 1, 0.88))
    fig.savefig(OUT / "fig-17-5-coc-drift.svg", format="svg", metadata={
        "Title": "Figure 17-5: the period of CoC4 and CoC5, period by period",
        "Description": "Fits of measured CoC4 and CoC5 (deposit, CC BY 4.0) by the X-Ray Calc "
                       "3.9.4.1250 engine. Script: scripts/figures/fig_17_figures.py"})


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    setup()
    OUT.mkdir(parents=True, exist_ok=True)
    demo = load("demo.json")
    c4, c5 = load("coc4-final.json"), load("coc5-final.json")
    for name, d in (("CoC4", c4), ("CoC5", c5)):
        out(f"{name}: Δθ {d['request']['resolution']}, widening {json.dumps(d['widening'])}")
        out(f"  final bounds {json.dumps(d['request']['bounds'])}")
    summary("CoC4 (final limits)", c4["runs"], 20)
    summary("CoC5 (final limits)", c5["runs"], 20)
    summary("Demo (the demo's own limits)", demo["runs"], 30)
    k, t = truth_demo()
    out(f"  demo truth: top D {t[0]:.2f}, bottom D {t[-1]:.2f}, max {t.max():.2f} at period {k[t.argmax()]}, "
        f"mean {t.mean():.3f}, drift {t[-1] - t[0]:+.3f}")
    figure_17_2(demo)
    figure_17_3(demo)
    figure_17_4(c4, c5)
    (SRC / "numbers.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\nwrote figures-src/ch17/numbers.txt")
