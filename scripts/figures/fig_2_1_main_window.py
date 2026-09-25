"""Figures 2-1 and 2-2: the X-Ray Calc main window, from one raw screenshot.

Source: figures-src/screenshots/xrc-3.9.4.1250-main-window-demo.png. It is
X-Ray Calc 3.9.4.1250 x64 (the published release, run from a scratchpad copy),
light theme, 96 dpi, the window set to 1620 x 900 (the capture is the 1606 x 893
visible frame). The demo project ML(30x2)P3_Best.xrcx as the 3.9.4.1250 installer
ships it (the author's revision of 2026-09-25: Population 5000, Iterations 200,
the For fit limits of Chapter 3) was opened with `-f <file> -a`, so the active
model was calculated on opening.

Fig 2-1 is the whole window with numbered regions. Fig 2-2 is the calculation
settings panel at 1:1, so the labels stay readable in print.

Run:  python scripts/figures/fig_2_1_main_window.py
Out:  public/figures/fig-2-1-main-window.png, public/figures/fig-2-2-calc-settings.png

Retake the screenshot, and update the name and the version here, whenever a
control shown in either figure changes (STYLE.md §6).
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from PIL.PngImagePlugin import PngInfo

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "figures-src" / "screenshots" / "xrc-3.9.4.1250-main-window-demo.png"
OUT_1 = ROOT / "public" / "figures" / "fig-2-1-main-window.png"
OUT_2 = ROOT / "public" / "figures" / "fig-2-2-calc-settings.png"
VERSION = "X-Ray Calc 3.9.4.1250"

ACCENT = (26, 82, 118)  # --accent in src/styles/textbook.css

# Regions of the 1606 x 893 capture, (left, top, right, bottom) in pixels,
# numbered as in the Fig 2-1 caption. Region 5 holds the chart and the residual
# strip under it.
REGIONS = {
    1: (7, 137, 240, 780),      # project panel
    2: (248, 96, 594, 472),     # structure panel
    3: (608, 96, 990, 214),     # calculation settings
    4: (994, 100, 1598, 214),   # fitting settings
    5: (608, 224, 1598, 614),   # main chart and residual strip
    6: (608, 618, 1598, 670),   # Chart Info bar
    7: (608, 674, 1598, 862),   # chart pages
}
# Where each badge sits (its center), clear of the controls it names.
BADGES = {1: (205, 470), 2: (555, 520), 3: (975, 72), 4: (1560, 72), 5: (1530, 420),
          6: (570, 644), 7: (1560, 800)}
CALC_PANEL = REGIONS[3]


def font(size):
    for name in ("arialbd.ttf", "segoeuib.ttf", "DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def meta(title):
    info = PngInfo()
    info.add_text("Title", title)
    info.add_text("Source", f"{SRC.name}; {VERSION}; script scripts/figures/fig_2_1_main_window.py")
    return info


def main():
    shot = Image.open(SRC).convert("RGB")

    fig = shot.copy()
    d = ImageDraw.Draw(fig)
    f = font(34)
    for n, box in REGIONS.items():
        d.rectangle(box, outline=ACCENT, width=4)
    for n, (cx, cy) in BADGES.items():
        r = 26
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=ACCENT, outline="white", width=3)
        d.text((cx, cy), str(n), fill="white", font=f, anchor="mm")
    OUT_1.parent.mkdir(parents=True, exist_ok=True)
    fig.save(OUT_1, pnginfo=meta("Figure 2-1: the X-Ray Calc main window"), dpi=(96, 96))

    panel = shot.crop(CALC_PANEL)
    panel.save(OUT_2, pnginfo=meta("Figure 2-2: the calculation settings"), dpi=(96, 96))
    print(f"wrote {OUT_1.name} {fig.size} and {OUT_2.name} {panel.size}")


if __name__ == "__main__":
    main()
