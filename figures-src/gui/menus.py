"""Read the main menu of a running X-Ray Calc: click each top menu, read the popup that opens."""
import ctypes
import json
import sys
import time

import win32api
import win32con
import win32gui

import h

MN_GETHMENU = 0x01E1


def popup_items(m, pre, out):
    for i in range(win32gui.GetMenuItemCount(m)):
        buf = ctypes.create_unicode_buffer(256)
        h.user32.GetMenuStringW(m, i, buf, 256, win32con.MF_BYPOSITION)
        name = buf.value.replace("&", "").split("\t")[0].strip()
        sub = win32gui.GetSubMenu(m, i)
        mid = win32gui.GetMenuItemID(m, i)
        if sub:
            out[pre + name + "/"] = "sub"
        elif name:
            out[pre + name] = mid


def top_rects(hwnd):
    m = win32gui.GetMenu(hwnd)
    out = []
    for i in range(win32gui.GetMenuItemCount(m)):
        r = ctypes.wintypes.RECT()
        ctypes.windll.user32.GetMenuItemRect(hwnd, m, i, ctypes.byref(r))
        buf = ctypes.create_unicode_buffer(256)
        h.user32.GetMenuStringW(m, i, buf, 256, win32con.MF_BYPOSITION)
        out.append((buf.value.replace("&", ""), (r.left + r.right) // 2, (r.top + r.bottom) // 2))
    return out


def read(hwnd, open_sub=()):
    out = {}
    h.top(hwnd, True)
    h.fg(hwnd)
    time.sleep(0.5)
    for name, x, y in top_rects(hwnd):
        win32api.SetCursorPos((x, y))
        time.sleep(0.2)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0)
        time.sleep(0.8)
        for p in [x for x, c, t in h.windows() if c == "#32768"]:
            m = win32gui.SendMessage(p, MN_GETHMENU, 0, 0)
            if m:
                popup_items(m, name + "/", out)
        h.key(win32con.VK_ESCAPE)
        h.key(win32con.VK_ESCAPE)
        time.sleep(0.3)
    h.top(hwnd, False)
    return out


if __name__ == "__main__":
    hwnd = int(sys.argv[1])
    items = read(hwnd)
    for k, v in items.items():
        print(v, k)
    json.dump(items, open(sys.argv[2], "w", encoding="utf-8"), indent=1)
