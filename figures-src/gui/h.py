"""Small toolkit for driving X-Ray Calc 3 (a copy of the release, XRC_BIN) and capturing screenshots.

Screenshots follow the book's rule: window 1620 x 900, light theme, 96 dpi, captured with the
DWM frame bounds while topmost."""
import ctypes
import json
import os
import subprocess
import sys
import time
from ctypes import wintypes

import win32api
import win32clipboard
import win32con
import win32gui
import win32process
from PIL import ImageGrab

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts", "figures"))
import local_paths  # noqa: E402

BIN = str(local_paths.get("XRC_BIN"))
EXE = os.path.join(BIN, "XRayCalc3.x64.exe")
user32 = ctypes.windll.user32


def frame(h):
    r = wintypes.RECT()
    ctypes.windll.dwmapi.DwmGetWindowAttribute(h, 9, ctypes.byref(r), ctypes.sizeof(r))
    return r.left, r.top, r.right, r.bottom


def top(h, on=True):
    win32gui.SetWindowPos(h, win32con.HWND_TOPMOST if on else win32con.HWND_NOTOPMOST, 0, 0, 0, 0,
                          win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)


def fg(h):
    try:
        win32api.keybd_event(win32con.VK_MENU, 0, 0, 0)
        win32api.keybd_event(win32con.VK_MENU, 0, 2, 0)
        win32gui.SetForegroundWindow(h)
    except Exception:
        pass


def grab(h, path, keep_top=False):
    top(h, True)
    time.sleep(0.6)
    ImageGrab.grab(bbox=frame(h), all_screens=True).save(path)
    if not keep_top:
        top(h, False)
    return frame(h)


def gettext(h):
    n = win32gui.SendMessage(h, win32con.WM_GETTEXTLENGTH, 0, 0)
    buf = ctypes.create_unicode_buffer(n + 2)
    user32.SendMessageW(h, win32con.WM_GETTEXT, n + 1, buf)
    return buf.value


def children(h):
    out = []
    win32gui.EnumChildWindows(h, lambda x, a: a.append((x, win32gui.GetClassName(x), gettext(x))), out)
    return out


def windows(pid=None, visible=True):
    out = []

    def cb(x, _):
        if visible and not win32gui.IsWindowVisible(x):
            return
        if pid and win32process.GetWindowThreadProcessId(x)[1] != pid:
            return
        out.append((x, win32gui.GetClassName(x), win32gui.GetWindowText(x)))
    win32gui.EnumWindows(cb, None)
    return out


def wait(pred, tries=60, dt=0.5):
    for _ in range(tries):
        r = pred()
        if r:
            return r
        time.sleep(dt)
    return None


def wait_window(pid, cls=None, title=None, tries=60):
    def f():
        for x, c, t in windows(pid):
            if (cls is None or c == cls) and (title is None or t == title):
                return x
    return wait(f, tries)


def launch(project, auto=True):
    args = [EXE, "-f", project] + (["-a"] if auto else [])
    p = subprocess.Popen(args, cwd=BIN)
    h = wait(lambda: next((x for x, c, t in windows(p.pid) if t.startswith("X-Ray Calc 3")), None), 80)
    time.sleep(3)
    win32gui.ShowWindow(h, win32con.SW_RESTORE)
    win32gui.MoveWindow(h, 10, 10, 1620, 900, True)
    time.sleep(2)
    return p, h


def menu_items(h):
    """{path: id} for the main menu, path like 'Calc/Auto Fitting'."""
    out = {}

    def walk(m, pre):
        for i in range(win32gui.GetMenuItemCount(m)):
            buf = ctypes.create_unicode_buffer(256)
            user32.GetMenuStringW(m, i, buf, 256, win32con.MF_BYPOSITION)
            name = buf.value.replace("&", "").split("\t")[0].strip()
            sub = win32gui.GetSubMenu(m, i)
            if sub:
                walk(sub, pre + name + "/")
            else:
                out[pre + name] = win32gui.GetMenuItemID(m, i)
    walk(win32gui.GetMenu(h), "")
    return out


def menu(h, path):
    items = menu_items(h)
    mid = items.get(path)
    if mid is None:
        raise KeyError(f"{path} not in {list(items)}")
    win32gui.PostMessage(h, win32con.WM_COMMAND, mid, 0)


def click(hh, dx=None, dy=None):
    rr = win32gui.GetWindowRect(hh)
    x = rr[0] + (dx if dx is not None else (rr[2] - rr[0]) // 2)
    y = rr[1] + (dy if dy is not None else (rr[3] - rr[1]) // 2)
    win32api.SetCursorPos((x, y))
    time.sleep(0.3)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0)
    time.sleep(0.05)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0)


def chord(k, mod=win32con.VK_CONTROL):
    win32api.keybd_event(mod, 0, 0, 0)
    win32api.keybd_event(k, 0, 0, 0)
    time.sleep(0.05)
    win32api.keybd_event(k, 0, 2, 0)
    win32api.keybd_event(mod, 0, 2, 0)
    time.sleep(0.4)


def key(k):
    win32api.keybd_event(k, 0, 0, 0)
    time.sleep(0.05)
    win32api.keybd_event(k, 0, 2, 0)
    time.sleep(0.2)


def clip_set(text):
    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardText(text, win32con.CF_UNICODETEXT)
    win32clipboard.CloseClipboard()


def clip_get():
    win32clipboard.OpenClipboard()
    try:
        return win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT)
    finally:
        win32clipboard.CloseClipboard()


def set_edit(hh, text):
    user32.SendMessageW(hh, win32con.WM_SETTEXT, 0, ctypes.c_wchar_p(text))


def dump(obj, path):
    json.dump(obj, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
