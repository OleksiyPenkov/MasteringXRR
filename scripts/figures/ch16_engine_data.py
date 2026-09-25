"""Chapter 16: the fit settings on CoC4.

The command-line server that ships with X-Ray Calc (XRC_MCP.exe in the build
folder, engine 3.9.4.1250 since the rerun of 2026-09-25), driven through xrc_engine.Engine. The book never
names the server.

Every fit is the Chapter 15 fit: the starting model of Chapter 12, the limits of
Table 15-1 with the top layer's σ at 0-10 Å, Periodic mode with the period
held, SeedR on, PW χ² on, TW None, the scale solved within 0.2, no smoothing,
the Chapter 14 floor and range. Only the setting under study changes.

  population.json  population × iterations: 500, 2000, 5000 at 200 iterations,
                   500 at 2000 (the same number of scored structures as
                   5000 × 200) and 5000 at 100; five seeds each, Δθ = 0.012°
  resolution.json  Δθ from 0.009 to 0.020° in steps of 0.001°, the first seed
                   only (the procedure's scan), and the five seeds at each Δθ
                   of the laboratory's window 0.012-0.015°

  fringes-*.dat    Figure 16-2: the best run at Δθ = 0.012° and at 0.014°
                   (lowest χ² of the five), calculated at that Δθ from
                   θ = 0.80 to 1.70° in 0.0025° steps, floored at one count

Each run keeps χ², the scale, the fitted layers, the elapsed time and the
fringe comparison between orders 1 and 2 that the server reports.

Run:  python scripts/figures/ch16_engine_data.py [fits|curves]
Out:  figures-src/ch16/
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ch14_engine_data as c14  # noqa: E402
from xrc_engine import Engine  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "figures-src" / "ch16"
POPULATION = [(500, 200), (2000, 200), (5000, 200), (500, 2000), (5000, 100)]
SCAN = [round(0.009 + 0.001 * i, 3) for i in range(12)]
WINDOW = [0.012, 0.013, 0.014, 0.015]


def summary(layer):
    return {k: layer[k] for k in ("thickness", "sigma", "density")}


def request():
    a = c14.load(c14.OUT / "anchor.json")
    rng = c14.load(c14.OUT / "range.json")["CoC4"]
    bounds = c14.bounds()
    for b in bounds:
        if b["stack"] == 1 and b["parameter"] == "sigma":
            b["min"] = 0.0                     # Chapter 15: Widen, 1-10 Å -> 0-10 Å
    return {**c14.base(round(a["one_count_scaled"], 9), rng["end_2theta"] / 2),
            "free": c14.FREE, "bounds": bounds, "scale_solve": True, "scale_solve_window": 0.2}


def run(eng, req, pop, iters, seed, dtheta):
    r = eng.fit({**req, "resolution": dtheta,
                 "optimizer": {"iterations": iters, "population": pop, "range_seed": True},
                 "seed": seed})
    st = r["fitted_structure"]["stacks"]
    rep = r.get("report", {})
    row = {"population": pop, "iterations": iters, "seed": seed, "resolution": dtheta,
           "chi2": r["chi2"], "chi2_plain": r.get("chi2_plain"),
           "scale_ratio": r.get("scale_ratio"), "scale_clamped": r.get("scale_clamped"),
           "elapsed_s": r.get("elapsed_s"), "device": r.get("device"),
           "near_bounds": rep.get("near_bounds"), "fringes": rep.get("fringes"),
           "C": summary(st[0]["layers"][0]), "Co": summary(st[0]["layers"][1]),
           "top": summary(st[1]["layers"][0])}
    print(f"pop {pop:5d} it {iters:4d} Δθ {dtheta:.3f} seed {seed}: χ² {row['chi2']:.4f} "
          f"Co ρ {row['Co']['density']:.3f} top H {row['top']['thickness']:.2f} "
          f"t {row['elapsed_s']}", flush=True)
    return row


def structure(row):
    s = json.loads(json.dumps(c14.START))
    for layer, key in ((s["stacks"][0]["layers"][0], "C"), (s["stacks"][0]["layers"][1], "Co"),
                       (s["stacks"][1]["layers"][0], "top")):
        layer.update(row[key])
    return s


def curves():
    d = json.loads((OUT / "resolution.json").read_text(encoding="utf-8"))
    runs = d["scan"] + d["window"]
    one = c14.load(c14.OUT / "anchor.json")["one_count_scaled"]
    eng = Engine()
    try:
        for dt in (0.012, 0.014):
            best = min((r for r in runs if r["resolution"] == dt), key=lambda r: r["chi2"])
            c = eng.call("calc_reflectivity", {
                "structure": structure(best), "lambda": c14.LAMBDA, "theta_min": 0.80,
                "theta_max": 1.70, "points": 361, "delta_theta": dt, "polarization": "s",
                "r_min": one, "max_inline_points": 0})
            txt = (eng.work / c["file"]).read_text(encoding="utf-8")
            (OUT / f"fringes-{dt:.3f}.dat").write_text(
                f"# best run at Δθ {dt}: seed {best['seed']}, χ² {best['chi2']:.4f}, "
                f"scale ratio {best['scale_ratio']}\n" + txt, encoding="utf-8")
            print("wrote", f"fringes-{dt:.3f}.dat", best["seed"], best["chi2"], best["scale_ratio"])
    finally:
        eng.close()


def main():
    if sys.argv[1:] == ["curves"]:
        return curves()
    req = request()
    OUT.mkdir(parents=True, exist_ok=True)
    eng = Engine()
    try:
        s = eng.describe()
        print(f"engine: X-Ray Calc {s['xraycalc3_exe_version']}, git {s['git_revision']}")
        first = run(eng, req, 5000, 200, c14.SEEDS[0], 0.012)
        print("result keys:", sorted(first.keys()), "\nfringes:", json.dumps(first["fringes"])[:800])
        pop = [run(eng, req, p, n, seed, 0.012) for p, n in POPULATION for seed in c14.SEEDS]
        (OUT / "population.json").write_text(json.dumps(
            {"request": {k: v for k, v in req.items() if k != "curve"}, "runs": pop}, indent=1),
            encoding="utf-8")
        scan = [run(eng, req, 5000, 200, c14.SEEDS[0], d) for d in SCAN]
        window = [run(eng, req, 5000, 200, seed, d) for d in WINDOW for seed in c14.SEEDS[1:]]
        (OUT / "resolution.json").write_text(json.dumps(
            {"request": {k: v for k, v in req.items() if k != "curve"}, "scan": scan,
             "window": window}, indent=1), encoding="utf-8")
    finally:
        eng.close()
    print("wrote population.json, resolution.json")


if __name__ == "__main__":
    main()
