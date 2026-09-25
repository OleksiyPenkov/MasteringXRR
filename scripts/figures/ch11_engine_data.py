"""Chapter 11: reading the CoC4 measurement before the first fit.

The command-line server that ships with X-Ray Calc (XRC_MCP.exe in the build
folder, engine 3.9.4), driven through xrc_engine.Engine. The book never names
the server. Its import is the GUI's .xrdml reader and its assessment is the
unit Data > Assess XRR quality ... runs, so the numbers are the program's.

The measurement is the raw CoC4 file of the fitting procedure's deposit
(curves/CoC4.xrdml, CC BY 4.0). The server reads measurements only from an
inbox folder in its work folder, so the file is copied there for the run and
deleted with it; nothing is copied into the book.

Steps
  1. import the file; keep the curve as the import leaves it (θ, normalised to
     1 at the maximum, zero counts floored) and the header
  2. number the Bragg orders the way procedure v5 §1.5 says: predict each order
     with refraction, take the maximum in a window around the prediction, refit
     sin²θ against m² and repeat until the assignment stops changing. Orders
     1-6, the ones that stand out clearly, make the seed (§6.6); orders 7 and 8
     are then looked for where the seed puts them
  3. the assessment with the CoC4 expert model as the design
  4. δ of C and Co at the file's λ, for δ̄ of the expert model
  5. model curves: the expert structure with both thicknesses scaled so the
     period is the seeded D (the author's practice), and the same at D + 1 %,
     at Δθ = 0.012° (the expert's width); and the seeded-D model with no blur
     and a fine step, whose own peaks test the straight line

  measurement.json    the import's header
  curve-measured.dat  θ, R as imported
  orders.json         the numbered orders (2θ, counts) and the seed
  assess-design.json  the eight checks with the expert model as the design
  constants.json      δ, β of C and Co at the file's λ and their table densities
  curve-seed.dat, curve-plus1.dat, curve-seed-sharp.dat   the model curves

Run:  python scripts/figures/ch11_engine_data.py
Out:  figures-src/ch11/
"""
import json
import math
import shutil
from pathlib import Path

import numpy as np

from xrc_engine import Engine

import local_paths

DEPOSIT = local_paths.deposit("curves")
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "figures-src" / "ch11"
MID = "CoC4/CoC4.xrdml"
LAMBDA = 1.541874     # Å, (1.540598 + 0.5 × 1.544426) / 1.5, the file's lines and ratio
DTHETA = 0.012          # °, the expert's width in the CoC4 project (params.dsc [ANGLE] width)
SEED_ORDERS = 6         # orders 1-6: the ones whose index is unambiguous
MAX_ORDER = 8
WINDOW = 0.04           # ° in θ (0.08° in 2θ) either side of a predicted order

# The expert's CoC4 fit (fits/CoC4-expert-full-fit.xrcx in the deposit; every CoC4 number
# of the methods paper comes from this file). Values as stored in the project.
H_C, H_CO = 30.66625, 24.100008
EXPERT = {"substrate": {"material": "SiO2", "sigma": 4.4, "density": 2.65},
          "stacks": [{"N": 20, "layers": [
              {"material": "C", "thickness": H_C, "sigma": 5.584755, "density": 1.860679},
              {"material": "Co", "thickness": H_CO, "sigma": 2.456746, "density": 8.096237}]}]}


def scaled(d):
    """The expert structure with both thicknesses scaled by one factor to the period d."""
    f = d / (H_C + H_CO)
    s = json.loads(json.dumps(EXPERT))
    for layer in s["stacks"][0]["layers"]:
        layer["thickness"] *= f
    return s


def line(orders, lam):
    """Least squares of sin²θ against m²: the period and 2δ̄."""
    m = np.array([o["m"] for o in orders], float)
    s2 = np.sin(np.radians([o["theta"] for o in orders])) ** 2
    a, b = np.polyfit(m ** 2, s2, 1)
    return lam / (2 * math.sqrt(a)), b


def predict(m, d, two_delta, lam):
    return math.degrees(math.asin(math.sqrt((m * lam / (2 * d)) ** 2 + two_delta)))


def peak(theta, r, centre):
    s = (theta > centre - WINDOW) & (theta < centre + WINDOW)
    i = np.argmax(r[s])
    return float(theta[s][i]), float(r[s][i])


def number_orders(theta, r, lam):
    """Add the orders one at a time: predict the next with refraction from those found so far,
    take the maximum within a quarter of the order spacing, refit, and go on. Then repeat the
    whole assignment with the final line until it stops changing (procedure §1.5)."""
    # Order 1: the strongest maximum past the critical edge (above 2θ = 1°).
    s = theta > 0.5
    t1, v1 = float(theta[s][np.argmax(r[s])]), float(r[s].max())
    orders = [{"m": 1, "theta": t1, "R": v1}]
    d, two_delta = lam / (2 * math.sin(math.radians(t1))), 0.0     # plain law: a first guess
    for m in range(2, SEED_ORDERS + 1):
        c = predict(m, d, two_delta, lam)
        half = 0.25 * math.degrees(lam / (2 * d))                    # a quarter of the spacing in θ
        sel = (theta > c - half) & (theta < c + half)
        i = np.argmax(r[sel])
        orders.append({"m": m, "theta": float(theta[sel][i]), "R": float(r[sel][i])})
        d, two_delta = line(orders, lam)
    for _ in range(20):
        new = []
        for o in orders:
            t, v = peak(theta, r, predict(o["m"], d, two_delta, lam))
            new.append({"m": o["m"], "theta": t, "R": v})
        if [o["theta"] for o in new] == [o["theta"] for o in orders]:
            break
        orders = new
        d, two_delta = line(orders, lam)
    return orders, d, two_delta


def main():
    e = Engine()
    try:
        inbox = e.work / "inbox" / "CoC4"
        inbox.mkdir(parents=True)
        shutil.copyfile(DEPOSIT / "CoC4.xrdml", inbox / "CoC4.xrdml")
        meas = e.call("get_measurement", {"measurement_id": MID, "max_points": 6000})
        # The server prints λ to five decimals; the import's own value is the Kα doublet
        # weighted by the file's ratio, 1.541874 Å (Chapter 10), which it rounds to.
        assert abs(meas["lambda"] - LAMBDA) < 1e-5, meas["lambda"]
        lam = LAMBDA
        key = next(k for k, v in meas.items() if isinstance(v, list) and v and isinstance(v[0], list))
        data = np.array(meas[key], float)
        theta, r = data[:, 0], data[:, 1]

        orders, d, two_delta = number_orders(theta, r, lam)
        weak = []
        for m in range(SEED_ORDERS + 1, MAX_ORDER + 1):
            t, v = peak(theta, r, predict(m, d, two_delta, lam))
            weak.append({"m": m, "theta": t, "R": v})

        assess = e.call("assess_xrr", {"measurement_id": MID, "structure": EXPERT, "resolution": DTHETA})
        consts = {m: e.call("optical_constants", {"material": m, "lambda": lam}) for m in ("C", "Co")}

        OUT.mkdir(parents=True, exist_ok=True)
        curves = {"curve-seed.dat": (scaled(d), DTHETA, 7.4, 7400),
                  "curve-plus1.dat": (scaled(1.01 * d), DTHETA, 7.4, 7400),
                  "curve-seed-sharp.dat": (scaled(d), 0.0, 6.0, 24000)}
        for name, (s, dt, tmax, pts) in curves.items():
            c = e.call("calc_reflectivity", {"structure": s, "lambda": lam, "theta_min": 0.001,
                                             "theta_max": tmax, "points": pts, "delta_theta": dt,
                                             "polarization": "s", "r_min": 1e-12,
                                             "max_inline_points": 0})
            shutil.copyfile(e.work / c["file"], OUT / name)

        with open(OUT / "curve-measured.dat", "w", encoding="utf-8") as f:
            f.write("theta_deg\tR_normalised\n")
            for t, v in zip(theta, r):
                f.write(f"{t}\t{v}\n")
        head = {k: v for k, v in meas.items() if k != key}
        (OUT / "measurement.json").write_text(json.dumps(head, indent=1), encoding="utf-8")
        (OUT / "orders.json").write_text(json.dumps(
            {"lambda": lam, "seed_orders": orders, "weak_orders": weak,
             "D_seed": d, "two_delta_seed": two_delta, "window_theta_deg": WINDOW,
             "expert": EXPERT}, indent=1), encoding="utf-8")
        (OUT / "assess-design.json").write_text(json.dumps(assess, indent=1), encoding="utf-8")
        (OUT / "constants.json").write_text(json.dumps(consts, indent=1), encoding="utf-8")
        srv = e.describe()
        print(f"engine: X-Ray Calc {srv['xraycalc3_exe_version']}, git {srv['git_revision']}; "
              f"λ = {lam} ({meas.get('lambda_source')})")
        print(f"seed from orders 1-{SEED_ORDERS}: D = {d:.4f} Å, 2δ̄ = {two_delta:.4e}")
        print(assess.get("summary_text", ""))
    finally:
        e.close()


if __name__ == "__main__":
    main()
