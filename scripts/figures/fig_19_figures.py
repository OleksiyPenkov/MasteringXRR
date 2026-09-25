"""Figure 19-1 of Chapter 19, and the numbers of Tables 19-3 and 19-4.

  Figure 19-1  the order ratios (calculated / measured peak) of CoC4 and CoC5
               without interlayers (the Chapter 18 fits with the period free)
               and with a CoC interlayer on each interface, under the three
               assignments: wider under C, wider under Co, and equal (the h of
               the scan with the lowest χ²); five runs each; the band
               0.75-1.25 shaded

The runs are made by ch19_engine_data.py; their reports already use the solved
scale (engine d8ee5e1), so the ratio is r_calc / i_meas as reported.

Run:  python scripts/figures/fig_19_figures.py   (after ch19_engine_data.py)
Out:  public/figures/fig-19-1-interlayer-test.svg; the summary on stdout and in
      figures-src/ch19/summary.txt
"""
import json
import statistics as st
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fig_18_figures import ACCENT, BAND, GREEN, MUTED, ORANGE, STROKE, clean, setup  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
S18 = ROOT / "figures-src" / "ch18"
S19 = ROOT / "figures-src" / "ch19"
OUT = ROOT / "public" / "figures"
PURPLE = "#6c3483"


def load(p):
    return json.loads(p.read_text(encoding="utf-8"))


def ratio(o):
    return o["r_calc"] / o["i_meas"]


def cases(name):
    """(label, color, runs) for the fit without interlayers and each assignment."""
    base = sorted(load(S18 / f"{name}-free.json")["runs"], key=lambda r: r["chi2"])
    inter = load(S19 / f"{name}-inter.json")
    eq = {k: v for k, v in inter.items() if k.startswith("equal-")}
    best_eq = min(eq, key=lambda k: min(r["chi2"] for r in eq[k]["runs"]))
    out = [("no interlayer", MUTED, base),
           ("wider under C", ACCENT, sorted(inter["upper"]["runs"], key=lambda r: r["chi2"])),
           ("wider under Co", ORANGE, sorted(inter["lower"]["runs"], key=lambda r: r["chi2"])),
           (f"equal, {best_eq.split('-')[1]} Å", GREEN, sorted(eq[best_eq]["runs"], key=lambda r: r["chi2"]))]
    return out, eq


def panel(ax, groups, title):
    ax.axhspan(0.75, 1.25, color=BAND, lw=0)
    ax.axhline(1.0, color=MUTED, lw=0.6)
    offs = np.linspace(-0.27, 0.27, len(groups))
    nmax = 1
    for (label, col, runs), off in zip(groups, offs):
        for i, r in enumerate(runs):
            vis = [o for o in r["orders"] if o["visible"]]
            nmax = max(nmax, max(o["n"] for o in vis))
            ax.plot(np.array([o["n"] for o in vis]) + off, [ratio(o) for o in vis], "o",
                    ms=4 if i == 0 else 2.8, color=col, alpha=1 if i == 0 else 0.45, mec="none",
                    label=label if i == 0 else None)
    ax.set_xticks(range(1, nmax + 1))
    ax.set_xlim(0.5, nmax + 0.5)
    ax.set_ylim(0, 1.6)
    ax.set_title(title, fontsize=9, color=STROKE, loc="left")
    ax.set_xlabel("order")
    clean(ax)


def figure():
    setup()
    fig, axes = plt.subplots(1, 2, figsize=(5.35, 2.9), gridspec_kw={"width_ratios": [8, 4.6]})
    g4, _ = cases("coc4")
    g5, _ = cases("coc5")
    panel(axes[0], g4, "CoC4")
    panel(axes[1], g5, "CoC5")
    axes[0].set_ylabel("calculated / measured")
    h, l = axes[0].get_legend_handles_labels()
    l = [x.split(",")[0] if x.startswith("equal") else x for x in l]
    fig.legend(h, l, frameon=False, fontsize=8, loc="upper center", ncol=4)
    fig.tight_layout(rect=(0, 0, 1, 0.88))
    fig.savefig(OUT / "fig-19-1-interlayer-test.svg", format="svg", metadata={
        "Title": "Figure 19-1: the order table with and without interlayers",
        "Description": "Fits by the X-Ray Calc 3.9.4.1250 and 3.9.4.1270 engines; measured CoC4 and CoC5 from the "
                       "fitting procedure's deposit (CC BY 4.0). Script: scripts/figures/fig_19_figures.py"})


def sd(v):
    return st.stdev(v) if len(v) > 1 else 0.0


def summary():
    lines = []
    p = lines.append
    for name, weak in (("coc4", (7, 8)), ("coc5", (4,))):
        groups, eq = cases(name)
        p(f"===== {name}")
        for label, _, runs in groups:
            c = [r["chi2"] for r in runs]
            w = {n: [ratio(o) for r in runs for o in r["orders"] if o["n"] == n and o["visible"]] for n in weak}
            other = sorted({o["n"] for r in runs for o in r["orders"]
                            if o["visible"] and o["n"] not in weak and abs(ratio(o) - 1) > 0.25})
            nfail = {n: sum(1 for r in runs for o in r["orders"] if o["n"] == n and o["visible"]
                            and abs(ratio(o) - 1) > 0.25) for n in other}
            p(f"  {label:16s} χ² best {min(c):.4f} range {min(c):.4f}-{max(c):.4f} sd {sd(c):.4f} | "
              + " ".join(f"order {n}: {min(v):.2f}-{max(v):.2f}" for n, v in w.items())
              + f" | other fails (runs): {nfail}")
            if label != "no interlayer":
                best = runs[0]
                ils = [(i, L) for i, L in enumerate(best["period"])]
                p("      best: " + "; ".join(f"{L['material']} H {L['thickness']:.2f} σ {L['sigma']:.2f} ρ {L['density']:.2f}"
                                          for i, L in ils) + f" | D {best['D']:.3f}")
                for i, L in ils:
                    vals = {q: sd([r["period"][i][q] for r in runs]) for q in ("thickness", "sigma", "density")}
                    p(f"      sd {i} {L['material']:4s} H {vals['thickness']:.2f} σ {vals['sigma']:.2f} ρ {vals['density']:.2f}")
        p("  equal scan (h: best χ², range):")
        for k, v in sorted(eq.items(), key=lambda kv: float(kv[0].split('-')[1])):
            c = [r["chi2"] for r in v["runs"]]
            p(f"    {k.split('-')[1]:>3s} Å  best {min(c):.4f}  range {min(c):.4f}-{max(c):.4f}")
    f = S19 / "coc4-nosurf.json"
    if f.exists():
        runs = sorted(load(f)["runs"], key=lambda r: r["chi2"])
        base = sorted(load(S19 / "coc4-withsurf.json")["runs"], key=lambda r: r["chi2"])
        p("===== coc4 contamination layer: with (Chapter 18) against without")
        for label, rs in (("with", base), ("without", runs)):
            c = [r["chi2"] for r in rs]
            b = rs[0]
            p(f"  {label:8s} χ² {min(c):.4f}-{max(c):.4f} plain {b.get('chi2_plain')} D {b['D']:.3f} | "
              + " ".join(f"{o['n']}:{ratio(o):.2f}" for o in b["orders"] if o["visible"])
              + " | edge " + " ".join(f"{q['r_calc'] / q['i_meas']:.2f}" for q in b["edge"]["points"])
              + " | bands " + " ".join(f"{x['mean']:+.3f}" for x in b["bands"]))
            if b.get("fringes"):
                fr = b["fringes"]
                p(f"      fringes: {json.dumps({k: v for k, v in fr.items() if k != 'pairs'})[:300]}")
            per = b.get("period") or [b["C"], b["Co"]]
            p("      period: " + "; ".join(f"H {L['thickness']:.2f} σ {L['sigma']:.2f} ρ {L['density']:.2f}" for L in per)
              + (f" | top {b['top']}" if b.get("top") else ""))
    S19.mkdir(parents=True, exist_ok=True)
    (S19 / "summary.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    summary()
    figure()
