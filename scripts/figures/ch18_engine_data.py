"""Chapter 18: judging the fits of Chapter 17.

The command-line server that ships with X-Ray Calc (XRC_MCP.exe in the build
folder, engine 3.9.4.1250 since the rerun of 2026-09-25), driven through xrc_engine.Engine. The book never
names the server.

  free     Periodic mode with the period free within ±10 % of the start period,
           as the GUI's Free period (X-Ray Calc 804ba07, default 10 %) does it.
           The final limits of Chapter 17 (coc4-final.json, coc5-final.json),
           the preset's five seeds, population 5000, 200 iterations, SeedR on.
           Out: coc4-free.json, coc5-free.json

  curves   the measured curve and the fitted curve of the CoC4 fit Chapter 17
           reports (Polynomial order 1, its best seed), and of the CoC5
           free-period fit (best seed), rerun with the same seed so the job
           folder holds them. calc.dat and measured.dat are at the anchored
           scale; the solved scale ratio is written into the header.
           Out: coc4-poly1-curves.dat, coc5-free-curves.dat

Every run here comes from an engine whose fit report applies the solved scale
itself (the Chapter 17 runs were rerun on 3.9.4.1250 on 2026-09-25; the first
Chapter 17 engine, git 1e40446, left the solved scale out and needed each ratio
divided by scale_ratio). The report's measured values are the measured curve
times the solved scale ratio, so its ratios and band means are the chart's as
they stand. For counts, the chart keeps the measured curve at the anchored
scale and draws the model divided by the ratio: both report values are divided
by scale_ratio (chart()).

Run:  python scripts/figures/ch18_engine_data.py [free|curves|numbers ...]
Out:  figures-src/ch18/
"""
import json
import math
import shutil
import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ch14_engine_data as c14  # noqa: E402
import ch16_engine_data as c16  # noqa: E402
import ch17_engine_data as c17  # noqa: E402
from xrc_engine import Engine  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
IN17 = ROOT / "figures-src" / "ch17"
OUT = ROOT / "figures-src" / "ch18"
SEEDS = c14.SEEDS


def base_request(eng, name):
    d = c14.load(IN17 / f"{name}-final.json")
    req = {**(c16.request() if name == "coc4" else c17.coc5_request(eng)[0]),
           "resolution": d["request"]["resolution"], "bounds": d["request"]["bounds"]}
    return req, d


def free_request(req):
    d0 = sum(x["thickness"] for x in req["structure"]["stacks"][0]["layers"])
    return {**req, "free": req["free"] + [{"target": "period", "stack": 0}],
            "bounds": req["bounds"] + [{"target": "period", "stack": 0,
                                        "min": d0 * 0.9, "max": d0 * 1.1}]}


def do_free(eng):
    for name in ("coc4", "coc5"):
        req, _ = base_request(eng, name)
        fr = free_request(req)
        runs = [c17.run(eng, fr, "periodic", s) for s in SEEDS]
        for r in runs:
            r["mode"] = "periodic_free"
        c17.OUT = OUT
        c17.save(f"{name}-free.json", {"request": {k: v for k, v in fr.items() if k != "curve"},
                                         "runs": runs})


def job_files(eng, request):
    """Run one fit and copy calc.dat and measured.dat out of its job folder."""
    job = eng.call("fit_xrr", request)["job_id"]
    while eng.call("job_wait", {"job_id": job, "wait_s": 600}).get("state") not in (
            "finished", "failed", "cancelled"):
        pass
    res = eng.call("job_result", {"job_id": job})
    folder = next(p for p in eng.work.rglob("calc.dat") if job in str(p)).parent
    return res, folder


def do_curves(eng):
    OUT.mkdir(parents=True, exist_ok=True)
    cases = [("coc4", "poly1", IN17 / "coc4-final.json", "coc4-poly1-curves.dat"),
             ("coc5", "periodic_free", OUT / "coc5-free.json", "coc5-free-curves.dat")]
    for name, mode, src, out in cases:
        req, _ = base_request(eng, name)
        d = c14.load(src)
        best = min((r for r in d["runs"] if r["mode"] == mode), key=lambda r: r["chi2"])
        if mode == "poly1":
            extra = c17.MODES["poly1"]
            body = {k: v for k, v in extra.items() if k != "poly_order"}
            opt = {**c17.OPT, "poly_order": extra["poly_order"]}
            request = {**req, **body, "optimizer": opt, "seed": best["seed"]}
        else:
            request = {**free_request(req), "optimizer": c17.OPT, "seed": best["seed"]}
        res, folder = job_files(eng, request)
        print(name, mode, "seed", best["seed"], "stored χ²", best["chi2"], "rerun χ²", res["chi2"],
              "scale ratio", res.get("scale_ratio"), flush=True)
        calc = (folder / "calc.dat").read_text(encoding="utf-8").splitlines()
        meas = (folder / "measured.dat").read_text(encoding="utf-8").splitlines()
        (OUT / out).write_text(
            f"# {name} {mode}, seed {best['seed']}, chi2 {res['chi2']}, "
            f"scale_ratio {res.get('scale_ratio')}, r_min {req['r_min']}\n"
            "# section calc (theta, R at the anchored scale)\n" + "\n".join(calc) +
            "\n# section measured (theta, I at the anchored scale)\n" + "\n".join(meas) + "\n",
            encoding="utf-8")
        for f in ("report.json",):
            if (folder / f).exists():
                shutil.copy(folder / f, OUT / out.replace("-curves.dat", "-report.json"))
        print("wrote", out)


# ---------------------------------------------------------------- numbers

def chart(run):
    """The report's checks at the chart's scale.

    The report's measured values are the measured curve times the solved scale ratio s, and
    its calculated values are the model. The chart keeps the measured curve at the anchored
    scale and draws the model divided by s, so both are divided by s; the ratios and the band
    means don't change. A report with no edge check (no first minimum) gives an empty edge."""
    s = run.get("scale_ratio") or 1.0
    orders = [{**o, "ratio_chart": o["r_calc"] / o["i_meas"], "r_chart": o["r_calc"] / s,
               "i_meas": o["i_meas"] / s} for o in run["orders"]]
    edge = [{**p, "ratio_chart": p["r_calc"] / p["i_meas"], "i_meas": p["i_meas"] / s}
            for p in ((run.get("edge") or {}).get("points") or [])]
    bands = [{**b, "mean_chart": b["mean"]} for b in run["bands"]]
    return orders, edge, bands


def sd(v):
    return st.stdev(v) if len(v) > 1 else 0.0


def numbers():
    lines = []
    p = lines.append
    sets = [("CoC4", IN17 / "coc4-final.json", OUT / "coc4-free.json"),
            ("CoC5", IN17 / "coc5-final.json", OUT / "coc5-free.json"),
            ("demo", IN17 / "demo.json", None)]
    for label, f, ffree in sets:
        runs = c14.load(f)["runs"]
        if ffree and ffree.exists():
            runs = runs + c14.load(ffree)["runs"]
        p(f"===== {label}")
        modes = {}
        for r in runs:
            modes.setdefault(r["mode"], []).append(r)
        for m, rs in modes.items():
            best = min(rs, key=lambda r: r["chi2"])
            p(f"-- {m}: χ² {[round(r['chi2'], 4) for r in rs]} best {best['chi2']:.4f} "
              f"(seed {best['seed']}) sd {sd([r['chi2'] for r in rs]):.4f}")
            for r in rs:
                o, e, b = chart(r)
                vis = [x for x in o if x["visible"]]
                p(f"   seed {r['seed']} χ² {r['chi2']:.4f} sr {r['scale_ratio']:.4f} | orders "
                  + " ".join(f"{x['n']}:{x['ratio_chart']:.2f}" for x in vis)
                  + " | fail " + ",".join(str(x['n']) for x in vis if abs(x['ratio_chart'] - 1) > 0.25)
                  + " | edge " + " ".join(f"{x['ratio_chart']:.2f}" for x in e)
                  + " | bands " + " ".join(f"{x['mean_chart']:+.3f}" for x in b)
                  + f" | max|band| {max(abs(x['mean_chart']) for x in b):.3f}")
            o, e, b = chart(best)
            p(f"   best-run order table (θ meas, θ calc, 2θ meas, I meas, R chart, ratio, visible):")
            for x in o:
                p(f"     {x['n']}: {x['theta_meas_deg']:.4f} {x['theta_calc_deg']:.4f} "
                  f"{2 * x['theta_meas_deg']:.3f} {x['i_meas']:.3e} {x['r_chart']:.3e} "
                  f"{x['ratio_chart']:.3f} {x['visible']}")
            p("   best-run edge (θ, 2θ, I, ratio): " + "; ".join(
                f"{x['theta_deg']:.4f} {2 * x['theta_deg']:.4f} {x['i_meas']:.4f} {x['ratio_chart']:.3f}"
                for x in e))
            p("   best-run bands (θ range, n, mean, rms): " + "; ".join(
                f"{x['theta_deg'][0]:.3f}-{x['theta_deg'][1]:.3f} n{x['n']} {x['mean_chart']:+.3f} "
                f"{x['rms']:.3f}" for x in b))
            if label == "demo":
                continue
            # spreads over the runs
            rows = {}
            for L in ("C", "Co", "top"):
                for q in ("thickness", "sigma", "density"):
                    rows[f"{L}.{q}"] = [r[L][q] for r in rs]
            rows["D (mean)"] = [r["D"] for r in rs]
            if "D_top" in rs[0]:
                rows["D top"] = [r["D_top"] for r in rs]
                rows["D bottom"] = [r["D_bottom"] for r in rs]
                rows["drift"] = [r["drift"] for r in rs]
                for L in ("C", "Co"):
                    if "thickness_profile" in rs[0][L]:
                        rows[f"{L}.H top"] = [r[L]["thickness_profile"][0] for r in rs]
                        rows[f"{L}.H bottom"] = [r[L]["thickness_profile"][-1] for r in rs]
            rows["top.H + C.H"] = [r["top"]["thickness"] + r["C"]["thickness"] for r in rs]
            p("   best run ± sd over the runs:")
            for k, v in rows.items():
                bv = v[rs.index(best)]
                p(f"     {k:14s} {bv:9.4f} ± {sd(v):.3f}   range {min(v):.3f}-{max(v):.3f}")
            p("   σ pairs (C, Co): " + str([(round(r['C']['sigma'], 2), round(r['Co']['sigma'], 2))
                                          for r in rs]))
            p("   near bounds (best run): " + json.dumps(best.get("near_bounds")))
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "numbers.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


def main():
    what = sys.argv[1:] or ["free", "curves", "numbers"]
    if what == ["numbers"]:
        numbers()
        return
    eng = Engine()
    try:
        s = eng.describe()
        print(f"engine: X-Ray Calc {s['xraycalc3_exe_version']}, git {s['git_revision']}")
        for w in what:
            if w == "numbers":
                numbers()
            else:
                {"free": do_free, "curves": do_curves}[w](eng)
    finally:
        eng.close()


if __name__ == "__main__":
    main()
