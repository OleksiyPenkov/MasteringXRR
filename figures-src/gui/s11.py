"""Session for Figure 11-2: the Chart Info bar, zoomed on order 5 of CoC4 (see
scripts/figures/fig_11_2_chart_info.py for the recipe).

  python s11.py open        copy of CoC4-expert-full-fit.xrcx with 2teta=1, LinkedData=-1; launch
  python s11.py load        Data > Load ... CoC4.xrdml through the file dialog
  python s11.py ...         further steps done one at a time
"""
import json
import os
import sys
import time

import win32api
import win32con
import win32gui

import h
import xrc

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "s11")
os.makedirs(OUT, exist_ok=True)
STATE = os.path.join(OUT, "state.json")
SRC = str(h.local_paths.deposit("fits", "CoC4-expert-full-fit.xrcx"))
CURVE = str(h.local_paths.deposit("curves", "CoC4.xrdml"))
PROJ = os.path.join(OUT, "ch11-coc4-expert.xrcx")

what = sys.argv[1]
if what == "open":
    xrc.set_params(SRC, PROJ, ANGLE={"2teta": 1}, STATE={"LinkedData": -1})
    p, hwnd = h.launch(PROJ)
    json.dump({"pid": p.pid, "hwnd": hwnd}, open(STATE, "w"))
    h.grab(hwnd, os.path.join(OUT, "open.png"))
    print("opened", p.pid, hwnd)
    sys.exit()

st = json.load(open(STATE))
pid, hwnd = st["pid"], st["hwnd"]
if what == "load":
    xrc.cmd(hwnd, "data_load")
    dlg = h.wait_window(pid, cls="#32770", tries=30)
    time.sleep(1.5)
    edits = [x for x, c, t in h.children(dlg) if c == "Edit"]
    h.set_edit(edits[0], CURVE)
    time.sleep(0.5)
    win32gui.PostMessage(dlg, win32con.WM_COMMAND, 1, 0)       # Open
    time.sleep(4)
    print(h.windows(pid))
    h.grab(hwnd, os.path.join(OUT, "loaded.png"))
elif what == "wins":
    for w in h.windows(pid):
        print(w)
elif what == "shot":
    h.grab(hwnd, os.path.join(OUT, sys.argv[2]))
elif what == "edits":
    for x, c, t in h.children(hwnd):
        if c in ("TEdit", "TRzEdit", "TRzNumericEdit"):
            r = win32gui.GetWindowRect(x)
            print(x, c, repr(t), r)
elif what == "set":            # set <hwnd> <text>: set an edit and send Enter
    x = int(sys.argv[2])
    h.set_edit(x, sys.argv[3])
    win32gui.PostMessage(x, win32con.WM_KEYDOWN, win32con.VK_RETURN, 0)
    win32gui.PostMessage(x, win32con.WM_KEYUP, win32con.VK_RETURN, 0)
    time.sleep(0.5)
elif what == "run":
    xrc.cmd(hwnd, "run")
    time.sleep(4)
    h.grab(hwnd, os.path.join(OUT, "run.png"))
elif what == "click":          # click at window-image coords
    l, t, r, b = h.frame(hwnd)
    h.top(hwnd, True)
    h.fg(hwnd)
    win32api.SetCursorPos((l + int(sys.argv[2]), t + int(sys.argv[3])))
    time.sleep(0.3)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0)
    time.sleep(1)
    h.top(hwnd, False)
elif what == "drag":           # drag x1 y1 x2 y2 (window-image coords)
    l, t, r, b = h.frame(hwnd)
    x1, y1, x2, y2 = (int(v) for v in sys.argv[2:6])
    h.top(hwnd, True)
    h.fg(hwnd)
    win32api.SetCursorPos((l + x1, t + y1))
    time.sleep(0.3)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0)
    for k in range(1, 21):
        win32api.SetCursorPos((l + x1 + (x2 - x1) * k // 20, t + y1 + (y2 - y1) * k // 20))
        time.sleep(0.03)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0)
    time.sleep(1.5)
    h.top(hwnd, False)
elif what == "hover":          # hover x y then grab (keeps the cursor there, topmost)
    l, t, r, b = h.frame(hwnd)
    h.top(hwnd, True)
    h.fg(hwnd)
    win32api.SetCursorPos((l + int(sys.argv[2]), t + int(sys.argv[3])))
    time.sleep(1.5)
    from PIL import ImageGrab
    ImageGrab.grab(bbox=h.frame(hwnd), all_screens=True).save(os.path.join(OUT, sys.argv[4]))
    h.top(hwnd, False)
