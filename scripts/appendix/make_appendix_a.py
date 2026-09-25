"""Writes src/content/chapters/appendix-a-notation.mdx from the tables below.

The symbols are those of NOTATION.md §3, with a reader's meaning and the chapter that
introduces each. NOTATION.md stays canonical: src/lib/appendix-notation.test.ts fails when a
symbol of NOTATION §3 is missing here. Run:  python scripts/appendix/make_appendix_a.py
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'src' / 'content' / 'chapters' / 'appendix-a-notation.mdx'

CH = {
    'ch1': 'ch1-what-xrr-fitting-is', 'ch2': 'ch2-meet-x-ray-calc-3', 'ch3': 'ch3-your-first-fit',
    'ch4': 'ch4-x-rays-meet-a-surface', 'ch6': 'ch6-many-films-bragg-peaks',
    'ch7': 'ch7-roughness-interlayers-dirty-surface', 'ch8': 'ch8-how-x-ray-calc-computes-a-curve',
    'ch9': 'ch9-how-x-ray-calc-finds-a-fit', 'ch10': 'ch10-is-this-curve-worth-fitting',
    'ch11': 'ch11-reading-the-curve', 'ch12': 'ch12-building-the-starting-model',
    'ch14': 'ch14-preparing-the-data', 'ch15': 'ch15-choosing-what-to-fit', 'ch16': 'ch16-fit-settings',
    'ch17': 'ch17-periodic-or-polynomial',
}


def link(ref):
    ch, frag = ref.split('#')
    num = ch[2:]
    return f'<a href={{`${{import.meta.env.BASE_URL}}/{CH[ch]}#{frag}`}}>Chapter {num}</a>'


# (symbol, meaning, unit, 'chN#fragment')
BEAM = [
    ('θ', 'The grazing angle of incidence, measured from the surface. Every formula uses θ.', '°', 'ch2#2θ-or-θ-the-angle-on-your-screen'),
    ('2θ', 'The scattering angle. The chart shows it by default.', '°', 'ch2#2θ-or-θ-the-angle-on-your-screen'),
    ('λ', 'The wavelength. On screen: **λ(Å)**.', 'Å', 'ch10#the-wavelength-comes-from-the-file'),
    ('E', 'The photon energy, E = hc/λ, with hc = 12398.6 eV·Å.', 'eV', 'ch4#where-δ-and-β-come-from'),
    ('q', 'The wave-vector transfer in vacuum, q = 4π sin θ / λ.', 'Å⁻¹', 'ch7#a-boundary-with-a-width'),
    ('q₀, q′', 'In the roughness factor: q in vacuum, and q refracted across the interface.', 'Å⁻¹', 'ch7#a-boundary-with-a-width'),
    ('k_j', 'The wave vector across the layers in medium j.', 'Å⁻¹', 'ch8#from-the-substrate-up-the-recursion'),
    ('F_j, r_j', 'The reflection of the interface under medium j, with its roughness factor; the reflection of everything from that interface down.', 'none', 'ch8#from-the-substrate-up-the-recursion'),
    ('Δθ', 'The angular resolution: the FWHM of the Gaussian blur of the calculated curve. Always a θ value.', '° (θ)', 'ch8#the-resolution-a-blur-of-the-calculated-curve'),
    ('s, p', 'The two polarization states. On screen: **Polarization**.', 'none', 'ch8#polarization-s-type-or-sp-type'),
]
OPTICAL = [
    ('n', 'The complex refractive index, n = 1 − δ + iβ.', 'none', 'ch4#a-refractive-index-just-below-1'),
    ('ε', 'The dielectric constant, ε = 1 − 2δ + 2iβ.', 'none', 'ch8#from-the-substrate-up-the-recursion'),
    ('δ', 'The refractive decrement, proportional to ρλ²f₁/A.', 'none', 'ch4#a-refractive-index-just-below-1'),
    ('β', 'The absorption index, proportional to ρλ²f₂/A.', 'none', 'ch4#a-refractive-index-just-below-1'),
    ('f₁, f₂', 'The atomic scattering factors, real and imaginary, from the Henke tables.', 'electrons', 'ch4#where-δ-and-β-come-from'),
    ('A', 'The molar mass. On screen: **A (g/mol)**.', 'g/mol', 'ch4#where-δ-and-β-come-from'),
    ('r_e', 'The classical electron radius, 2.82 × 10⁻⁵ Å.', 'Å', 'ch4#where-δ-and-β-come-from'),
    ('N_A', 'The Avogadro constant, 6.02 × 10²³ mol⁻¹.', 'mol⁻¹', 'ch4#where-δ-and-β-come-from'),
    ('θ_t', 'The angle of the transmitted beam inside a material, measured from the surface.', '°', 'ch4#the-critical-angle-and-the-plateau'),
    ('θ_c', 'The critical angle, θ_c ≈ √(2δ) in radians.', '°', 'ch4#the-critical-angle-and-the-plateau'),
]
STRUCTURE = [
    ('Material', 'The chemical composition of a layer, such as Mo, SiO2 or B4C. It sets f₁, f₂ and A. It is never fitted.', 'none', 'ch1#what-an-xrr-measurement-records'),
    ('Layer', 'One material with three parameters: H, σ and ρ.', 'none', 'ch1#what-an-xrr-measurement-records'),
    ('Stack', 'A set of layers, single or repeated N times.', 'none', 'ch1#what-an-xrr-measurement-records'),
    ('Structure', 'All the stacks, the substrate included.', 'none', 'ch1#what-an-xrr-measurement-records'),
    ('Substrate', 'A stack of one layer of infinite thickness. It is held in a fit.', 'none', 'ch12#the-substrate'),
    ('H', 'The thickness of a layer.', 'Å', 'ch1#what-an-xrr-measurement-records'),
    ('σ', 'The roughness of a layer\'s upper interface. The substrate\'s σ is the roughness of its surface.', 'Å', 'ch7#a-boundary-with-a-width'),
    ('ρ', 'The density. ρ = 0 means the bulk density of the material\'s table.', 'g/cm³', 'ch4#where-δ-and-β-come-from'),
    ('D', 'The period of a periodic stack, the sum of the H of its layers. The **D** box shows the top period.', 'Å', 'ch6#a-stack-that-repeats'),
    ('N', 'The number of periods of a stack.', 'none', 'ch6#a-stack-that-repeats'),
    ('m', 'The Bragg order index, m = 1, 2, 3, …', 'none', 'ch6#the-bragg-law-with-refraction'),
    ('k', 'The period index in a periodic stack, counted from the surface: k = 1 is the top period.', 'none', 'ch17#two-ways-to-describe-a-stack'),
    ('C₀, C₁, …', 'The coefficients of a polynomial profile: value(k) = C₀ + C₁(k − 1) + C₂(k − 1)² + … C₀ is the value of the top period.', 'as the parameter', 'ch17#two-ways-to-describe-a-stack'),
    ('ΔD', 'The period drift: the bottom period minus the top one, ΔD = D(N) − D(1).', 'Å', 'ch17#decide-on-the-drift-not-on-χ'),
    ('θ_m', 'The angle of the m-th Bragg order.', '° (θ)', 'ch6#the-bragg-law-with-refraction'),
    ('δ̄', 'The refractive decrement averaged over one period, as it enters the Bragg law with refraction.', 'none', 'ch6#the-bragg-law-with-refraction'),
    ('D_m', 'The period that the plain Bragg law gives from order m alone, D_m = mλ/(2 sin θ_m).', 'Å', 'ch6#why-evenly-spaced-orders-mislead-you'),
    ('Γ', 'The layer ratio: the thickness of the heavy layer of a two-layer period divided by D.', 'none', 'ch6#the-layer-ratio-weak-and-missing-orders'),
]
FIT = [
    ('R', 'The reflectivity, as calculated.', 'none', 'ch1#what-an-xrr-measurement-records'),
    ('I', 'The measured intensity.', 'counts', 'ch10#what-the-import-does-to-the-counts'),
    ('θ_max, I_max', 'The angle and the intensity of the measured maximum below the critical edge, the plateau maximum.', '°, counts', 'ch11#the-plateau-and-the-background'),
    ('background', 'The median intensity past the last visible order, never less than one count.', 'counts', 'ch11#the-plateau-and-the-background'),
    ('r_min', 'The floor: calculated values below it are raised to it, in the curve and in χ². On screen: **R min**.', 'none', 'ch14#the-floor-one-count'),
    ('one count', 'One detector count on the curve that an `.xrdml` import scales to 1: 1 / (peak rate × counting time).', 'none', 'ch10#what-the-import-does-to-the-counts'),
    ('λ from the file', 'For copper with both Kα lines, (Kα1 + r·Kα2)/(1 + r) = 1.541874 Å at r = 0.5; behind a monochromator or hybrid mirror, Kα1 = 1.540598 Å.', 'Å', 'ch10#the-wavelength-comes-from-the-file'),
    ('scale', 'The factor that puts the measured curve on the reflectivity axis.', 'none', 'ch14#setting-the-scale-normalize-auto'),
    ('w', 'The window of the solved scale: the scale may move by a factor of up to 1 + w from its anchor. On screen: **Window**.', 'none', 'ch14#letting-the-fit-solve-the-scale'),
    ('χ²', 'The cost function as displayed: the weighted mean squared relative residual of log I, times 1000.', 'none', 'ch9#what-χ-measures'),
    ('plain χ²', 'The same sum with both weights set to 1. It is shown, and never minimized.', 'none', 'ch9#what-χ-measures'),
    ('PW χ²', 'The peak weighting of χ².', 'none', 'ch9#what-χ-measures'),
    ('TW χ²', 'The angle weighting of χ²: none, θ², θ, √θ, 1/θ² or 1/√θ of the chart axis.', 'none', 'ch9#what-χ-measures'),
    ('Min, Max', 'The fit limits of one parameter. The parameter is fitted only when Min ≠ Max.', 'as the parameter', 'ch15#the-fitting-limits-dialog'),
    ('ΔH, Δσ, Δρ', 'The fractions that **Initialize** uses: Min = V(1 − Δ), Max = V(1 + Δ).', 'none', 'ch15#generous-limits'),
    ('p', 'The polynomial order in Polynomial mode. On screen: **Order**.', 'none', 'ch17#raising-the-order'),
    ('population', 'The number of particles in the swarm.', 'none', 'ch16#population-before-iterations'),
    ('iterations', 'The largest number of iterations of a fit.', 'none', 'ch16#population-before-iterations'),
    ('seed spread', 'The sample standard deviation of a fitted parameter over repeated runs.', 'as the parameter', 'ch16#several-runs-and-their-spread'),
    ('seed', 'The start value of the random numbers of one fit.', 'none', 'ch9#random-seeds-why-two-runs-disagree'),
    ('SeedR', 'Start the swarm spread over each parameter\'s whole Min–Max range.', 'none', 'ch9#the-swarm'),
    ('Vmax, Ksxr', 'The largest step, and the scatter around a structure, as fractions of each parameter\'s range.', 'none', 'ch9#the-swarm'),
    ('Jmax, SHmax, k1, k2', 'The Shake settings: iterations without improvement before a shake; shakes before a return to the best; the lift of the best χ²; the enlargement of Vmax and Ksxr.', 'none', 'ch9#shakes-leaving-a-valley'),
    ('Tolerance', 'The fit stops when the best χ² falls below it.', 'none', 'ch9#when-the-fit-stops'),
    ('x, v, b, g, u₁, u₂, c₁, c₂, κ', 'The particle-swarm step: position, step, best particle of the iteration, best structure so far, random numbers in [0, 1], the two pulls, the constriction factor.', 'none', 'ch9#the-swarm'),
]
ABBR = [
    ('XRR', 'X-ray reflectivity', 'ch1#what-an-xrr-measurement-records'),
    ('PMM', 'Periodic multilayer mirror', 'ch6#a-stack-that-repeats'),
    ('LFPSO', 'Lévy-flight particle swarm optimization, the fitting algorithm of X-Ray Calc', 'ch9#the-swarm'),
    ('FWHM', 'Full width at half maximum', 'ch8#the-resolution-a-blur-of-the-calculated-curve'),
    ('GUI', 'Graphical user interface', 'ch2#the-main-window'),
]


def esc(s):
    # MDX: braces and angle brackets would be read as JSX.
    return s.replace('{', '&#123;').replace('}', '&#125;').replace('<', '&lt;')


def md(s):
    import re
    s = esc(s)
    s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'`(.+?)`', r'<code>\1</code>', s)
    return s


def sym(s):
    """Symbol cell: X_y → X<sub>y</sub>, keeping commas and spaces."""
    import re
    return re.sub(r'([A-Za-zθ])_([a-zA-Z0-9]+)', r'\1<sub>\2</sub>', esc(s))


def table(caption_id, caption, rows, cols=('Symbol', 'Meaning', 'Unit', 'Introduced in')):
    out = [f'<p id="{caption_id}" class="table-caption">{caption}</p>', '',
           '<table className="data-table keep-header-case">',
           '  <thead><tr>' + ''.join(f'<th>{c}</th>' for c in cols) + '</tr></thead>', '  <tbody>']
    for r in rows:
        if len(r) == 4:
            s, m, u, ref = r
            cells = [sym(s), md(m), esc(u), link(ref)]
        else:
            s, m, ref = r
            cells = [esc(s), md(m), link(ref)]
        out.append('    <tr>' + ''.join(f'<td>{c}</td>' for c in cells) + '</tr>')
    out += ['  </tbody>', '</table>', '']
    return '\n'.join(out)


HEAD = """---
title: 'Notation and Units'
part: 'back'
number: 'A'
order: 270
inThisChapter:
  - The units used throughout the book
  - How angles are labeled
  - Every symbol, with the chapter that introduces it
---

{/* Appendix A. Outline approved 2026-09-25 (OUTLINE.md, back matter, choice 1 (a)). Generated by scripts/appendix/make_appendix_a.py from NOTATION.md; edit the script, not this file. */}

This appendix collects the notation of the book. Each symbol links to the chapter that introduces it.

## Units

The book uses the units of X-Ray Calc, so every number matches the screen.

- **Every length** (thickness, roughness, period, wavelength) is in ångströms, Å. 10 Å = 1 nm.
- **Density** is in g/cm³.
- **Angles** are in degrees, and every angle is labeled θ or 2θ.
- **Photon energy** is in eV. It appears only as an input that the program converts to λ.
- **Reflectivity** has no unit. Measured intensity is in counts, or in counts/s for an `.xrdml` import.

Numbers use a decimal point. A range is written with an en-dash and no spaces: 0.012–0.015°. A number keeps the precision of its source.

## θ and 2θ

θ is the grazing angle, measured from the surface. Every formula in the book uses θ. 2θ is the scattering angle. It is what the X-Ray Calc chart shows by default, with the **2θ** box ticked. Every angle read off the chart, or typed into a range, a limit or a trim, is therefore 2θ. The conversion is θ = (2θ)/2.

The resolution Δθ is always a θ value, whatever the chart shows. On a 2θ axis the program doubles it.

## Symbols

"""

TAIL = """## The Bragg law with refraction

Every period in the book is read from the orders with this law (<a href={`${import.meta.env.BASE_URL}/ch6-many-films-bragg-peaks#the-bragg-law-with-refraction`}>Chapter 6: The Bragg law with refraction</a>):

$$
\\sin^2\\theta_m = \\left(\\frac{m\\lambda}{2D}\\right)^2 + 2\\bar{\\delta}
$$

## Labels that can mislead

- **N means two things on the screen.** In the structure panel it is the number of periods. In the calculation settings it is the number of calculated points. The book writes N only for periods.
- **Some labels are drawn in the Symbol font.** The screen shows θ, Δθ, 2θ, λ(Å), θ1 and θ2. The book quotes the labels as they appear.
- **The molar mass** in **Tools > Edit Henke table...** reads **A (g/mol)** from 3.9.4, and **N (a.u.)** in earlier versions. It is neither a number of periods nor a number of points.

## Abbreviations

"""

SOURCES = """## Sources

- **NOTATION.md** of this book, §1–3 and §5–7: the units, the angle convention, the symbols and their sources, the on-screen labels and the abbreviations. Each symbol's own source (the X-Ray Calc Help, the X-Ray Calc source, the fitting procedure, Spiller) is named there and in the chapter linked.
- **X-Ray Calc Help:** *Models* → *Terminology* (material, layer, stack, structure, substrate; from Penkov et al. 2024); *Calculation* → *Algorithm*; *Fitting* → *Understanding the Cost Function*.
- **The X-Ray Calc 3 source:** hc = 12398.6 eV·Å (`Shared\\Math\\math_globals.pas`); the resolution doubled on a 2θ axis (`Shared\\Math\\unit_calc.pas`); the period index counted from the surface.

Cross-references: <a href={`${import.meta.env.BASE_URL}/ch2-meet-x-ray-calc-3#2θ-or-θ-the-angle-on-your-screen`}>Chapter 2: 2θ or θ</a>; <a href={`${import.meta.env.BASE_URL}/ch4-x-rays-meet-a-surface#where-δ-and-β-come-from`}>Chapter 4: Where δ and β come from</a>; <a href={`${import.meta.env.BASE_URL}/ch6-many-films-bragg-peaks#the-bragg-law-with-refraction`}>Chapter 6: The Bragg law with refraction</a>; <a href={`${import.meta.env.BASE_URL}/appendix-d-glossary#a`}>Appendix D: Glossary</a>.
"""


def main():
    parts = [HEAD]
    parts.append('### Beam and geometry\n\n' + table('table-a-1', '<strong>Table A-1:</strong> Beam and geometry.', BEAM))
    parts.append('### Optical constants\n\n' + table('table-a-2', '<strong>Table A-2:</strong> Optical constants.', OPTICAL))
    parts.append('### The structure\n\nThe structure terms are those of X-Ray Calc.\n\n' + table('table-a-3', '<strong>Table A-3:</strong> The structure.', STRUCTURE))
    parts.append('### The measured curve and the fit\n\n' + table('table-a-4', '<strong>Table A-4:</strong> The measured curve and the fit.', FIT))
    parts.append(TAIL)
    parts.append(table('table-a-5', '<strong>Table A-5:</strong> Abbreviations.', ABBR, cols=('Abbreviation', 'Meaning', 'First use')))
    parts.append(SOURCES)
    OUT.write_text('\n'.join(parts), encoding='utf-8')
    print('wrote', OUT)


if __name__ == '__main__':
    main()
