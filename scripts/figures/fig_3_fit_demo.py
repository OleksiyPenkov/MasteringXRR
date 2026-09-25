"""Figures 3-1, 3-2 and 3-3: the first fit of the demo project, from raw screenshots.

Sources, all X-Ray Calc 3.9.4.1250 x64 (the published release, run from a
scratchpad copy), light theme, 96 dpi, window 1620 x 900 (captured as the
1606 x 893 visible frame), the demo ML(30x2)P3_Best.xrcx as the 3.9.4.1250
installer ships it, each run from a fresh copy opened with -f <file> -a (fit on an
NVIDIA GeForce RTX 5080):
  figures-src/screenshots/xrc-3.9.4.1250-fit-limits-demo.png  the Fitting Limits dialog
                                                               opened by Calc > Auto Fitting (F7)
  figures-src/screenshots/xrc-3.9.4.1250-fit-run1-demo.png    the window after run 1
  figures-src/screenshots/xrc-3.9.4.1250-fit-run2-demo.png    the window after run 2 (Table 3-1)
  figures-src/screenshots/xrc-3.9.4.1250-thickness-run1.png   run 1, Thickness page
  figures-src/screenshots/xrc-3.9.4.1250-thickness-run2.png   run 2, Thickness page
Each run was saved with Ctrl+S into figures-src/fits/ch3-run{1,2}.xrcx (Table 3-1,
scripts/figures/ch3_table.py).

Fig 3-1 is the dialog as captured. Fig 3-2 is the working area of run 1: the
chart with its residual strip, the Chart Info bar and the Convergence page.
Fig 3-3 is the Thickness page of run 1.

Run:  python scripts/figures/fig_3_fit_demo.py
Out:  public/figures/fig-3-1-fitting-limits.png, fig-3-2-first-fit.png, fig-3-3-thickness-profile.png
"""
from pathlib import Path

from PIL import Image
from PIL.PngImagePlugin import PngInfo

ROOT = Path(__file__).resolve().parents[2]
SHOTS = ROOT / "figures-src" / "screenshots"
OUT = ROOT / "public" / "figures"
VERSION = "X-Ray Calc 3.9.4.1250 x64"
WORKING_AREA = (606, 220, 1600, 866)   # chart and residual strip, Chart Info bar, chart pages
CHART_PAGES = (606, 672, 1600, 866)    # the Thickness page


def save(img, name, title, src):
    info = PngInfo()
    info.add_text("Title", title)
    info.add_text("Source", f"{src}; {VERSION}; script scripts/figures/fig_3_fit_demo.py")
    img.save(OUT / name, pnginfo=info, dpi=(96, 96))
    print("wrote", name, img.size)


def main():
    src1 = "xrc-3.9.4.1250-fit-limits-demo.png"
    save(Image.open(SHOTS / src1).convert("RGB"), "fig-3-1-fitting-limits.png",
         "Figure 3-1: the Fitting Limits dialog", src1)
    src2 = "xrc-3.9.4.1250-fit-run1-demo.png"
    save(Image.open(SHOTS / src2).convert("RGB").crop(WORKING_AREA), "fig-3-2-first-fit.png",
         "Figure 3-2: the working area after the first fit", src2)
    src3 = "xrc-3.9.4.1250-thickness-run1.png"
    save(Image.open(SHOTS / src3).convert("RGB").crop(CHART_PAGES), "fig-3-3-thickness-profile.png",
         "Figure 3-3: the Thickness page after the first fit", src3)


if __name__ == "__main__":
    main()
