"""Chapter 8: resolution, polarization and sampling curves from the X-Ray Calc engine.

The same route as ch4_engine_data.py to ch7_engine_data.py: the command-line
server that ships with X-Ray Calc (XRC_MCP.exe in the build folder, engine
3.9.4.1250 since the rerun of 2026-09-25), driven over stdin, so every curve is the engine's own. The book
never names the server.

Every case uses the CoC5 expert model of Chapter 6 (fits/CoC5-expert.xrcx in the
fitting procedure's deposit): 20 × (C 31.2135 Å, σ 4.3254, ρ 2.0621; Co 18.8183 Å,
σ 5.7386, ρ 6.2509) on SiO2, σ 3.8, ρ 2.65. λ = 1.5406 Å, reflectivity floor
10⁻¹⁵ so that nothing is clipped. The server takes θ, and its delta_theta is the
FWHM in θ, the value of the GUI's Δθ field.

  dt0, dt0.01, dt0.03   Δθ = 0, 0.01°, 0.03°, s-polarization, θ = 0.001–4.5°, 9000 points
  pol-s, pol-sp         Δθ = 0, s and sp (the average of s and p), θ = 0.001–20°, 20000 points
  coarse                Δθ = 0, s, θ = 0.001–4.5° in 150 points (a step of 0.03° in θ)

Run:  python scripts/figures/ch8_engine_data.py
Out:  figures-src/ch8/curve-<case>.dat
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
OUT = ROOT / "figures-src" / "ch8"

LAMBDA = 1.5406
R_MIN = 1e-15
COC5 = {"substrate": {"material": "SiO2", "sigma": 3.8, "density": 2.65},
        "stacks": [{"N": 20, "layers": [
            {"material": "C", "thickness": 31.2135, "sigma": 4.3254, "density": 2.0621},
            {"material": "Co", "thickness": 18.8183, "sigma": 5.7386, "density": 6.2509}]}]}

# case: (Δθ, polarization, θ max, points)
CASES = {
    "dt0": (0, "s", 4.5, 9000),
    "dt0.01": (0.01, "s", 4.5, 9000),
    "dt0.03": (0.03, "s", 4.5, 9000),
    "pol-s": (0, "s", 20.0, 20000),
    "pol-sp": (0, "sp", 20.0, 20000),
    "coarse": (0, "s", 4.5, 150),
}


def call(i, name, args):
    return json.dumps({"jsonrpc": "2.0", "id": i, "method": "tools/call",
                       "params": {"name": name, "arguments": args}})


def main():
    work = Path(tempfile.mkdtemp(prefix="xrc_ch8_"))
    try:
        names = list(CASES)
        lines = [json.dumps({"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": {}})]
        for i, n in enumerate(names, start=1):
            dt, pol, tmax, pts = CASES[n]
            lines.append(call(i, "calc_reflectivity", {
                "structure": COC5, "lambda": LAMBDA, "theta_min": 0.001, "theta_max": tmax,
                "points": pts, "delta_theta": dt, "polarization": pol, "r_min": R_MIN,
                "max_inline_points": 0}))
        lines.append(call(99, "describe_server", {}))
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
            r = replies[i]
            print(f"{n}: polarization {r.get('polarization', '?')}, delta_theta {r.get('delta_theta', '?')}")
        s = replies[99]["server"]
        print(f"engine: X-Ray Calc {s['xraycalc3_exe_version']}, git {s['git_revision']}")
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main()
