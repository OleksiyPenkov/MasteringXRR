"""Chapter 17: Periodic against Polynomial mode on CoC4 and CoC5.

The command-line server that ships with X-Ray Calc (XRC_MCP.exe in the build
folder, engine 3.9.4.1250 since the rerun of 2026-09-25), driven through xrc_engine.Engine. The book never
names the server.

CoC4 carries the Chapter 16 fit forward: the Chapter 12 starting model, the
Chapter 14 conditioning, the Chapter 15 limits (top-layer σ 0-10 Å) and
Δθ = 0.014° (Chapter 16), population 5000, 200 iterations, SeedR on, the
preset's five seeds.

CoC5 is conditioned the same way from its own curve (Chapter 10): the expert
layers of Chapter 9 scaled to the period of the straight-line fit of its four
visible orders (figures-src/ch14/range.json), the preset's contamination
layer on top, the same limit rules, the floor at one count × scale, the range
end of Chapter 14, and Δθ chosen by a one-run Periodic scan over 0.012-0.015°.

For each curve, five runs each of
  periodic   the period held at its start value (the GUI's Periodic mode)
  poly1      Polynomial mode of order 1, σ and ρ paired (procedure §9.5, the
             preset's poly_order_first)
  poly3      Polynomial mode of order 3, σ and ρ paired (the author's default,
             paper §4)
Each run keeps χ², the scale, the fitted layers (with the thickness profiles),
the period at the surface end and at the substrate end, and the server's
order table.

  control    Periodic mode with the start period moved to the mean period of
             the best poly1 run (a GUI user can do this by editing the H
             fields), five runs; and, as a diagnostic for the author only,
             Periodic mode with the period freed within ±10 % (the GUI can't
             do this; procedure §7.1)

  demo       the Chapter 3 demo (ML(30x2)P3_Best.xrcx, Data 1.dat, calculated
             from Target, whose Si thickness drifts 25.00 -> 28.60 -> 26.96 Å):
             Polynomial mode with every box paired (a periodic stack whose
             period floats), and orders 1 and 3 with σ and ρ paired; the
             demo's own start, limits and settings (λ 1.54043 Å, Δθ 0.015°)

  final      the chapter's runs. For each curve the limits are widened by the
             near-bound rule (Chapter 15): any limit a run of any mode ends on or
             within 5 % of the range from is moved out by half the range (the
             GUI's Widen), except a σ at 0 and a density at the bulk ceiling;
             repeat until no run is near a widenable limit (at most 4 rounds).
             Modes: periodic (held), pairedall (every box ticked: the period
             floats), poly1, poly3. Out: coc4-final.json, coc5-final.json

  curves     Figure 17-2: the demo curve and the best one-period fit (every box
             ticked), calculated at the demo's settings, with the scale the
             fit solved. Out: demo-curves.dat

Run:  python scripts/figures/ch17_engine_data.py [coc4|coc5|control|demo|final|curves ...]
Out:  figures-src/ch17/
"""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import local_paths  # noqa: E402
import ch14_engine_data as c14  # noqa: E402
import ch16_engine_data as c16  # noqa: E402
from xrc_engine import Engine  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "figures-src" / "ch17"
SEEDS = c14.SEEDS
OPT = {"iterations": 200, "population": 5000, "range_seed": True}
MODES = {"periodic": {},
         "poly1": {"profile": True, "paired": ["sigma", "density"], "poly_order": 1},
         "poly3": {"profile": True, "paired": ["sigma", "density"], "poly_order": 3}}

# CoC5: the expert layers of Chapter 9 (the deposited reference fit)
C5_C = {"material": "C", "thickness": 31.2135, "sigma": 4.3254, "density": 2.0621}
C5_CO = {"material": "Co", "thickness": 18.8183, "sigma": 5.7386, "density": 6.2509}
C5_THETA_MAX = 0.20075               # θ of the plateau maximum (Chapter 10)


def layer_summary(layer):
    out = {k: layer[k] for k in ("thickness", "sigma", "density")}
    if "thickness_profile" in layer:
        out["thickness_profile"] = layer["thickness_profile"]
        out["thickness"] = float(np.mean(layer["thickness_profile"]))
    return out


def run(eng, req, mode, seed):
    extra = MODES[mode]
    opt = {**OPT, **({"poly_order": extra["poly_order"]} if "poly_order" in extra else {})}
    body = {k: v for k, v in extra.items() if k != "poly_order"}
    r = eng.fit({**req, **body, "optimizer": opt, "seed": seed})
    st = r["fitted_structure"]["stacks"]
    c, co = (layer_summary(x) for x in st[0]["layers"])
    if "thickness_profile" in c or "thickness_profile" in co:
        n = st[0].get("N", 20)
        pc = np.array(c.get("thickness_profile", [c["thickness"]] * n))
        pco = np.array(co.get("thickness_profile", [co["thickness"]] * n))
        d = pc + pco
        period = {"D": float(d.mean()), "D_top": float(d[0]), "D_bottom": float(d[-1]),
                  "drift": float(d[-1] - d[0])}
    else:
        period = {"D": c["thickness"] + co["thickness"], "drift": 0.0}
    rep = r.get("report", {})
    row = {"mode": mode, "seed": seed, "chi2": r["chi2"], "chi2_plain": r.get("chi2_plain"),
           "scale_ratio": r.get("scale_ratio"), "scale_clamped": r.get("scale_clamped"),
           "near_bounds": rep.get("near_bounds"), "orders": rep.get("orders"),
           "edge": rep.get("edge"), "bands": rep.get("bands"), "elapsed_s": r.get("elapsed_s"),
           **period, "C": c, "Co": co, "top": layer_summary(st[1]["layers"][0]),
           "optimizer_used": r.get("optimizer_used")}
    print(f"{mode:8s} seed {seed}: χ² {row['chi2']:.4f} D {period['D']:.3f} "
          f"drift {period['drift']:+.3f} σC {c['sigma']:.2f} σCo {co['sigma']:.2f} "
          f"ρCo {co['density']:.3f} nb {row['near_bounds']}", flush=True)
    return row


def save(name, obj):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(json.dumps(obj, indent=1), encoding="utf-8")
    print("wrote", name)


def do_coc4(eng):
    req = {**c16.request(), "resolution": 0.014}
    runs = [run(eng, req, m, s) for m in MODES for s in SEEDS]
    save("coc4.json", {"request": {k: v for k, v in req.items() if k != "curve"}, "runs": runs})


def coc5_request(eng):
    rng = c14.load(c14.OUT / "range.json")["CoC5"]
    f = rng["D"] / (C5_C["thickness"] + C5_CO["thickness"])
    c = {**C5_C, "thickness": round(C5_C["thickness"] * f, 2), "sigma": 4.0, "density": 2.0}
    co = {**C5_CO, "thickness": round(C5_CO["thickness"] * f, 2), "sigma": 4.0, "density": 8.0}
    start = {"substrate": c14.START["substrate"],
             "stacks": [{"N": 20, "layers": [c, co]}, json.loads(json.dumps(c14.START["stacks"][1]))]}
    b = []
    for (s, l, lay, rho, sig) in ((0, 0, c, (1.5, 2.4), (1, 8)), (0, 1, co, (6.0, 8.79), (1, 8)),
                                  (1, 0, start["stacks"][1]["layers"][0], (0.6, 1.4), (0, 10))):
        h = (5, 40) if s == 1 else (round(lay["thickness"] * 2 / 3, 2), round(lay["thickness"] * 4 / 3, 2))
        b += [{"stack": s, "layer": l, "parameter": "thickness", "min": h[0], "max": h[1]},
              {"stack": s, "layer": l, "parameter": "sigma", "min": sig[0], "max": sig[1]},
              {"stack": s, "layer": l, "parameter": "density", "min": rho[0], "max": rho[1]}]
    d = np.loadtxt(ROOT / "figures-src" / "ch10" / "curve-measured.dat", skiprows=1)
    cnt = c14.load(ROOT / "figures-src" / "ch10" / "assess-design.json")["checks"]["counting"]
    one = 1 / (cnt["peak_rate_cps"] * cnt["counting_time_s"])
    req = {"curve": [[float(t), float(r)] for t, r in d], "lambda": c14.LAMBDA, "polarization": "s",
           "structure": start, "scale": "auto", "auto_theta_max": 0.5,
           "theta_range": {"min": C5_THETA_MAX, "max": rng["end_2theta"] / 2},
           "chi2": {"theta_weight": 0, "point_weight": True}, "smooth": {"passes": 0},
           "points_inline_max": 0, "free": c14.FREE, "bounds": b,
           "scale_solve": True, "scale_solve_window": 0.2, "resolution": 0.012, "r_min": 1e-7}
    a = eng.fit({**req, "free": [{"stack": 0, "layer": 1, "parameters": ["density"]}],
                 "bounds": [{"stack": 0, "layer": 1, "parameter": "density", "min": 0.5, "max": 20}],
                 "optimizer": {"iterations": 1, "population": 2, "range_seed": False}, "seed": 1})
    req["r_min"] = round(one * a["scale"], 12)
    print("CoC5 start D", rng["D"], "scale", a["scale"], "r_min", req["r_min"])
    return req, {"scale": a["scale"], "one_count_import": one, "D_start": rng["D"]}


def do_coc5(eng):
    req, anchor = coc5_request(eng)
    scan = [run(eng, {**req, "resolution": dt}, "periodic", SEEDS[0]) for dt in c16.WINDOW]
    for s, dt in zip(scan, c16.WINDOW):
        s["resolution"] = dt
    best = min(scan, key=lambda r: r["chi2"])["resolution"]
    print("CoC5 Δθ by the scan:", best)
    req["resolution"] = best
    runs = [run(eng, req, m, s) for m in MODES for s in SEEDS]
    save("coc5.json", {"request": {k: v for k, v in req.items() if k != "curve"},
                       "anchor": anchor, "scan": scan, "runs": runs})


def scaled(req, d_new):
    st = json.loads(json.dumps(req["structure"]))
    lay = st["stacks"][0]["layers"]
    f = d_new / (lay[0]["thickness"] + lay[1]["thickness"])
    for x in lay:
        x["thickness"] = round(x["thickness"] * f, 4)
    return {**req, "structure": st}


def do_control(eng):
    out = {}
    for name in ("coc4", "coc5"):
        d = c14.load(OUT / f"{name}.json")
        req = {**(c16.request() if name == "coc4" else coc5_request(eng)[0]),
               "resolution": d["request"]["resolution"]}
        best = min((r for r in d["runs"] if r["mode"] == "poly1"), key=lambda r: r["chi2"])
        r_at = scaled(req, best["D"])
        at = [run(eng, r_at, "periodic", s) for s in SEEDS]
        d0 = sum(x["thickness"] for x in req["structure"]["stacks"][0]["layers"])
        free = {**req, "free": req["free"] + [{"target": "period", "stack": 0}],
                "bounds": req["bounds"] + [{"target": "period", "stack": 0, "min": d0 * 0.9, "max": d0 * 1.1}]}
        fp = []
        for s in SEEDS:
            try:
                fp.append(run(eng, free, "periodic", s))
            except Exception as e:  # noqa: BLE001
                print("period free failed:", e)
                break
        out[name] = {"D_start": best["D"], "periodic_at_poly_D": at, "periodic_period_free": fp}
    save("control.json", out)


DEMO = local_paths.deploy("Examples", "ML(30x2)P3_Best.xrcx")


def do_demo(eng):
    import zipfile
    z = zipfile.ZipFile(DEMO)
    name = next(n for n in z.namelist() if n.startswith("data_"))
    rows = [ln.split("	") for ln in z.read(name).decode("utf-8-sig").splitlines()[2:] if ln.strip()]
    curve = [[float(t) / 2, float(r)] for t, r in rows if float(r) > 0]
    si = {"material": "Si", "thickness": 24.0, "sigma": 4.0, "density": 2.0}
    mo = {"material": "Mo", "thickness": 18.0, "sigma": 4.0, "density": 9.5}
    top = {"material": "Si", "thickness": 60.0, "sigma": 2.0, "density": 2.0}
    st = {"substrate": {"material": "Si", "sigma": 5.0},
          "stacks": [{"N": 30, "layers": [si, mo]}, {"N": 1, "layers": [top]}]}
    lim = {(0, 0): ((18, 35), (1, 5), (1.8, 2.4)), (0, 1): ((8, 23), (1, 5), (9.0, 10.25)),
           (1, 0): ((30, 80), (1, 5), (1.8, 2.4))}
    b = [{"stack": s_, "layer": l, "parameter": p_, "min": v[0], "max": v[1]}
         for (s_, l), vs in lim.items() for p_, v in zip(("thickness", "sigma", "density"), vs)]
    tmax = max(curve, key=lambda x: x[1] if x[0] < 0.5 else 0)[0]
    req = {"curve": curve, "lambda": 1.54043, "polarization": "s", "structure": st,
           "free": c14.FREE, "bounds": b, "scale": "auto", "auto_theta_max": 0.5,
           "scale_solve": True, "scale_solve_window": 0.2, "r_min": 1e-8,
           "theta_range": {"min": tmax, "max": curve[-1][0]}, "resolution": 0.015,
           "chi2": {"theta_weight": 0, "point_weight": True}, "smooth": {"passes": 0},
           "points_inline_max": 0}
    MODES["pairedall"] = {"profile": True, "paired": ["thickness", "sigma", "density"], "poly_order": 1}
    runs = [run(eng, req, m, s_) for m in ("pairedall", "poly1", "poly3") for s_ in SEEDS]
    save("demo.json", {"request": {k: v for k, v in req.items() if k != "curve"}, "runs": runs})


CEILING = {"C": 2.4, "Co": 8.79}      # the preset's ρ Max (Chapter 15)


def widen(req, runs):
    """One round of the near-bound rule. Returns the widened bounds and the list of changes."""
    bounds = json.loads(json.dumps(req["bounds"]))
    mats = {(0, 0): req["structure"]["stacks"][0]["layers"][0]["material"],
            (0, 1): req["structure"]["stacks"][0]["layers"][1]["material"], (1, 0): "top"}
    changes = []
    for b in bounds:
        lo, hi = b["min"], b["max"]
        span = hi - lo
        for r in runs:
            for nb in r["near_bounds"] or []:
                if (nb.get("stack"), nb.get("layer"), nb.get("parameter")) != (b["stack"], b["layer"], b["parameter"]):
                    continue
                if nb["margin_fraction"] > 0.05:
                    continue
                side = nb["bound"]
                if side == "min" and b["min"] == lo and lo > (0.1 if b["parameter"] == "thickness" else 0):
                    # Widen stops at 0; the engine needs a thickness limit above 0
                    floor = 0.1 if b["parameter"] == "thickness" else 0.0
                    b["min"] = round(max(floor, lo - span / 2), 3)
                if side == "max" and b["max"] == hi:
                    cap = CEILING.get(mats[(b["stack"], b["layer"])]) if b["parameter"] == "density" else None
                    if cap is None or hi < cap:
                        b["max"] = round(hi + span / 2 if cap is None else min(cap, hi + span / 2), 3)
        if (b["min"], b["max"]) != (lo, hi):
            changes.append({**{k: b[k] for k in ("stack", "layer", "parameter")}, "from": [lo, hi],
                            "to": [b["min"], b["max"]]})
    return bounds, changes


def do_final(eng):
    for name in ("coc4", "coc5"):
        d = c14.load(OUT / f"{name}.json")
        req = {**(c16.request() if name == "coc4" else coc5_request(eng)[0]),
               "resolution": d["request"]["resolution"]}
        MODES["pairedall"] = {"profile": True, "paired": ["thickness", "sigma", "density"], "poly_order": 1}
        history = []
        for rnd in range(5):
            runs = [run(eng, req, m, s_) for m in ("periodic", "pairedall", "poly1", "poly3") for s_ in SEEDS]
            bounds, changes = widen(req, runs)
            history.append({"round": rnd, "changes": changes})
            print(name, "round", rnd, "changes", changes, flush=True)
            if not changes or rnd == 4:
                break
            req = {**req, "bounds": bounds}
        save(f"{name}-final.json", {"request": {k: v for k, v in req.items() if k != "curve"},
                                     "widening": history, "runs": runs})


def do_curves(eng):
    d = c14.load(OUT / "demo.json")
    req = d["request"]
    best = min((r for r in d["runs"] if r["mode"] == "pairedall"), key=lambda r: r["chi2"])
    st = json.loads(json.dumps(req["structure"]))
    st["stacks"][0]["layers"][0].update(best["C"])
    st["stacks"][0]["layers"][1].update(best["Co"])
    st["stacks"][1]["layers"][0].update(best["top"])
    c = eng.call("calc_reflectivity", {"structure": st, "lambda": req["lambda"], "theta_min": 0.05,
                                       "theta_max": 6.0, "points": 5901, "delta_theta": req["resolution"],
                                       "polarization": "s", "r_min": 1e-8, "max_inline_points": 0})
    txt = (eng.work / c["file"]).read_text(encoding="utf-8")
    (OUT / "demo-curves.dat").write_text(
        f"# demo, best one-period fit (every box ticked): seed {best['seed']}, χ² {best['chi2']:.4f}, "
        f"scale ratio {best['scale_ratio']}, D {best['D']:.3f}" + chr(10) + txt, encoding="utf-8")
    print("wrote demo-curves.dat")


def main():
    what = sys.argv[1:] or ["coc4", "coc5", "control", "demo", "final", "curves"]
    eng = Engine()
    try:
        s = eng.describe()
        print(f"engine: X-Ray Calc {s['xraycalc3_exe_version']}, git {s['git_revision']}")
        for w in what:
            {"coc4": do_coc4, "coc5": do_coc5, "control": do_control, "demo": do_demo, "final": do_final, "curves": do_curves}[w](eng)
    finally:
        eng.close()


if __name__ == "__main__":
    main()
