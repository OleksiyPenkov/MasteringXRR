"""Figures 11-1 and 11-3, Tables 11-1 and 11-2 and the numbers of Chapter 11.

  Figure 11-1  the CoC4 measurement as imported, with θ_max, the numbered
               orders and the one-count floor marked
  Figure 11-3  orders 5-7: the measurement, the model at the seeded period
               and the model at the seeded period + 1 % (engine)
  Table 11-1   the orders: measured 2θ, counts, 2θ predicted with refraction
               from the seed (orders 1-6), difference, and m × 2θ1
  Table 11-2   three numberings of the same peaks: the period, 2δ̄, 2θc and
               the rms residual of the straight line

The straight line is sin²θm against m² by least squares (procedure v5 §6.6):
the slope gives D = λ / (2 √slope), the intercept 2δ̄, and θc = √(2δ̄). Its
standard errors come from the least-squares covariance with n − 2 degrees of
freedom. One count on the imported curve is 1 / (peak rate × counting time)
(procedure §1.5), from the header the import writes.

Run:  python scripts/figures/fig_11_figures.py   (after ch11_engine_data.py)
Out:  public/figures/fig-11-1-reading-coc4.svg, public/figures/fig-11-3-period-off.svg
"""
import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "figures-src" / "ch11"
OUT = ROOT / "public" / "figures"

STROKE = "#334155"
ACCENT = "#1a5276"
MUTED = "#94a3b8"
ORANGE = "#b9770e"
ENGINE = "Model reflectivity calculated by the X-Ray Calc 3.9.4.1250 engine (figures-src/ch11/)."


def setup():
    plt.rcParams.update({
        "font.family": "sans-serif",
        # Drawn at the print column's width (136 mm), printed at 1:1.
        "font.size": 9, "xtick.labelsize": 9, "ytick.labelsize": 9,
        "svg.fonttype": "none",
        "axes.edgecolor": STROKE, "axes.labelcolor": STROKE,
        "xtick.color": STROKE, "ytick.color": STROKE,
    })


def load(name):
    return json.loads((SRC / name).read_text(encoding="utf-8"))


def curve(name):
    d = np.loadtxt(SRC / name, skiprows=1)
    return d[:, 0], d[:, 1]


ORD = load("orders.json")
LAM = ORD["lambda"]
COUNT = load("assess-design.json")["checks"]["counting"]
ONE = 1 / (COUNT["peak_rate_cps"] * COUNT["counting_time_s"])      # one count on the imported curve


def fit(m, two_theta):
    """sin²θ against m²: D, 2δ̄, their standard errors, 2θc and the rms residual."""
    m = np.asarray(m, float)
    s2 = np.sin(np.radians(np.asarray(two_theta) / 2)) ** 2
    a_mat = np.vstack([m ** 2, np.ones_like(m)]).T
    (a, b), *_ = np.linalg.lstsq(a_mat, s2, rcond=None)
    res = s2 - a_mat @ np.array([a, b])
    out = {"D": LAM / (2 * math.sqrt(a)), "2d": b, "rms": float(np.sqrt(np.mean(res ** 2)))}
    out["2thc"] = 2 * math.degrees(math.sqrt(b)) if b > 0 else None
    if len(m) > 2:
        cov = (res @ res) / (len(m) - 2) * np.linalg.inv(a_mat.T @ a_mat)
        out["sD"] = out["D"] / 2 * math.sqrt(cov[0, 0]) / a
        out["s2d"] = math.sqrt(cov[1, 1])
        out["s2thc"] = out["2thc"] / 2 * out["s2d"] / b if b > 0 else None
    return out


def predict(m, d, two_delta):
    return 2 * math.degrees(math.asin(math.sqrt((m * LAM / (2 * d)) ** 2 + two_delta)))


def model_peaks(name, d, two_delta, orders):
    t, r = curve(name)
    out = []
    for m in orders:
        c = predict(m, d, two_delta) / 2
        s = (t > c - 0.05) & (t < c + 0.05)
        out.append(2 * float(t[s][np.argmax(r[s])]))
    return out


def falls(t, r, level):
    """First 2θ past the plateau maximum where R drops below level × the maximum."""
    i0 = int(np.argmax(np.where(t < 0.5, r, 0)))
    j = i0 + int(np.argmax(r[i0:] < level * r[i0]))
    return 2 * float(t[j])


def numbers():
    meas = load("measurement.json")
    a = load("assess-design.json")["checks"]
    tm, rm = curve("curve-measured.dat")
    print(f"engine λ = {LAM} Å ({meas['lambda_source']}); {meas['points']} points")
    print(f"counting: peak {COUNT['peak_counts']} counts at 2θ = {COUNT['peak_two_theta_deg']}°, "
          f"{COUNT['peak_rate_cps']} counts/s, {COUNT['counting_time_s']} s per point, "
          f"attenuation factors {COUNT['attenuation_factors']}; one count = {ONE:.4e}")
    z = a["zeros"]
    print(f"zeros: {z['value']} ({z['fraction'] * 100:.1f} %), first at 2θ = {z['first_two_theta_deg']}°")
    p = a["plateau_vs_first_order"]
    print(f"plateau vs first order: {p['value']:.3f} against the design's {p['model_ratio']:.3f} ({p['verdict']})")
    ov = a["orders_visible"]
    print(f"orders visible: {ov['value']} of {ov['orders_predicted_in_range']}, design expects "
          f"{ov['orders_expected_visible']} ({ov['verdict']})")

    seed = ORD["seed_orders"]
    allo = seed + ORD["weak_orders"]
    m6 = [o["m"] for o in seed]
    t6 = [2 * o["theta"] for o in seed]
    f6 = fit(m6, t6)
    print(f"\nseed, orders 1-6: D = {f6['D']:.4f} ± {f6['sD']:.4f} Å, 2δ̄ = {f6['2d']:.4e} ± {f6['s2d']:.2e}, "
          f"2θc = {f6['2thc']:.4f} ± {f6['s2thc']:.4f}°, rms {f6['rms']:.2e}")
    f8 = fit([o["m"] for o in allo], [2 * o["theta"] for o in allo])
    print(f"all eight orders:  D = {f8['D']:.4f} ± {f8['sD']:.4f} Å, 2δ̄ = {f8['2d']:.4e}, "
          f"2θc = {f8['2thc']:.4f} ± {f8['s2thc']:.4f}°")

    print("\nTable 11-1 (2θ; predicted from the seed of orders 1-6):")
    print("  m   2θ meas.   counts      2θ pred.  diff     m×2θ1    even − meas.")
    t1 = t6[0]
    for o in allo:
        tt = 2 * o["theta"]
        pr = predict(o["m"], f6["D"], f6["2d"])
        print(f"  {o['m']}   {tt:.4f}   {o['R'] / ONE:10.1f}  {pr:.4f}  {tt - pr:+.4f}  {o['m'] * t1:.4f}  {o['m'] * t1 - tt:+.3f}")
    sp = (t6[-1] - t6[0]) / 5
    print(f"  mean spacing of orders 1-6: {sp:.3f}°")

    gamma = ORD["expert"]["stacks"][0]["layers"][1]["thickness"] / sum(
        l["thickness"] for l in ORD["expert"]["stacks"][0]["layers"])
    print(f"\nΓ (expert fit) = {gamma:.3f}; sin²(mπΓ): " +
          ", ".join(f"{m}: {math.sin(m * math.pi * gamma) ** 2:.2f}" for m in range(1, 9)))

    # High orders by window: the mean count in ±0.04° of the prediction against the mean in
    # 0.2-0.8° either side.
    print("\nwindow test (2θ ± 0.04° around the prediction, counts per point):")
    tt2 = tm * 2
    for m in range(4, 10):
        c = predict(m, f6["D"], f6["2d"])
        w = (tt2 > c - 0.04) & (tt2 < c + 0.04)
        off = ((tt2 > c - 0.8) & (tt2 < c - 0.2)) | ((tt2 > c + 0.2) & (tt2 < c + 0.8))
        print(f"  m={m} at {c:.3f}°: in window {rm[w].mean() / ONE:.2f} (sum {rm[w].sum() / ONE:.0f}, "
              f"{w.sum()} pts), around {rm[off].mean() / ONE:.2f}")
    print("  (the imported tail repeats a floored value for each zero count, so these means are upper bounds)")

    print("\nTable 11-2, three numberings:")
    rows = [("correct, orders 1-6", m6, t6),
            ("every order one too high", [m + 1 for m in m6], t6),
            ("weak 2nd order missed", [1, 2, 3, 4, 5], [t6[0]] + t6[2:])]
    for label, m, t in rows:
        f = fit(m, t)
        th = f"{f['2thc']:.3f}°" if f["2thc"] else "none (2δ̄ < 0)"
        print(f"  {label:26s} D = {f['D']:.2f} Å  2δ̄ = {f['2d']:+.3e}  2θc = {th:14s} rms = {f['rms']:.2e} "
              f"({f['rms'] / f6['rms']:.0f} × the correct)")

    # The edge of the measured curve, and the edge δ̄ of the expert model puts there.
    print("\nedge of the measured curve (fraction of the plateau maximum → 2θ):")
    for lev in (0.9, 0.5, 0.1):
        print(f"  {lev}: {falls(tm, rm, lev):.4f}°")
    c = load("constants.json")
    lay = {l["material"]: l for l in ORD["expert"]["stacks"][0]["layers"]}
    dsum = sum(l["thickness"] for l in lay.values())
    dbar = sum(lay[k]["thickness"] * c[k]["delta"] * lay[k]["density"] / c[k]["density_used"]
               for k in lay) / dsum
    for k in lay:
        print(f"  δ({k}) = {c[k]['delta']:.4e} at {c[k]['density_used']} g/cm³ → "
              f"{c[k]['delta'] * lay[k]['density'] / c[k]['density_used']:.4e} at {lay[k]['density']:.3f}")
    print(f"  expert model: δ̄ = {dbar:.4e}, 2δ̄ = {2 * dbar:.4e}, 2θc = {2 * math.degrees(math.sqrt(2 * dbar)):.4f}°")
    ts, rs = curve("curve-seed.dat")
    for lev in (0.9, 0.5, 0.1):
        print(f"  seeded model falls to {lev} at 2θ = {falls(ts, rs, lev):.4f}°")
    # The seeded model's own peaks, no blur: how far the line's intercept is from its δ̄.
    pk = model_peaks("curve-seed-sharp.dat", f6["D"], f6["2d"], range(1, 7))
    fm = fit(range(1, 7), pk)
    print(f"  seeded model's own peaks 1-6 (no blur): D = {fm['D']:.4f} Å (model {f6['D']:.4f}), "
          f"2δ̄ = {fm['2d']:.4e}, {(fm['2d'] / (2 * dbar) - 1) * 100:+.1f} % against the model's 2δ̄; "
          f"2θc = {fm['2thc']:.4f}°")
    print(f"  seed intercept against the model's 2δ̄: {(f6['2d'] / (2 * dbar) - 1) * 100:+.1f} %")
    return f6


def figure_11_1(f6):
    tm, rm = curve("curve-measured.dat")
    fig, ax = plt.subplots(figsize=(5.35, 3.1))
    ax.plot(tm * 2, rm, color=MUTED, lw=0.7)
    ax.set_yscale("log")
    ax.set_ylim(3e-7, 3)
    ax.set_xlim(0, 15)
    ax.set_xlabel("2θ (°)")
    ax.set_ylabel("R (imported, 1 at the maximum)")
    ax.axhline(ONE, color=ORANGE, lw=0.8, ls="--")
    ax.text(14.8, ONE / 2.4, "one count", color=ORANGE, fontsize=8.5, ha="right", va="top")
    i0 = int(np.argmax(rm))
    ax.plot([tm[i0] * 2], [rm[i0]], "o", ms=4, color=ACCENT)
    ax.annotate(rf"$\theta_{{\max}}$: 2θ = {tm[i0] * 2:.3f}°", (tm[i0] * 2, rm[i0]), xytext=(2.3, 0.35),
                color=ACCENT, fontsize=8.5, arrowprops={"arrowstyle": "-", "color": ACCENT, "lw": 0.6})
    for o in ORD["seed_orders"] + ORD["weak_orders"]:
        x, y = 2 * o["theta"], o["R"]
        ax.text(x, y * 2.2, str(o["m"]), color=ACCENT if o["m"] <= 6 else ORANGE,
                fontsize=8.5, ha="center", fontweight="bold")
    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)
    fig.tight_layout()
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / "fig-11-1-reading-coc4.svg", format="svg", metadata={
        "Title": "Figure 11-1: what to read on the CoC4 curve",
        "Description": "Measured CoC4 (deposit, CC BY 4.0), as the X-Ray Calc 3.9.4.1250 import leaves it. "
                       "Script: scripts/figures/fig_11_figures.py"})


def figure_11_3(f6):
    tm, rm = curve("curve-measured.dat")
    ts, rs = curve("curve-seed.dat")
    tp, rp = curve("curve-plus1.dat")
    fig, axes = plt.subplots(1, 3, figsize=(5.35, 2.5), sharey=False)
    shift = {}
    for ax, m in zip(axes, (5, 6, 7)):
        c = predict(m, f6["D"], f6["2d"])
        lo, hi = c - 0.35, c + 0.25
        for t, r, col, lw, lab in [(tm, rm, MUTED, 0.9, "measured"), (ts, rs, ACCENT, 1.0, "seeded D"),
                                   (tp, rp, ORANGE, 1.0, "D + 1 %")]:
            s = (t * 2 > lo) & (t * 2 < hi)
            ax.plot(t[s] * 2, r[s], color=col, lw=lw, label=lab)
        s1 = (ts * 2 > c - 0.1) & (ts * 2 < c + 0.1)
        s2 = (tp * 2 > c - 0.3) & (tp * 2 < c + 0.1)
        shift[m] = 2 * (tp[s2][np.argmax(rp[s2])] - ts[s1][np.argmax(rs[s1])])
        ax.set_yscale("log")
        ax.set_xlim(lo, hi)
        ax.set_title(f"order {m}", fontsize=9, color=STROKE, loc="left")
        ax.spines["right"].set_visible(False)
        ax.spines["top"].set_visible(False)
        ax.tick_params(axis="x", labelsize=8)
    axes[0].set_ylabel("R")
    axes[1].set_xlabel("2θ (°)")
    fig.legend(*axes[0].get_legend_handles_labels(), frameon=False, fontsize=8, loc="upper center",
               ncol=3, bbox_to_anchor=(0.5, 1.0))
    fig.tight_layout(rect=(0, 0, 1, 0.9))
    fig.savefig(OUT / "fig-11-3-period-off.svg", format="svg", metadata={
        "Title": "Figure 11-3: a period 1 % off",
        "Description": f"Measured CoC4 (deposit, CC BY 4.0). {ENGINE} Script: scripts/figures/fig_11_figures.py"})
    print("\nFigure 11-3, model peak shift for D + 1 % (2θ): " +
          ", ".join(f"order {m}: {v:+.3f}°" for m, v in shift.items()))
    # The width of an order, for comparison: FWHM of the seeded model's 5th order.
    c = predict(5, f6["D"], f6["2d"]) / 2
    s = (ts > c - 0.1) & (ts < c + 0.1)
    t5, r5 = ts[s], rs[s]
    above = t5[r5 > r5.max() / 2]
    print(f"  seeded model, order 5: FWHM = {2 * (above.max() - above.min()):.3f}° in 2θ")


def main():
    setup()
    f6 = numbers()
    figure_11_1(f6)
    figure_11_3(f6)


if __name__ == "__main__":
    main()
