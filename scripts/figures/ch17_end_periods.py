"""Chapter 17: why a polynomial profile is weakly held at the ends of the stack.

Two numbers for the Going Deeper box "why the ends of the stack are the weak
part":

1. How strongly the curve holds each period on its own. The best order-1 run
   of CoC4 (figures-src/ch17/coc4-final.json) is written out period by period,
   as 20 stacks of one period under the contamination layer. Then one period at
   a time is made thicker and thinner by DELTA (both layers scaled, so the
   ratio stays), and χ² is scored with the scale solved as in the fit. The
   curvature (χ²₊ + χ²₋ − 2χ²₀) / DELTA² says how much the curve cares about
   that period alone.

2. What the polynomial adds. Even if every period were held equally and
   independently, a least-squares polynomial through N periods is less certain
   at the ends: the standard deviation of its value in period k is
   √h_k times that of one period, h_k the leverage (the diagonal of the hat
   matrix X(XᵀX)⁻¹Xᵀ).

The command-line server that ships with X-Ray Calc, driven through
xrc_engine.Engine (set XRC_MCP_EXE to a copy of the build). The book never
names the server.

Run:  python scripts/figures/ch17_end_periods.py
Out:  figures-src/ch17/end-periods.json
"""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ch16_engine_data as c16  # noqa: E402
from xrc_engine import Engine  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "figures-src" / "ch17"
DELTA = 0.3                                  # Å, added to one period

SCORE_FREE = [{"stack": 0, "layer": 1, "parameters": ["density"]}]
SCORE_BOUNDS = [{"stack": 0, "layer": 1, "parameter": "density", "min": 0.5, "max": 20}]


def best_run():
    d = json.loads((OUT / "coc4-final.json").read_text(encoding="utf-8"))
    g = [r for r in d["runs"] if r["mode"] == "poly1"]
    return d["request"], min(g, key=lambda r: r["chi2"])


def layer(material, h, src):
    return {"material": material, "thickness": round(float(h), 5),
            "sigma": src["sigma"], "density": src["density"]}


def structure(req, run, periods_c, periods_co, top_first):
    """Periods listed as one-period stacks; stacks run substrate side first."""
    idx = range(len(periods_c))
    order = list(reversed(idx)) if top_first else list(idx)
    stacks = [{"N": 1, "layers": [layer("C", periods_c[k], run["C"]),
                                  layer("Co", periods_co[k], run["Co"])]} for k in order]
    top = run["top"]
    stacks.append({"N": 1, "layers": [{"material": "C", **top}]})
    return {"substrate": req["structure"]["substrate"], "stacks": stacks}


def score(eng, req, st):
    r = eng.fit({**req, "structure": st, "free": SCORE_FREE, "bounds": SCORE_BOUNDS,
                 "optimizer": {"iterations": 1, "population": 2, "range_seed": False}, "seed": 1})
    return r["chi2_start"]


def leverage(n, order):
    x = np.arange(n, dtype=float)
    X = np.vander(x, order + 1, increasing=True)
    return np.diag(X @ np.linalg.inv(X.T @ X) @ X.T)


def main():
    rq, run = best_run()
    req = {**c16.request(), **{k: v for k, v in rq.items() if k not in ("free", "bounds", "structure")},
           "structure": rq["structure"]}
    pc = np.array(run["C"]["thickness_profile"])      # index 0 = top period
    pco = np.array(run["Co"]["thickness_profile"])
    n = len(pc)
    eng = Engine()
    try:
        # which way the stacks run: the ordering that reproduces the run's χ²
        base = {t: score(eng, req, structure(req, run, pc, pco, t)) for t in (True, False)}
        top_first = abs(base[True] - run["chi2"]) < abs(base[False] - run["chi2"])
        chi0 = base[top_first]
        print(f"run χ² {run['chi2']:.6f}; scored top-first {base[True]:.6f}, "
              f"bottom-first {base[False]:.6f}", flush=True)
        rows = []
        for k in range(n):
            vals = []
            for s in (+1, -1):
                f = (pc[k] + pco[k] + s * DELTA) / (pc[k] + pco[k])
                c, co = pc.copy(), pco.copy()
                c[k] *= f
                co[k] *= f
                vals.append(score(eng, req, structure(req, run, c, co, top_first)))
            curv = (vals[0] + vals[1] - 2 * chi0) / DELTA ** 2
            rows.append({"period": k + 1, "chi2_plus": vals[0], "chi2_minus": vals[1],
                         "curvature": curv})
            print(f"period {k + 1:2d}: χ² +{vals[0]:.5f} −{vals[1]:.5f} curvature {curv:.4f}",
                  flush=True)
        eng_version = eng.describe().get("version")
    finally:
        eng.close()
    out = {"source_run": {"file": "coc4-final.json", "mode": "poly1", "seed": run["seed"],
                          "chi2": run["chi2"]},
           "engine": eng_version, "delta_A": DELTA, "stacks_top_first": top_first,
           "chi2_base": chi0, "periods": rows,
           "leverage_sd": {str(o): [float(v) for v in np.sqrt(leverage(n, o))] for o in (1, 3)}}
    (OUT / "end-periods.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print("wrote end-periods.json")


if __name__ == "__main__":
    main()
