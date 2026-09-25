"""Chapter 9: χ² scores, χ² landscapes and seeded fits from the X-Ray Calc engine.

The command-line server that ships with X-Ray Calc (XRC_MCP.exe in the build
folder, engine 3.9.4.1250 since the rerun of 2026-09-25), driven through xrc_engine.py. The book never names
the server. Every χ² here is the engine's own TCalc.CalcChiSquare, the number the
GUI shows in the Chart Info bar.

The curve is the measured Co/C multilayer CoC5 of Chapters 1 and 6 (the fitting
procedure's deposit, curves/CoC5.csv), given to the engine in θ (the file's
2θ / 2), at λ = 1.541874 Å, the wavelength the CoC5 .xrdml implies. The settings are those of the
deposit's periodic CoC5 fit (jobs/campaign1-stage1/CoC5-round-3/
fit-20260918-222443-960a/request.json) with two changes: no smoothing (the
tested revision of paper §7.6) and Δθ = 0.009°, the expert's width for CoC5
(FIT-INDEX, author-grid-score-fit-20260918-144637-1bcc.json):
  Normalize (Auto) below θ = 0.5°, floor 8.0517e-7 (one count), fitting range
  θ = 0.20075–4.2°, PW χ² on, TW None, Solve scale in χ² on, window 0.2,
  s-polarization.
The model is the CoC5 expert fit of Chapter 6: 20 × (C 31.2135 Å, σ 4.3254,
ρ 2.0621; Co 18.8183 Å, σ 5.7386, ρ 6.2509) on SiO2, σ 3.8, ρ 2.65.

A structure is scored by a fit job of one iteration and two particles: the job
reports chi2_start, the χ² of the structure it was given, before any search.
The score does not depend on what the job is told to fit.

  scores.json    Table 9-1: the expert model under six χ² settings
  scan-D.json    χ² against the period D, both layers scaled, 20–110 Å
  scan-HC.json   χ² against the C thickness alone, Co held, 21–43 Å
  map-sigma.json χ² over σ_C × σ_Co, 1–8 Å each, the rest at the expert values
  seeds-periodic.json  eight Periodic fits, seeds 1–8, the period held at its
                 start value as in the GUI
  seeds-poly.json five Polynomial fits of order 3 with σ and ρ paired (the
                 author's default for a multilayer, paper §4), seeds 1–5
  Both start from the expert layers scaled to D = 50.23 Å (Chapter 6, the
  straight-line fit of the orders), population 5000, 200 iterations, SeedR on
  (Polynomial mode ignores it), with the deposit's bounds.

Run:  python scripts/figures/ch9_engine_data.py [scores|scans|map|seeds ...]
Out:  figures-src/ch9/*.json
"""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import local_paths  # noqa: E402
from xrc_engine import Engine  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "figures-src" / "ch9"
CURVE = local_paths.deposit("curves", "CoC5.csv")
LAMBDA = 1.541874  # Å, the Kα doublet the .xrdml implies (Chapter 10)

C = {"material": "C", "thickness": 31.2135, "sigma": 4.3254, "density": 2.0621}
CO = {"material": "Co", "thickness": 18.8183, "sigma": 5.7386, "density": 6.2509}
SUB = {"material": "SiO2", "sigma": 3.8, "density": 2.65}
D_START = 50.23  # Å, Chapter 6: the straight-line fit of the CoC5 orders

# A Periodic fit in the GUI holds the period at its start value (Help, Fitting
# Modes; unit_LFPSO_Periodic.pas), so the period is not freed here. A Polynomial
# fit lets it float.
FREE = [{"stack": 0, "layer": 0, "parameters": ["thickness", "sigma", "density"]},
        {"stack": 0, "layer": 1, "parameters": ["thickness", "sigma", "density"]}]
BOUNDS = [
    {"stack": 0, "layer": 0, "parameter": "thickness", "min": 21.33, "max": 42.67},
    {"stack": 0, "layer": 0, "parameter": "sigma", "min": 1, "max": 8},
    {"stack": 0, "layer": 0, "parameter": "density", "min": 1.5, "max": 2.4},
    {"stack": 0, "layer": 1, "parameter": "thickness", "min": 12, "max": 24},
    {"stack": 0, "layer": 1, "parameter": "sigma", "min": 1, "max": 8},
    {"stack": 0, "layer": 1, "parameter": "density", "min": 6, "max": 8.9}]


def structure(c=None, co=None):
    return {"substrate": SUB, "stacks": [{"N": 20, "layers": [{**C, **(c or {})}, {**CO, **(co or {})}]}]}


def base_request():
    d = np.loadtxt(CURVE, delimiter=",", skiprows=2)
    curve = [[round(t / 2, 6), i] for t, i in d if i > 0]
    return {"curve": curve, "lambda": LAMBDA, "polarization": "s", "structure": structure(),
            "free": FREE, "bounds": BOUNDS, "scale": "auto", "auto_theta_max": 0.5,
            "r_min": 8.0517e-7, "theta_range": {"min": 0.20075, "max": 4.2}, "resolution": 0.009,
            "chi2": {"theta_weight": 0, "point_weight": True}, "points_inline_max": 0}


# Scoring needs no search space, but the job checks the start model against its
# bounds; one loosely bounded free parameter keeps every scanned structure legal.
SCORE_FREE = [{"stack": 0, "layer": 1, "parameters": ["density"]}]
SCORE_BOUNDS = [{"stack": 0, "layer": 1, "parameter": "density", "min": 0.5, "max": 20}]


def score(eng, req, st, **over):
    r = eng.fit({**req, **over, "structure": st, "free": SCORE_FREE, "bounds": SCORE_BOUNDS,
                 "optimizer": {"iterations": 1, "population": 2, "range_seed": False}, "seed": 1})
    return {"chi2": r["chi2_start"], "chi2_plain": r["chi2_start_plain"],
            "scale_ratio": r["scale_start_ratio"]}


def save(name, obj):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(json.dumps(obj, indent=1), encoding="utf-8")
    print(f"wrote {name}")


def do_scores(eng, req):
    cases = [("PW on, TW None, scale solved", {}),
             ("PW off", {"chi2": {"theta_weight": 0, "point_weight": False}}),
             ("TW sqr (θ²)", {"chi2": {"theta_weight": 1, "point_weight": True}}),
             ("TW 1/sqr (1/θ²)", {"chi2": {"theta_weight": 4, "point_weight": True}}),
             ("scale anchored", {"scale_solve": False}),
             ("PW off, TW None, scale anchored", {"chi2": {"theta_weight": 0, "point_weight": False},
                                                  "scale_solve": False})]
    rows = []
    for label, over in cases:
        s = score(eng, req, structure(), **over)
        print(label, s)
        rows.append({"case": label, "settings": over, **s})
    save("scores.json", rows)


def do_scans(eng, req):
    d0 = C["thickness"] + CO["thickness"]
    rows = []
    for d in np.arange(20.0, 110.0001, 0.1):
        f = d / d0
        rows.append({"D": round(d, 3), **score(eng, req, structure({"thickness": C["thickness"] * f},
                                                                  {"thickness": CO["thickness"] * f}))})
    save("scan-D.json", rows)
    rows = []
    for h in np.arange(21.0, 43.0001, 0.1):
        rows.append({"H_C": round(h, 2), **score(eng, req, structure({"thickness": h}))})
    save("scan-HC.json", rows)


def do_map(eng, req):
    grid = np.round(np.arange(1.0, 8.0001, 0.2), 2)
    rows = []
    for sc in grid:
        for sco in grid:
            rows.append({"sigma_C": sc, "sigma_Co": sco,
                         **score(eng, req, structure({"sigma": sc}, {"sigma": sco}))})
        print(f"σ_C = {sc}")
    save("map-sigma.json", rows)


def start_model():
    """The expert layers scaled to D = 50.23 Å, the period Chapter 6 reads from
    the CoC5 orders by the straight-line method (the procedure's §6.6 seed)."""
    f = D_START / (C["thickness"] + CO["thickness"])
    return structure({"thickness": C["thickness"] * f}, {"thickness": CO["thickness"] * f})


def layer_summary(layer):
    out = {k: layer[k] for k in ("thickness", "sigma", "density")}
    if "thickness_profile" in layer:
        out["thickness_profile"] = layer["thickness_profile"]
        out["thickness"] = float(np.mean(layer["thickness_profile"]))
    return out


def do_seeds(eng, req):
    for name, extra, seeds in [
            ("seeds-periodic.json", {}, range(1, 9)),
            ("seeds-poly.json", {"profile": True, "paired": ["sigma", "density"]}, range(1, 6))]:
        opt = {"iterations": 200, "population": 5000, "range_seed": True}
        if extra:
            opt["poly_order"] = 3
        runs = []
        for seed in seeds:
            r = eng.fit({**req, **extra, "structure": start_model(), "optimizer": opt, "seed": seed})
            c, co = (layer_summary(x) for x in r["fitted_structure"]["stacks"][0]["layers"])
            if "thickness_profile" in c:
                d = np.array(c["thickness_profile"]) + np.array(co["thickness_profile"])
                period = {"D": float(d.mean()), "D_top": float(d[0]), "D_bottom": float(d[-1])}
            else:
                period = {"D": c["thickness"] + co["thickness"]}
            run = {"seed": seed, "chi2": r["chi2"], "chi2_plain": r["chi2_plain"],
                   "scale_ratio": r["scale_ratio"], "scale_clamped": r["scale_clamped"],
                   "near_bounds": r["report"].get("near_bounds"), "device": r["device_used"],
                   "elapsed_s": r["elapsed_s"], **period, "C": c, "Co": co}
            print(name, seed, round(r["chi2"], 4), round(period["D"], 3), round(c["sigma"], 2),
                  round(co["sigma"], 2), r["scale_clamped"], run["near_bounds"])
            runs.append(run)
        save(name, {"start_D": D_START, "optimizer": r["optimizer_used"], "extra": extra, "runs": runs})


def main():
    what = sys.argv[1:] or ["scores", "scans", "map", "seeds"]
    req = base_request()
    eng = Engine()
    try:
        s = eng.describe()
        print(f"engine: X-Ray Calc {s['xraycalc3_exe_version']}, git {s['git_revision']}, GPU {s.get('gpu')}")
        for w in what:
            {"scores": do_scores, "scans": do_scans, "map": do_map, "seeds": do_seeds}[w](eng, req)
    finally:
        eng.close()


if __name__ == "__main__":
    main()
