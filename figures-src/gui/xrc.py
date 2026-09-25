"""X-Ray Calc 3.9.4.1270 specifics: command ids (read from the live menus), the model editor, fits."""
import configparser
import io
import json
import shutil
import time
import zipfile

import win32api
import win32con
import win32gui

import h

# Main-menu command ids of 3.9.4.1270, read from the open popups (dfm order - 9)
CMD = {"save": 22, "save_as": 23, "duplicate": 31, "edit_model": 46, "data_load": 56,
       "run": 68, "calc_all": 69, "auto_fit": 71, "resume": 72, "export_fit": 84, "fit_report": 85}


def set_params(src, dst, **sections):
    """Copy an .xrcx and change params.dsc keys: set_params(a, b, FIT={'Mode': 2})."""
    zin = zipfile.ZipFile(src)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zout:
        for it in zin.infolist():
            data = zin.read(it.filename)
            if it.filename == "params.dsc":
                txt = data.decode("utf-8-sig")
                cp = configparser.ConfigParser(interpolation=None)
                cp.optionxform = str
                cp.read_string(txt)
                for sec, kv in sections.items():
                    for k, v in kv.items():
                        cp[sec][k] = str(v)
                s = io.StringIO()
                cp.write(s, space_around_delimiters=False)
                data = s.getvalue().replace("\n", "\r\n").encode("utf-8")
            zout.writestr(it, data)
    open(dst, "wb").write(buf.getvalue())


def cmd(hwnd, name):
    win32gui.PostMessage(hwnd, win32con.WM_COMMAND, CMD[name], 0)


def edit_model(pid, hwnd, fn):
    """Open the model text editor, change the JSON with fn (in place), paste it back and save."""
    cmd(hwnd, "edit_model")
    dlg = h.wait_window(pid, cls="TfrmJsonEditor")
    time.sleep(1)
    ed = [x for x, c, t in h.children(dlg) if c == "TSynEdit"][0]
    m = json.loads(h.gettext(ed))
    fn(m)
    h.clip_set(json.dumps(m, separators=(",", ":")))
    h.top(dlg, True)
    h.fg(dlg)
    time.sleep(0.5)
    h.click(ed, 200, 100)
    time.sleep(0.4)
    h.chord(ord("A"))
    h.chord(ord("V"))
    time.sleep(0.5)
    ok = json.loads(h.gettext(ed)) == m
    save = [x for x, c, t in h.children(dlg) if t == "Save"]
    h.click(save[0])
    time.sleep(1.5)
    return ok, m


def read_model(pid, hwnd):
    got = {}
    edit_model(pid, hwnd, lambda m: got.update(json.loads(json.dumps(m))))
    return got


def fit(pid, hwnd, which="auto_fit", wait_s=40, limits_png=None):
    """Open the Fitting Limits dialog, press Run/Resume, answer a warning with Yes, wait."""
    cmd(hwnd, which)
    lim = h.wait_window(pid, cls="TfrmLimits", tries=40)
    time.sleep(1.5)
    if limits_png:
        h.grab(lim, limits_png, keep_top=True)
    btns = [(x, t) for x, c, t in h.children(lim) if t in ("Run", "Resume")]
    h.top(lim, True)
    h.fg(lim)
    time.sleep(0.3)
    h.click(btns[0][0])
    h.top(lim, False)
    warn = None
    for _ in range(8):
        time.sleep(0.5)
        w = [(x, c, t) for x, c, t in h.windows(pid) if c in ("TMessageForm", "#32770")]
        if w:
            x = w[0][0]
            warn = [w[0][1], w[0][2]] + [t for _, c, t in h.children(x) if t]
            win32gui.PostMessage(x, win32con.WM_COMMAND, 6, 0)      # Yes
            time.sleep(1)
            if win32gui.IsWindow(x) and win32gui.IsWindowVisible(x):
                win32gui.PostMessage(x, win32con.WM_COMMAND, 1, 0)  # OK
            break
    time.sleep(wait_s)
    return btns[0][1], warn


def fit_report(pid, hwnd, png):
    cmd(hwnd, "fit_report")
    dlg = h.wait_window(pid, title="Fit report")
    time.sleep(1.5)
    frame = h.grab(dlg, png, keep_top=True)
    btn = [x for x, c, t in h.children(dlg) if t == "Copy as text"]
    h.fg(dlg)
    time.sleep(0.3)
    h.click(btn[0])
    time.sleep(1)
    text = h.clip_get()
    h.top(dlg, False)
    win32gui.PostMessage(dlg, win32con.WM_CLOSE, 0, 0)
    time.sleep(1)
    return text, frame


def texts(hwnd):
    return [(c, t) for x, c, t in h.children(hwnd) if t and c not in ("TRzBitBtn", "TBitBtn", "TButton")]
