"""Chapter 22: graded multilayers and supermirrors.

The command-line server that ships with X-Ray Calc (XRC_MCP.exe in the build
folder), driven through xrc_engine.Engine. The book never names the server.

The measured curves come from the X-Ray Calc 3 paper's project files (Penkov et
al. 2024), copied to figures-src/ch22/:
  W-BN(221101A)_BF.xrcx          W/BN on the Empyrean, the paper's Fig 10
  Sb-B4C_120925_Fitted_Best.xrcx Sb/B4C supermirror (DRON-3M), the paper's Fig 11
  Mo-Si_240204E_Fitted_best.xrcx a periodic Mo/Si mirror, for contrast

Tasks
  wbn   W/BN in Polynomial mode. The model of the author's project (C and BN on
        top, 60 × [W/BN], a W underlayer, Si), started from its values, with its
        limits where it has them. N = 60 (the model) and N = 36 (the deposition
        record: "Deposition stuck after 36 pairs"). Modes: uniform (every box
        ticked: one period, free to float), poly1/poly2/poly3 (H profiled, σ and
        ρ paired), poly3s (H and σ profiled, ρ paired). Five seeds each.
        λ 1.54043 Å and Δθ 0.015° from the project; R min 5e-7 (the project's);
        the range from θ_max to the end of the curve; the scale solved within 0.2.
        Out: wbn.json

  wbn-widening  the same with the near-bound rule applied first (a finding: it runs
        away). Out: wbn-widening.json
  wbn-curves  the best W/BN runs rerun with their seeds and calculated. Out: wbn-curves.json
  sb    the author's Sb/B4C fit scored. Out: sb.json
  sb-engine  the Sb/B4C supermirror in Irregular mode, fixed seeds: five runs from the
        stack values with Smooth off, five with Smooth on, five from the author's
        table; the author's limits and pairing; 5000 × 200. Needs a build with
        Irregular mode in the server (after 3.9.4.1130). Out: sb-engine.json
  sb-engine-curves  the best Smooth-off and Smooth-on runs calculated.
        Out: sb-engine-curves.json

Set XRC_MCP_EXE to a copy of the server; never run it from the build folder.

Run:  python scripts/figures/ch22_engine_data.py wbn
Out:  figures-src/ch22/
"""
import json
import sys
import zipfile
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from xrc_engine import Engine  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "figures-src" / "ch22"
SEEDS = [20260921, 20260922, 20260923, 20260924, 20260925]
OPT = {"iterations": 200, "population": 5000, "range_seed": True}


def curve(project):
    """The measured curve stored in a project file, as [θ, R]."""
    z = zipfile.ZipFile(OUT / project)
    name = next(n for n in z.namelist() if n.startswith("data_"))
    rows = []
    for ln in z.read(name).decode("utf-8-sig").splitlines()[2:]:
        p = ln.split()
        try:
            t2, r = float(p[0]), float(p[1])
        except (ValueError, IndexError):
            continue
        if r > 0:
            rows.append([t2 / 2, r])
    return rows


def theta_max(rows):
    return max((r for r in rows if r[0] < 0.5), key=lambda r: r[1])[0]


def lay(m, h, s, r):
    return {"material": m, "thickness": h, "sigma": s, "density": r}


# ---------------------------------------------------------------- W/BN
WBN = "W-BN(221101A)_BF.xrcx"
# The start values are the author's project (2023). The limits: H and σ from the
# project; ρ by the book's default rule, 0.7-1.0 of the bulk density in the
# program's table (Henke/*.bin: W 19.26, BN 2.10), except the top C layer
# (0.6-2.4: contamination to sputtered carbon, Chapter 15).
BULK = {"W": 19.26, "BN": 2.10}
WBN_LAYERS = {  # (stack, layer): (start, H limits, σ limits, ρ limits)
    (0, 0): (lay("W", 305.87, 1.48, 18.94), (280, 350), (1, 5), (13.48, 19.26)),   # underlayer
    (1, 0): (lay("W", 13.25, 3.06, 17.41), (10, 30), (1, 5), (13.48, 19.26)),      # period: W
    (1, 1): (lay("BN", 26.10, 3.11, 2.00), (15, 40), (1, 5), (1.47, 2.10)),        # period: BN
    (2, 0): (lay("C", 66.60, 4.0, 1.60), (30, 90), (1, 10), (0.6, 2.4)),           # top
    (2, 1): (lay("BN", 113.26, 2.79, 1.70), (90, 130), (1, 10), (1.47, 2.10)),     # cap
}
CEIL = {(0, 0): 19.26, (1, 0): 19.26, (1, 1): 2.10, (2, 0): 2.4, (2, 1): 2.10}
# the layers of a stack run surface first; the stacks run substrate first
WBN_MODES = {"uniform": {"profile": True, "paired": ["thickness", "sigma", "density"], "poly_order": 1},
             "poly1": {"profile": True, "paired": ["sigma", "density"], "poly_order": 1},
             "poly2": {"profile": True, "paired": ["sigma", "density"], "poly_order": 2},
             "poly3": {"profile": True, "paired": ["sigma", "density"], "poly_order": 3},
             "poly3s": {"profile": True, "paired": ["density"], "poly_order": 3}}


def wbn_request(n):
    rows = curve(WBN)
    st = {"substrate": {"material": "Si", "sigma": 5.0, "density": 2.2},
          "stacks": [{"N": 1, "layers": [WBN_LAYERS[(0, 0)][0]]},
                     {"N": n, "layers": [WBN_LAYERS[(1, 0)][0], WBN_LAYERS[(1, 1)][0]]},
                     {"N": 1, "layers": [WBN_LAYERS[(2, 0)][0], WBN_LAYERS[(2, 1)][0]]}]}
    free = [{"stack": s, "layer": l, "parameters": ["thickness", "sigma", "density"]} for s, l in WBN_LAYERS]
    bounds = [{"stack": s, "layer": l, "parameter": p, "min": v[0], "max": v[1]}
              for (s, l), (_, *lims) in WBN_LAYERS.items()
              for p, v in zip(("thickness", "sigma", "density"), lims)]
    return {"curve": rows, "lambda": 1.54043, "polarization": "s", "structure": st, "free": free,
            "bounds": bounds, "scale": "auto", "auto_theta_max": 0.5, "scale_solve": True,
            "scale_solve_window": 0.2, "r_min": 5e-7,
            "theta_range": {"min": theta_max(rows), "max": rows[-1][0]}, "resolution": 0.015,
            "chi2": {"theta_weight": 0, "point_weight": True}, "smooth": {"passes": 0},
            "points_inline_max": 0}


def summary(layer):
    out = {k: layer[k] for k in ("thickness", "sigma", "density")}
    for k in ("thickness_profile", "sigma_profile", "density_profile"):
        if k in layer:
            out[k] = layer[k]
    return out


def fit(eng, req, extra, seed):
    opt = {**OPT, "poly_order": extra["poly_order"]}
    body = {k: v for k, v in extra.items() if k != "poly_order"}
    r = eng.fit({**req, **body, "optimizer": opt, "seed": seed})
    return r


def row_of(r, n, mode, seed):
    st = r["fitted_structure"]["stacks"]
    w, bn = (summary(x) for x in st[1]["layers"])
    pw = np.array(w.get("thickness_profile", [w["thickness"]] * n))
    pb = np.array(bn.get("thickness_profile", [bn["thickness"]] * n))
    d = pw + pb
    rep = r.get("report", {})
    row = {"N": n, "mode": mode, "seed": seed, "chi2": r["chi2"], "scale": r.get("scale"),
           "scale_ratio": r.get("scale_ratio"), "scale_clamped": r.get("scale_clamped"),
           "D_top": float(d[0]), "D_bottom": float(d[-1]), "D_mean": float(d.mean()),
           "W": w, "BN": bn, "under": summary(st[0]["layers"][0]),
           "top": [summary(x) for x in st[2]["layers"]],
           "near_bounds": rep.get("near_bounds"), "orders": rep.get("orders"),
           "bands": rep.get("bands"), "edge": rep.get("edge"), "elapsed_s": r.get("elapsed_s")}
    print(f"N {n} {mode:8s} {seed}: χ² {row['chi2']:.4f} D {d[0]:.2f}->{d[-1]:.2f} "
          f"W {pw[0]:.2f}->{pw[-1]:.2f} BN {pb[0]:.2f}->{pb[-1]:.2f} σW {w['sigma']:.2f} "
          f"σBN {bn['sigma']:.2f} top C {row['top'][0]['thickness']:.1f} BN {row['top'][1]['thickness']:.1f} "
          f"nb {[(b['stack'], b['layer'], b['parameter'][0], b['bound']) for b in row['near_bounds'] or []]}",
          flush=True)
    return row


def widen(req, rows):
    """One round of the near-bound rule (Chapter 15): a limit that any run ends on
    or within 5 % of the range from moves out by half the range, except σ at 0,
    H at 1 Å and ρ at the bulk ceiling. Only runs within twice the round's best χ²
    count. Returns the list of changes."""
    changes = []
    best = min(r["chi2"] for r in rows)
    for row in (r for r in rows if r["chi2"] <= 2 * best):  # a run that got lost is no evidence
        for nb in row["near_bounds"] or []:
            if nb.get("target") != "layer":
                continue
            b = next(x for x in req["bounds"] if x["stack"] == nb["stack"] and x["layer"] == nb["layer"]
                     and x["parameter"] == nb["parameter"])
            if nb["parameter"] == "density" and nb["bound"] == "max" and b["max"] >= CEIL[(nb["stack"], nb["layer"])]:
                continue
            floor = 1.0 if nb["parameter"] == "thickness" else 0.0
            if nb["bound"] == "min" and b["min"] <= floor:
                continue
            half = (b["max"] - b["min"]) / 2
            if nb["bound"] == "min":
                new = max(floor, round(b["min"] - half, 3))
                changes.append((nb["stack"], nb["layer"], nb["parameter"], "min", b["min"], new))
                b["min"] = new
            else:
                new = round(b["max"] + half, 3)
                if nb["parameter"] == "density":
                    new = min(new, CEIL[(nb["stack"], nb["layer"])])
                changes.append((nb["stack"], nb["layer"], nb["parameter"], "max", b["max"], new))
                b["max"] = new
    return changes


def do_wbn_widening(eng):
    """The near-bound rule applied first (kept as a finding: on N = 36 it ran away
    through the weakly fixed underlayer and top layers). Out: wbn-widening.json"""
    out = {}
    for n in (60, 36):
        req = wbn_request(n)
        history = []
        for rnd in range(4):
            rows = [row_of(fit(eng, req, WBN_MODES[m], SEEDS[0]), n, m, SEEDS[0]) for m in WBN_MODES]
            ch = widen(req, rows)
            history.append(ch)
            print("round", rnd, "widened", ch, flush=True)
            if not ch:
                break
        runs = [row_of(fit(eng, req, extra, seed), n, mode, seed)
                for mode, extra in WBN_MODES.items() for seed in SEEDS]
        out[str(n)] = {"request": {k: v for k, v in req.items() if k != "curve"}, "widening": history,
                       "runs": runs}
        save("wbn-widening.json", out)


def do_wbn(eng):
    """The chapter's runs: the project's limits, no widening. Out: wbn.json"""
    out = {}
    for n in (60, 36):
        req = wbn_request(n)
        runs = [row_of(fit(eng, req, extra, seed), n, mode, seed)
                for mode, extra in WBN_MODES.items() for seed in SEEDS]
        out[str(n)] = {"request": {k: v for k, v in req.items() if k != "curve"}, "runs": runs}
        save("wbn.json", out)


WBN_CURVES = [("36", "uniform"), ("36", "poly1"), ("36", "poly2"), ("60", "poly2")]


def do_wbn_curves(eng):
    """Figure curves: the best run of each case, rerun with its seed (the same
    fit), then calculated over the measured range with its thickness profiles.
    Out: wbn-curves.json"""
    d = json.loads((OUT / "wbn.json").read_text(encoding="utf-8"))
    res = {}
    for n, mode in WBN_CURVES:
        best = min((r for r in d[n]["runs"] if r["mode"] == mode), key=lambda r: r["chi2"])
        req = wbn_request(int(n))
        r = fit(eng, req, WBN_MODES[mode], best["seed"])
        st = r["fitted_structure"]
        c = eng.call("calc_reflectivity", {"structure": st, "lambda": req["lambda"], "theta_min": 0.1,
                                           "theta_max": 6.0, "points": 5901,
                                           "delta_theta": req["resolution"], "polarization": "s",
                                           "r_min": 1e-9, "max_inline_points": 0})
        txt = (eng.work / c["file"]).read_text(encoding="utf-8")
        arr = [[float(x) for x in ln.split()[:2]] for ln in txt.splitlines() if ln and ln[0].isdigit()]
        res[f"{n}-{mode}"] = {"seed": best["seed"], "chi2": r["chi2"], "chi2_table": best["chi2"],
                              "scale": r.get("scale"), "scale_ratio": r.get("scale_ratio"),
                              "structure": st, "calc": arr}
        print(n, mode, "chi2", r["chi2"], "table", best["chi2"], "scale", r.get("scale"), r.get("scale_ratio"),
              flush=True)
    save("wbn-curves.json", res)


# ---------------------------------------------------------------- Sb/B4C
SB = "Sb-B4C_120925_Fitted_Best.xrcx"


def project_model(path):
    """The active model of a saved project: its stacks as the program lists them
    (surface first), each layer with its per-period profiles if the Table holds them."""
    import re
    z = zipfile.ZipFile(path)
    dsc = z.read("project.dsc")
    ini = z.read("params.dsc").decode("utf-8-sig")
    found = []
    for off in (0, 1):
        text = dsc[off:].decode("utf-16-le", "replace")
        for m in re.finditer(r'\{"Stacks".*?"Subs":\{[^}]*\}\}', text):
            found.append(json.loads(m.group(0)))
    # the model with per-period profiles is the fitted one
    model = max(found, key=lambda d: sum(L.get("ProfileH", "").count(";") for st in d["Stacks"] for L in st["Layers"]))
    return model, ini


def expand(model):
    """The engine's structure (stacks substrate first) with every period of a
    repeating stack written out as its own stack, from the Table's profiles."""
    stacks = []
    for st in model["Stacks"]:
        n = st["N"]
        per = []
        for k in range(n):
            layers = []
            for L in st["Layers"]:
                def val(key, prof, paired):
                    v = [float(x) for x in L.get(prof, "").split(";") if x.strip()]
                    return v[k] if len(v) == n and n > 1 and not L.get(paired) else L[key]
                layers.append({"material": L["M"], "thickness": val("H", "ProfileH", "HP"),
                               "sigma": val("s", "ProfileS", "SP"), "density": val("r", "ProfileR", "RP")})
            per.append({"N": 1, "layers": layers})
        stacks += per                       # period 1 (the surface) first
    stacks.reverse()                         # the engine wants the substrate first
    sub = model["Subs"]
    return {"substrate": {"material": sub["M"], "sigma": sub["s"], "density": sub["r"]}, "stacks": stacks}


def score(eng, structure, rows, resolution=0.015, r_min=5e-7, rng=None):
    """χ² of a structure with a 1-iteration, 2-particle job and nothing free
    except the top layer's density held in place by a zero-width window."""
    req = {"curve": rows, "lambda": 1.54043, "polarization": "s", "structure": structure,
           "free": [{"stack": len(structure["stacks"]) - 1, "layer": 0, "parameters": ["density"]}],
           "bounds": [{"stack": len(structure["stacks"]) - 1, "layer": 0, "parameter": "density",
                       "min": structure["stacks"][-1]["layers"][0]["density"] * 0.999999,
                       "max": structure["stacks"][-1]["layers"][0]["density"] * 1.000001}],
           "scale": "auto", "auto_theta_max": 0.5, "scale_solve": True, "scale_solve_window": 0.2,
           "r_min": r_min, "theta_range": rng or {"min": rows[0][0], "max": rows[-1][0]},
           "resolution": resolution, "chi2": {"theta_weight": 0, "point_weight": True},
           "smooth": {"passes": 0}, "points_inline_max": 0,
           "optimizer": {"iterations": 1, "population": 2, "range_seed": False}, "seed": 1}
    return eng.fit(req)


def do_sb(eng):
    """Score the author's fit (its per-period Table, written out as N = 1 stacks) with
    the engine, and keep its thickness per period. (It also scored any GUI runs in
    figures-src/ch22/gui/; the GUI runs of 2026-09-25 were withdrawn, because GUI
    Irregular fits up to 3.9.4.1130 lose their pairing at the first shake.)
    Out: sb.json"""
    rows = curve(SB)
    out = {"author": None, "runs": []}
    files = [("author", OUT / SB)] + [(f.stem, f) for f in sorted((OUT / "gui").glob("sb-s*-r*.xrcx"))]
    for tag, f in files:
        model, ini = project_model(f)
        st = expand(model)
        r = score(eng, st, rows)
        main = next(x for x in model["Stacks"] if x["N"] > 1)
        per = {}
        for L in main["Layers"]:
            v = [float(x) for x in L.get("ProfileH", "").split(";") if x.strip()]
            per[L["M"]] = v if len(v) == main["N"] and not L.get("HP") else [L["H"]] * main["N"]
        row = {"tag": tag, "chi2": r["chi2"], "chi2_plain": r.get("chi2_plain"), "scale_ratio": r.get("scale_ratio"),
               "smooth": "Smooth=1" in ini or "Smooth=True" in ini, "thickness": per,
               "top": [(L["M"], L["H"], L["s"], L["r"]) for L in model["Stacks"][0]["Layers"]],
               "main": [(L["M"], L["H"], L["s"], L["r"], L.get("HP"), L.get("SP"), L.get("RP")) for L in main["Layers"]]}
        print(tag, "χ²", round(r["chi2"], 4), "smooth", row["smooth"], flush=True)
        if tag == "author":
            out["author"] = row
        else:
            out["runs"].append(row)
    save("sb.json", out)


def sb_request(start_from_table=False):
    """The author's Sb/B4C project as an Irregular fit request: its model (period 1
    values, or the Table's per-period values), its limits and pairing, every
    parameter free; λ 1.54043 Å, Δθ 0.015°, R min 5e-7, PW χ² on, TW χ² none, the
    scale solved within 0.2, the whole measured range."""
    model, ini = project_model(OUT / SB)
    rows = curve(SB)
    gui = model["Stacks"]                      # surface first: Top, Main
    stacks, bounds, free, paired = [], [], [], []
    for gi, st in enumerate(reversed(gui)):    # the engine wants the substrate first
        layers = []
        for li, L in enumerate(st["Layers"]):
            lay = {"material": L["M"], "thickness": L["H"], "sigma": L["s"], "density": L["r"]}
            if start_from_table and st["N"] > 1:
                for key, prof, flag in (("thickness", "ProfileH", "HP"), ("sigma", "ProfileS", "SP"),
                                        ("density", "ProfileR", "RP")):
                    v = [float(x) for x in L.get(prof, "").split(";") if x.strip()]
                    if len(v) == st["N"] and not L.get(flag):
                        lay[key + "_profile"] = v
            layers.append(lay)
            free.append({"stack": gi, "layer": li, "parameters": ["thickness", "sigma", "density"]})
            for par, lo, hi in (("thickness", "Hmin", "Hmax"), ("sigma", "Smin", "Smax"),
                                ("density", "Rmin", "Rmax")):
                bounds.append({"stack": gi, "layer": li, "parameter": par, "min": L[lo], "max": L[hi]})
            if st["N"] > 1:
                pp = [par for par, flag in (("thickness", "HP"), ("sigma", "SP"), ("density", "RP")) if L.get(flag)]
                if pp:
                    paired.append({"stack": gi, "layer": li, "parameters": pp})
        stacks.append({"N": st["N"], "layers": layers})
    sub = model["Subs"]
    return {"curve": rows, "lambda": 1.54043, "polarization": "s",
            "structure": {"substrate": {"material": sub["M"], "sigma": sub["s"], "density": sub["r"]},
                          "stacks": stacks},
            "mode": "irregular", "paired": paired, "free": free, "bounds": bounds,
            "start_profiles": start_from_table,
            "scale": "auto", "auto_theta_max": 0.5, "scale_solve": True, "scale_solve_window": 0.2,
            "r_min": 5e-7, "theta_range": {"min": rows[0][0], "max": rows[-1][0]}, "resolution": 0.015,
            "chi2": {"theta_weight": 0, "point_weight": True}, "smooth": {"passes": 0},
            "points_inline_max": 0}


def do_sb_engine(eng):
    """The Sb/B4C supermirror in Irregular mode with fixed seeds: five runs from the
    single stack values with Smooth off, five with Smooth on (window automatic),
    and five from the author's per-period table. Population 5000, 200 iterations,
    SeedR on. Out: sb-engine.json"""
    out = {}
    for case, table, smooth in (("off", False, False), ("on", False, True), ("table", True, False)):
        req = sb_request(table)
        runs = []
        for seed in SEEDS:
            opt = {**OPT, "period_smooth": True, "period_smooth_window": -1} if smooth else dict(OPT)
            r = eng.fit({**req, "optimizer": opt, "seed": seed})
            main = r["fitted_structure"]["stacks"][0]
            per = {L["material"]: L.get("thickness_profile", [L["thickness"]] * main["N"]) for L in main["layers"]}
            sig = {L["material"]: L.get("sigma_profile") for L in main["layers"]}
            row = {"case": case, "seed": seed, "chi2": r["chi2"], "chi2_plain": r.get("chi2_plain"),
                   "scale_ratio": r.get("scale_ratio"), "scale_clamped": r.get("scale_clamped"),
                   "free_values": r.get("free_values"), "thickness": per, "sigma": sig,
                   "top": [(L["material"], L["thickness"], L["sigma"], L["density"])
                           for L in r["fitted_structure"]["stacks"][1]["layers"]],
                   "main": [(L["material"], L["thickness"], L["sigma"], L["density"]) for L in main["layers"]],
                   "near_bounds": len((r.get("report") or {}).get("near_bounds") or []),
                   "optimizer_used": r.get("optimizer_used"), "elapsed_s": r.get("elapsed_s")}
            runs.append(row)
            print(case, seed, "χ²", round(r["chi2"], 4), "free", r.get("free_values"), "nb", row["near_bounds"],
                  r.get("elapsed_s"), "s", flush=True)
        out[case] = {"request": {k: v for k, v in req.items() if k not in ("curve", "structure")}, "runs": runs}
        save("sb-engine.json", out)


def expand_fitted(st):
    """A fitted structure with *_profile arrays written out, one N = 1 stack per period
    (period 1 = the surface end), for calculating its curve."""
    out = []
    for stack in st["stacks"]:
        n = stack.get("N", 1)
        if n == 1:
            out.append({"N": 1, "layers": [{k: L[k] for k in ("material", "thickness", "sigma", "density")}
                                            for L in stack["layers"]]})
            continue
        per = []
        for k in range(n):
            per.append({"N": 1, "layers": [{"material": L["material"],
                                            **{q: (L[q + "_profile"][k] if q + "_profile" in L else L[q])
                                               for q in ("thickness", "sigma", "density")}}
                                           for L in stack["layers"]]})
        out += list(reversed(per))          # substrate first: period N first
    return {"substrate": st["substrate"], "stacks": out}


def do_sb_engine_curves(eng):
    """Figure 22-5: the best run with Smooth off and with Smooth on, rerun with its seed
    (the same fit), its fitted periods written out, calculated over the measured range.
    Out: sb-engine-curves.json"""
    d = json.loads((OUT / "sb-engine.json").read_text(encoding="utf-8"))
    res = {}
    for case, smooth in (("off", False), ("on", True)):
        best = min(d[case]["runs"], key=lambda r: r["chi2"])
        req = sb_request(False)
        opt = {**OPT, "period_smooth": True, "period_smooth_window": -1} if smooth else dict(OPT)
        r = eng.fit({**req, "optimizer": opt, "seed": best["seed"]})
        st = expand_fitted(r["fitted_structure"])
        c = eng.call("calc_reflectivity", {"structure": st, "lambda": 1.54043, "theta_min": 0.1,
                                           "theta_max": 3.8, "points": 3701, "delta_theta": 0.015,
                                           "polarization": "s", "r_min": 1e-9, "max_inline_points": 0})
        txt = (eng.work / c["file"]).read_text(encoding="utf-8")
        arr = [[float(x) for x in ln.split()[:2]] for ln in txt.splitlines() if ln and ln[0].isdigit()]
        res[f"smooth-{case}"] = {"seed": best["seed"], "chi2": r["chi2"], "chi2_table": best["chi2"],
                                 "scale": r.get("scale"), "scale_ratio": r.get("scale_ratio"), "calc": arr}
        print(case, best["seed"], r["chi2"], best["chi2"], flush=True)
    save("sb-engine-curves.json", res)


def save(name, obj):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(json.dumps(obj, indent=1), encoding="utf-8")


def main():
    eng = Engine()
    print(eng.describe())
    try:
        for task in sys.argv[1:] or ["wbn"]:
            {"wbn": do_wbn, "wbn-widening": do_wbn_widening, "wbn-curves": do_wbn_curves, "sb": do_sb, "sb-engine": do_sb_engine, "sb-engine-curves": do_sb_engine_curves}[task](eng)
    finally:
        eng.close()


if __name__ == "__main__":
    main()
