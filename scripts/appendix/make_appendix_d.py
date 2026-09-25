"""Writes src/content/chapters/appendix-d-glossary.mdx from the entries below.

Each entry links to the section that defines the term. The link text is read from the
chapter's own heading, so a renamed heading is picked up on the next run (and a vanished one
fails here). Run:  python scripts/appendix/make_appendix_d.py
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CHAPTERS = ROOT / 'src' / 'content' / 'chapters'
OUT = CHAPTERS / 'appendix-d-glossary.mdx'


def slug(h):
    s = h.strip().lower()
    s = re.sub(r'[^\w\s-]', '', s).replace('²', '')
    return re.sub(r'\s', '-', s)


def headings(stem):
    text = (CHAPTERS / f'{stem}.mdx').read_text(encoding='utf-8')
    return {slug(m): m for m in re.findall(r'^## (.+)$', text, re.M)}


def number(stem):
    m = re.match(r'ch(\d+)-', stem)
    return m.group(1) if m else None


def link(ref):
    stem, frag = ref.split('#')
    heads = headings(stem)
    if frag not in heads:
        raise SystemExit(f'no heading #{frag} in {stem}')
    title = re.sub(r'^\d+\.\s*', '', heads[frag]).rstrip('?')
    return (f'<a href={{`${{import.meta.env.BASE_URL}}/{stem}#{frag}`}}>'
            f'Chapter {number(stem)}: {title}</a>')


# (term, definition, [refs]) in alphabetical order; χ² sorts under C.
ENTRIES = [
    ('anchor', 'The point where **Data > Normalize (Auto)** sets the scale: the plateau maximum. With **Solve scale in χ²** on, the fit may move the scale away from it within the **Window**.',
     ['ch14-preparing-the-data#letting-the-fit-solve-the-scale']),
    ('background', 'The level the curve falls to past the last order: the median of the intensities past the last visible order, never less than one count. X-Ray Calc has no background term. The floor **R min** stands in its place.',
     ['ch11-reading-the-curve#the-plateau-and-the-background']),
    ('Bragg order', 'One of the tall, narrow peaks of a periodic stack, numbered m = 1, 2, 3, … Its position is set by the period. Its height depends on how the period is shared between the layers. Also called an order.',
     ['ch6-many-films-bragg-peaks#a-stack-that-repeats']),
    ('χ²', 'The cost function that X-Ray Calc shows and the fit minimizes: the weighted mean squared relative residual of log I, times 1000. Lower is better. It is one check of a fit among several.',
     ['ch9-how-x-ray-calc-finds-a-fit#what-χ-measures', 'ch18-judging-a-fit#χ-is-one-check-among-several']),
    ('contamination layer', 'The thin, light layer of hydrocarbons that every surface in air carries. It is modeled as its own stack, with N = 1, on top of the structure.',
     ['ch7-roughness-interlayers-dirty-surface#the-dirty-surface-a-contamination-layer']),
    ('critical angle, critical edge', 'Below the critical angle θ_c ≈ √(2δ) the beam cannot enter the material and is almost wholly reflected. The critical edge is the steep fall of the curve at θ_c. Its position carries the density near the surface.',
     ['ch4-x-rays-meet-a-surface#the-critical-angle-and-the-plateau']),
    ('density ceiling', 'The upper fit limit of a density, set at the bulk density of the material\'s table. It is the one limit with a physical meaning, and it is raised only for a stated reason.',
     ['ch15-choosing-what-to-fit#the-density-ceiling']),
    ('drift', 'A change of layer thickness with depth that nobody intended, caused by a deposition rate that changed during the run. The period drift is ΔD = D(N) − D(1).',
     ['ch7-roughness-interlayers-dirty-surface#a-stack-that-drifts', 'ch17-periodic-or-polynomial#decide-on-the-drift-not-on-χ']),
    ('edge check', 'The ratio of the calculated to the measured curve at three angles on the critical edge. One laboratory requires each ratio within a factor of 1.5.',
     ['ch18-judging-a-fit#the-edge']),
    ('extension', 'An item stored under a model that adds to its structure: a Function profile, added with the **Add extension** button, or the Table that an Irregular fit leaves. Before a new fit, the program asks whether to keep the extensions of the previous one.',
     ['ch22-graded-multilayers-and-supermirrors#a-gradient-in-polynomial-mode', 'ch22-graded-multilayers-and-supermirrors#a-supermirror-in-irregular-mode']),
    ('fit limits', 'The lowest and highest value a parameter may take in a fit, **Min** and **Max**, set in the **Fitting Limits** dialog. A parameter is fitted only when its Min and Max differ and it is not frozen. With **SeedR** ticked, the limits are the whole search space.',
     ['ch15-choosing-what-to-fit#what-is-free-and-what-the-limits-are-for']),
    ('fitting range', 'The span of angles that the fit compares, the data left after **Data > Trim**. It starts at θ_max and covers at least the first seven orders that the period predicts.',
     ['ch14-preparing-the-data#where-the-fitting-range-starts-and-ends']),
    ('floor', 'The value **R min** in the Chart Info bar. Every calculated value below it is raised to it, in each calculation and in χ². It is set to one count on the scaled curve.',
     ['ch14-preparing-the-data#the-floor-one-count']),
    ('footprint', 'The length of the beam on the specimen. At the smallest angles it can exceed the specimen, and the measured plateau is then low. X-Ray Calc does not correct for it.',
     ['ch26-ten-things-x-ray-calc-does-not-fit#5-the-beam-footprint']),
    ('Free period ±', 'A Periodic-mode option. Ticked, it lets the period move by up to the percentage in the box after it. Unticked, the fit keeps the period at its start value.',
     ['ch17-periodic-or-polynomial#two-ways-to-describe-a-stack']),
    ('freeze', 'To hold a parameter at its value in the next fit while keeping its limits. **Thaw** releases it. A frozen value is an input and is reported as one. The **Fix** button is a different control.',
     ['ch15-choosing-what-to-fit#freezing-a-parameter']),
    ('fringe', 'See Kiessig fringe.', []),
    ('fringe check', 'The mean contrast of the fringes between orders 1 and 2, measured against calculated. It is reported without a limit. When the fringes and the orders disagree, the orders decide.',
     ['ch18-judging-a-fit#the-fringes']),
    ('Function profile', 'An extension that holds a polynomial for one parameter (H, σ or ρ) of one layer. Polynomial mode starts its higher orders from an enabled Function profile.',
     ['ch22-graded-multilayers-and-supermirrors#a-gradient-in-polynomial-mode']),
    ('graded', 'Changing with depth on purpose, as in a supermirror. Each period reflects at its own angle, so the orders become wider and lower.',
     ['ch22-graded-multilayers-and-supermirrors#graded-on-purpose']),
    ('Henke table', 'The table of a material: f₁ and f₂ against the photon energy, the molar mass and the bulk density. The element values come from Henke, Gullikson and Davis (1993).',
     ['ch4-x-rays-meet-a-surface#where-δ-and-β-come-from']),
    ('interlayer', 'A mixed zone where two materials meet, thick enough to act as a layer of its own. It is modeled as one more layer of a compound material, such as CoC or MoSi2.',
     ['ch7-roughness-interlayers-dirty-surface#interlayers-when-the-two-interfaces-of-a-period-differ']),
    ('Irregular mode', 'The fitting mode that fits every period of a stack on its own. A ticked box after a field holds that parameter at one value in every period.',
     ['ch17-periodic-or-polynomial#two-ways-to-describe-a-stack', 'ch22-graded-multilayers-and-supermirrors#a-supermirror-in-irregular-mode']),
    ('iterations', 'The largest number of steps of the swarm in one fit. The book uses 200.',
     ['ch16-fit-settings#population-before-iterations']),
    ('Kiessig fringe', 'One of the small, regular oscillations caused by interference between the reflections at the top and the bottom of a film or a stack. A thicker coating gives closer fringes. Also called a fringe.',
     ['ch5-one-film-kiessig-fringes#two-reflections-one-film']),
    ('layer', 'One material with three parameters: the thickness H, the roughness σ and the density ρ.',
     ['ch1-what-xrr-fitting-is#what-a-fit-gives-you-back']),
    ('layer ratio', 'Γ, the thickness of the heavy layer of a two-layer period divided by the period. It sets the relative heights of the orders. When mΓ is a whole number, order m nearly vanishes.',
     ['ch6-many-films-bragg-peaks#the-layer-ratio-weak-and-missing-orders']),
    ('LFPSO', 'Lévy-flight particle swarm optimization, the search method of X-Ray Calc: a particle swarm in which some steps are mostly small and sometimes very long.',
     ['ch9-how-x-ray-calc-finds-a-fit#the-swarm']),
    ('material', 'The chemical composition of a layer, such as Mo, SiO2 or B4C. It selects the table of optical constants. It is never fitted.',
     ['ch1-what-xrr-fitting-is#what-a-fit-gives-you-back']),
    ('near-bound rule', 'A value that ends on a limit, or within 5 % of the range from it, was set by the limit. The limit is extended in that direction and the fit repeated, until no value is near a limit. Every extension is reported. The density ceiling is the exception.',
     ['ch15-choosing-what-to-fit#the-near-bound-rule']),
    ('Névot–Croce factor', 'The Gaussian roughness factor that multiplies the reflection of every interface. It uses the wave-vector transfer on both sides of the interface.',
     ['ch7-roughness-interlayers-dirty-surface#a-boundary-with-a-width']),
    ('one count', 'One detector count on the curve of an `.xrdml` import: 1 / (peak rate × counting time). The floor is set to one count after normalization.',
     ['ch10-is-this-curve-worth-fitting#what-the-import-does-to-the-counts']),
    ('order', 'See Bragg order.', []),
    ('order table', 'For every visible Bragg order, the measured peak, the calculated peak and their ratio, calculated over measured. One laboratory requires every ratio within 0.75–1.25.',
     ['ch18-judging-a-fit#the-order-table']),
    ('Paired', 'The box after a layer\'s H, σ or ρ field. Ticked, it holds that parameter at one value in every period, in Irregular and Polynomial mode, when N > 1.',
     ['ch17-periodic-or-polynomial#two-ways-to-describe-a-stack']),
    ('Parratt recursion', 'The exact calculation of the curve. It starts at the substrate and moves up one interface at a time, combining each interface\'s reflection with the reflection of everything below it.',
     ['ch8-how-x-ray-calc-computes-a-curve#from-the-substrate-up-the-recursion']),
    ('period', 'D, the sum of the thicknesses of one repeat of a periodic stack. The positions of the Bragg orders give it.',
     ['ch6-many-films-bragg-peaks#a-stack-that-repeats']),
    ('Periodic mode', 'The fitting mode that fits one H, σ and ρ per layer, the same in every period. The period stays at its start value unless **Free period ±** is ticked.',
     ['ch17-periodic-or-polynomial#two-ways-to-describe-a-stack']),
    ('plain χ²', 'The same sum as χ² with both weights set to 1. It is shown for comparison and is never minimized.',
     ['ch9-how-x-ray-calc-finds-a-fit#what-χ-measures']),
    ('plateau', 'The flat top of the curve at the smallest angles, where almost the whole beam is reflected.',
     ['ch4-x-rays-meet-a-surface#the-critical-angle-and-the-plateau']),
    ('Polynomial mode', 'The fitting mode in which a parameter\'s value in period k is a polynomial, C₀ + C₁(k − 1) + C₂(k − 1)² + …, with k = 1 the top period. The **Order** field sets the highest power. The period is free.',
     ['ch17-periodic-or-polynomial#two-ways-to-describe-a-stack']),
    ('population', 'The number of particles in the swarm. The book uses 5000 for a multilayer and 2000 for a single film.',
     ['ch16-fit-settings#population-before-iterations']),
    ('residual by band', 'The mean of log₁₀(calculated / measured) in each of eight equal bands of the fitting range. A band mean beyond ±0.1 is a warning, and the ends of the stack are checked first. **Result > Residual strip** draws the band means under the chart.',
     ['ch18-judging-a-fit#the-residual-by-band']),
    ('resolution', 'Δθ, the width of the Gaussian that blurs the calculated curve as the instrument blurs the measured one. It is always a θ value. It is chosen for each curve by a scan and never fitted.',
     ['ch8-how-x-ray-calc-computes-a-curve#the-resolution-a-blur-of-the-calculated-curve', 'ch16-fit-settings#choosing-δθ-by-a-scan']),
    ('roughness', 'σ, the width of a boundary, treated as Gaussian. It includes roughness and intermixing, which the curve cannot tell apart. A layer\'s σ belongs to its upper interface.',
     ['ch7-roughness-interlayers-dirty-surface#a-boundary-with-a-width']),
    ('scale', 'The factor that puts the measured counts on the reflectivity axis. **Data > Normalize (Auto)** sets it.',
     ['ch14-preparing-the-data#setting-the-scale-normalize-auto']),
    ('seed', 'The start value of the random numbers of one fit. Two runs that differ only in the seed can end in different places. X-Ray Calc records the seed of every fit. Typed into **Seed** in **Advanced fitting settings**, it repeats that fit on the same device.',
     ['ch9-how-x-ray-calc-finds-a-fit#random-seeds-why-two-runs-disagree']),
    ('SeedR', 'The option that starts the swarm spread over each parameter\'s whole Min–Max range. Unticked, the swarm starts around the starting model. Polynomial mode always starts that way, so there the box is grayed out.',
     ['ch9-how-x-ray-calc-finds-a-fit#the-swarm']),
    ('sensitivity map', 'A list with one line for each one-parameter change of the starting model, naming the feature of the curve that moved. It shows which parameter to move when a fit disagrees with the data.',
     ['ch13-the-sensitivity-check#why-check-before-you-fit']),
    ('Shake', 'The step that scatters the swarm again around the best structure so far when χ² has stopped improving.',
     ['ch9-how-x-ray-calc-finds-a-fit#shakes-leaving-a-valley']),
    ('solved scale', 'With **Solve scale in χ²** ticked, the scale factor that gives each scored structure its lowest χ², within the **Window** around the anchor. The Chart Info bar shows it as "solved x…", with "at bound" when it reached the edge of the window.',
     ['ch14-preparing-the-data#letting-the-fit-solve-the-scale']),
    ('spread over runs', 'The sample standard deviation of a fitted parameter over five runs that differ only in the seed. It shows how well the curve fixes the parameter. It is not an error bar of the measurement.',
     ['ch16-fit-settings#several-runs-and-their-spread']),
    ('stack', 'A set of layers, single or repeated N times.',
     ['ch1-what-xrr-fitting-is#what-a-fit-gives-you-back']),
    ('stand-in layer', 'A parameter that does the work of a layer missing from the model: a σ that grows, or a density that moves, until the curve matches. The remedy is to add the missing layer.',
     ['ch19-when-the-fit-will-not-converge#the-model-is-too-simple']),
    ('starting model', 'The structure the fit starts from. Its materials, layer order, N and substrate are kept as entered. Its other values are start values.',
     ['ch12-building-the-starting-model#what-the-starting-model-decides']),
    ('structure', 'All the stacks together, the substrate included.',
     ['ch1-what-xrr-fitting-is#what-a-fit-gives-you-back']),
    ('substrate', 'A stack of one layer of infinite thickness at the bottom of the structure. Its material, σ and ρ are held and never fitted.',
     ['ch12-building-the-starting-model#the-substrate']),
    ('sum', 'The total of two neighboring layers, reported when the runs agree on the total but not on how it divides. The split is then reported as undetermined.',
     ['ch18-judging-a-fit#two-layers-as-a-sum']),
    ('supermirror', 'A graded multilayer in which every period differs, so that it reflects a wide band of angles.',
     ['ch22-graded-multilayers-and-supermirrors#graded-on-purpose']),
    ('swarm', 'The set of particles of the search. Each particle is one complete candidate structure. Each step combines the previous step, a pull toward the best particle of the iteration and a pull toward the best structure so far.',
     ['ch9-how-x-ray-calc-finds-a-fit#the-swarm']),
    ('Table', 'The extension in which an Irregular fit keeps the values of every period. The structure panel shows only the top period.',
     ['ch22-graded-multilayers-and-supermirrors#a-supermirror-in-irregular-mode']),
    ('undetermined', 'Said of a parameter whose spread over the runs is larger than the precision one would claim. It is reported without a number. One laboratory\'s limits are 0.5 Å for H and σ, 0.2 g/cm³ for ρ and 0.1 Å for the period.',
     ['ch18-judging-a-fit#what-the-runs-dont-agree-on']),
    ('verdict', 'The result of the checks of a fit, written one check at a time with the calibration of each limit. A fail is a result and is reported. **Data > Assess XRR quality ...** also gives a verdict for each check of a measurement: pass, warn, fail or unknown.',
     ['ch18-judging-a-fit#writing-the-verdict', 'ch10-is-this-curve-worth-fitting#is-this-curve-worth-fitting']),
]


def md(s):
    # Glossary entries are Markdown paragraphs: bold and code spans stay Markdown.
    return s


def letter(term):
    t = term[0].upper()
    return 'C' if t == 'Χ' else t


HEAD = """---
title: 'Glossary'
part: 'back'
number: 'D'
order: 300
inThisChapter:
  - The terms of the book, in alphabetical order
  - Where each term is defined
---

{/* Appendix D. Outline approved 2026-09-25 (OUTLINE.md, back matter, choice 3 (a)). Generated by scripts/appendix/make_appendix_d.py; edit the script, not this file. */}

Each entry gives the meaning of a term as this book uses it, and links to the section that defines it. Symbols and units are in <a href={`${import.meta.env.BASE_URL}/appendix-a-notation#symbols`}>Appendix A: Symbols</a>. The names of menus, buttons and fields are in <a href={`${import.meta.env.BASE_URL}/appendix-b-menus#the-menus`}>Appendix B: The menus</a>.
"""

SOURCES = """## Sources

- **This book**, the section linked in each entry. The definitions are shortened from those sections, which name their own sources.
- **NOTATION.md** of this book, §3 and §4: the structure terms (from the X-Ray Calc Help, *Models* → *Terminology*) and the one word used for each thing.

Cross-references: <a href={`${import.meta.env.BASE_URL}/appendix-a-notation#symbols`}>Appendix A: Notation and Units</a>; <a href={`${import.meta.env.BASE_URL}/appendix-b-menus#the-menus`}>Appendix B: Menus, Buttons and Keys</a>.
"""


def main():
    out = [HEAD]
    current = None
    for term, text, refs in ENTRIES:
        L = letter(term)
        if L != current:
            out.append(f'\n## {L}\n')
            current = L
        links = '; '.join(link(r) for r in refs)
        body = md(text)
        if links:
            body += f' See {links}.'
        out.append(f'**{md(term)}.** {body}\n')
    out.append('\n' + SOURCES)
    OUT.write_text('\n'.join(out), encoding='utf-8')
    print('wrote', OUT, len(ENTRIES), 'entries')


if __name__ == '__main__':
    main()
