"""Chapter 15: the near-bound rule on CoC4.

The command-line server that ships with X-Ray Calc (XRC_MCP.exe in the build
folder, engine 3.9.4.1250 since the rerun of 2026-09-25), driven through xrc_engine.Engine. The book never
names the server.

In every fit of Chapter 14 (figures-src/ch14/fits.json) the σ of the top
carbon layer ended at its lower limit of 1 Å. The procedure (v5 §7.5) says to
extend that bound and fit again. In the program the Widen button of the
Fitting Limits dialog does it: a value within 1 % of the range from a limit
moves that limit out by half the range, and no limit goes below zero
(unit_SmartLimits.pas, WidenAtLimit and ClampToPhysics). For the top layer's
σ, 1-10 Å becomes 0-10 Å.

Everything else is the Chapter 14 fit with the scale solved at the program's
default window of 0.2: the starting model of Chapter 12, Periodic mode with the
period held, five seeds, population 5000, 200 iterations, SeedR on, PW χ² on,
TW None, Δθ = 0.012°, no smoothing, the Chapter 14 floor and range.

  near-bound.json   the five widened fits, and the five Chapter 14 fits they
                    are compared with

Run:  python scripts/figures/ch15_engine_data.py
Out:  figures-src/ch15/
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ch14_engine_data as c14  # noqa: E402
from xrc_engine import Engine  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "figures-src" / "ch15"


def summary(layer):
    return {k: layer[k] for k in ("thickness", "sigma", "density")}


def main():
    a = c14.load(c14.OUT / "anchor.json")
    rng = c14.load(c14.OUT / "range.json")["CoC4"]
    bounds = c14.bounds()
    for b in bounds:
        if b["stack"] == 1 and b["parameter"] == "sigma":
            b["min"] = 0.0                     # Widen: 1 - 0.5 × 9 = -3.5, clamped to 0
    req = {**c14.base(round(a["one_count_scaled"], 9), rng["end_2theta"] / 2),
           "free": c14.FREE, "bounds": bounds, "scale_solve": True, "scale_solve_window": 0.2}
    opt = {"iterations": 200, "population": 5000, "range_seed": True}
    eng = Engine()
    rows = []
    try:
        s = eng.describe()
        print(f"engine: X-Ray Calc {s['xraycalc3_exe_version']}, git {s['git_revision']}")
        for seed in c14.SEEDS:
            r = eng.fit({**req, "optimizer": opt, "seed": seed})
            st = r["fitted_structure"]["stacks"]
            row = {"seed": seed, "chi2": r["chi2"], "chi2_plain": r["chi2_plain"],
                   "scale_ratio": r["scale_ratio"], "scale_clamped": r["scale_clamped"],
                   "near_bounds": r["report"].get("near_bounds"),
                   "C": summary(st[0]["layers"][0]), "Co": summary(st[0]["layers"][1]),
                   "top": summary(st[1]["layers"][0])}
            print(seed, round(r["chi2"], 4), {k: round(v, 3) for k, v in row["top"].items()},
                  round(row["C"]["density"], 3), round(row["Co"]["density"], 3), row["near_bounds"])
            rows.append(row)
    finally:
        eng.close()
    before = [r for r in c14.load(c14.OUT / "fits.json")["runs"] if r["case"] == "solved 0.2"]
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "near-bound.json").write_text(json.dumps(
        {"request": {k: v for k, v in req.items() if k != "curve"}, "optimizer": opt,
         "widened": rows, "chapter14": before}, indent=1), encoding="utf-8")
    print("wrote near-bound.json")


if __name__ == "__main__":
    main()
