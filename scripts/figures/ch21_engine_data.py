"""Chapter 21: two single films, fitted by the procedure's single-film rules.

The command-line server that ships with X-Ray Calc (XRC_MCP.exe in the build
folder, engine 3.9.4.1270 since the rerun of 2026-09-25), driven through xrc_engine.Engine. The book never
names the server.

The curves (the author's measurements, 2θ in degrees and raw counts):
  C1   single carbon film on glass, P2-06 (C(260917B)), deposited 1000 s
       (curve: the procedure's deposit, submission\\zenodo\\curves\\C1.csv)
  Co   single cobalt film on glass, P2-08 (Co(260921A)), deposited 800 s
       (curve: exp-03 inbox P2-08\\xrr.dat, attached to ELN item 1481)
Both are fitted as the laboratory's procedure v5 refits of 2026-09-24 did
(ELN item 1492 for Co), rerun on the current engine: λ 1.541874 Å, the scale
solved within 0.2, smoothing off, θ weight 0 with the point weights, the
preset's seeds, population 2000 (single film), 200 iterations, SeedR on,
R min at one count, the range ends of those refits (θ 1.6775° for C1, 2.7° for
Co), Δθ chosen by a one-run scan over 0.012-0.015° on the final model, then
the near-bound rule (Chapter 15) for two rounds.

Models (the stacks are listed from the substrate up, as the engine takes them):
  c1-edge   one C layer, range from θ_max (the edge included): the shoulder
  c1-film   one C layer, range from θ = 0.3° (the single-film start)
  c1-surf   C film + contamination layer, from θ = 0.3°  (the procedure's model)
  co-bare   one Co layer
  co-c      Co + contamination layer
  co-coo    Co + CoO + contamination layer  (the fit of record's model)
Limits: H ±1/3 of the start (the contamination layer 5-40 Å, the oxide
5-40 Å); σ 1-10 Å (single film); ρ C 1.5-2.4, Co 6.0-8.79, CoO 0.7-1.0 × its
table's 6.2 (4.34-6.2), contamination 0.6-1.4. Substrate SiO2 2.50 g/cm³,
σ 3.8 Å (soda-lime glass, Chapter 12).

Run:  python scripts/figures/ch21_engine_data.py [fits|curves|numbers ...]
Out:  figures-src/ch21/
"""
import json
import statistics as st
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import local_paths  # noqa: E402
import ch14_engine_data as c14  # noqa: E402
from xrc_engine import Engine  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "figures-src" / "ch21"
SEEDS = c14.SEEDS
LAMBDA = c14.LAMBDA
OPT = {"iterations": 200, "population": 2000, "range_seed": True}
SCAN = [0.012, 0.013, 0.014, 0.015]
ROUNDS = 2
CURVES = {
    "c1": local_paths.deposit("curves", "C1.csv"),
    "co": local_paths.get("P2_08_CURVE"),
}
THETA_END = {"c1": 1.6775, "co": 2.7}
FILM_START = 0.3                                   # preset single_film.theta_min_deg
SUB = {"material": "SiO2", "density": 2.5, "sigma": 3.8}
SURF = ({"material": "C", "thickness": 15.0, "sigma": 3.0, "density": 0.9},
        {"thickness": (5.0, 40.0), "sigma": (1.0, 10.0), "density": (0.6, 1.4)})
CEILING = {"C": 2.4, "Co": 8.79, "CoO": 6.2}       # the named ceilings; CoO its table's bulk
NO_CAP = {"surf"}                                   # the contamination layer, as in Chapter 17


def curve(name):
    rows = []
    for ln in CURVES[name].read_text(encoding="utf-8").splitlines():
        p = ln.replace(",", " ").split()
        try:
            t2, c = float(p[0]), float(p[1])
        except (ValueError, IndexError):
            continue
        if c > 0:
            rows.append([t2 / 2, c])
    return rows


def theta_max(rows):
    return max((r for r in rows if r[0] < 0.5), key=lambda r: r[1])[0]


def layer(material, h, s, rho, hb, sb=(1.0, 10.0), rb=None):
    return ({"material": material, "thickness": h, "sigma": s, "density": rho},
            {"thickness": hb, "sigma": sb, "density": rb})


def third(h):
    return (round(h * 2 / 3, 2), round(h * 4 / 3, 2))


MODELS = {
    "c1-edge": ("c1", "edge", [("film", layer("C", 300.0, 4.0, 2.0, third(300.0), rb=(1.5, 2.4)))]),
    "c1-film": ("c1", "film", [("film", layer("C", 300.0, 4.0, 2.0, third(300.0), rb=(1.5, 2.4)))]),
    "c1-surf": ("c1", "film", [("film", layer("C", 300.0, 4.0, 2.0, third(300.0), rb=(1.5, 2.4))),
                               ("surf", SURF)]),
    "co-bare": ("co", "edge", [("film", layer("Co", 290.0, 4.0, 8.0, third(290.0), rb=(6.0, 8.79)))]),
    "co-c": ("co", "edge", [("film", layer("Co", 290.0, 4.0, 8.0, third(290.0), rb=(6.0, 8.79))),
                            ("surf", SURF)]),
    "co-coo": ("co", "edge", [("film", layer("Co", 290.0, 4.0, 8.0, third(290.0), rb=(6.0, 8.79))),
                              ("oxide", layer("CoO", 17.0, 5.0, 5.58, (5.0, 40.0), rb=(4.34, 6.2))),
                              ("surf", SURF)]),
}


def request(eng, key):
    name, start, stacks = MODELS[key]
    rows = curve(name)
    tmax = theta_max(rows)
    st_ = {"substrate": dict(SUB), "stacks": [{"N": 1, "layers": [dict(lay)]} for _, (lay, _) in stacks]}
    free = [{"stack": i, "layer": 0, "parameters": ["thickness", "sigma", "density"]} for i in range(len(stacks))]
    bounds = [{"stack": i, "layer": 0, "parameter": p, "min": b[p][0], "max": b[p][1]}
              for i, (_, (_, b)) in enumerate(stacks) for p in ("thickness", "sigma", "density")]
    req = {"curve": rows, "lambda": LAMBDA, "polarization": "s", "structure": st_,
           "scale": "auto", "auto_theta_max": 0.5, "scale_solve": True, "scale_solve_window": 0.2,
           "theta_range": {"min": tmax if start == "edge" else FILM_START, "max": THETA_END[name]},
           "chi2": {"theta_weight": 0, "point_weight": True}, "smooth": {"passes": 0},
           "points_inline_max": 0, "free": free, "bounds": bounds, "resolution": 0.013, "r_min": 1e-7}
    # R min at one count: one count times the anchored scale (a 1-iteration probe gives the scale)
    a = eng.fit({**req, "optimizer": {"iterations": 1, "population": 2, "range_seed": False}, "seed": 1})
    req["r_min"] = round(1.0 * a["scale"], 12)
    return req, {"theta_max": tmax, "scale": a["scale"], "roles": [r for r, _ in stacks]}


def summary(lay):
    return {k: lay[k] for k in ("material", "thickness", "sigma", "density")}


def run(eng, req, key, seed):
    r = eng.fit({**req, "optimizer": OPT, "seed": seed})
    stacks = [summary(s["layers"][0]) for s in r["fitted_structure"]["stacks"]]
    rep = r.get("report", {})
    row = {"key": key, "seed": seed, "chi2": r["chi2"], "chi2_plain": r.get("chi2_plain"),
           "scale": r.get("scale"), "scale_ratio": r.get("scale_ratio"), "scale_clamped": r.get("scale_clamped"),
           "near_bounds": rep.get("near_bounds"), "edge": rep.get("edge"), "fringes": rep.get("fringes"),
           "bands": rep.get("bands"), "resolution": req["resolution"], "layers": stacks}
    print(f"{key:8s} seed {seed} Δθ {req['resolution']}: χ² {row['chi2']:.4f} | "
          + " ".join(f"{x['material']}:{x['thickness']:.2f}/{x['sigma']:.2f}/{x['density']:.2f}" for x in stacks)
          + f" | nb {[(n.get('stack'), n.get('parameter'), n.get('bound')) for n in row['near_bounds'] or []]}",
          flush=True)
    return row


def widen(req, roles, runs):
    bounds = json.loads(json.dumps(req["bounds"]))
    mats = {i: s["layers"][0]["material"] for i, s in enumerate(req["structure"]["stacks"])}
    changes = []
    for b in bounds:
        lo, hi = b["min"], b["max"]
        span = hi - lo
        for r in runs:
            for nb in r["near_bounds"] or []:
                if (nb.get("stack"), nb.get("parameter")) != (b["stack"], b["parameter"]) or nb["margin_fraction"] > 0.05:
                    continue
                if nb["bound"] == "min" and b["min"] == lo:
                    floor = {"thickness": 0.1, "density": 0.1}.get(b["parameter"], 0.0)
                    if lo > floor:
                        b["min"] = round(max(floor, lo - span / 2), 3)
                if nb["bound"] == "max" and b["max"] == hi:
                    cap = None
                    if b["parameter"] == "density" and roles[b["stack"]] not in NO_CAP:
                        cap = CEILING.get(mats[b["stack"]])
                    if cap is None or hi < cap:
                        b["max"] = round(hi + span / 2 if cap is None else min(cap, hi + span / 2), 3)
        if (b["min"], b["max"]) != (lo, hi):
            changes.append({"stack": b["stack"], "parameter": b["parameter"], "from": [lo, hi], "to": [b["min"], b["max"]]})
    return bounds, changes


def save(name, obj):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(json.dumps(obj, indent=1), encoding="utf-8")
    print("wrote", name, flush=True)


def do_fits(eng):
    out = {}
    f = OUT / "fits.json"
    if f.exists():
        out = c14.load(f)
    for key in MODELS:
        if key in out:
            continue
        req, info = request(eng, key)
        scan = []
        for dt in SCAN:
            scan.append(run(eng, {**req, "resolution": dt}, key, SEEDS[0]))
        req["resolution"] = min(scan, key=lambda r: r["chi2"])["resolution"]
        history = []
        for rnd in range(ROUNDS + 1):
            runs = [run(eng, req, key, s) for s in SEEDS]
            if rnd == ROUNDS:
                break
            bounds, changes = widen(req, info["roles"], runs)
            history.append({"round": rnd, "changes": changes})
            print(key, "round", rnd, "changes", changes, flush=True)
            if not changes:
                break
            req = {**req, "bounds": bounds}
        out[key] = {"request": {k: v for k, v in req.items() if k != "curve"}, "info": info,
                    "scan": [{"resolution": s["resolution"], "chi2": s["chi2"]} for s in scan],
                    "widening": history, "runs": runs}
        save("fits.json", out)


def do_curves(eng):
    """The measured curve and each model's best fit near the edge and over the range."""
    d = c14.load(OUT / "fits.json")
    res = {}
    for key, blk in d.items():
        best = min(blk["runs"], key=lambda r: r["chi2"])
        name = MODELS[key][0]
        st_ = json.loads(json.dumps(blk["request"]["structure"]))
        for s, lay in zip(st_["stacks"], best["layers"]):
            s["layers"][0].update({k: lay[k] for k in ("thickness", "sigma", "density")})
        c = eng.call("calc_reflectivity", {"structure": st_, "lambda": LAMBDA, "theta_min": 0.1,
                                           "theta_max": THETA_END[name], "points": 3000,
                                           "delta_theta": best["resolution"], "polarization": "s",
                                           "r_min": 1e-9, "max_inline_points": 0})
        txt = (eng.work / c["file"]).read_text(encoding="utf-8")
        arr = [[float(x) for x in ln.split()[:2]] for ln in txt.splitlines() if ln and ln[0].isdigit()]
        res[key] = {"seed": best["seed"], "chi2": best["chi2"], "scale": best["scale"],
                    "scale_ratio": best["scale_ratio"], "calc": arr}
    save("curves.json", res)


def sd(v):
    return st.stdev(v) if len(v) > 1 else 0.0


def numbers():
    d = c14.load(OUT / "fits.json")
    lines = []
    p = lines.append
    for key, blk in d.items():
        rs = blk["runs"]
        best = min(rs, key=lambda r: r["chi2"])
        p(f"===== {key}: θ_max {blk['info']['theta_max']} range {blk['request']['theta_range']} Δθ {blk['request']['resolution']} "
          f"| scan {[(s['resolution'], round(s['chi2'], 4)) for s in blk['scan']]}")
        p(f"   widening {blk['widening']}")
        p(f"   χ² {[round(r['chi2'], 4) for r in rs]} best {best['chi2']:.4f} (seed {best['seed']}) sd {sd([r['chi2'] for r in rs]):.4f} "
          f"plain {best['chi2_plain']} scale_ratio {best['scale_ratio']}")
        for i, lay in enumerate(best["layers"]):
            vals = {q: [r["layers"][i][q] for r in rs] for q in ("thickness", "sigma", "density")}
            p(f"   {i} {lay['material']:4s} " + "  ".join(f"{q[0]} {lay[q]:.3f} ± {sd(v):.3f} ({min(v):.2f}-{max(v):.2f})"
                                                       for q, v in vals.items()))
        if len(best["layers"]) > 1:
            tot = [sum(x["thickness"] for x in r["layers"]) for r in rs]
            top = [sum(x["thickness"] for x in r["layers"][1:]) for r in rs]
            p(f"   total H {tot[rs.index(best)]:.3f} ± {sd(tot):.3f}; layers above the film {top[rs.index(best)]:.3f} ± {sd(top):.3f}")
        e = best.get("edge") or {}
        p("   edge " + " ".join(f"{q['theta_deg']:.4f}:{q['r_calc'] / q['i_meas']:.2f}" for q in e.get("points", [])))
        fr = best.get("fringes") or {}
        p(f"   fringes meas {fr.get('measured', {}).get('mean_contrast')} calc {fr.get('calculated', {}).get('mean_contrast')} n {fr.get('count')}")
        p("   bands " + " ".join(f"{b['mean']:+.3f}" for b in best.get("bands") or []))
        p(f"   near bounds (best) {best['near_bounds']}")
    (OUT / "numbers.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


def main():
    what = sys.argv[1:] or ["fits", "curves", "numbers"]
    if what == ["numbers"]:
        numbers()
        return
    eng = Engine()
    try:
        s = eng.describe()
        print(f"engine: X-Ray Calc {s['xraycalc3_exe_version']}, git {s['git_revision']}")
        for w in what:
            {"fits": do_fits, "curves": do_curves, "numbers": lambda e: numbers()}[w](eng)
    finally:
        eng.close()


if __name__ == "__main__":
    main()
