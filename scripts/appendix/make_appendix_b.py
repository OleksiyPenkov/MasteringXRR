"""Writes src/content/chapters/appendix-b-menus.mdx from the tables below.

Labels are those the chapters use (the build the book follows); keys are read from
XRayCalc3\\Forms\\frm_Main.dfm. Link text comes from each chapter's own heading.
Run:  python scripts/appendix/make_appendix_b.py
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CHAPTERS = ROOT / 'src' / 'content' / 'chapters'
OUT = CHAPTERS / 'appendix-b-menus.mdx'


def slug(h):
    s = h.strip().lower()
    s = re.sub(r'[^\w\s-]', '', s).replace('²', '')
    return re.sub(r'\s', '-', s)


def page_label(stem):
    m = re.match(r'ch(\d+)-', stem)
    if m:
        return f'Chapter {m.group(1)}'
    m = re.match(r'appendix-([a-d])-', stem)
    if m:
        return f'Appendix {m.group(1).upper()}'
    return 'Introduction'


def link(ref):
    stem, frag = ref.split('#')
    text = (CHAPTERS / f'{stem}.mdx').read_text(encoding='utf-8')
    heads = {slug(h): h for h in re.findall(r'^## (.+)$', text, re.M)}
    if frag not in heads:
        raise SystemExit(f'no heading #{frag} in {stem}')
    title = re.sub(r'^\d+\.\s*', '', heads[frag]).rstrip('?')
    return f'<a href={{`${{import.meta.env.BASE_URL}}/{stem}#{frag}`}}>{page_label(stem)}: {title}</a>'


def cell(s):
    s = s.replace('{', '&#123;').replace('}', '&#125;').replace('<', '&lt;').replace('>', '&gt;')
    s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'`(.+?)`', r'<code>\1</code>', s)
    return s


def table(tid, caption, cols, rows):
    out = [f'<p id="{tid}" class="table-caption"><strong>{tid.replace("table-", "Table ").replace("b-", "B-")}:</strong> {caption}</p>', '',
           '<table className="data-table keep-header-case">',
           '  <thead><tr>' + ''.join(f'<th>{c}</th>' for c in cols) + '</tr></thead>', '  <tbody>']
    for r in rows:
        *cells, ref = r
        out.append('    <tr>' + ''.join(f'<td>{cell(c)}</td>' for c in cells) + f'<td>{link(ref)}</td></tr>')
    out += ['  </tbody>', '</table>', '']
    return '\n'.join(out)


# (command, what it does, key, ref)
MENUS = {
    'File': [
        ('Open project ...', 'Opens a project, a `.xrcx` file.', 'F3', 'ch2-meet-x-ray-calc-3#opening-a-demo-project'),
        ('Save project', 'Saves the project: the structure with its limits and flags, the settings, the prepared data and the record of the last fit.', 'Ctrl+S', 'ch23-reporting-a-fit#what-the-program-keeps-and-what-it-doesnt'),
        ('Save project As ...', 'Saves the project under a new name. The book keeps one project for each run.', 'F2', 'ch23-reporting-a-fit#keeping-the-files'),
        ('Settings ...', 'The program settings: the graphics card, the processor cores, automatic saving and the folders.', '', 'ch8-how-x-ray-calc-computes-a-curve#how-many-points'),
    ],
    'Project': [
        ('Duplicate Model', 'Copies the active model, to try a change or to keep the model from before a run.', '', 'ch16-fit-settings#several-runs-and-their-spread'),
    ],
    'Structure': [
        ('Add Stack', 'Adds a stack at the bottom, above the substrate, and opens **Stack properties**.', '', 'ch12-building-the-starting-model#the-periodic-stack'),
        ('Insert Stack', 'Adds a stack above the selected one, as for the contamination layer.', '', 'ch12-building-the-starting-model#the-top-of-the-stack-contamination-layer-and-cap'),
        ('Add Layer', 'Adds a layer at the bottom of the selected stack and opens **Layer properties**.', '', 'ch12-building-the-starting-model#the-periodic-stack'),
        ('Edit as text ...', 'Shows the model as text, in which values and limits can be typed.', '', 'ch12-building-the-starting-model#the-model-as-text'),
        ('Import structure ...', 'Reads a model from a `.json` file into a new model.', '', 'ch12-building-the-starting-model#the-model-as-text'),
        ('Undo', 'Takes back the last change of the structure. It does not undo a change of the data.', 'Ctrl+Z', 'ch12-building-the-starting-model#the-model-as-text'),
    ],
    'Data': [
        ('Load ...', 'Loads a measured curve from an `.xrdml` or a text file.', '', 'ch10-is-this-curve-worth-fitting#two-ways-in-an-xrdml-file-or-a-text-file'),
        ('From clipboard', 'Pastes a measured curve of two columns from the clipboard.', '', 'ch10-is-this-curve-worth-fitting#two-ways-in-an-xrdml-file-or-a-text-file'),
        ('Normalize ...', 'Divides the measured curve by a coefficient you enter.', '', 'ch14-preparing-the-data#setting-the-scale-normalize-auto'),
        ('Normalize (Auto)', 'Scales the measured curve to the model at its largest value below θ = 0.5°.', '', 'ch14-preparing-the-data#setting-the-scale-normalize-auto'),
        ('Smooth', 'Replaces each point by a six-point mean. The book leaves it off.', '', 'ch14-preparing-the-data#why-smoothing-stays-off'),
        ('Trim', 'Deletes the measured points outside θ1–θ2.', '', 'ch14-preparing-the-data#trimming-the-data-to-the-range'),
        ('Assess XRR quality ...', 'Runs eight checks on the measurement.', '', 'ch10-is-this-curve-worth-fitting#is-this-curve-worth-fitting'),
    ],
    'Calc': [
        ('Run', 'Calculates the active model. The χ² appears in the Chart Info bar.', 'F5', 'ch2-meet-x-ray-calc-3#your-first-calculation'),
        ('Calc all models', 'Calculates every model of the project.', 'F6', 'ch13-the-sensitivity-check#doing-it-in-x-ray-calc'),
        ('Auto Fitting', 'Opens the **Fitting Limits** dialog. Its **Run** button starts the fit.', 'F7', 'ch15-choosing-what-to-fit#the-fitting-limits-dialog'),
        ('Resume Fitting', 'Opens the **Fitting Limits** dialog with **Resume**. The windows of the parameters that are not frozen move to the last result.', '', 'ch19-when-the-fit-will-not-converge#fitting-in-stages'),
    ],
    'Result': [
        ('Save as graphics ...', 'Saves a picture of the chart.', '', 'ch23-reporting-a-fit#keeping-the-files'),
        ('Copy as BMP', 'Copies a picture of the chart to the clipboard.', '', 'ch23-reporting-a-fit#keeping-the-files'),
        ('Export fit results...', 'Writes the record of the last fit as a `.json` file.', '', 'ch23-reporting-a-fit#what-the-program-keeps-and-what-it-doesnt'),
        ('Fit report ...', 'Shows the checks of a fit: the orders, the edge, the fringes, the bands and the parameters near a limit.', '', 'ch18-judging-a-fit#reading-the-checks-in-x-ray-calc'),
        ('Residual strip > Show', 'Draws log₁₀(calculated / measured) in a strip under the chart. The items **±0.1 lines**, **Band means** and **Floored points** of the same submenu add the warning level, the mean of each band and the points on the floor. All four are on by default.', '', 'ch18-judging-a-fit#the-residual-by-band'),
    ],
    'Tools': [
        ('Create new material ...', 'Makes the table of a new material from elements or existing materials.', '', 'appendix-c-optical-constants#adding-a-material'),
        ('Edit Henke table...', 'Shows the table of one material, with its bulk density and molar mass.', '', 'appendix-c-optical-constants#checking-a-table'),
    ],
    'Help': [
        ('User Manual', 'Opens the manual of the program.', 'F1', 'introduction#beyond-the-book'),
    ],
}

# (control, where it is, what it does, ref)
BUTTONS = [
    ('**Limits**', 'the structure panel', 'Opens the **Fitting Limits** dialog with **Save**.', 'ch15-choosing-what-to-fit#the-fitting-limits-dialog'),
    ('the increment box', 'the structure toolbar', 'Sets the step of the arrows beside each field.', 'ch13-the-sensitivity-check#doing-it-in-x-ray-calc'),
    ('the box after H, σ or ρ', 'each layer', 'Holds that parameter at one value in every period (Paired).', 'ch17-periodic-or-polynomial#two-ways-to-describe-a-stack'),
    ('**Freeze stack**, **Thaw stack**', 'right-click on a stack', 'Freezes or releases every parameter of the stack.', 'ch15-choosing-what-to-fit#freezing-a-parameter'),
    ('**Add extension**', 'the Project panel toolbar', 'Adds an extension, such as a Function profile.', 'ch22-graded-multilayers-and-supermirrors#a-gradient-in-polynomial-mode'),
    ('the delete button, hint "Delete item"', 'the Project panel toolbar', 'Deletes the selected item of the project.', 'ch17-periodic-or-polynomial#reading-a-drift-in-x-ray-calc'),
    ('**Calculate all**', 'the chart toolbar', 'Calculates every model, as **Calc all models** does.', 'ch13-the-sensitivity-check#doing-it-in-x-ray-calc'),
    ('**Stop**', 'the top of the chart, while a calculation or a fit runs', 'Ends the calculation or the fit.', 'ch9-how-x-ray-calc-finds-a-fit#when-the-fit-stops'),
    ('**Run**, **Resume**, **Save**', 'the **Fitting Limits** dialog', 'Starts the fit, resumes it, or saves the limits, depending on how the dialog was opened.', 'ch15-choosing-what-to-fit#the-fitting-limits-dialog'),
    ('**Initialize**, **Narrow**, **Widen**, **Fix**', 'the **Fitting Limits** dialog', 'Sets the limits from the values and **ΔH**, **Δσ**, **Δρ**; narrows or widens them; repairs them.', 'ch15-choosing-what-to-fit#generous-limits'),
    ('**Freeze**, **Thaw**', 'the **Fitting Limits** dialog', 'Holds the selected parameters at their values, or releases them.', 'ch15-choosing-what-to-fit#freezing-a-parameter'),
    ('**Assess**, **Copy summary**', 'the **XRR quality** window (**Data > Assess XRR quality ...**)', 'Runs the checks, and copies their text.', 'ch10-is-this-curve-worth-fitting#is-this-curve-worth-fitting'),
    ('**Copy as text**', 'the **Fit report** window', 'Copies the report as text.', 'ch18-judging-a-fit#reading-the-checks-in-x-ray-calc'),
    ('**Thickness**, **Density**', 'the pages under the chart', 'Draw the thickness or the density of every layer, period by period.', 'ch17-periodic-or-polynomial#reading-a-drift-in-x-ray-calc'),
]

# (field, default, the book's value, ref)
FIT_FIELDS = [
    ('**Population**', '100', '5000; 2000 for a single film', 'ch16-fit-settings#the-settings-and-the-ones-you-change'),
    ('**Iterations**', '100', '200', 'ch16-fit-settings#the-settings-and-the-ones-you-change'),
    ('**Shake**', 'ticked', 'ticked', 'ch9-how-x-ray-calc-finds-a-fit#shakes-leaving-a-valley'),
    ('**SeedR**', 'ticked', 'ticked', 'ch9-how-x-ray-calc-finds-a-fit#the-swarm'),
    ('**Mode**', 'Irregular', 'Periodic, then Polynomial', 'ch17-periodic-or-polynomial#two-ways-to-describe-a-stack'),
    ('**Free period ±**', 'unticked, 10 %', 'ticked, 10 %', 'ch17-periodic-or-polynomial#step-1-one-period-with-the-period-free'),
    ('**Order**', '1', '1, raised one step at a time', 'ch17-periodic-or-polynomial#raising-the-order'),
    ('**Smooth**', 'unticked', 'off', 'ch14-preparing-the-data#why-smoothing-stays-off'),
    ('**PW χ²**', 'ticked', 'ticked', 'ch9-how-x-ray-calc-finds-a-fit#what-χ-measures'),
    ('**TW χ²**', '**None**', '**None**', 'ch9-how-x-ray-calc-finds-a-fit#what-χ-measures'),
    ('**Solve scale in χ²**', 'ticked', 'ticked', 'ch14-preparing-the-data#letting-the-fit-solve-the-scale'),
    ('**Window**', '0.2', '0.2', 'ch14-preparing-the-data#letting-the-fit-solve-the-scale'),
]
CALC_FIELDS = [
    ('**2θ**', 'ticked', 'ticked', 'ch2-meet-x-ray-calc-3#2θ-or-θ-the-angle-on-your-screen'),
    ('**λ(Å)**', '1.54043 in a new project', 'from the `.xrdml` file, or typed in', 'ch10-is-this-curve-worth-fitting#the-wavelength-comes-from-the-file'),
    ('**Δθ**', '0.015 in a new project', 'chosen by a scan', 'ch16-fit-settings#choosing-δθ-by-a-scan'),
    ('**Polarization**', '**s-type**', '**s-type**', 'ch8-how-x-ray-calc-computes-a-curve#polarization-s-type-or-sp-type'),
    ('**N** (points)', '2000', 'not used with a linked curve', 'ch8-how-x-ray-calc-computes-a-curve#how-many-points'),
    ('**R min** (Chart Info bar)', '10⁻⁷', 'one count on the scaled curve', 'ch14-preparing-the-data#the-floor-one-count'),
    ('**ΔH**, **Δσ**, **Δρ** (**Fitting Limits**)', '0.25', '0.25', 'ch15-choosing-what-to-fit#generous-limits'),
    ('**Tolerance** (**Advanced fitting settings**)', '0.005', '0.005', 'ch9-how-x-ray-calc-finds-a-fit#when-the-fit-stops'),
    ('**Vmax**, **Ksxr** (**Advanced fitting settings**)', '0.3, 0.2', '0.3, 0.2', 'ch9-how-x-ray-calc-finds-a-fit#the-swarm'),
    ('**Jmax**, **SHmax**, **k1**, **k2** (**Advanced fitting settings**)', '1, 3, 1.41, 1.41', 'the defaults', 'ch9-how-x-ray-calc-finds-a-fit#shakes-leaving-a-valley'),
]

# (key, command, ref)
KEYS = [
    ('F1', '**Help > User Manual**', 'introduction#beyond-the-book'),
    ('F2', '**File > Save project As ...**', 'ch23-reporting-a-fit#keeping-the-files'),
    ('F3', '**File > Open project ...**', 'ch2-meet-x-ray-calc-3#opening-a-demo-project'),
    ('Shift+F3', '**Reopen** (the Project panel button): reads the project again from its file', 'ch2-meet-x-ray-calc-3#opening-a-demo-project'),
    ('F5', '**Calc > Run**', 'ch2-meet-x-ray-calc-3#your-first-calculation'),
    ('F6', '**Calc > Calc all models**', 'ch13-the-sensitivity-check#doing-it-in-x-ray-calc'),
    ('F7', '**Calc > Auto Fitting**', 'ch15-choosing-what-to-fit#the-fitting-limits-dialog'),
    ('Ctrl+S', '**File > Save project**', 'ch23-reporting-a-fit#what-the-program-keeps-and-what-it-doesnt'),
    ('Ctrl+Z', '**Structure > Undo**', 'ch12-building-the-starting-model#the-model-as-text'),
    ('Insert', '**Structure > Insert Layer**', 'ch12-building-the-starting-model#the-periodic-stack'),
    ('Ctrl+Delete', '**Structure > Delete** (the selected layer)', 'ch12-building-the-starting-model#the-periodic-stack'),
    ('Ctrl+Shift+C', '**Structure > Copy Layer**', 'ch12-building-the-starting-model#the-periodic-stack'),
    ('Ctrl+Shift+X', '**Structure > Cut** (the selected layer)', 'ch12-building-the-starting-model#the-periodic-stack'),
    ('Ctrl+Shift+V', '**Structure > Paste** (a layer)', 'ch12-building-the-starting-model#the-periodic-stack'),
]

HEAD = """---
title: 'Menus, Buttons and Keys'
part: 'back'
number: 'B'
order: 280
inThisChapter:
  - The menu commands the book uses
  - The buttons and the fields, with their defaults
  - The keys
---

{/* Appendix B. Outline approved 2026-09-25 (OUTLINE.md, back matter, choice 2 (a)). Generated by scripts/appendix/make_appendix_b.py; edit the script, not this file. */}

This appendix lists the commands, buttons, fields and keys that the book uses, with the section that explains each. The labels are those of the X-Ray Calc build that the chapters describe. Commands the book does not use are left out.

## The menus

"""

MOUSE = """## Keys and the mouse

<p id="table-b-12" class="table-caption"><strong>Table B-12:</strong> The keys of X-Ray Calc, read from the program.</p>

"""

MOUSE_TAIL = """
The mouse does the rest:

- **Drag a box** on the chart to zoom in. **Double-click** the chart to return to the full view (<a href={`${import.meta.env.BASE_URL}/ch11-reading-the-curve#the-chart-info-bar`}>Chapter 11: The Chart Info bar</a>).
- **Double-click** an item of the project, a stack or a layer to open its dialog (<a href={`${import.meta.env.BASE_URL}/ch2-meet-x-ray-calc-3#opening-a-demo-project`}>Chapter 2: Opening a demo project</a>).
- **Right-click** a stack to freeze or release it (<a href={`${import.meta.env.BASE_URL}/ch15-choosing-what-to-fit#freezing-a-parameter`}>Chapter 15: Freezing a parameter</a>).
- **Press Enter** after typing a limit or **R min**, so that the value is taken.

"""

SOURCES = """## Sources

- **The X-Ray Calc 3 source:** the menus and their actions, the captions and the keys (`XRayCalc3\\Forms\\frm_Main.dfm`, the `TAction` objects with their `ShortCut` values); the **Stop** button at the top of the chart, shown only while a calculation or a fit runs (`XRayCalc3\\Views\\frame_ChartInfo.dfm`, `btnStop`; `frm_Main.pas`); the delete button of the Project panel (`XRayCalc3\\Views\\frame_ProjectPanel.dfm`, hint "Delete item"); the **Residual strip** submenu (`frm_Main.dfm`, `mnuResidual`), its four items on by default (`XRayCalc3\\Units\\unit_Config.pas`); the defaults of a new project (`XRayCalc3\\Views\\frame_CalcSettings.dfm`). Release 3.9.4.1250. The labels and defaults are those the chapters give, each checked in the chapter linked.
- **X-Ray Calc Help:** *Quick Reference* (the toolbars, and the keyboard shortcuts: the same fourteen keys as Table B-12).

Cross-references: <a href={`${import.meta.env.BASE_URL}/ch2-meet-x-ray-calc-3#the-main-window`}>Chapter 2: The main window</a>; <a href={`${import.meta.env.BASE_URL}/ch16-fit-settings#the-settings-and-the-ones-you-change`}>Chapter 16: The settings, and the ones you change</a>; <a href={`${import.meta.env.BASE_URL}/appendix-a-notation#symbols`}>Appendix A: Notation and Units</a>; <a href={`${import.meta.env.BASE_URL}/appendix-d-glossary#a`}>Appendix D: Glossary</a>.
"""


def main():
    out = [HEAD]
    n = 0
    for menu, rows in MENUS.items():
        n += 1
        out.append(f'### {menu}\n')
        out.append(table(f'table-b-{n}', f'The **{menu}** menu.'.replace('**', ''), ('Command', 'What it does', 'Key', 'Explained in'), rows))
    n += 1
    out.append('## Buttons and dialogs\n')
    out.append(table(f'table-b-{n}', 'Buttons and other controls.', ('Control', 'Where', 'What it does', 'Explained in'), BUTTONS))
    n += 1
    out.append('## The settings, with their defaults\n')
    out.append('The default is the value in a new project. A project stores its own settings, so a project you open can differ.\n')
    out.append(table(f'table-b-{n}', 'The fit settings.', ('Field', 'Default', 'This book', 'Explained in'), FIT_FIELDS))
    n += 1
    out.append(table(f'table-b-{n}', 'The calculation settings and other fields.', ('Field', 'Default', 'This book', 'Explained in'), CALC_FIELDS))
    n += 1
    assert n == 12, n
    out.append(MOUSE)
    out.append('\n'.join(table('table-b-12', '', ('Key', 'Command', 'Explained in'), KEYS).split('\n')[2:]))
    out.append(MOUSE_TAIL)
    out.append(SOURCES)
    OUT.write_text('\n'.join(out), encoding='utf-8')
    print('wrote', OUT)


if __name__ == '__main__':
    main()
