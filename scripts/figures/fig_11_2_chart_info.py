"""Figure 11-2: the main chart zoomed on a Bragg peak, with the Chart Info bar.

Source: figures-src/screenshots/ch11-chart-info-full.png. It is X-Ray Calc
3.9.4.1270 (a copy of the x64 release build), light theme, 96 dpi (100 % display scale), the
window set to 1620 x 900 and captured with its DWM frame bounds (1606 x 893 pixels) while
topmost. Driver: figures-src/gui/s11.py (2026-09-25).

What was done in the program, from a copy of the expert fit
CoC4-expert-full-fit.xrcx (XRR-Fitting-Skill, submission/zenodo/fits):
- params.dsc of the copy edited before opening: 2teta=1 (the 2θ box ticked),
  LinkedData=-1 (the old data item is in θ, so it was unlinked);
- opened with `-f <file> -a`;
- Data > Load ... with submission/zenodo/curves/CoC4.xrdml; λ became 1.541874 Å;
- the old data item P2-04/xrr.dat unticked in the chart legend;
- θ1 0.05, θ2 14 (the fields are in 2θ when the 2θ box is ticked), N 4651;
- Calc > Run;
- a left-button drag on the chart from 2θ 7.7° to 8.5°;
- Result > Residual strip > Show unticked (the strip is empty here, because
  the data item is not linked to the model);
- the mouse cursor left on the top of the measured 5th-order peak, where the
  Chart Info bar reads X 8.103 and Y 1.02E-4.

The crop keeps the chart and the Chart Info bar under it, with a few pixels
of the grey panel around them, and nothing else.

Run:  python scripts/figures/fig_11_2_chart_info.py
Out:  public/figures/fig-11-2-chart-info.png

Retake the screenshot, and update the name and the version here, whenever a
control shown in the figure changes (STYLE.md §6).
"""
from pathlib import Path

from PIL import Image
from PIL.PngImagePlugin import PngInfo

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "figures-src" / "screenshots" / "ch11-chart-info-full.png"
OUT = ROOT / "public" / "figures" / "fig-11-2-chart-info.png"
VERSION = "X-Ray Calc 3.9.4.1270"

# The chart (x 608-1596, y 226-612) and the Chart Info bar (y 618-665) in the
# 1606 x 893 capture, (left, top, right, bottom) in pixels. The chart pages
# start at y 673 and the panel border is at x 600 and x 1604.
CROP = (603, 221, 1601, 670)


def main():
    shot = Image.open(SRC).convert("RGB")
    assert shot.size == (1606, 893), f"unexpected capture size {shot.size}"
    fig = shot.crop(CROP)
    info = PngInfo()
    info.add_text("Title", "Figure 11-2: the chart zoomed on the 5th Bragg order, with the Chart Info bar")
    info.add_text("Source", f"{SRC.name}; {VERSION}; script scripts/figures/fig_11_2_chart_info.py")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.save(OUT, pnginfo=info, dpi=(96, 96))
    print(f"wrote {OUT.name} {fig.size}")


if __name__ == "__main__":
    main()
