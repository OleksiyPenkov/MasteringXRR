"""Session for Figures 17-1, 17-3 and 18-1: CoC4 in Polynomial mode of order 1, in the program.

Start: figures-src/ch19/coc4-gui-staged.xrcx (CoC4 with the conditioning of Chapter 14:
2θ 0.4165-13.3659°, Δθ 0.014°, R min 1.383e-6, λ 1.541874 Å), switched to Polynomial mode,
order 1. The model: the best free-period fit of Chapter 18 (seed 20260925) as the start, the
limits of the Chapter 17 fits (figures-src/ch17/coc4-final.json), the boxes after H of the ML
layers cleared and those after σ and ρ ticked (Chapter 17, steps 1-3).

  python s17.py open      launch, set the model, calculate, capture the start
  python s17.py fit       Calc > Auto Fitting, Run; capture the result
  python s17.py report    Result > Fit report ...; capture and copy its text
  python s17.py save      File > Save
  python s17.py close
"""
import json
import os
import sys
import time

import win32con
import win32gui

import h
import xrc

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "s17")
os.makedirs(OUT, exist_ok=True)
STATE = os.path.join(OUT, "state.json")
BOOK = str(h.local_paths.ROOT)
PROJ = os.path.join(OUT, "ch17-coc4-poly1.xrcx")

START = {"Top": {"H": 11.508, "s": 0.013446, "r": 0.877321},
         "C": {"H": 31.3439, "s": 4.34591, "r": 2.00455},
         "Co": {"H": 23.4458, "s": 2.62413, "r": 7.61481}}
LIM = {"Top": ((0.1, 40), (0.0, 15.0), (0.2, 1.8)),
       "C": ((20.93, 41.87), (1, 8), (1.5, 2.4)),
       "Co": ((15.53, 31.07), (1, 8), (6.0, 8.79))}


def set_model(m):
    for s in m["Stacks"]:
        for L in s["Layers"]:
            key = "Top" if s["T"] == "Top" else L["M"]
            v, (hl, sl, rl) = START[key], LIM[key]
            L.update({"H": v["H"], "s": v["s"], "r": v["r"],
                      "Hmin": hl[0], "Hmax": hl[1], "Smin": sl[0], "Smax": sl[1], "Rmin": rl[0], "Rmax": rl[1],
                      "HF": False, "SF": False, "RF": False,
                      "ProfileH": "", "ProfileS": "", "ProfileR": ""})
            ml = s["T"] == "ML"
            L.update({"HP": False, "SP": ml, "RP": ml})


def log(k, v):
    p = os.path.join(OUT, "log.json")
    d = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}
    d[k] = v
    h.dump(d, p)


what = sys.argv[1]
if what == "open":
    xrc.set_params(os.path.join(BOOK, r"figures-src\ch19\coc4-gui-staged.xrcx"), PROJ,
                   FIT={"Mode": 2, "PolyOrder": 1, "TWChi": 0, "FreePeriod": 1})
    p, hwnd = h.launch(PROJ)
    json.dump({"pid": p.pid, "hwnd": hwnd}, open(STATE, "w"))
    ok, m = xrc.edit_model(p.pid, hwnd, set_model)
    log("model-start", m)
    log("paste-ok", ok)
    xrc.cmd(hwnd, "run")
    time.sleep(4)
    h.grab(hwnd, os.path.join(OUT, "start.png"))
    log("start-texts", xrc.texts(hwnd))
    print("opened", p.pid, hwnd, "paste ok", ok)
else:
    st = json.load(open(STATE))
    pid, hwnd = st["pid"], st["hwnd"]
    if what == "fit":
        btn, warn = xrc.fit(pid, hwnd, "auto_fit", wait_s=float(sys.argv[2]) if len(sys.argv) > 2 else 40,
                            limits_png=os.path.join(OUT, "limits.png"))
        log("fit-button", btn)
        log("fit-warning", warn)
        xrc.cmd(hwnd, "run")
        time.sleep(4)
        h.grab(hwnd, os.path.join(OUT, "after.png"))
        log("after-texts", xrc.texts(hwnd))
        print("fit", btn, warn)
    elif what == "report":
        text, fr = xrc.fit_report(pid, hwnd, os.path.join(OUT, "fit-report.png"))
        open(os.path.join(OUT, "fit-report.txt"), "w", encoding="utf-8").write(text)
        print(text[:3000])
    elif what == "shot":
        h.grab(hwnd, os.path.join(OUT, sys.argv[2]))
    elif what == "save":
        xrc.cmd(hwnd, "save")
        time.sleep(3)
        print([t for x, c, t in h.windows(pid)])
    elif what == "close":
        win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
