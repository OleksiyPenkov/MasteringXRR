"""Chapter 5: single-film curves from the X-Ray Calc engine.

The same route as ch4_engine_data.py: the command-line server that ships with
X-Ray Calc (XRC_MCP.exe in the build folder), driven over stdin, so every curve
is the engine's own. The book never names the server.

Five films of 200 Å on a Si substrate, at λ = 1.5406 Å, Δθ = 0 (no blur),
s-polarization (the GUI default):

  C-bulk     C at the bulk density of its Henke table (ρ = 0 in the GUI)
  C-1.8      C at 1.8 g/cm³
  Mo         Mo at bulk density, smooth
  Mo-top5    Mo with σ = 5 Å on its upper interface (the top surface)
  Mo-int5    Mo with σ = 5 Å on the substrate, which in X-Ray Calc is the
             roughness of the film/substrate interface (NOTATION §3, σ)

Run:  python scripts/figures/ch5_engine_data.py
Out:  figures-src/ch5/curve-<case>.dat
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
OUT = ROOT / "figures-src" / "ch5"

LAMBDA = 1.5406
THICKNESS = 200.0


def film(material, density=None, sigma_top=0.0, sigma_interface=0.0):
    layer = {"material": material, "thickness": THICKNESS, "sigma": sigma_top}
    if density is not None:
        layer["density"] = density
    return {"substrate": {"material": "Si", "sigma": sigma_interface},
            "stacks": [{"N": 1, "layers": [layer]}]}


CASES = {
    "C-bulk": film("C"),
    "C-1.8": film("C", density=1.8),
    "Mo": film("Mo"),
    "Mo-top5": film("Mo", sigma_top=5.0),
    "Mo-int5": film("Mo", sigma_interface=5.0),
}


def main():
    work = Path(tempfile.mkdtemp(prefix="xrc_ch5_"))
    try:
        names = list(CASES)
        lines = [json.dumps({"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": {}})]
        for i, n in enumerate(names, start=1):
            lines.append(json.dumps({"jsonrpc": "2.0", "id": i, "method": "tools/call", "params": {
                "name": "calc_reflectivity", "arguments": {
                    "structure": CASES[n], "lambda": LAMBDA, "theta_min": 0.001, "theta_max": 3.0,
                    "points": 3000, "delta_theta": 0, "polarization": "s", "max_inline_points": 0}}}))
        run = subprocess.run([str(EXE), "--workdir", str(work)], input="\n".join(lines) + "\n",
                             capture_output=True, text=True, encoding="utf-8", timeout=300)
        replies = {}
        for line in run.stdout.splitlines():
            msg = json.loads(line)
            if msg.get("id", 0) > 0:
                if msg["result"].get("isError"):
                    raise SystemExit(f"engine error on {names[msg['id'] - 1]}: {msg['result']['content'][0]['text']}")
                replies[msg["id"]] = json.loads(msg["result"]["content"][0]["text"])
        OUT.mkdir(parents=True, exist_ok=True)
        for i, n in enumerate(names, start=1):
            shutil.copyfile(work / replies[i]["file"], OUT / f"curve-{n}.dat")
            used = replies[i]["structure_used"]["stacks"][0]["layers"][0]
            print(f"{n}: {used}")
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main()
