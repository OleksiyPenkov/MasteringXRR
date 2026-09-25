"""Chapter 7: roughness, interlayer and drift curves from the X-Ray Calc engine.

The same route as ch4_engine_data.py to ch6_engine_data.py: the command-line
server that ships with X-Ray Calc (XRC_MCP.exe in the build folder), driven
over stdin, so every curve is the engine's own. The book never names the server.

All curves at λ = 1.5406 Å, Δθ = 0 (no blur), s-polarization (the GUI default),
with the reflectivity floor lowered to 10⁻¹² so that nothing is clipped.
The server lists stacks from the substrate up, and the layers of a stack from
the top down.

  Mo-smooth    bare Mo, σ = 0
  Mo-rough     bare Mo, σ = 5 Å (the engine's Névot–Croce factor)
  Mo-graded    bare Mo, σ = 0, under 80 slices of Mo 0.5 Å thick whose density
               rises as ρ_bulk · ½[1 + erf(z / (σ√2))], σ = 5 Å, z = −20 … +20 Å:
               the same average profile as Mo-rough, built as a gradual transition
               (Spiller pp. 113–114)
  CoC-none     Co/C, 20 × (31.2 Å C over 18.8 Å Co), on Si, σ = 3 Å everywhere
  CoC-upper    the same with an 8 Å CoC interlayer under C (C grown on Co);
               4 Å taken from each of C and Co, so D stays 50 Å
  CoC-lower    the same interlayer under Co (Co grown on C)
  drift        the Chapter 3 demo's gradient: 30 periods of Si over 15 Å Mo on
               Si, with H_Si(k) = 25 + 0.14(k−1) + 0.012(k−1)² − 0.0005(k−1)³,
               k = 1 at the surface, all smooth; one stack per period, because
               this route takes no profiles
  uniform      the same with every Si at the mean, 27.30 Å (period 42.30 Å)

In the bare-Mo cases the "layer" is 10 Å of Mo on a Mo substrate, as in
Chapter 4: the server refuses a structure without a stack.

Run:  python scripts/figures/ch7_engine_data.py
Out:  figures-src/ch7/curve-<case>.dat
"""
import json
import os
import math
import shutil
import subprocess
import tempfile
from pathlib import Path

import local_paths

# A copy of the release, never the build folder (set XRC_MCP_EXE; see xrc_engine.py).
EXE = local_paths.get("XRC_MCP_EXE")
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "figures-src" / "ch7"

LAMBDA = 1.5406
R_MIN = 1e-12
MO_BULK = 10.22  # g/cm³, the Mo Henke table (Chapter 4, Table 4-1)
SIGMA = 5.0
SLICE = 0.5


def bare_mo(sigma):
    return {"substrate": {"material": "Mo", "sigma": 0},
            "stacks": [{"N": 1, "layers": [{"material": "Mo", "thickness": 10, "sigma": sigma}]}]}


def graded_mo():
    layers = []
    z = -20.0 + SLICE / 2
    while z < 20.0:
        f = 0.5 * (1 + math.erf(z / (SIGMA * math.sqrt(2))))
        # ρ = 0 would mean "bulk" to the engine, so the thinnest slices get a tiny density.
        layers.append({"material": "Mo", "thickness": SLICE, "sigma": 0, "density": max(f * MO_BULK, 1e-4)})
        z += SLICE
    return {"substrate": {"material": "Mo", "sigma": 0}, "stacks": [{"N": 1, "layers": layers}]}


def coc(inter=None):
    s = 3.0
    if inter is None:
        layers = [{"material": "C", "thickness": 31.2, "sigma": s},
                  {"material": "Co", "thickness": 18.8, "sigma": s}]
    else:
        c = {"material": "C", "thickness": 27.2, "sigma": s}
        co = {"material": "Co", "thickness": 14.8, "sigma": s}
        il = {"material": "CoC", "thickness": 8.0, "sigma": s}
        layers = [c, il, co] if inter == "upper" else [c, co, il]
    return {"substrate": {"material": "Si", "sigma": s}, "stacks": [{"N": 20, "layers": layers}]}


def demo(graded):
    def h_si(k):
        return 25 + 0.14 * (k - 1) + 0.012 * (k - 1) ** 2 - 0.0005 * (k - 1) ** 3
    stacks = []
    for k in range(30, 0, -1):  # substrate first
        h = h_si(k) if graded else 27.30
        stacks.append({"N": 1, "layers": [{"material": "Si", "thickness": round(h, 6), "sigma": 0},
                                          {"material": "Mo", "thickness": 15, "sigma": 0}]})
    return {"substrate": {"material": "Si", "sigma": 0}, "stacks": stacks}


# case: (structure, θ max in degrees, points)
CASES = {
    "Mo-smooth": (bare_mo(0), 3.0, 3000),
    "Mo-rough": (bare_mo(SIGMA), 3.0, 3000),
    "Mo-graded": (graded_mo(), 3.0, 3000),
    "CoC-none": (coc(), 4.5, 6000),
    "CoC-upper": (coc("upper"), 4.5, 6000),
    "CoC-lower": (coc("lower"), 4.5, 6000),
    "drift": (demo(True), 6.0, 9000),
    "uniform": (demo(False), 6.0, 9000),
}


def call(i, name, args):
    return json.dumps({"jsonrpc": "2.0", "id": i, "method": "tools/call",
                       "params": {"name": name, "arguments": args}})


def main():
    work = Path(tempfile.mkdtemp(prefix="xrc_ch7_"))
    try:
        names = list(CASES)
        lines = [json.dumps({"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": {}})]
        for i, n in enumerate(names, start=1):
            s, tmax, pts = CASES[n]
            lines.append(call(i, "calc_reflectivity", {
                "structure": s, "lambda": LAMBDA, "theta_min": 0.001, "theta_max": tmax,
                "points": pts, "delta_theta": 0, "polarization": "s", "r_min": R_MIN,
                "max_inline_points": 0}))
        run = subprocess.run([str(EXE), "--workdir", str(work)], input="\n".join(lines) + "\n",
                             capture_output=True, text=True, encoding="utf-8", timeout=600)
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
            st = replies[i]["structure_used"]["stacks"]
            first = st[0]["layers"]
            print(f"{n}: {len(st)} stack(s); first stack {[(l['material'], l['thickness'], l.get('density')) for l in first][:4]}")
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main()
