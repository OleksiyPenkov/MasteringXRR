"""Chapter 10: the assessment of the CoC5 measurement, and the CoC5 model curve.

The command-line server that ships with X-Ray Calc (XRC_MCP.exe in the build
folder, engine 3.9.4.1250 since the rerun of 2026-09-25), driven over stdin. The book never names the server.
Its assessment is the unit the GUI's Data > Assess XRR quality ... runs
(unit_MCPAssess.pas, used by frm_XRRAssess), so its numbers are the dialog's.

The measurement is the raw CoC5 file of the fitting procedure's deposit
(curves/CoC5.xrdml, CC BY 4.0). The server reads measurements only from an
inbox folder, so the file is copied into a temporary work folder for the run
and deleted with it; nothing is copied into the book.

  assess-design.json   the eight checks with the CoC5 expert model as the design,
                       Δθ = 0.009° (the expert's width), the GUI dialog's other
                       defaults (visible factor 3, 3 points per fringe) and no
                       detector limit, specimen length or beam width
  assess-none.json     the same without a design
  measurement.json     the header the import writes (λ, counting time, zeros)
  curve-measured.dat   the curve as the import leaves it: θ, normalised to 1 at
                       the maximum, zero counts floored
  curve-model.dat      the CoC5 expert model at the file's λ, Δθ = 0.009°,
                       θ = 0.001–7°, 7000 points, floor 10⁻¹²

Run:  python scripts/figures/ch10_engine_data.py
Out:  figures-src/ch10/
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
DEPOSIT = local_paths.deposit("curves")
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "figures-src" / "ch10"

EXPERT = {"substrate": {"material": "SiO2", "sigma": 3.8, "density": 2.65},
          "stacks": [{"N": 20, "layers": [
              {"material": "C", "thickness": 31.2135, "sigma": 4.3254, "density": 2.0621},
              {"material": "Co", "thickness": 18.8183, "sigma": 5.7386, "density": 6.2509}]}]}
MID = "CoC5/CoC5.xrdml"
DTHETA = 0.009


def call(i, name, args):
    return json.dumps({"jsonrpc": "2.0", "id": i, "method": "tools/call",
                       "params": {"name": name, "arguments": args}})


def main():
    work = Path(tempfile.mkdtemp(prefix="xrc_ch10_"))
    try:
        (work / "inbox" / "CoC5").mkdir(parents=True)
        shutil.copyfile(DEPOSIT / "CoC5.xrdml", work / "inbox" / "CoC5" / "CoC5.xrdml")
        lines = [json.dumps({"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": {}}),
                 call(1, "get_measurement", {"measurement_id": MID, "max_points": 5000}),
                 call(2, "assess_xrr", {"measurement_id": MID, "structure": EXPERT, "resolution": DTHETA}),
                 call(3, "assess_xrr", {"measurement_id": MID, "resolution": DTHETA}),
                 call(99, "describe_server", {})]
        run = subprocess.run([str(EXE), "--workdir", str(work)], input="\n".join(lines) + "\n",
                             capture_output=True, text=True, encoding="utf-8", timeout=600)
        rep = {}
        for line in run.stdout.splitlines():
            msg = json.loads(line)
            if msg.get("id", 0) > 0:
                if msg["result"].get("isError"):
                    raise SystemExit(f"engine error on id {msg['id']}: {msg['result']['content'][0]['text']}")
                rep[msg["id"]] = json.loads(msg["result"]["content"][0]["text"])
        lam = rep[1]["lambda"]
        # The model at the wavelength the file gives, in a second pass.
        lines = [json.dumps({"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": {}}),
                 call(4, "calc_reflectivity", {"structure": EXPERT, "lambda": lam, "theta_min": 0.001,
                                               "theta_max": 7.0, "points": 7000, "delta_theta": DTHETA,
                                               "polarization": "s", "r_min": 1e-12,
                                               "max_inline_points": 0})]
        run = subprocess.run([str(EXE), "--workdir", str(work)], input="\n".join(lines) + "\n",
                             capture_output=True, text=True, encoding="utf-8", timeout=600)
        for line in run.stdout.splitlines():
            msg = json.loads(line)
            if msg.get("id") == 4:
                model = json.loads(msg["result"]["content"][0]["text"])
        OUT.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(work / model["file"], OUT / "curve-model.dat")
        data_key = next(k for k, v in rep[1].items() if isinstance(v, list) and v and isinstance(v[0], list))
        with open(OUT / "curve-measured.dat", "w", encoding="utf-8") as f:
            f.write("theta_deg\tR_normalised\n")
            for t, r in rep[1][data_key]:
                f.write(f"{t}\t{r}\n")
        meas = {k: v for k, v in rep[1].items() if k != data_key}
        (OUT / "measurement.json").write_text(json.dumps(meas, indent=1), encoding="utf-8")
        (OUT / "assess-design.json").write_text(json.dumps(rep[2], indent=1), encoding="utf-8")
        (OUT / "assess-none.json").write_text(json.dumps(rep[3], indent=1), encoding="utf-8")
        s = rep[99]["server"]
        print(f"engine: X-Ray Calc {s['xraycalc3_exe_version']}, git {s['git_revision']}; λ = {lam} ({rep[1]['lambda_source']})")
        print(rep[2]["summary_text"])
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main()
