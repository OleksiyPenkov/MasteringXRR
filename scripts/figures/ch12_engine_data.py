"""Chapter 12: the CoC4 starting model, calculated.

The command-line server that ships with X-Ray Calc (XRC_MCP.exe in the build
folder, engine 3.9.4), driven through xrc_engine.Engine. The book never names
the server. The measured curve is the one Chapter 11 imported
(figures-src/ch11/curve-measured.dat).

The starting model is the one the chapter builds, in the GUI's words:
  Top   N = 1    C  15 Å, σ 3 Å, ρ 0.9 g/cm³     (one laboratory's contamination layer)
  ML    N = 20   C  31.40 Å, σ 4 Å, ρ 2.0 g/cm³  (design 31 Å scaled to D = 54.70 Å)
                 Co 23.30 Å, σ 4 Å, ρ 8.0 g/cm³  (design 23 Å scaled the same)
  Substrate      SiO2, σ 3.8 Å, ρ 2.50 g/cm³     (one laboratory's soda-lime glass)
The server's JSON lists stacks from the substrate up (the GUI lists them from the surface
down); the layers inside a stack are surface first in both.

  curve-start.dat       the starting model, λ = 1.541874 Å, Δθ = 0.012°, θ = 0.001-7.4°
  curve-start-bare.dat  the same without the contamination layer

Run:  python scripts/figures/ch12_engine_data.py
Out:  figures-src/ch12/
"""
import json
import shutil
from pathlib import Path

from xrc_engine import Engine

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "figures-src" / "ch12"
LAMBDA = 1.541874   # Å, the CoC4 file's wavelength (Chapter 10)
DTHETA = 0.012      # °, one laboratory's starting resolution (preset instrument.resolution_deg.start)

ML = {"N": 20, "layers": [{"material": "C", "thickness": 31.40, "sigma": 4.0, "density": 2.0},
                          {"material": "Co", "thickness": 23.30, "sigma": 4.0, "density": 8.0}]}
TOP = {"N": 1, "layers": [{"material": "C", "thickness": 15.0, "sigma": 3.0, "density": 0.9}]}
SUBS = {"material": "SiO2", "sigma": 3.8, "density": 2.50}
START = {"substrate": SUBS, "stacks": [ML, TOP]}      # substrate up: ML, then the top layer
BARE = {"substrate": SUBS, "stacks": [ML]}


def main():
    e = Engine()
    try:
        OUT.mkdir(parents=True, exist_ok=True)
        for name, s in (("curve-start.dat", START), ("curve-start-bare.dat", BARE)):
            c = e.call("calc_reflectivity", {"structure": s, "lambda": LAMBDA, "theta_min": 0.001,
                                             "theta_max": 7.4, "points": 7400, "delta_theta": DTHETA,
                                             "polarization": "s", "r_min": 1e-12,
                                             "max_inline_points": 0})
            shutil.copyfile(e.work / c["file"], OUT / name)
        (OUT / "start-model.json").write_text(json.dumps(START, indent=1), encoding="utf-8")
        srv = e.describe()
        print(f"engine: X-Ray Calc {srv['xraycalc3_exe_version']}, git {srv['git_revision']}")
    finally:
        e.close()


if __name__ == "__main__":
    main()
