"""Figures 17-1, 17-3, 18-1, 19-2 and 19-3: crops of X-Ray Calc 3.9.4.1270 captures.

The captures are in figures-src/screenshots/ (light theme, 96 dpi, the main window set to
1620 x 900 and captured with its DWM frame bounds, 1606 x 893 pixels, while topmost). They were
taken on 2026-09-25 by the drivers in figures-src/gui/:
  s17.py   CoC4 in Polynomial mode of order 1, one run in the program (Figures 17-1, 17-3,
           18-1): ch17-polynomial-full.png, ch17-profile-function.png, ch18-fit-report.png
           (the Fit report window enlarged to 920 pixels so that all eight orders show)
  s19.py   the staged fit of Chapter 19 (Figures 19-2, 19-3): ch19-staged-frozen-full.png,
           ch19-staged-resume-limits.png
Figure 17-1 joins two crops of the main window: the Fitting panel over the project tree and
the structure panel. Before the capture the mode was switched to Periodic and back to
Polynomial, because opening a project or selecting a model leaves the boxes after σ and ρ
disabled in Polynomial mode in this build (reported to the author).

Run:  python scripts/figures/fig_gui_captures.py
Out:  public/figures/fig-17-1-polynomial-mode.png, fig-17-3-profile-function.png,
      fig-18-1-fit-report.png, fig-19-2-frozen-stack.png, fig-19-3-resume-limits.png
"""
from pathlib import Path

from PIL import Image
from PIL.PngImagePlugin import PngInfo

ROOT = Path(__file__).resolve().parents[2]
SHOTS = ROOT / "figures-src" / "screenshots"
OUT = ROOT / "public" / "figures"
VERSION = "X-Ray Calc 3.9.4.1270"


def save(img, name, title, src):
    info = PngInfo()
    info.add_text("Title", title)
    info.add_text("Source", f"{src}; {VERSION}; script scripts/figures/fig_gui_captures.py")
    img.save(OUT / name, pnginfo=info, dpi=(96, 96))
    print("wrote", name, img.size)


def main():
    full = Image.open(SHOTS / "ch17-polynomial-full.png").convert("RGB")
    assert full.size == (1606, 893), full.size
    top = full.crop((996, 101, 1602, 209))        # the Fitting panel
    bottom = full.crop((0, 98, 610, 474))         # project tree and structure panel
    fig = Image.new("RGB", (610, top.height + bottom.height), (240, 240, 240))
    fig.paste(top, (0, 0))
    fig.paste(bottom, (0, top.height))
    save(fig, "fig-17-1-polynomial-mode.png", "Figure 17-1: Polynomial mode of order 1",
         "ch17-polynomial-full.png")
    save(Image.open(SHOTS / "ch17-profile-function.png").convert("RGB"), "fig-17-3-profile-function.png",
         "Figure 17-3: the Profile function editor of F(H ML/C)", "ch17-profile-function.png")
    save(Image.open(SHOTS / "ch18-fit-report.png").convert("RGB"), "fig-18-1-fit-report.png",
         "Figure 18-1: Result > Fit report", "ch18-fit-report.png")
    frozen = Image.open(SHOTS / "ch19-staged-frozen-full.png").convert("RGB")
    assert frozen.size == (1606, 893), frozen.size
    save(frozen.crop((245, 100, 1600, 470)), "fig-19-2-frozen-stack.png",
         "Figure 19-2: the second pass of a staged fit, ML frozen", "ch19-staged-frozen-full.png")
    save(Image.open(SHOTS / "ch19-staged-resume-limits.png").convert("RGB"), "fig-19-3-resume-limits.png",
         "Figure 19-3: the Fitting Limits dialog on Resume", "ch19-staged-resume-limits.png")


if __name__ == "__main__":
    main()
