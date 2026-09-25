"""Table 3-1: the numbers of the two demo fits, recomputed from the saved projects.

figures-src/fits/ch3-run1.xrcx and ch3-run2.xrcx are the demo ML(30x2)P3_Best.xrcx
(as corrected by the author on 2026-09-23) after one fit each, X-Ray Calc
3.9.3.1010 x64, 5000 x 200, saved with File > Save project. chi2 and the fitting
times are not in the file; they were read off the screen (Table 3-1 notes).

How a profile is stored (X-Ray Calc source, confirmed by the X-Ray Calc code
session on 2026-09-23):
- A function (gradient) extension is a polynomial in the period index k, with
  k = 1 the TOP period (surface end):
      value(k) = C0 + C1 (k-1) + C2 (k-1)^2 + C3 (k-1)^3 + ...
  Shared/Math/math_globals.pas:80-91; applied in unit_materials.pas:237-247.
- C0 is not stored in the extension. It is the value in the layer's own field
  (frame_ProjectPanel.pas:1702), so the H field shows the TOP period.
- The extension record stores Order and C1..C_Order as float32
  (unit_XRCProjectTree.pas:515-538, 662-668). Here they are found after the
  UTF-16 name, 30 bytes on, behind an int32 count.
- Target's "Gradient 1" grades Main/Si thickness; For fit's "F(H Main/Si)" is the
  profile Polynomial mode fitted. Nothing else is graded.

Run:  python scripts/figures/ch3_table.py
"""
import json
import re
import struct
import zipfile
from pathlib import Path

FITS = Path(__file__).resolve().parents[2] / "figures-src" / "fits"
N = 30  # periods of the Main stack


def coefficients(dsc: bytes, name: str) -> list[float]:
    raw = name.encode("utf-16-le")
    i = dsc.find(raw)
    if i < 0:
        raise SystemExit(f"extension {name!r} not found")
    c = i + len(raw) + 30
    n = struct.unpack("<i", dsc[c - 4:c])[0]
    return [struct.unpack("<f", dsc[c + 4 * j:c + 4 * j + 4])[0] for j in range(n)]


def models(dsc: bytes) -> list[dict]:
    found = []
    for off in (0, 1):  # the model JSONs sit at either byte alignment
        text = dsc[off:].decode("utf-16-le", "replace")
        for m in re.finditer(r'\{"Stacks".*?"Subs":\{[^}]*\}\}', text):
            found.append((off + 2 * m.start(), json.loads(m.group(0))))
    return [d for _, d in sorted(found, key=lambda t: t[0])]


def profile(c0: float, c: list[float]) -> list[float]:
    return [c0 + sum(cj * (k - 1) ** (j + 1) for j, cj in enumerate(c)) for k in range(1, N + 1)]


def layers(model: dict) -> dict:
    return {(st["T"], L["M"]): L for st in model["Stacks"] for L in st["Layers"]}


def main():
    for run in ("ch3-run1", "ch3-run2"):
        dsc = zipfile.ZipFile(FITS / f"{run}.xrcx").read("project.dsc")
        target, fit = [m for m in models(dsc) if m["Stacks"][0]["Layers"][0]["Hmax"] == 0][0], \
                      [m for m in models(dsc) if m["Stacks"][0]["Layers"][0]["Hmax"] != 0][0]
        T, F = layers(target), layers(fit)
        pt = profile(T[("Main", "Si")]["H"], coefficients(dsc, "Gradient 1"))
        pf = profile(F[("Main", "Si")]["H"], coefficients(dsc, "F(H Main/Si)"))
        mo_t, mo_f = T[("Main", "Mo")]["H"], F[("Main", "Mo")]["H"]
        print(f"== {run}")
        for key, lbl in ((("Top", "Si"), "Top Si"), (("Main", "Si"), "Si"), (("Main", "Mo"), "Mo")):
            f, t = F[key], T[key]
            print(f"  {lbl:7s} H {f['H']:6.2f} ({t['H']})  sigma {f['s']:.2f} ({t['s']})  rho {f['r']:.2f} ({t['r']:.2f})")
        for k in (1, 21, 30):
            print(f"  Si H, period {k:2d}: fit {pf[k-1]:.2f}  target {pt[k-1]:.2f}")
        print(f"  Si H, mean: fit {sum(pf)/N:.2f}  target {sum(pt)/N:.2f};"
              f" largest difference {max(abs(a - b) for a, b in zip(pf, pt)):.2f}")
        print(f"  period, mean: fit {sum(pf)/N + mo_f:.2f}  target {sum(pt)/N + mo_t:.2f};"
              f" top period: fit {pf[0] + mo_f:.2f}  target {pt[0] + mo_t:.2f}")


if __name__ == "__main__":
    main()
