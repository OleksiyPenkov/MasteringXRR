"""Chapter 14: the scale, the floor, the fitting range and the solved scale for CoC4.

The command-line server that ships with X-Ray Calc (XRC_MCP.exe in the build
folder, engine 3.9.4.1250 since the rerun of 2026-09-25), driven through xrc_engine.Engine. The book never
names the server. Its "scale": "auto" below θ = 0.5° is the GUI's Data >
Normalize (Auto) on this curve: the largest CoC4 value is the plateau at
θ = 0.20825° (2θ = 0.4165°), below 0.5°, so both divide by the same D_max / R_model.

The measured curve is the CoC4 import of Chapter 11 (figures-src/ch11/
curve-measured.dat: θ, normalised to 1 at the maximum, zero counts floored).
The starting model is the one of Chapter 12 (figures-src/ch12/start-model.json).

Steps
  1. anchor: a one-iteration, two-particle job scores the starting model and
     echoes the scale Normalize (Auto) sets (R_model at θ_max, since the data
     are 1 there), and the solved ratio of the starting model
  2. the floor: one count (Chapter 11: 1 / (peak rate × counting time)) × that scale
  3. the range end for CoC4 (8 orders visible, Chapter 11): a quarter of the
     spacing past order 8, the spacing from the Chapter 11 seed's predictions;
     and for CoC5 (4 orders visible, Chapter 10): a straight line through
     orders 1-4 (procedure §6.6), then half a spacing past predicted order 7
  4. Table 14-2: Periodic fits (the period held at the Chapter 11 seed, as the
     GUI does) from the starting model with the scale held (Solve scale in χ²
     off), solved within 0.2 (the GUI default) and solved within 0.7 (one
     laboratory's preset), five seeds each (the preset's seed list),
     population 5000, 200 iterations, SeedR on, PW χ² on, TW None, Δθ = 0.012°,
     no smoothing, the floor and range of steps 2-3. Free: H, σ, ρ of C and Co
     and of the top C layer. Bounds: H two thirds to four thirds of the start;
     σ 1-8 Å; ρ(C) 1.5-2.4, ρ(Co) 6.0-8.79 g/cm³ (the preset's materials); the
     top layer the preset's contamination bounds (5-40 Å, σ 1-10 Å, ρ 0.6-1.4).

  anchor.json   the scale, one count × scale, the starting model's solved ratio
  range.json    the CoC4 and CoC5 range ends and the order predictions
  fits.json     Table 14-2, every run

Run:  python scripts/figures/ch14_engine_data.py [anchor|fits]
Out:  figures-src/ch14/
"""
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from xrc_engine import Engine  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "figures-src" / "ch14"
CH11 = ROOT / "figures-src" / "ch11"
LAMBDA = 1.541874
DTHETA = 0.012
THETA_MAX = 0.20825                # θ of the plateau maximum (2θ = 0.4165°), Chapter 11
SEEDS = [20260921, 20260922, 20260923, 20260924, 20260925]   # the preset's optimizer.seeds.list


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def curve():
    d = np.loadtxt(CH11 / "curve-measured.dat", skiprows=1)
    return [[float(t), float(r)] for t, r in d]


START = load(ROOT / "figures-src" / "ch12" / "start-model.json")
ORD = load(CH11 / "orders.json")
COUNT = load(CH11 / "assess-design.json")["checks"]["counting"]
ONE = 1 / (COUNT["peak_rate_cps"] * COUNT["counting_time_s"])


def predict(m, d, two_delta, lam=LAMBDA):
    """2θ of order m from the Bragg law with refraction."""
    return 2 * math.degrees(math.asin(math.sqrt((m * lam / (2 * d)) ** 2 + two_delta)))


def line(m, two_theta, lam=LAMBDA):
    m = np.asarray(m, float)
    s2 = np.sin(np.radians(np.asarray(two_theta) / 2)) ** 2
    a, b = np.polyfit(m ** 2, s2, 1)
    return lam / (2 * math.sqrt(a)), b


def ranges():
    d, td = ORD["D_seed"], ORD["two_delta_seed"]
    last = 2 * ORD["weak_orders"][-1]["theta"]                 # order 8, measured
    sp = predict(9, d, td) - predict(8, d, td)
    coc4 = {"D": d, "two_delta": td, "visible": 8, "last_visible_2theta": last,
            "spacing_8_9": sp, "end_2theta": last + 0.25 * sp,
            "predicted": {m: predict(m, d, td) for m in range(1, 10)},
            "measured_end_2theta": 2 * max(t for t, _ in curve())}
    a5 = load(ROOT / "figures-src" / "ch10" / "assess-design.json")["checks"]["orders_visible"]
    vis = [o for o in a5["orders"] if o["visible"]]
    d5, td5 = line([o["n"] for o in vis], [o["theta_meas_two_theta_deg"] for o in vis])
    p7, p8 = predict(7, d5, td5), predict(8, d5, td5)
    t5 = np.loadtxt(ROOT / "figures-src" / "ch10" / "curve-measured.dat", skiprows=1)[:, 0]
    coc5 = {"D": d5, "two_delta": td5, "visible": len(vis),
            "measured_orders_2theta": [o["theta_meas_two_theta_deg"] for o in vis],
            "predicted": {m: predict(m, d5, td5) for m in range(1, 9)},
            "end_2theta": p7 + 0.5 * (p8 - p7), "measured_end_2theta": 2 * float(t5.max()),
            "old_end_2theta": 8.4}          # the deposit's range end, "past the last visible order" (Chapter 9)
    return coc4, coc5


FREE = [{"stack": s, "layer": l, "parameters": ["thickness", "sigma", "density"]}
        for s, l in ((0, 0), (0, 1), (1, 0))]


def bounds():
    c, co = START["stacks"][0]["layers"]
    top = START["stacks"][1]["layers"][0]
    b = []
    for (s, l, lay, rho, sig) in ((0, 0, c, (1.5, 2.4), (1, 8)), (0, 1, co, (6.0, 8.79), (1, 8)),
                                  (1, 0, top, (0.6, 1.4), (1, 10))):
        h = (5, 40) if s == 1 else (round(lay["thickness"] * 2 / 3, 2), round(lay["thickness"] * 4 / 3, 2))
        b += [{"stack": s, "layer": l, "parameter": "thickness", "min": h[0], "max": h[1]},
              {"stack": s, "layer": l, "parameter": "sigma", "min": sig[0], "max": sig[1]},
              {"stack": s, "layer": l, "parameter": "density", "min": rho[0], "max": rho[1]}]
    return b


def base(r_min, theta_end):
    return {"curve": curve(), "lambda": LAMBDA, "polarization": "s", "structure": START,
            "scale": "auto", "auto_theta_max": 0.5, "r_min": r_min,
            "theta_range": {"min": THETA_MAX, "max": theta_end}, "resolution": DTHETA,
            "chi2": {"theta_weight": 0, "point_weight": True}, "smooth": {"passes": 0},
            "points_inline_max": 0}


def save(name, obj):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(json.dumps(obj, indent=1), encoding="utf-8")
    print(f"wrote {name}")


def do_anchor(eng):
    coc4, coc5 = ranges()
    save("range.json", {"CoC4": coc4, "CoC5": coc5})
    req = base(1e-7, coc4["end_2theta"] / 2)
    r = eng.fit({**req, "free": [{"stack": 0, "layer": 1, "parameters": ["density"]}],
                 "bounds": [{"stack": 0, "layer": 1, "parameter": "density", "min": 0.5, "max": 20}],
                 "scale_solve": True, "scale_solve_window": 0.7,
                 "optimizer": {"iterations": 1, "population": 2, "range_seed": False}, "seed": 1})
    a = {"scale": r["scale"], "divisor": 1 / r["scale"], "scale_theta": r["scale_theta"],
         "one_count_import": ONE, "one_count_scaled": ONE * r["scale"],
         "start_solved_ratio_w07": r["scale_start_ratio"]}
    save("anchor.json", a)
    print(a, coc4["end_2theta"], coc5["end_2theta"])


def summary(layer):
    return {k: layer[k] for k in ("thickness", "sigma", "density")}


def do_fits(eng):
    a = load(OUT / "anchor.json")
    rng = load(OUT / "range.json")["CoC4"]
    req = {**base(round(a["one_count_scaled"], 9), rng["end_2theta"] / 2), "free": FREE, "bounds": bounds()}
    opt = {"iterations": 200, "population": 5000, "range_seed": True}
    rows = []
    for label, over in (("held", {"scale_solve": False}),
                        ("solved 0.2", {"scale_solve": True, "scale_solve_window": 0.2}),
                        ("solved 0.7", {"scale_solve": True, "scale_solve_window": 0.7})):
        for seed in SEEDS:
            r = eng.fit({**req, **over, "optimizer": opt, "seed": seed})
            s = r["fitted_structure"]["stacks"]
            c, co = (summary(x) for x in s[0]["layers"])
            row = {"case": label, "seed": seed, "chi2": r["chi2"], "chi2_plain": r["chi2_plain"],
                   "scale_ratio": r.get("scale_ratio"), "scale_clamped": r.get("scale_clamped"),
                   "near_bounds": r["report"].get("near_bounds"), "C": c, "Co": co,
                   "top": summary(s[1]["layers"][0]), "elapsed_s": r["elapsed_s"]}
            print(label, seed, round(r["chi2"], 4), row["scale_ratio"], row["scale_clamped"],
                  round(c["density"], 3), round(co["density"], 3), round(c["sigma"], 2), round(co["sigma"], 2))
            rows.append(row)
    save("fits.json", {"request": {k: v for k, v in req.items() if k != "curve"}, "optimizer": opt,
                       "runs": rows})


def main():
    what = sys.argv[1:] or ["anchor", "fits"]
    eng = Engine()
    try:
        s = eng.describe()
        print(f"engine: X-Ray Calc {s['xraycalc3_exe_version']}, git {s['git_revision']}")
        for w in what:
            {"anchor": do_anchor, "fits": do_fits}[w](eng)
    finally:
        eng.close()


if __name__ == "__main__":
    main()
