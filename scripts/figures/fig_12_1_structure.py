"""Figure 12-1: the structure panel holding the CoC4 starting model.

Source: figures-src/screenshots/ch12-starting-model-full.png. It is X-Ray Calc
3.9.4.1030 (the x64 build in _Out\\BIN, 2026-09-24), light theme, 96 dpi (100 %
display scale), the window set to 1620 x 900 and captured with its DWM frame
bounds (1606 x 893 pixels) while topmost.

What was done in the program, from a copy of the expert fit
CoC4-expert-full-fit.xrcx (XRR-Fitting-Skill, submission/zenodo/fits):
- params.dsc of the copy edited before opening: 2teta=1 (the 2θ box ticked),
  LinkedData=-1 (the old data item is in θ, so it was unlinked);
- opened with `-f <file> -a`;
- Data > Load ... ("Load curve from file", XRDML filter) with
  submission/zenodo/curves/CoC4.xrdml; λ became 1.541874 Å;
- the old data item P2-04/xrr.dat unticked in the chart legend;
- θ1 0.05, θ2 14 (the fields are in 2θ when the 2θ box is ticked), N 4651;
- Structure > Edit as text ..., the whole text replaced (Ctrl+A, Ctrl+V) with
  the one-line model
  {"Stacks":[{"T":"Top","N":1,"Layers":[{"M":"C","H":15,"s":3,"r":0.9}]},
   {"T":"ML","N":20,"Layers":[{"M":"C","H":31.4,"s":4,"r":2},
   {"M":"Co","H":23.3,"s":4,"r":8}]}],"Subs":{"M":"SiO2","s":3.8,"r":2.5}}
  and the editor's Save button pressed;
- Calc > Run.
The text the editor showed when reopened is figures-src/ch12/model-as-text.json.

The crop keeps the structure panel only: the column header (Stack / Layer,
H, σ, ρ, N), the Top stack (N 1), the ML stack (N 20) and the Substrate
block, with a few pixels of the grey panel around them. The Chart Info bar is
far from this panel (its D box is at x 832-925, y 645-665), so it is left out.

Run:  python scripts/figures/fig_12_1_structure.py
Out:  public/figures/fig-12-1-starting-model.png

Retake the screenshot, and update the name and the version here, whenever a
control shown in the figure changes (STYLE.md §6).
"""
from pathlib import Path

from PIL import Image
from PIL.PngImagePlugin import PngInfo

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "figures-src" / "screenshots" / "ch12-starting-model-full.png"
OUT = ROOT / "public" / "figures" / "fig-12-1-starting-model.png"
VERSION = "X-Ray Calc 3.9.4.1030"

# The structure panel in the 1606 x 893 capture, (left, top, right, bottom) in
# pixels. Its scroll area is x 247-596; the column header starts at y 144 and
# the Substrate block ends at y 468.
CROP = (244, 140, 598, 476)


def main():
    shot = Image.open(SRC).convert("RGB")
    assert shot.size == (1606, 893), f"unexpected capture size {shot.size}"
    fig = shot.crop(CROP)
    info = PngInfo()
    info.add_text("Title", "Figure 12-1: the structure panel holding the CoC4 starting model")
    info.add_text("Source", f"{SRC.name}; {VERSION}; script scripts/figures/fig_12_1_structure.py")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.save(OUT, pnginfo=info, dpi=(96, 96))
    print(f"wrote {OUT.name} {fig.size}")


if __name__ == "__main__":
    main()
