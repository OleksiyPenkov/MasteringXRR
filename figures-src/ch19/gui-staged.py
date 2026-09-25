"""Session for Figures 19-2, 19-3 and Table 19-5: a staged fit of CoC4 in the program.

Start: figures-src/ch19/coc4-gui-staged.xrcx (CoC4, conditioning of Chapter 14), Periodic mode with
Free period ± 10 %, TW χ² None. The model: the best free-period fit of Chapter 18 (seed 20260925),
the limits of the Chapter 17 fits for the period, the preset's windows for the contamination
layer (H 5-40 Å, σ 0-10 Å, ρ 0.6-1.4 g/cm³), as in the first staged run (gui-staged-log.json).
  pass 1  Calc > Auto Fitting, Run, everything free, TW χ² None
  pass 2  the ML stack frozen (Fix on H, σ, ρ), TW χ² 1/sqr, Calc > Resume Fitting
  pass 3  thawed, TW χ² None, Calc > Resume Fitting
After each pass: Calc > Run, the window and its texts, the Fit report text.
"""
import ctypes
import json
import os
import sys
import time

import win32api
import win32con
import win32gui

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "gui"))
import h  # noqa: E402
import xrc  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "s19")
os.makedirs(OUT, exist_ok=True)
BOOK = str(h.local_paths.ROOT)
PROJ = os.path.join(OUT, "ch19-coc4-staged.xrcx")
WAIT = 30

START = {"Top": {"H": 11.508, "s": 0.013446, "r": 0.877321},
         "C": {"H": 31.3439, "s": 4.34591, "r": 2.00455},
         "Co": {"H": 23.4458, "s": 2.62413, "r": 7.61481}}
LIM = {"Top": ((5, 40), (0, 10), (0.6, 1.4)),
       "C": ((20.93, 41.87), (1, 8), (1.5, 2.4)),
       "Co": ((15.53, 31.07), (1, 8), (6.0, 8.79))}
log = {}


def set_model(m):
    for s in m["Stacks"]:
        for L in s["Layers"]:
            key = "Top" if s["T"] == "Top" else L["M"]
            v, (hl, sl, rl) = START[key], LIM[key]
            L.update({"H": v["H"], "s": v["s"], "r": v["r"],
                      "Hmin": hl[0], "Hmax": hl[1], "Smin": sl[0], "Smax": sl[1], "Rmin": rl[0], "Rmax": rl[1],
                      "HF": False, "SF": False, "RF": False, "HP": False, "SP": False, "RP": False,
                      "ProfileH": "", "ProfileS": "", "ProfileR": ""})


def flags(on):
    def f(m):
        for s in m["Stacks"]:
            for L in s["Layers"]:
                for k in ("HF", "SF", "RF"):
                    L[k] = on if s["T"] == "ML" else False
    return f


def set_tw(hwnd, index):
    for x, c, t in h.children(hwnd):
        if "ComboBox" in c and win32gui.SendMessage(x, win32con.CB_GETCOUNT, 0, 0) == 6:
            buf = ctypes.create_unicode_buffer(32)
            ctypes.windll.user32.SendMessageW(x, win32con.CB_GETLBTEXT, 4, buf)
            if buf.value == "1/sqr":
                win32gui.SendMessage(x, win32con.CB_SETCURSEL, index, 0)
                cid = win32gui.GetDlgCtrlID(x)
                win32gui.SendMessage(win32gui.GetParent(x), win32con.WM_COMMAND,
                                     (win32con.CBN_SELCHANGE << 16) | (cid & 0xFFFF), x)
                time.sleep(0.5)
                return h.gettext(x)
    return None


def warn_grab(pid, tag):
    """Grab a Warning box if one is up (called from the fit loop through a hook)."""


def after(pid, hwnd, tag):
    xrc.cmd(hwnd, "run")
    time.sleep(4)
    l, t, r, b = h.frame(hwnd)
    win32api.SetCursorPos((l + 1500, t + 880))
    h.grab(hwnd, os.path.join(OUT, f"{tag}-main.png"))
    log[tag + "-texts"] = xrc.texts(hwnd)
    text, _ = xrc.fit_report(pid, hwnd, os.path.join(OUT, f"{tag}-report.png"))
    log[tag + "-report"] = text


def fit(pid, hwnd, which, tag):
    """xrc.fit, but grab the warning box before answering it."""
    xrc.cmd(hwnd, which)
    lim = h.wait_window(pid, cls="TfrmLimits", tries=40)
    time.sleep(1.5)
    h.grab(lim, os.path.join(OUT, f"{tag}-limits.png"), keep_top=True)
    btns = [(x, t) for x, c, t in h.children(lim) if t in ("Run", "Resume")]
    h.fg(lim)
    time.sleep(0.3)
    h.click(btns[0][0])
    h.top(lim, False)
    log[tag + "-button"] = btns[0][1]
    for _ in range(10):
        time.sleep(0.5)
        w = [(x, c, t) for x, c, t in h.windows(pid) if c in ("TMessageForm", "#32770")]
        if w:
            x = w[0][0]
            time.sleep(0.5)
            h.grab(x, os.path.join(OUT, f"{tag}-warning.png"), keep_top=True)
            log[tag + "-warning"] = [w[0][1], w[0][2]] + [t for _, c, t in h.children(x) if t]
            win32gui.PostMessage(x, win32con.WM_COMMAND, 6, 0)
            time.sleep(1)
            if win32gui.IsWindow(x) and win32gui.IsWindowVisible(x):
                win32gui.PostMessage(x, win32con.WM_COMMAND, 1, 0)
            break
    time.sleep(WAIT)


xrc.set_params(os.path.join(BOOK, r"figures-src\ch19\coc4-gui-staged.xrcx"), PROJ,
               FIT={"Mode": 1, "TWChi": 0, "FreePeriod": 1, "PeriodWindow": 10})
p, hwnd = h.launch(PROJ)
pid = p.pid
try:
    log["paste-ok"], log["model-start"] = xrc.edit_model(pid, hwnd, set_model)
    log["tw1"] = set_tw(hwnd, 0)
    xrc.cmd(hwnd, "run")
    time.sleep(4)
    h.grab(hwnd, os.path.join(OUT, "s0-main.png"))
    log["s0-texts"] = xrc.texts(hwnd)
    # pass 1
    fit(pid, hwnd, "auto_fit", "s1")
    after(pid, hwnd, "s1")
    # pass 2
    log["freeze-ok"], log["model2"] = xrc.edit_model(pid, hwnd, flags(True))
    log["tw2"] = set_tw(hwnd, 4)
    xrc.cmd(hwnd, "run")
    time.sleep(4)
    l, t, r, b = h.frame(hwnd)
    win32api.SetCursorPos((l + 1500, t + 880))
    h.grab(hwnd, os.path.join(OUT, "s2-before.png"))
    fit(pid, hwnd, "resume", "s2")
    after(pid, hwnd, "s2")
    # pass 3
    log["thaw-ok"], log["model3"] = xrc.edit_model(pid, hwnd, flags(False))
    log["tw3"] = set_tw(hwnd, 0)
    fit(pid, hwnd, "resume", "s3")
    after(pid, hwnd, "s3")
    log["model-final"] = xrc.read_model(pid, hwnd)
    xrc.cmd(hwnd, "save")
    time.sleep(4)
finally:
    h.dump(log, os.path.join(OUT, "log.json"))
    p.kill()
    print("done", {k: v for k, v in log.items() if not k.endswith(("texts", "report")) and not k.startswith("model")})
