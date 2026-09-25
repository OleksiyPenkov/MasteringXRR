"""Figure 20-1 of Chapter 20, and the numbers of Table 20-1.

  Figure 20-1  the fitted Co density of CoC4 and CoC5 under each model the book
               fitted, five runs each (the run with the lowest χ² large, the
               others small), with the bulk density of the Co table (8.79 g/cm³)
               as a line: the runs of one model agree to 0.01-0.1 g/cm³, the
               models differ by up to 0.7 g/cm³

No new fits. The runs:
  period held          figures-src/ch17/<curve>-final.json, mode periodic
  period free          figures-src/ch18/<curve>-free.json
  Polynomial 1, 3      figures-src/ch17/<curve>-final.json, modes poly1, poly3
  no contamination     figures-src/ch19/coc4-nosurf.json (CoC4 only)
  interlayers          figures-src/ch19/<curve>-inter.json: upper, lower, equal-4

Run:  python scripts/figures/fig_20_figures.py
Out:  public/figures/fig-20-1-co-density.svg; figures-src/ch20/numbers.txt
"""
import json
import statistics as st
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fig_18_figures import ACCENT, MUTED, ORANGE, STROKE, clean, setup  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
FS = ROOT / "figures-src"
OUT = ROOT / "public" / "figures"
BULK_CO = 8.79          # Nro of Henke/Co.bin


def load(p):
    return json.loads(p.read_text(encoding="utf-8"))


def two_layer(runs, key):
    return [(r["chi2"], r[key]["density"], r["C" if key == "Co" else key]["density"]) for r in runs]


def models(name):
    """(label, [(χ², ρ Co, ρ C), ...]) in the order of the figure."""
    f17 = load(FS / "ch17" / f"{name}-final.json")["runs"]
    out = [("period held", [(r["chi2"], r["Co"]["density"], r["C"]["density"]) for r in f17 if r["mode"] == "periodic"]),
           ("period free", [(r["chi2"], r["Co"]["density"], r["C"]["density"])
                            for r in load(FS / "ch18" / f"{name}-free.json")["runs"]]),
           ("Polynomial 1", [(r["chi2"], r["Co"]["density"], r["C"]["density"]) for r in f17 if r["mode"] == "poly1"]),
           ("Polynomial 3", [(r["chi2"], r["Co"]["density"], r["C"]["density"]) for r in f17 if r["mode"] == "poly3"])]
    if name == "coc4":
        out.append(("no surface layer",
                    [(r["chi2"], r["period"][1]["density"], r["period"][0]["density"])
                     for r in load(FS / "ch19" / "coc4-nosurf.json")["runs"]]))
    inter = load(FS / "ch19" / f"{name}-inter.json")
    for k, lab in (("upper", "interlayer under C"), ("lower", "interlayer under Co"),
                   ("equal-4", "interlayers equal")):
        out.append((lab, [(r["chi2"], r["period"][2]["density"], r["period"][0]["density"]) for r in inter[k]["runs"]]))
    return out


def figure():
    setup()
    fig, axes = plt.subplots(1, 2, figsize=(5.35, 3.4), sharey=True)
    for ax, name, title in ((axes[0], "coc4", "CoC4"), (axes[1], "coc5", "CoC5")):
        ms = models(name)
        ax.axhline(BULK_CO, color=MUTED, lw=0.8, ls="--")
        for i, (lab, runs) in enumerate(ms):
            runs = sorted(runs)
            col = ORANGE if lab.startswith("interlayer") else ACCENT
            ax.plot([i] * (len(runs) - 1), [r[1] for r in runs[1:]], "o", ms=3, color=col, alpha=0.45, mec="none")
            ax.plot([i], [runs[0][1]], "o", ms=5, color=col, mec="none")
        ax.set_xticks(range(len(ms)))
        ax.set_xticklabels([m[0] for m in ms], rotation=60, ha="right", fontsize=8)
        ax.set_title(title, fontsize=9, color=STROKE, loc="left")
        clean(ax)
    axes[0].set_ylabel("fitted Co density (g/cm³)")
    axes[0].set_ylim(5.8, 9.0)
    axes[1].text(len(models("coc5")) - 0.6, BULK_CO - 0.05, "bulk 8.79", ha="right", va="top",
                 fontsize=8, color=MUTED)
    fig.tight_layout()
    fig.savefig(OUT / "fig-20-1-co-density.svg", format="svg", metadata={
        "Title": "Figure 20-1: the fitted Co density under each model",
        "Description": "Fits by the X-Ray Calc 3.9.4.1250 and 3.9.4.1270 engines (Chapters 17-19); measured CoC4 and CoC5 "
                       "from the fitting procedure's deposit (CC BY 4.0). Script: scripts/figures/fig_20_figures.py"})


def numbers():
    lines = []
    for name in ("coc4", "coc5"):
        lines.append(f"===== {name}  (model: best-run ρCo, sd over runs, range | best-run ρC, sd | best χ²)")
        for lab, runs in models(name):
            runs = sorted(runs)
            co = [r[1] for r in runs]
            c = [r[2] for r in runs]
            lines.append(f"  {lab:28s} Co {runs[0][1]:.2f} sd {st.stdev(co):.2f} range {min(co):.2f}-{max(co):.2f} "
                         f"({runs[0][1] / BULK_CO:.2f} of bulk) | C {runs[0][2]:.2f} sd {st.stdev(c):.2f} | χ² {runs[0][0]:.4f}")
    (FS / "ch20").mkdir(parents=True, exist_ok=True)
    (FS / "ch20" / "numbers.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    numbers()
    figure()
