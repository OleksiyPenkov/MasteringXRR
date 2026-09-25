"""Figure 15-1, Tables 15-1 and 15-2 and the numbers of Chapter 15.

  Figure 15-1  the Fitting Limits dialog with the CoC4 limits (screenshot)
  Table 15-1   what Initialize gives for CoC4 at ΔH = Δσ = Δρ = 0.25, against
               one laboratory's limits
  Table 15-2   the near-bound rule on CoC4: the Chapter 14 fits (top-layer σ
               1-10 Å) and the same fits with that limit widened to 0-10 Å

Figure 15-1 source: figures-src/screenshots/ch15-fitting-limits-full.png, X-Ray
Calc 3.9.4.1030 (the x64 build in _Out\\BIN), light theme, 96 dpi (100 %
display scale), the dialog at its designed size, captured with its DWM frame
bounds while topmost. The program opened a copy of the Chapter 12 project; the
CoC4 starting model with its limits (figures-src/ch15/coc4-limits-model.json)
was pasted into Structure > Edit as text ... and saved, and the dialog opened
with the Limits button of the structure panel (so its action button reads
Save). figures-src/screenshots/ch15-fitting-limits-initialize.png is the same
dialog after one click on Initialize with the default 0.25 in all three boxes;
Table 15-1 is checked against it.

Initialize (XRayCalc3/Forms/frm_Limits.pas, btnInitClick, X-Ray Calc commit
ec5042f): Min = V(1 - Δ), Max = V(1 + Δ), shown with two decimals; for ρ the
maximum is capped at the bulk density of the material's Henke table (the Nro
field of Henke/<material>.bin) unless V is already above it. Then ClampToPhysics and ApplyGeometryCoupling (σ Max no larger
than the layer's H or the H below), neither of which bites on CoC4.

Run:  python scripts/figures/fig_15_figures.py   (after ch15_engine_data.py)
Out:  public/figures/fig-15-1-fitting-limits.png, figures-src/ch15/numbers.txt
"""
import json
import statistics as st
import struct
from decimal import ROUND_HALF_UP, Decimal
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from PIL.PngImagePlugin import PngInfo

import local_paths

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "figures-src" / "ch15"
OUT = ROOT / "public" / "figures"
SHOT = ROOT / "figures-src" / "screenshots" / "ch15-fitting-limits-full.png"
HENKE = local_paths.deploy("Henke")

# The CoC4 starting model of Chapter 12, surface first, and one laboratory's
# limits (procedure v5 §7.2-7.3 and the preset; the thicknesses 2/3 and 4/3 of
# the start, as in Chapter 14).
LAYERS = [  # (stack, material, H, σ, ρ, lab limits H, σ, ρ)
    ("Top", "C", 15.0, 3.0, 0.9, (5, 40), (1, 10), (0.6, 1.4)),
    ("ML", "C", 31.4, 4.0, 2.0, (20.93, 41.87), (1, 8), (1.5, 2.4)),
    ("ML", "Co", 23.3, 4.0, 8.0, (15.53, 31.07), (1, 8), (6.0, 8.79)),
]
DELTA = 0.25

lines = []


def out(s=""):
    print(s)
    lines.append(s)


def bulk(material):
    b = (HENKE / f"{material}.bin").read_bytes()
    n = struct.unpack("<i", b[:4])[0]
    _na, nro = struct.unpack("<ff", b[4 + n:12 + n])
    return float(np.float32(nro))


# The cells of the capture after Initialize (ch15-fitting-limits-initialize.png).
SCREEN = {("Top", "C"): ("11.25", "18.75", "2.25", "3.75", "0.67", "1.12"),
          ("ML", "C"): ("23.55", "39.25", "3.00", "5.00", "1.50", "2.27"),
          ("ML", "Co"): ("17.47", "29.13", "3.00", "5.00", "6.00", "8.79")}


def two_dec(x):
    """FloatToStrF(x, ffFixed, 5, 2): two decimals, a half rounded up."""
    return str(Decimal(float(x)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def init_window(centre, d):
    """Convert() of btnInitClick: Val := Inp + Inp * D, all single."""
    c, d = np.float32(centre), np.float32(d)
    return (two_dec(np.float32(c + c * -d)), two_dec(np.float32(c + c * d)))


def init_rho(v, d, bulk):
    """ρ in btnInitClick since ec5042f: Min = V(1 − Δρ), Max = max(V, min(V(1 + Δρ), bulk))."""
    v, d, b = np.float32(v), np.float32(d), np.float32(bulk)
    # the product is evaluated in double (Delphi's Single * Single), then compared with the single bulk
    return (two_dec(np.float32(v + v * -d)), two_dec(max(float(v), min(float(v) * float(np.float32(1) + d), float(b)))))


def figure_15_1():
    shot = Image.open(SHOT).convert("RGB")
    assert shot.size == (698, 508), f"unexpected capture size {shot.size}"
    info = PngInfo()
    info.add_text("Title", "Figure 15-1: the Fitting Limits dialog with the CoC4 limits")
    info.add_text("Source", f"{SHOT.name}; X-Ray Calc 3.9.4.1030; script scripts/figures/fig_15_figures.py")
    shot.save(OUT / "fig-15-1-fitting-limits.png", pnginfo=info, dpi=(96, 96))
    out(f"wrote fig-15-1-fitting-limits.png {shot.size}")


def table_15_1():
    out("\nTable 15-1: Initialize at Δ = 0.25 against the laboratory's limits")
    for stack, m, h, s, r, lh, ls, lr in LAYERS:
        rb = bulk(m)
        ih, is_, ir = init_window(h, DELTA), init_window(s, DELTA), init_rho(r, DELTA, rb)
        assert ih + is_ + ir == SCREEN[(stack, m)], (ih + is_ + ir, SCREEN[(stack, m)])
        out(f"  {stack}/{m}: start H {h} σ {s} ρ {r}; Henke bulk {rb:.3f}")
        out(f"    Initialize  H {ih[0]}–{ih[1]}  σ {is_[0]}–{is_[1]}  ρ {ir[0]}–{ir[1]}"
            f"{'  (ρ start outside)' if not float(ir[0]) <= r <= float(ir[1]) else ''}")
        out(f"    laboratory  H {lh[0]}–{lh[1]}  σ {ls[0]}–{ls[1]}  ρ {lr[0]}–{lr[1]}")
        out(f"    ρ Max / bulk: Initialize {float(ir[1]) / rb:.3f}, laboratory {lr[1] / rb:.3f}")


def ms(xs, nd):
    return f"{st.mean(xs):.{nd}f} ± {st.stdev(xs):.{nd}f}"


def table_15_2():
    d = json.loads((SRC / "near-bound.json").read_text(encoding="utf-8"))
    out("\nTable 15-2: mean ± sample sd over five seeds")
    for name, rows in (("Chapter 14, top σ 1–10 Å", d["chapter14"]), ("widened, top σ 0–10 Å", d["widened"])):
        top = [r["top"] for r in rows]
        C = [r["C"] for r in rows]
        Co = [r["Co"] for r in rows]
        out(f"  {name}")
        out(f"    top σ {ms([t['sigma'] for t in top], 3)}  (min {min(t['sigma'] for t in top):.4f}, "
            f"max {max(t['sigma'] for t in top):.4f})")
        out(f"    top H {ms([t['thickness'] for t in top], 2)}  top ρ {ms([t['density'] for t in top], 3)}")
        out(f"    C  H {ms([c['thickness'] for c in C], 2)}  σ {ms([c['sigma'] for c in C], 2)}  ρ {ms([c['density'] for c in C], 3)}")
        out(f"    Co H {ms([c['thickness'] for c in Co], 2)}  σ {ms([c['sigma'] for c in Co], 2)}  ρ {ms([c['density'] for c in Co], 3)}")
        out(f"    scale {ms([r['scale_ratio'] for r in rows], 3)}  χ² {ms([r['chi2'] for r in rows], 3)}"
            f"  (min {min(r['chi2'] for r in rows):.4f}, max {max(r['chi2'] for r in rows):.4f})")
        out(f"    near bounds: {[(b['parameter'], b['bound'], round(b['value'], 4)) for r in rows for b in r['near_bounds'] or []]}")
    # the near-bound margin, in the procedure's terms (5 % of the range)
    w = d["widened"]
    out(f"\n  widened: top σ as a fraction of its 0–10 Å range: "
        f"{max(r['top']['sigma'] for r in w) / 10:.4f} at most (rule: 0.05)")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    figure_15_1()
    table_15_1()
    table_15_2()
    (SRC / "numbers.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\nwrote figures-src/ch15/numbers.txt")
