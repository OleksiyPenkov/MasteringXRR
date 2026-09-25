"""Figures 14-1 to 14-3, Table 14-2 and the numbers of Chapter 14.

  Figure 14-1  one pass of Data > Smooth on CoC4: the Kiessig fringes between
               orders 1 and 2, and orders 5 and 6, before and after
  Figure 14-2  the fitting range: CoC4 after Normalize (Auto) with the floor,
               the predicted orders and the range; CoC5 as imported, four
               orders visible, the range running to the seventh predicted order
  Figure 14-3  the fit settings (screenshot crop)
  Table 14-2   CoC4 fitted with the scale held, solved within 0.2 and within 0.7

One pass of Data > Smooth is MovAvg(Data, 5) in unit_DataProcessing.pas,
copied here line for line: a window of 5 means six points (i − 5 .. i), their
plain mean on the linear R, written to point i − 2. So point k becomes the
mean of k − 3 .. k + 2; the first three points keep their values, and the last
three take the mean of the last six.

Figure 14-3 source: figures-src/screenshots/ch14-fit-settings-full.png, X-Ray
Calc 3.9.4.1270 x64 (the published release, run from a scratchpad copy), light
theme, 96 dpi (100 % display scale), the window set to 1620 x 900 and captured
with its DWM frame bounds (1606 x 893 pixels) while topmost. The program opened a
copy of the expert fit CoC4-expert-full-fit.xrcx (XRR-Fitting-Skill,
submission/zenodo/fits) with `-f <file> -a`, its params.dsc edited before
opening: Namx=200, Pop=5000, TWChi=0 (None), Polarisation=0 (s-type). The file
has no [SCALE] section, so Solve scale in χ² opened checked with Window 0.2, the
defaults. The fitting mode is the file's, Periodic, so the Smooth box and the
Order field are grayed out, and Free period ± is unticked.

Run:  python scripts/figures/fig_14_figures.py   (after ch14_engine_data.py)
Out:  public/figures/fig-14-1-smoothing.svg, fig-14-2-fitting-range.svg,
      fig-14-3-fit-settings.png
"""
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from PIL.PngImagePlugin import PngInfo

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "figures-src" / "ch14"
OUT = ROOT / "public" / "figures"
SHOT = ROOT / "figures-src" / "screenshots" / "ch14-fit-settings-full.png"
CROP = (992, 98, 1600, 216)        # the Fitting, Mode, scale and Advanced Settings groups

STROKE = "#334155"
ACCENT = "#1a5276"
MUTED = "#94a3b8"
ORANGE = "#b9770e"
BAND = "#e8eef4"


def setup():
    plt.rcParams.update({
        "font.family": "sans-serif", "font.size": 9, "xtick.labelsize": 9, "ytick.labelsize": 9,
        "svg.fonttype": "none", "axes.edgecolor": STROKE, "axes.labelcolor": STROKE,
        "xtick.color": STROKE, "ytick.color": STROKE,
    })


def load(name):
    return json.loads((SRC / name).read_text(encoding="utf-8"))


def curve(path):
    d = np.loadtxt(path, skiprows=1)
    return d[:, 0], d[:, 1]


def movavg(r, w=5):
    """MovAvg(Data, W) of unit_DataProcessing.pas, for W > 1."""
    n = len(r)
    out = np.empty(n)
    off = w // 2
    v = 0.0
    for i in range(w, n):
        v = r[i - w:i + 1].sum() / (w + 1)
        out[i - off] = v
    out[:off + 1] = r[:off + 1]
    out[n - 1 - off:] = v
    return out


A = load("anchor.json")
RNG = load("range.json")
TM, RM = curve(ROOT / "figures-src" / "ch11" / "curve-measured.dat")
RN = RM * A["scale"]                        # after Normalize (Auto)


def clean(ax):
    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)


def smoothing_numbers(rs):
    print("\nsmoothing, one pass of Data > Smooth (MovAvg 5):")
    t2 = TM * 2
    pred = RNG["CoC4"]["predicted"]
    for m in range(1, 9):
        c = pred[str(m)]
        s = (t2 > c - 0.1) & (t2 < c + 0.1)
        print(f"  order {m}: peak {RN[s].max():.3e} → {rs[s].max():.3e} ({rs[s].max() / RN[s].max():.2f}×)")
    # fringes between orders 1 and 2: mean depth of the minima (neighbouring max / min)
    s = (t2 > 1.9) & (t2 < 3.0)
    for lab, r in (("raw", RN), ("one pass", rs)):
        x = r[s]
        mx = [i for i in range(1, len(x) - 1) if x[i] >= x[i - 1] and x[i] >= x[i + 1]]
        mn = [i for i in range(1, len(x) - 1) if x[i] <= x[i - 1] and x[i] <= x[i + 1]]
        print(f"  fringes 2θ 1.9–3.0°, {lab}: max/min of the whole band {x.max() / x.min():.2f}; "
              f"{len(mx)} local maxima, {len(mn)} local minima")


def figure_14_1():
    rs = movavg(RN)
    smoothing_numbers(rs)
    fig, axes = plt.subplots(1, 2, figsize=(5.35, 2.6))
    for ax, (lo, hi), title in ((axes[0], (2.45, 3.05), "fringes between orders 1 and 2"),
                                (axes[1], (7.9, 9.95), "orders 5 and 6")):
        s = (TM * 2 > lo) & (TM * 2 < hi)
        ax.plot(TM[s] * 2, RN[s], color=MUTED, lw=0.8, label="measured")
        ax.plot(TM[s] * 2, rs[s], color=ACCENT, lw=1.0, label="after one pass")
        ax.set_yscale("log")
        ax.set_xlim(lo, hi)
        ax.set_title(title, fontsize=9, color=STROKE, loc="left")
        ax.set_xlabel("2θ (°)")
        clean(ax)
    axes[0].set_ylabel("R")
    fig.legend(*axes[0].get_legend_handles_labels(), frameon=False, fontsize=8, loc="upper center",
               ncol=2, bbox_to_anchor=(0.5, 1.0))
    fig.tight_layout(rect=(0, 0, 1, 0.9))
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / "fig-14-1-smoothing.svg", format="svg", metadata={
        "Title": "Figure 14-1: one pass of Data > Smooth on CoC4",
        "Description": "Measured CoC4 (deposit, CC BY 4.0) after Normalize (Auto); the pass is "
                       "MovAvg(Data, 5) of X-Ray Calc 3.9.4.1030. Script: scripts/figures/fig_14_figures.py"})


def figure_14_2():
    c4, c5 = RNG["CoC4"], RNG["CoC5"]
    t5, r5 = curve(ROOT / "figures-src" / "ch10" / "curve-measured.dat")
    one5 = 1 / (6107733 * 0.176)          # CoC5 header: peak rate and counting time (Chapter 10)
    fig, axes = plt.subplots(2, 1, figsize=(5.35, 4.6))
    panels = ((axes[0], TM * 2, RN, 0.4165, c4, A["one_count_scaled"], "CoC4 after Normalize (Auto): 8 orders visible",
               "R"),
              (axes[1], t5 * 2, r5, 0.4015, c5, one5, "CoC5 as imported: 4 orders visible", "R (imported)"))
    for ax, t, r, start, c, one, title, ylab in panels:
        ax.axvspan(start, c["end_2theta"], color=BAND, lw=0)
        ax.plot(t, r, color=MUTED, lw=0.6)
        ax.axhline(one, color=ORANGE, lw=0.8, ls="--")
        ax.set_yscale("log")
        ax.set_ylim(one / 4, 4)
        ax.set_xlim(0, 15)
        ax.set_ylabel(ylab)
        ax.set_title(title, fontsize=9, color=STROKE, loc="left")
        nvis = c["visible"]
        for m, x in c["predicted"].items():
            m = int(m)
            col = ACCENT if m <= nvis else ORANGE
            ax.plot([x, x], [one * 1.6, one * 4.5], color=col, lw=1.1)
            ax.text(x, one * 6, str(m), color=col, fontsize=8, ha="center", fontweight="bold")
        ax.axvline(c["measured_end_2theta"], color=STROKE, lw=0.6, ls=":")
        ax.text(c["end_2theta"] - 0.1, 1.2, f"range {start:.2f}–{c['end_2theta']:.2f}°",
                color=ACCENT, fontsize=8, ha="right")
        ax.text(0.2, one / 2.6, "floor: one count", color=ORANGE, fontsize=8, va="center")
        clean(ax)
    axes[1].set_xlabel("2θ (°)")
    fig.tight_layout()
    fig.savefig(OUT / "fig-14-2-fitting-range.svg", format="svg", metadata={
        "Title": "Figure 14-2: where the fitting range ends",
        "Description": "Measured CoC4 and CoC5 (deposit, CC BY 4.0); order positions from the straight line "
                       "of procedure v5 §6.6. Script: scripts/figures/fig_14_figures.py"})
    print(f"\nrange CoC4: 2θ {0.4165}–{c4['end_2theta']:.3f}° (order 8 at {c4['last_visible_2theta']}°, "
          f"spacing 8→9 {c4['spacing_8_9']:.3f}°), measured end {c4['measured_end_2theta']:.3f}°")
    p = c5["predicted"]
    print(f"range CoC5: seed D = {c5['D']:.2f} Å, 2δ̄ = {c5['two_delta']:.3e}; order 7 predicted at {p['7']:.3f}°, "
          f"8 at {p['8']:.3f}°; end {c5['end_2theta']:.3f}°, measured end {c5['measured_end_2theta']:.3f}°, "
          f"old end {c5['old_end_2theta']}°")


def figure_14_3():
    shot = Image.open(SHOT).convert("RGB")
    assert shot.size == (1606, 893), f"unexpected capture size {shot.size}"
    fig = shot.crop(CROP)
    info = PngInfo()
    info.add_text("Title", "Figure 14-3: the fit settings, with Solve scale in χ² and Window")
    info.add_text("Source", f"{SHOT.name}; X-Ray Calc 3.9.4.1270; script scripts/figures/fig_14_figures.py")
    fig.save(OUT / "fig-14-3-fit-settings.png", pnginfo=info, dpi=(96, 96))
    print(f"\nwrote fig-14-3-fit-settings.png {fig.size}")


def table_14_2():
    runs = load("fits.json")["runs"]
    print("\nTable 14-2 (mean ± sample sd over five seeds; best = lowest χ²):")
    for case in ("held", "solved 0.2", "solved 0.7"):
        rr = [r for r in runs if r["case"] == case]
        best = min(rr, key=lambda r: r["chi2"])

        def ms(f):
            v = np.array([f(r) for r in rr])
            return f"{v.mean():.3f} ± {v.std(ddof=1):.3f}"
        print(f"  {case:11s} ratio {ms(lambda r: r['scale_ratio'] or 1)}  ρC {ms(lambda r: r['C']['density'])}  "
              f"ρCo {ms(lambda r: r['Co']['density'])}  HC {ms(lambda r: r['C']['thickness'])}  "
              f"HCo {ms(lambda r: r['Co']['thickness'])}  χ² {ms(lambda r: r['chi2'])}  "
              f"clamped {[r['scale_clamped'] for r in rr].count(True)}")
        print(f"      best seed {best['seed']}: χ² {best['chi2']:.4f}, ratio {best['scale_ratio']}, "
              f"C {best['C']}, Co {best['Co']}, top {best['top']}")
        print(f"      σ pairs (C, Co): {[(round(r['C']['sigma'], 2), round(r['Co']['sigma'], 2)) for r in rr]}")
    print(f"  window 0.2 allows {1 / 1.2:.4f}–1.2; 0.7 allows {1 / 1.7:.4f}–1.7")


def main():
    setup()
    print(f"Normalize (Auto): data divided by {A['divisor']:.4f} (R_model at θ_max = {A['scale']}); "
          f"one count {A['one_count_import']:.4e} → {A['one_count_scaled']:.4e}; "
          f"start model solved ratio (window 0.7) {A['start_solved_ratio_w07']}")
    figure_14_1()
    figure_14_2()
    figure_14_3()
    table_14_2()


if __name__ == "__main__":
    main()
