"""Chapter 13: the sensitivity check on the CoC4 starting model.

The command-line server that ships with X-Ray Calc (XRC_MCP.exe in the build
folder, engine 3.9.4), driven through xrc_engine.Engine. The book never names
the server.

The base is the starting model of Chapter 12 (ch12_engine_data.py). Every
other curve changes one parameter of it. The steps include the variants of the
fitting procedure v5 §3.1, with one laboratory's values where the procedure
points to its preset:
  period ±2 %                    both thicknesses scaled
  layer ratio both ways          ±2 Å moved between C and Co, period kept
  σ of each layer at 1 and 8 Å   the preset's σ bounds (materials.sigma_A.bounds)
  ρ of each layer ±15 %
  surface layer 20 Å, 1.2 g/cm³  the preset's sensitivity variant
  N halved and doubled           10 and 40
and intermediate steps for the sliders of the web figure. Each curve at
λ = 1.541874 Å, Δθ = 0.012°, s-polarization, θ = 0.001-7.4° in steps of
0.001°, floor 10⁻¹².

  curve-<param>-<step>.dat   one per step; curve-base.dat
  steps.json                 the parameters, their steps and their structures
  public/data/ch13-sensitivity.json   the widget's data (see pack())

Run:  python scripts/figures/ch13_engine_data.py
Out:  figures-src/ch13/, public/data/ch13-sensitivity.json
"""
import base64
import copy
import json
import shutil
from pathlib import Path

import numpy as np

from xrc_engine import Engine

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "figures-src" / "ch13"
WIDGET = ROOT / "public" / "data" / "ch13-sensitivity.json"
MEASURED = ROOT / "figures-src" / "ch11" / "curve-measured.dat"
LAMBDA = 1.541874
DTHETA = 0.012
THETA_MAX_WIDGET = 7.0     # ° θ, 2θ = 14°, the end of the CoC4 scan
DECIMATE = 3               # the widget keeps every third point: 0.006° in 2θ

BASE = {"substrate": {"material": "SiO2", "sigma": 3.8, "density": 2.50},
        "stacks": [{"N": 20, "layers": [{"material": "C", "thickness": 31.40, "sigma": 4.0, "density": 2.0},
                                        {"material": "Co", "thickness": 23.30, "sigma": 4.0, "density": 8.0}]},
                   {"N": 1, "layers": [{"material": "C", "thickness": 15.0, "sigma": 3.0, "density": 0.9}]}]}


def ml(s):
    return s["stacks"][0]["layers"]


def period(pct):
    def fn(s):
        for layer in ml(s):
            layer["thickness"] *= 1 + pct / 100
    return fn


def ratio(dh):
    def fn(s):
        ml(s)[0]["thickness"] -= dh
        ml(s)[1]["thickness"] += dh
    return fn


def sigma(i, v):
    def fn(s):
        ml(s)[i]["sigma"] = v
    return fn


def rho(i, pct):
    def fn(s):
        ml(s)[i]["density"] *= 1 + pct / 100
    return fn


def top(h, r):
    def fn(s):
        if h == 0:
            del s["stacks"][1]
        else:
            s["stacks"][1]["layers"][0].update({"thickness": h, "density": r})
    return fn


def nper(v):
    def fn(s):
        s["stacks"][0]["N"] = v
    return fn


# parameter → (label, unit, base value text, [(step key, step label, fn), ...]); base is step 0
PARAMS = {
    "period": ("Period D", "Å", "54.70", [(f"{p:+g}", f"{54.70 * (1 + p / 100):.2f} ({p:+g} %)", period(p))
                                          for p in (-2, -1, 1, 2)]),
    "ratio": ("Co thickness at the same period", "Å", "23.30", [(f"{d:+g}", f"{23.30 + d:.2f} ({d:+g} Å)", ratio(d))
                                                                 for d in (-2, -1, 1, 2)]),
    "sigC": ("σ of C", "Å", "4", [(f"{v:g}", f"{v:g}", sigma(0, v)) for v in (1, 2.5, 6, 8)]),
    "sigCo": ("σ of Co", "Å", "4", [(f"{v:g}", f"{v:g}", sigma(1, v)) for v in (1, 2.5, 6, 8)]),
    "rhoC": ("ρ of C", "g/cm³", "2.00", [(f"{p:+g}", f"{2.0 * (1 + p / 100):.2f} ({p:+g} %)", rho(0, p))
                                        for p in (-15, -7.5, 7.5, 15)]),
    "rhoCo": ("ρ of Co", "g/cm³", "8.00", [(f"{p:+g}", f"{8.0 * (1 + p / 100):.2f} ({p:+g} %)", rho(1, p))
                                          for p in (-15, -7.5, 7.5, 15)]),
    "top": ("Surface layer", "", "15 Å, 0.90 g/cm³", [("none", "none", top(0, 0)),
                                                      ("20", "20 Å, 1.20 g/cm³", top(20.0, 1.2))]),
    "N": ("Number of periods N", "", "20", [(f"{v}", f"{v}", nper(v)) for v in (10, 15, 30, 40)]),
}


def calc(e, s, name):
    c = e.call("calc_reflectivity", {"structure": s, "lambda": LAMBDA, "theta_min": 0.001,
                                     "theta_max": 7.4, "points": 7400, "delta_theta": DTHETA,
                                     "polarization": "s", "r_min": 1e-12, "max_inline_points": 0})
    shutil.copyfile(e.work / c["file"], OUT / name)


def b64_log(r):
    """log10 R × 1000 as little-endian int16, base64: 0.001 decades is far below what a chart shows."""
    v = np.round(np.log10(np.maximum(r, 1e-12)) * 1000).astype("<i2")
    return base64.b64encode(v.tobytes()).decode("ascii")


def load(name):
    d = np.loadtxt(OUT / name, skiprows=1)
    return d[:, 0], d[:, 1]


def pack(steps):
    t, r = load("curve-base.dat")
    keep = (np.arange(len(t)) % DECIMATE == 0) & (t <= THETA_MAX_WIDGET + 1e-9)
    tt = 2 * t[keep]
    step = float(np.round(np.median(np.diff(tt)), 6))
    assert np.allclose(np.diff(tt), step, atol=1e-6), "the engine grid is not uniform"
    tm, rm = np.loadtxt(MEASURED, skiprows=1).T
    mstep = float(np.round(np.median(np.diff(2 * tm)), 6))
    assert np.allclose(np.diff(2 * tm), mstep, atol=1e-6), "the measured grid is not uniform"
    data = {
        "source": "X-Ray Calc 3.9.4.1250 engine; scripts/figures/ch13_engine_data.py",
        "lambda_A": LAMBDA, "delta_theta_deg": DTHETA,
        "model_grid": {"start_2theta": float(np.round(tt[0], 6)), "step_2theta": step, "n": int(len(tt))},
        "measured": {"start_2theta": float(np.round(2 * tm[0], 6)), "step_2theta": mstep, "n": int(len(tm)),
                     "log10R_milli": b64_log(rm), "name": "CoC4, measured (CC BY 4.0), normalized to 1 at its maximum"},
        "base": b64_log(r[keep]),
        "params": [],
    }
    for key, (label, unit, base_text, stp) in PARAMS.items():
        entry = {"key": key, "label": label, "unit": unit, "base_label": base_text, "steps": []}
        for sk, slabel, _ in stp:
            _, rv = load(f"curve-{key}-{sk}.dat")
            entry["steps"].append({"key": sk, "label": slabel, "log10R_milli": b64_log(rv[keep])})
        data["params"].append(entry)
    WIDGET.parent.mkdir(parents=True, exist_ok=True)
    WIDGET.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
    print(f"widget data: {WIDGET.stat().st_size / 1024:.0f} kB, model grid {len(tt)} points, measured {len(tm)}")


def main():
    e = Engine()
    try:
        OUT.mkdir(parents=True, exist_ok=True)
        steps = {"base": BASE}
        calc(e, BASE, "curve-base.dat")
        for key, (_, _, _, stp) in PARAMS.items():
            for sk, _, fn in stp:
                s = copy.deepcopy(BASE)
                fn(s)
                steps[f"{key}-{sk}"] = s
                calc(e, s, f"curve-{key}-{sk}.dat")
        (OUT / "steps.json").write_text(json.dumps(steps, indent=1), encoding="utf-8")
        srv = e.describe()
        print(f"engine: X-Ray Calc {srv['xraycalc3_exe_version']}, git {srv['git_revision']}; {len(steps)} curves")
    finally:
        e.close()
    pack(steps)


if __name__ == "__main__":
    main()
