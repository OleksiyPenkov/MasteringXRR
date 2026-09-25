"""Chapter 6: multilayer curves and optical constants from the X-Ray Calc engine.

The same route as ch4_engine_data.py and ch5_engine_data.py: the command-line
server that ships with X-Ray Calc (XRC_MCP.exe in the build folder), driven
over stdin, so every curve is the engine's own. The book never names the server.

All curves at λ = 1.5406 Å, Δθ = 0 (no blur), s-polarization (the GUI default),
with the reflectivity floor lowered to 10⁻¹² so that no order is clipped.
Layers are listed from the surface down, as the server expects.

  D100         Co/C, D = 100 Å, Γ = 0.3 (70 Å C over 30 Å Co), N = 20, smooth,
               on Si: the evenly-spaced-orders example (Figure 6-2)
  G0.5         Co/C, D = 50 Å, N = 20, smooth, on Si, Γ = 0.5   (Figure 6-3)
  G0.333       the same, Γ = 1/3
  G0.376       the same, Γ = 0.376 (the ratio of the CoC5 expert fit)
  G0.376-N10   the same with N = 10 (checks the fringe count between orders)
  CoC5         the CoC5 expert model (fits/CoC5-expert.xrcx in the deposit):
               20 × (C 31.2135 Å, σ 4.3254, ρ 2.0621; Co 18.8183 Å, σ 5.7386,
               ρ 6.2509) on SiO2, σ 3.8, ρ 2.65                   (Figure 6-4)
  CoC5-sigma   the same with σ + 2 Å on both layers
  CoC5-ratio   the same with 2 Å moved from C to Co (same period, Γ 0.376 → 0.416)

Optical constants of C and Co at bulk density give δ̄ for the refraction
ticks of Figure 6-2.

Run:  python scripts/figures/ch6_engine_data.py
Out:  figures-src/ch6/curve-<case>.dat, figures-src/ch6/optical-constants.json
"""
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import local_paths

# A copy of the release, never the build folder (set XRC_MCP_EXE; see xrc_engine.py).
EXE = local_paths.get("XRC_MCP_EXE")
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "figures-src" / "ch6"

LAMBDA = 1.5406
R_MIN = 1e-12  # the engine clamps R to this floor; the default 1e-7 would clip the high orders


def coc(d, ratio, n=20):
    co = d * ratio
    return {"substrate": {"material": "Si", "sigma": 0},
            "stacks": [{"N": n, "layers": [{"material": "C", "thickness": d - co, "sigma": 0},
                                           {"material": "Co", "thickness": co, "sigma": 0}]}]}


def coc5(dsigma=0.0, dco=0.0):
    return {"substrate": {"material": "SiO2", "sigma": 3.8, "density": 2.65},
            "stacks": [{"N": 20, "layers": [
                {"material": "C", "thickness": 31.2135 - dco, "sigma": 4.3254 + dsigma, "density": 2.0621},
                {"material": "Co", "thickness": 18.8183 + dco, "sigma": 5.7386 + dsigma, "density": 6.2509}]}]}


# case: (structure, θ max in degrees, points)
CASES = {
    "D100": (coc(100, 0.3), 4.0, 8000),
    "G0.5": (coc(50, 0.5), 6.0, 6000),
    "G0.333": (coc(50, 1 / 3), 6.0, 6000),
    "G0.376": (coc(50, 0.376), 6.0, 6000),
    "G0.376-N10": (coc(50, 0.376, n=10), 6.0, 6000),
    "CoC5": (coc5(), 4.5, 4500),
    "CoC5-sigma": (coc5(dsigma=2.0), 4.5, 4500),
    "CoC5-ratio": (coc5(dco=2.0), 4.5, 4500),
}
MATERIALS = ["C", "Co"]


def call(i, name, args):
    return json.dumps({"jsonrpc": "2.0", "id": i, "method": "tools/call",
                       "params": {"name": name, "arguments": args}})


def main():
    work = Path(tempfile.mkdtemp(prefix="xrc_ch6_"))
    try:
        names = list(CASES)
        lines = [json.dumps({"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": {}})]
        for i, n in enumerate(names, start=1):
            s, tmax, pts = CASES[n]
            lines.append(call(i, "calc_reflectivity", {
                "structure": s, "lambda": LAMBDA, "theta_min": 0.001, "theta_max": tmax,
                "points": pts, "delta_theta": 0, "polarization": "s", "r_min": R_MIN,
                "max_inline_points": 0}))
        for i, m in enumerate(MATERIALS, start=100):
            lines.append(call(i, "optical_constants", {"material": m, "lambda": LAMBDA}))
        run = subprocess.run([str(EXE), "--workdir", str(work)], input="\n".join(lines) + "\n",
                             capture_output=True, text=True, encoding="utf-8", timeout=600)
        replies = {}
        for line in run.stdout.splitlines():
            msg = json.loads(line)
            if msg.get("id", 0) > 0:
                if msg["result"].get("isError"):
                    raise SystemExit(f"engine error on id {msg['id']}: {msg['result']['content'][0]['text']}")
                replies[msg["id"]] = json.loads(msg["result"]["content"][0]["text"])
        OUT.mkdir(parents=True, exist_ok=True)
        for i, n in enumerate(names, start=1):
            shutil.copyfile(work / replies[i]["file"], OUT / f"curve-{n}.dat")
            print(f"{n}: {replies[i]['structure_used']['stacks'][0]['layers']}")
        constants = [replies[i] for i in range(100, 100 + len(MATERIALS))]
        (OUT / "optical-constants.json").write_text(json.dumps(
            {"lambda_A": LAMBDA, "materials": constants}, indent=1), encoding="utf-8")
        for c in constants:
            print(f"{c['material']}: ρ={c['density_used']} δ={c['delta']} β={c['beta']}")
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main()
