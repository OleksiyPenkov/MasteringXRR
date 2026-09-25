"""Chapter 19: testing the model before blaming the measurement.

The command-line server that ships with X-Ray Calc (XRC_MCP.exe in the build
folder, engine 3.9.4.1270 since the rerun of 2026-09-25), driven through xrc_engine.Engine. The book never
names the server.

Every run starts from the Chapter 18 request for the curve: Periodic mode with
the period free within ±10 % of the start period (the GUI's Free period), the
final limits of Chapter 17, the preset's five seeds, population 5000, 200
iterations, SeedR on (figures-src/ch18/coc4-free.json, coc5-free.json).

  inter    CoC4 and CoC5 with a CoC interlayer on each interface of the period.
           The period, top to bottom: C, CoC (C grown on Co), Co, CoC (Co grown
           on C). Each interlayer starts at 4 Å, and C and Co start 4 Å thinner,
           so the start period is unchanged. The assignment (procedure §10.10) is
           set through the limits, as Chapter 18 teaches: the wider interlayer
           4-15 Å, the narrower 0.1-4 Å.
             upper   wider CoC under C (C on Co)
             lower   wider CoC under Co (Co on C)
             equal   both held at one fixed thickness h (not free), scanned
                     over EQUAL_H. Neither the GUI nor the engine can tie two
                     layers during a fit (the box "Pair to another layer" only
                     moves the partner's H while you edit; X-Ray Calc session,
                     2026-09-25), so the equal case is a profile over h.
           CoC ρ 4.34-6.2 g/cm³ (the default rule, 0.7-1.0 of the table bulk 6.2; start
           5.58), σ 1-8 Å. The limits of C and Co go
           down by 8 Å at the minimum, room for two interlayers. Then the
           near-bound rule of Chapter 15, as in ch17_engine_data.do_final: any
           limit a run ends within 5 % of the range from moves out by half the
           range, except a σ at 0, a density at the bulk ceiling and the 4 Å
           split between the two interlayers. Two rounds for upper and lower
           (CoC4 upper, run first, had five); none for the equal profile.
           Out: coc4-inter.json, coc5-inter.json

  nosurf   CoC4 without the contamination layer: the period stack alone, the
           same mode, limits and seeds. Out: coc4-nosurf.json
  withsurf the Chapter 18 CoC4 fit rerun with the same seeds, to keep its
           fringe report. Out: coc4-withsurf.json

Run:  python scripts/figures/ch19_engine_data.py [inter|nosurf|numbers ...]
Out:  figures-src/ch19/
"""
import json
import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ch14_engine_data as c14  # noqa: E402
import ch17_engine_data as c17  # noqa: E402
import ch18_engine_data as c18  # noqa: E402
from xrc_engine import Engine  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
IN18 = ROOT / "figures-src" / "ch18"
OUT = ROOT / "figures-src" / "ch19"
SEEDS = c14.SEEDS
OPT = c17.OPT
SPLIT = 4.0
# CoC is not in the preset's materials.named, so its default rule applies: 0.7, 1.0 and 0.9 of the
# bulk density of its Henke table, 6.2 g/cm3 (procedure §7.3). The first runs (kept as
# *-inter-v1-rho2-879.json) used 2.0-8.79 and broke the bulk ceiling of §7.6.
IL_RHO = (round(0.7 * 6.2, 3), 6.2, round(0.9 * 6.2, 3))
IL_START = 4.0
CEILING = {"C": 2.4, "Co": 8.79, "CoC": 6.2}   # CoC: the Nro of Henke/CoC.bin
ASSIGN = {"upper": ((SPLIT, 15.0), (0.1, SPLIT)),
          "lower": ((0.1, SPLIT), (SPLIT, 15.0)),
          "equal": None}
EQUAL_H = [1.0, 2.0, 4.0, 6.0]
ROUNDS = 2          # near-bound rounds for upper and lower (coc4 upper ran 5 before the cap)


def base(eng, name):
    """The Chapter 18 free-period request, with the curve."""
    req, _ = c18.base_request(eng, name)
    return c18.free_request(req)


def with_interlayers(req, assign, h=None):
    s = json.loads(json.dumps(req["structure"]))
    c, co = s["stacks"][0]["layers"]
    h0 = IL_START if h is None else h
    c = {**c, "thickness": round(c["thickness"] - h0, 4)}
    co = {**co, "thickness": round(co["thickness"] - h0, 4)}
    il = {"material": "CoC", "thickness": h0, "sigma": 4.0, "density": IL_RHO[2]}
    s["stacks"][0]["layers"] = [c, dict(il), co, dict(il)]
    il_par = ["sigma", "density"] if assign == "equal" else ["thickness", "sigma", "density"]
    free = [{"stack": 0, "layer": i, "parameters": ["thickness", "sigma", "density"] if i in (0, 2) else il_par}
            for i in range(4)]
    free += [{"stack": 1, "layer": 0, "parameters": ["thickness", "sigma", "density"]},
             {"target": "period", "stack": 0}]
    old = {(b.get("stack"), b.get("layer"), b.get("parameter")): b for b in req["bounds"] if "layer" in b}
    b = []
    for new_l, old_l in ((0, 0), (2, 1)):
        for p in ("thickness", "sigma", "density"):
            ob = old[(0, old_l, p)]
            lo = max(0.1, ob["min"] - 8) if p == "thickness" else ob["min"]
            b.append({"stack": 0, "layer": new_l, "parameter": p, "min": lo, "max": ob["max"]})
    (hu, hl) = ASSIGN[assign] or ((h0, h0), (h0, h0))
    for new_l, hb in ((1, hu), (3, hl)):
        if assign != "equal":
            b.append({"stack": 0, "layer": new_l, "parameter": "thickness", "min": hb[0], "max": hb[1]})
        b += [{"stack": 0, "layer": new_l, "parameter": "sigma", "min": 1.0, "max": 8.0},
              {"stack": 0, "layer": new_l, "parameter": "density", "min": IL_RHO[0], "max": IL_RHO[1]}]
    b += [x for x in req["bounds"] if x.get("stack") == 1]
    b += [x for x in req["bounds"] if x.get("target") == "period"]
    return {**req, "structure": s, "free": free, "bounds": b}


def without_surface(req):
    s = json.loads(json.dumps(req["structure"]))
    s["stacks"] = s["stacks"][:1]
    free = [x for x in req["free"] if x.get("stack") != 1 or x.get("target") == "period"]
    bounds = [x for x in req["bounds"] if x.get("stack") != 1 or x.get("target") == "period"]
    return {**req, "structure": s, "free": free, "bounds": bounds}


def summary(layer):
    return {k: layer[k] for k in ("material", "thickness", "sigma", "density")}


def run(eng, req, label, seed):
    r = eng.fit({**req, "optimizer": OPT, "seed": seed})
    stacks = r["fitted_structure"]["stacks"]
    period = [summary(x) for x in stacks[0]["layers"]]
    rep = r.get("report", {})
    row = {"label": label, "seed": seed, "chi2": r["chi2"], "chi2_plain": r.get("chi2_plain"),
           "scale_ratio": r.get("scale_ratio"), "scale_clamped": r.get("scale_clamped"),
           "near_bounds": rep.get("near_bounds"), "orders": rep.get("orders"),
           "edge": rep.get("edge"), "bands": rep.get("bands"), "fringes": rep.get("fringes"),
           "elapsed_s": r.get("elapsed_s"), "D": sum(x["thickness"] for x in period),
           "period": period, "top": summary(stacks[1]["layers"][0]) if len(stacks) > 1 else None}
    vis = [o for o in row["orders"] or [] if o["visible"]]
    print(f"{label:12s} seed {seed}: χ² {row['chi2']:.4f} D {row['D']:.3f} "
          + " ".join(f"{x['material']}:{x['thickness']:.2f}/{x['sigma']:.2f}/{x['density']:.2f}" for x in period)
          + " | " + " ".join(f"{o['n']}:{o['r_calc'] / o['i_meas']:.2f}" for o in vis)
          + f" | nb {[(n.get('layer'), n.get('parameter'), n.get('bound')) for n in row['near_bounds'] or []]}",
          flush=True)
    return row


def widen(req, runs):
    """One round of the near-bound rule over every layer limit (Chapter 15)."""
    bounds = json.loads(json.dumps(req["bounds"]))
    mats = {(si, li): lay["material"] for si, s_ in enumerate(req["structure"]["stacks"])
            for li, lay in enumerate(s_["layers"])}
    mats[(1, 0)] = "top"
    changes = []
    for b in bounds:
        if "layer" not in b:
            continue
        lo, hi = b["min"], b["max"]
        span = hi - lo
        for r in runs:
            for nb in r["near_bounds"] or []:
                if (nb.get("stack"), nb.get("layer"), nb.get("parameter")) != (b["stack"], b["layer"], b["parameter"]):
                    continue
                if nb["margin_fraction"] > 0.05:
                    continue
                split = b["parameter"] == "thickness" and mats[(b["stack"], b["layer"])] == "CoC"
                if nb["bound"] == "min" and b["min"] == lo and not (split and lo == SPLIT):
                    # a thickness needs a limit above 0; a density of 0 means "bulk" to the engine
                    floor = {"thickness": 0.1, "density": 0.1}.get(b["parameter"], 0.0)
                    if lo > floor:
                        b["min"] = round(max(floor, lo - span / 2), 3)
                if nb["bound"] == "max" and b["max"] == hi and not (split and hi == SPLIT):
                    cap = CEILING.get(mats[(b["stack"], b["layer"])]) if b["parameter"] == "density" else None
                    if cap is None or hi < cap:
                        b["max"] = round(hi + span / 2 if cap is None else min(cap, hi + span / 2), 3)
        if (b["min"], b["max"]) != (lo, hi):
            changes.append({**{k: b[k] for k in ("stack", "layer", "parameter")}, "from": [lo, hi],
                            "to": [b["min"], b["max"]]})
    return bounds, changes


def save(name, obj):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(json.dumps(obj, indent=1), encoding="utf-8")
    print("wrote", name)


def do_inter(eng, names=("coc4", "coc5"), assigns=("upper", "lower", "equal")):
    for name in names:
        f = OUT / f"{name}-inter.json"
        out = c14.load(f) if f.exists() else {}
        cases = [(a, None) for a in assigns if a != "equal"]
        cases += [(f"equal-{h:g}", h) for h in EQUAL_H] if "equal" in assigns else []
        for a, h in cases:
            if a in out:
                continue
            req = with_interlayers(base(eng, name), "equal" if h is not None else a, h)
            history = []
            rounds = 1 if h is not None else ROUNDS
            for rnd in range(rounds):
                runs = [run(eng, req, f"{name}-{a}", s) for s in SEEDS]
                bounds, changes = widen(req, runs)
                history.append({"round": rnd, "changes": changes})
                print(name, a, "round", rnd, "changes", changes, flush=True)
                if not changes or rnd == rounds - 1:
                    break
                req = {**req, "bounds": bounds}
            out[a] = {"request": {k: v for k, v in req.items() if k != "curve"},
                      "widening": history, "runs": runs}
            save(f"{name}-inter.json", out)


def do_nosurf(eng):
    req = without_surface(base(eng, "coc4"))
    runs = [run(eng, req, "coc4-nosurf", s) for s in SEEDS]
    save("coc4-nosurf.json", {"request": {k: v for k, v in req.items() if k != "curve"}, "runs": runs})


def do_withsurf(eng):
    """The Chapter 18 CoC4 fit again (same request and seeds), to keep its fringe report."""
    req = base(eng, "coc4")
    runs = [run(eng, req, "coc4-withsurf", s) for s in SEEDS]
    save("coc4-withsurf.json", {"request": {k: v for k, v in req.items() if k != "curve"}, "runs": runs})


# ---------------------------------------------------------------- numbers

def sd(v):
    return st.stdev(v) if len(v) > 1 else 0.0


def edge_text(r):
    # The report has no edge check when the calculated curve shows no first
    # minimum after the first fitted point (unit_MCPFitReport.pas).
    e = r.get("edge")
    if not e or not e.get("points"):
        return "none (no first minimum)"
    return " ".join(f"{p['r_calc'] / p['i_meas']:.2f}" for p in e["points"])


def line(r):
    vis = [o for o in r["orders"] if o["visible"]]
    return (f"   seed {r['seed']} χ² {r['chi2']:.4f} plain {r['chi2_plain'] or 0:.4f} sr {r['scale_ratio']:.4f} D {r['D']:.3f} | orders "
            + " ".join(f"{o['n']}:{o['r_calc'] / o['i_meas']:.2f}" for o in vis)
            + " | fail " + ",".join(str(o['n']) for o in vis if abs(o['r_calc'] / o['i_meas'] - 1) > 0.25)
            + " | edge " + edge_text(r)
            + " | bands " + " ".join(f"{b['mean']:+.3f}" for b in r["bands"])
            + (f" | fringes meas {r['fringes'].get('measured', {}).get('mean_contrast')} "
               f"calc {r['fringes'].get('calculated', {}).get('mean_contrast')}" if r.get("fringes") else ""))


def numbers():
    lines = []
    p = lines.append
    for f in ("coc4-free.json", "coc5-free.json"):
        d = c14.load(IN18 / f)
        p(f"===== baseline {f}")
        for r in d["runs"]:
            p(f"   seed {r['seed']} χ² {r['chi2']:.4f}")
    for name in ("coc4", "coc5"):
        f = OUT / f"{name}-inter.json"
        if not f.exists():
            continue
        d = c14.load(f)
        for a, blk in d.items():
            rs = blk["runs"]
            best = min(rs, key=lambda r: r["chi2"])
            p(f"===== {name} {a}: χ² {[round(r['chi2'], 4) for r in rs]} best {best['chi2']:.4f} sd {sd([r['chi2'] for r in rs]):.4f}")
            p(f"   widening: {blk['widening']}")
            for r in rs:
                p(line(r))
            for i, lay in enumerate(best["period"]):
                vals = {q: [r["period"][i][q] for r in rs] for q in ("thickness", "sigma", "density")}
                p(f"     {i} {lay['material']:4s} " + "  ".join(
                    f"{q[0]} {lay[q]:.3f}±{sd(v):.3f}" for q, v in vals.items()))
            p(f"     top {best['top']}")
            p(f"     near bounds (best): {best['near_bounds']}")
    f = OUT / "coc4-nosurf.json"
    if f.exists():
        rs = c14.load(f)["runs"]
        best = min(rs, key=lambda r: r["chi2"])
        p(f"===== coc4 nosurf: χ² {[round(r['chi2'], 4) for r in rs]} best {best['chi2']:.4f}")
        for r in rs:
            p(line(r))
        for i, lay in enumerate(best["period"]):
            vals = {q: [r["period"][i][q] for r in rs] for q in ("thickness", "sigma", "density")}
            p(f"     {i} {lay['material']:4s} " + "  ".join(
                f"{q[0]} {lay[q]:.3f}±{sd(v):.3f}" for q, v in vals.items()))
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "numbers.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


def main():
    what = sys.argv[1:] or ["inter", "nosurf", "numbers"]
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
            elif w.startswith("inter:"):
                _, n, a = w.split(":")
                do_inter(eng, (n,), (a,))
            else:
                {"inter": do_inter, "nosurf": do_nosurf, "withsurf": do_withsurf}[w](eng)
    finally:
        eng.close()


if __name__ == "__main__":
    main()
