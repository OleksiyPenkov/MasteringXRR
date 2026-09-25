"""Chapter 4: optical constants and single-surface curves from the X-Ray Calc engine.

Every number in Table 4-1 and every curve in Figures 4-2 and 4-3 comes from
the program itself, not from a re-implementation. The engine is reached through
the command-line server that ships with it (XRC_MCP.exe in the build folder),
driven over stdin as one JSON-RPC session. The book never names the server; it
is only the route to the engine the GUI uses.

  optical_constants   δ and β of each material at λ = 1.5406 Å, bulk density
                      from the program's own Henke table (ρ = 0 in the GUI)
  calc_reflectivity   R(θ) of a bare, smooth substrate: σ = 0, Δθ = 0 (no
                      blur), s-polarization (the GUI default,
                      frame_CalcSettings.dfm, rgPolarisation ItemIndex = 0)
                      and, with the same settings, the "which δ" example of
                      the chapter: a 50 Å Si cap on 30 × (25 Å Si, 15 Å Mo)
                      on Si, all σ = 0 (the demo's layers without the gradient)

The server refuses a structure without a stack, so each "bare substrate" is
the substrate under one 10 Å layer of the same material, same density, σ = 0.
The layer and the substrate have the same ε and no interface roughness, so the
boundary between them reflects nothing: the curve is that of the bare surface.

Run:  python scripts/figures/ch4_engine_data.py
Out:  figures-src/ch4/optical-constants.json, figures-src/ch4/curve-<material>.dat,
      figures-src/ch4/curve-MoSi-multilayer.dat
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
OUT = ROOT / "figures-src" / "ch4"

LAMBDA = 1.5406  # Å, Cu Kα1; the example wavelength of NOTATION §3
TABLE_MATERIALS = ["C", "B4C", "Si", "SiO2", "Co", "Mo", "Ru", "W"]
CURVE_MATERIALS = ["Si", "Mo", "W"]
THETA_MIN, THETA_MAX, POINTS = 0.001, 3.0, 3000  # θ, degrees


def call(i, name, args):
    return json.dumps({"jsonrpc": "2.0", "id": i, "method": "tools/call",
                       "params": {"name": name, "arguments": args}})


def bare(material):
    return {"substrate": {"material": material, "sigma": 0},
            "stacks": [{"N": 1, "layers": [{"material": material, "thickness": 10, "sigma": 0}]}]}


MULTILAYER = {"substrate": {"material": "Si", "sigma": 0},
              "stacks": [{"N": 30, "layers": [{"material": "Si", "thickness": 25, "sigma": 0},
                                              {"material": "Mo", "thickness": 15, "sigma": 0}]}],
              "cap": {"material": "Si", "thickness": 50, "sigma": 0}}


def main():
    work = Path(tempfile.mkdtemp(prefix="xrc_ch4_"))
    try:
        lines = [json.dumps({"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": {}})]
        for i, m in enumerate(TABLE_MATERIALS, start=1):
            lines.append(call(i, "optical_constants", {"material": m, "lambda": LAMBDA}))
        for i, m in enumerate(CURVE_MATERIALS, start=100):
            lines.append(call(i, "calc_reflectivity", {
                "structure": bare(m), "lambda": LAMBDA, "theta_min": THETA_MIN,
                "theta_max": THETA_MAX, "points": POINTS, "delta_theta": 0,
                "polarization": "s", "max_inline_points": 0}))
        lines.append(call(200, "calc_reflectivity", {
            "structure": MULTILAYER, "lambda": LAMBDA, "theta_min": THETA_MIN, "theta_max": 1.0,
            "points": 1000, "delta_theta": 0, "polarization": "s", "max_inline_points": 0}))
        run = subprocess.run([str(EXE), "--workdir", str(work)], input="\n".join(lines) + "\n",
                             capture_output=True, text=True, encoding="utf-8", timeout=300)
        replies = {}
        for line in run.stdout.splitlines():
            msg = json.loads(line)
            if "result" in msg and "content" in msg["result"]:
                if msg["result"].get("isError"):
                    raise SystemExit(f"engine error on id {msg['id']}: {msg['result']['content'][0]['text']}")
                replies[msg["id"]] = json.loads(msg["result"]["content"][0]["text"])

        OUT.mkdir(parents=True, exist_ok=True)
        constants = [replies[i] for i in range(1, len(TABLE_MATERIALS) + 1)]
        (OUT / "optical-constants.json").write_text(json.dumps(
            {"lambda_A": LAMBDA, "engine": str(EXE), "materials": constants}, indent=1), encoding="utf-8")
        for i, m in enumerate(CURVE_MATERIALS, start=100):
            r = replies[i]
            shutil.copyfile(work / r["file"], OUT / f"curve-{m}.dat")
            print(f"{m}: critical_angle_deg (engine) = {r['critical_angle_deg']}")
        shutil.copyfile(work / replies[200]["file"], OUT / "curve-MoSi-multilayer.dat")
        for c in constants:
            print(f"{c['material']:5s} ρ={c['density_used']} δ={c['delta']} β={c['beta']}")
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main()
