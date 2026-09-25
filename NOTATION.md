# NOTATION: symbols, units, and terms

_Canonical file. Written 2026-09-23. **No new symbol, term or abbreviation enters the manuscript
without being added here in the same pass.** Each entry names its source. When sources disagree,
the order is code > Help > wiki > procedure (see `CLAUDE.md`)._

## 1. Units: one system, no exceptions

Author decision, 2026-09-23. These are the program's own units, so the book always matches the
screen.

| Quantity | Unit | Notes |
|---|---|---|
| Every length: thickness, roughness, period, wavelength | **Å** | Also where the literature quotes nm. A conversion (10 Å = 1 nm) may appear once, in Chapter 4 |
| Wave-vector transfer q | **Å⁻¹** | |
| Density | **g/cm³** | |
| Angle | **degrees (°)** | θ or 2θ, always labeled (§2) |
| Photon energy | **eV** | Only as an input the program converts to λ (§3) |
| Reflectivity | dimensionless | Measured intensity is in counts, or counts/s for an `.xrdml` import |

## 2. Angles: 2θ on the screen, θ in the physics

Author decision, 2026-09-23.

- **θ is the grazing angle**, measured from the surface. **Every formula in the book uses θ.**
  Spiller measures φ from the surface normal. Convert with θ = 90° − φ, and never show φ.
- **2θ is the scattering angle.** It is what the X-Ray Calc chart shows by default (the **2θ**
  checkbox in the calculation settings, on by default: `frame_CalcSettings.pas:284`). An
  `.xrdml` 2Theta–Omega scan and most text files also use it. **Every angle the reader reads off
  the chart or types into a range, limit or trim is 2θ.** This is the author's own practice
  (paper Table 2: "Left limit moved to 2θ 0.6°").
- **Write the label every time:** "2θ = 1.2°" or "θ = 0.6°". A bare "0.6°" for an angle is not
  allowed.
- **Conversion:** θ = (2θ)/2. State it in Chapter 2, where the checkbox first appears, and again
  in the Remember icon of Chapter 11.
- **The resolution Δθ is always a θ value**, whatever the checkbox shows. The engine doubles it
  internally on a 2θ axis (`unit_calc.pas:312`, width = DT × K, with K = 2 for 2θ). The field is
  labeled **Δθ**.

## 3. Symbols

### Beam and geometry

| Symbol | Meaning | Unit | Source / note |
|---|---|---|---|
| θ | Grazing angle of incidence | ° | Help *Calculation*. On-screen fields **θ1**, **θ2** give the calculation range |
| 2θ | Scattering angle; the chart's default axis | ° | §2 |
| λ | Wavelength | Å | On-screen **λ(Å)**. The author's lab uses 1.5406 Å or the Kα doublet 1.541874 Å read from the `.xrdml` (Help *Data*). These are examples, never defaults |
| E | Photon energy, E = hc/λ | eV | hc = **12398.6 eV·Å**, the engine constant (`Shared\Math\math_globals.pas`, `H`) |
| q | Wave-vector transfer in vacuum, q = 4π sin θ / λ | Å⁻¹ | Help *Calculation* writes it q₀. The book writes q |
| q₀, q′ | In the roughness factor exp(−q₀q′σ²/2): q₀ is q in vacuum, q′ the wave-vector transfer refracted across the interface | Å⁻¹ | Help *Calculation* → *Algorithm*; `unit_calc.pas:591–642`. Chapter 7 only, where the two must be told apart |
| k_j | Wave vector across the layers in medium j, k_j = (2π/λ)√(ε_j − cos²θ) | Å⁻¹ | `unit_calc.pas:677–688`. Chapter 8, Going Deeper only |
| F_j, r_j | F_j: the reflection of the interface under medium j, with its roughness factor; r_j: the reflection of everything from that interface down (Parratt's recursion) | — | Parratt (1954), Eq. 8; `unit_calc.pas:557–642`. Chapter 8, Going Deeper only |
| Δθ | Angular resolution: the FWHM of the Gaussian blur applied to the calculated curve | ° (θ) | On-screen **Δθ**. A setting chosen for each measurement, not a property of the instrument (procedure §8) |
| s, p | Polarization states | — | On-screen **Polarization**. They give the same result at grazing angles (procedure §2.5) |

### Optical constants

| Symbol | Meaning | Unit | Source / note |
|---|---|---|---|
| n | Complex refractive index, n = 1 − δ + iβ | — | Sign of iβ as in the engine |
| ε | Dielectric constant, ε = 1 − 2δ + 2iβ | — | Help *Calculation*. Confirmed in `unit_materials.pas:249–251` (Re = 1 − f₁c, Im = +f₂c) |
| δ | Refractive decrement | — | Proportional to ρλ²f₁/A |
| β | Absorption index | — | Proportional to ρλ²f₂/A |
| f₁, f₂ | Atomic scattering factors, real and imaginary | electrons | Henke tables (Henke et al. 1993), interpolated linearly in E |
| A | Molar mass | g/mol | Help *Calculation*. The Henke table editor labels it **A (g/mol)** from 3.9.4, and **N (a.u.)** before (`editor_HenkeTable.dfm:52`) |
| r_e | Classical electron radius, 2.82 × 10⁻⁵ Å | Å | Spiller p. 8 (r₀ = 2.82 × 10⁻¹³ cm; the book writes r_e). The code stores only the product in `ClassicalElectronRadius` = 0.54014 × 10⁻⁵ (`unit_materials.pas:90`), which is r_e N_A/π with λ in Å and ρ in g/cm³ (Chapter 4, Going Deeper). The comment said 2π before 3.9.4; the value was always right |
| N_A | Avogadro constant, 6.02 × 10²³ mol⁻¹ | mol⁻¹ | Spiller p. 13. Chapter 4: ρN_A/A is the number of atoms per unit volume |
| θ_t | Angle of the transmitted beam inside a material, measured from the surface | ° | Chapter 4 only (Snell’s law at grazing incidence) |
| θ_c | Critical angle, θ_c ≈ √(2δ) (radians) | ° in text | Spiller ch. 3. Always say which δ is meant: that of the top layer, or the average |

### Structure

These are X-Ray Calc's terms (Help *Models* → *Terminology*, from Penkov et al. 2024).

| Symbol / term | Meaning | Unit | Source / note |
|---|---|---|---|
| **Material** | The chemical composition of a layer (Mo, SiO2, B4C). It sets f₁, f₂ and A. It is never fitted | — | Help *Terminology* |
| **Layer** | One material with three parameters: H, σ, ρ | — | Help *Terminology* |
| **Stack** | A set of layers. It is single, or periodic (repeated N times) | — | Help *Terminology* |
| **Structure** | All the stacks, including the substrate | — | Help *Terminology* |
| **Substrate** | A special stack of one layer of infinite thickness. It is held fixed in a fit | — | Help *Terminology*; procedure §2.1 |
| H | Layer thickness | Å | Help *Terminology* (H). Never d or t |
| σ | Roughness (interface width) of a layer's **upper** interface. The substrate's σ is the roughness of the substrate surface | Å | Help *Calculation*. Confirmed in `unit_calc.pas:642`: the interface between layers i and i+1 takes σ of layer i+1 |
| ρ | Density. **ρ = 0 means "use the Henke bulk density"**, for layers and, since 3.9.1, for the substrate | g/cm³ | Help *Models* → *Density 0* |
| D | Period of a periodic stack, the sum of its layers' H | Å | Help *Fitting* ("period D"). **The procedure's d is written D in the book**. In a graded stack D changes with k. The **D** box of the Chart Info bar sums the layers' H fields, so it shows the top period (k = 1), not the mean (demo, Chapter 3) |
| N | Number of periods of a stack | — | Help *Terminology*. **Warning:** the calculation-settings field labeled **N** is the number of calculated points (§5) |
| m | Bragg order index, m = 1, 2, 3, … | — | Procedure §1.5 |
| k | Period index within a periodic stack, **counted from the surface**: k = 1 is the top period | — | The program's convention for profiles (`Shared\Math\math_globals.pas:80–91`). Chapter 3 |
| C₀, C₁, … | Coefficients of a polynomial profile: value(k) = C₀ + C₁(k − 1) + C₂(k − 1)² + … | unit of the parameter | C₀ is the value shown in the layer's own field, the top period (`frame_ProjectPanel.pas:1702`). C₁ and higher are stored in the profile item, e.g. **F(H Main/Si)**. Chapter 3 (Going Deeper), Chapter 17 |
| ΔD | Period drift: the period of the bottom period minus the period of the top one, ΔD = D(N) − D(1) | Å | Procedure §9.7 ("substrate end minus surface end"). For order 1 it is (N − 1) times the sum of the layers' C₁. Chapter 17 |
| θ_m | Angle of the m-th Bragg order | ° (θ) | Procedure §1.5 |
| δ̄ | Refractive decrement averaged over one period, as it enters the Bragg law with refraction | — | Procedure §1.5 writes 2δ. The book writes 2δ̄ to show it is an average |
| D_m | The period that the plain Bragg law gives from order m alone, D_m = mλ/(2 sin θ_m) | Å | Spiller pp. 272–273 (d_Bragg). Chapter 6, Table 6-1 and Going Deeper |
| Γ | Layer ratio: the thickness of the heavy layer of a two-layer period divided by D. Order m has the strength factor sin²(mπΓ), the same for Γ and 1 − Γ | — | Spiller p. 107, Eq. 7.11, writes γ for "material one". The book writes Γ (author, 2026-09-24). Chapter 6 |

**The Bragg law with refraction**, in the book's notation (procedure §1.5 and §6.6):

$$
\sin^2\theta_m = \left(\frac{m\lambda}{2D}\right)^2 + 2\bar{\delta}
$$

### Measured curve and fitting

| Symbol / term | Meaning | Unit | Source / note |
|---|---|---|---|
| R | Reflectivity (calculated) | — | |
| I | Measured intensity | counts | Procedure §1 |
| θ_max, I_max | The angle and intensity of the measured maximum below the critical edge (the plateau maximum) | °, counts | Procedure §1.2. Read on the chart as 2θ; label it |
| background | Median intensity past the last visible order, with a floor of one count | counts | Procedure §1.3. Help *Data*: the median of the last 100 points in *Assess XRR quality* |
| r_min | The reflectivity floor: calculated values below it are raised to it, in the curve and in χ² | — | On-screen **R min** in the Chart Info bar, default 10⁻⁷ (`frame_ChartInfo.dfm`; labeled since 2026-09-24, formerly unlabeled and called "Min limit" in the Help). Procedure §6.1 sets it to one count × scale (Chapter 14) |
| one count | One detector count on the curve an `.xrdml` import scales to 1: 1 / (peak rate × counting time) | — | Procedure §1.5; both numbers in the item's description. CoC5: 9.30 × 10⁻⁷ (Chapter 10) |
| λ from the file | Cu Kα with both lines: (Kα1 + r·Kα2)/(1 + r) = 1.541874 Å at r = 0.5; Kα1 = 1.540598 Å behind a monochromator or hybrid mirror | Å | `unit_xrdml.pas:279–299`; written into **λ(Å)** on import. The book's CoC5 numbers use 1.541874 Å from Chapter 10 on (and Chapters 6 and 9 were rerun at it) |
| scale | The factor that puts the measured curve on the reflectivity axis | — | **Data > Normalize (Auto)** (Help *Data*) |
| w | Solved-scale window: the scale may move by a factor of up to (1 + w) from the anchor | — | On-screen **Window** beside **Solve scale in χ²**, default 0.2 (Help *Fitting*) |
| χ² | The cost function as displayed: the weighted mean squared relative residual of log I, × 1000 | — | Help *Fitting* → *Understanding the Cost Function*. The formula is given there; Chapter 9 copies it |
| plain χ² | The same sum with both weights set to 1. It is shown for comparison and never minimized | — | Help *Fitting*. On-screen **plain χ²** |
| PW χ² | Peak weighting: points > 3× the moving average get the weight I/average | — | On-screen **PW χ²** |
| TW χ² | Angle weighting: 1, θ², θ, √θ, 1/θ² or 1/√θ | — | On-screen **TW**. θ here is the chart axis value, so 2θ by default (Help *Fitting*) |
| Min, Max | The fit limits of one parameter. The parameter is fitted only when Min ≠ Max | same as the parameter | **Fitting Limits** dialog, opened with the **Limits** button of the structure panel (`frm_Limits.dfm:9`, `frame_StructurePanel.dfm:212`). The Help calls the button **Set Fit Limits**. The code wins. The dialog's columns are **Hmin**, **Hmax**, **Smin**, **Smax**, **RMin**, **RMax**; the model text's keys are `Hmin` … `Rmax` (Chapters 12, 15) |
| ΔH, Δσ, Δρ | The fractions **Initialize** uses: Min = V(1 − Δ), Max = V(1 + Δ); for ρ the maximum stops at the table's bulk density unless V is above it (X-Ray Calc commit ec5042f) | — | On-screen **ΔH**, **Δσ**, **Δρ** in the **Fitting Limits** dialog (Symbol-font `DH`, `Ds`, `Dr` in `frm_Limits.dfm`), 0.25 each. Chapter 15 |
| p | Polynomial order in Polynomial mode | — | On-screen **Order**, 1 by default (`frame_CalcSettings.dfm`, `edPolyOrder`). The author's practice is 3 (paper §4); the procedure starts at 1 and raises it only by the χ² margin (§9.5, §9.8). Chapter 17 |
| population | Number of particles in the swarm | — | On-screen **Population**. **The book's recommended default is 5000, with 200 iterations** (author, 2026-09-23; the corrected demo projects store the same). On a GPU (on by default: **Use the GPU for fitting when one is available**, `unit_Config.pas`), a fit of this size takes a few seconds (author, 2026-09-23). It is also the author's practice for multilayers (paper §4) |
| iterations | Maximum number of LFPSO iterations | — | On-screen **Iterations**. The recommended default is 200 (see population) |
| seed spread | The sample standard deviation of a fitted parameter across repeated fits | same as the parameter | Procedure §8.4. In the GUI: repeat the fit (OUTLINE open question 3) |
| seed | The start value of the random numbers of one fit. With the **Seed** field blank (the default) the GUI draws a new one for every fit; typing a recorded seed repeats that fit on the same device | — | **Advanced fitting settings**, **General** group, **Seed** (`frm_FitSettings.dfm`); drawn and recorded in `unit_CalcOrchestrator.pas` (`NewFitSeed`), key `seed` of the fit record. The field is not saved with the project (Help *Fitting*). Chapter 9 |
| SeedR | Start the swarm spread over each parameter's whole Min–Max range. Unchecked, or in Polynomial mode, it starts within ±Ksxr of the range around the starting model | — | On-screen **SeedR**, checked by default (Help *Fitting*), grayed out in Polynomial mode (`frame_CalcSettings.pas`, `cbSeedRange.Enabled`). Chapter 9 |
| Vmax, Ksxr | The largest step, and the scatter around a structure, as fractions of each parameter's range | — | **Advanced fitting settings**: **Vmax** 0.3 (**LFPSO** group), **Ksxr** 0.2 (**Polynomial** group, used in every mode). Chapter 9 |
| Jmax, SHmax, k1, k2 | Shake settings: iterations without improvement before a shake; shakes before a return to the best; the lift of the best χ²; the enlargement of Vmax and Ksxr | — | **Advanced fitting settings**, **LFPSO** group: 1, 3, 1.41, 1.41. The 2024 paper swaps the names k1 and k2; the book uses the dialog's. Chapter 9 |
| Tolerance | The fit stops when the best χ² falls below it | — | **Advanced fitting settings**, **General** group, 0.005. The dialog has four group boxes and no tabs (`frm_FitSettings.dfm`). Chapter 9 |
| x, v, b, g, u₁, u₂, c₁, c₂, κ | The particle-swarm step: position, step, best particle of the iteration, best structure so far, random numbers in [0, 1], the pulls (2.05 each), the constriction factor (≈ 0.7298) | — | Chapter 9 Going Deeper only. The Help writes the pulls as φ and κ as χ; the book avoids both (φ is Spiller's angle, χ clashes with χ²) |

## 4. Terms: one word for one thing

| Use | Do not use | Meaning |
|---|---|---|
| **roughness** (σ) | interface width, interfacial roughness, diffuseness | The program's name. Chapter 7 explains that it includes intermixing |
| **period** (D) | bilayer thickness, d-spacing, periodicity | |
| **Bragg order**, **order** | Bragg peak, diffraction peak (except once, to introduce the term) | The m-th maximum of a periodic stack |
| **Kiessig fringe**, **fringe** | oscillation, ripple | The interference maxima of the whole film or stack |
| **critical edge** | critical-angle drop, TER edge | The fall of the curve at θ_c |
| **plateau** | total-reflection region, TER plateau | The flat part below θ_c |
| **starting model** | initial guess, seed model, start model | Procedure §2 |
| **seed** | random state | Only for the start value of a fit's random numbers (Chapter 9). Never for the starting model |
| **fit limits** | bounds, constraints | The program's name. "Bound" may appear in the text when describing one end ("the lower bound") |
| **freeze** / **frozen** | fix, lock (for this action) | Help *Fitting* → *Freezing Parameters*. **Fix** is a different button |
| **density ceiling** | density cap, maximum density | The upper limit of ρ set at the bulk density of the material's table: the one limit with a physical meaning (procedure §7.4, §7.6; Chapter 15) |
| **near-bound rule** | boundary rule | Procedure §7.5: a value on a limit or within 5 % of the range from it is extended and refitted (Chapter 15) |
| **Irregular**, **Periodic**, **Polynomial** mode | profile mode, free mode | The GUI's names. The procedure's "profile mode" = Polynomial |
| **Paired** (the box after a field) | linked, shared, tied | The unlabeled box after the H, σ and ρ field of a layer: ticked holds that parameter at one value in every period (Irregular and Polynomial mode, N > 1; its hint says "paired", `unit_XRCLayerControl.pas:146, 175–184`). The box before the material name is a different control, with the hint "Pair to another layer": an editing aid that keeps the sum of two layers' H while one is edited by hand; no fit reads it and the project doesn't save it (`unit_XRCLayerControl.pas:203–212, 466–475`; X-Ray Calc session 2026-09-25). Chapter 17 |
| **contamination layer** | surface layer, adventitious carbon layer | The light hydrocarbon layer on every surface in air (procedure §2.3) |
| **interlayer** | intermixed zone, diffusion layer | A thin layer at an interface, when the design or the fit adds one |
| **drift** | gradient, grading (for accidental change) | A layer thickness that changes with depth because a deposition rate changed |
| **graded** | drifting | Intended variation with depth (supermirrors, Chapter 22) |
| **undetermined** | uncertain, unreliable | Procedure §10.7: the repeated fits disagree by more than the number would claim. One laboratory's limits: 0.5 Å (H, σ), 0.2 g/cm³ (ρ), 0.1 Å (period). Chapter 18 |
| **order table**, **order ratio** | peak ratio, peak-height ratio | Procedure §10.3: for each visible Bragg order, the calculated peak divided by the measured one, at the chart's (solved) scale. Chapter 18 |
| **edge check**, **fringe check**, **residual by band** | — | Procedure §10.3: the curve checks of a fit besides χ² and the order table. A band mean is the mean of log₁₀(calculated / measured) over one eighth of the fitting range in θ. Chapter 18 |
| **verdict** | assessment, grade | The result of the checks of Chapter 18, written check by check with the calibration of each limit (procedure §10.5, §13 slot 21) |

## 5. Clashes and on-screen quirks

- **N means two things on screen.** In the structure it is the number of periods. In the
  calculation settings it is the number of calculated points. The book writes **N** only for
  periods. For points it writes "the number of points (the **N** field in the calculation
  settings)".
- **Symbol-font captions:** some labels in the `.dfm` files are stored in the Symbol font. `q`
  is shown as θ, `Dq` as Δθ, `2q` as 2θ, `l(A)` as λ(Å), and `q1`/`q2` as θ1/θ2. Quote the label
  as it *appears* on screen.
- **The Henke table editor's molar-mass field** (**Tools > Edit Henke table...**) reads
  **A (g/mol)** from 3.9.4. Earlier versions label it **N (a.u.)**, which is not a number of
  periods or points. Chapter 4 names both.
- **Two hc constants in the code:** the book uses only the engine's 12398.6 eV·Å. The MCP
  server's 12398.42 is not the book's concern (`CLAUDE.md`).

## 6. Abbreviations

| Abbreviation | Meaning | First use |
|---|---|---|
| XRR | X-ray reflectivity | Chapter 1 |
| PMM | Periodic multilayer mirror (the Help and the paper use it) | Chapter 6 |
| LFPSO | Lévy-flight particle swarm optimization, the program's fitting algorithm | Chapter 9 |
| FWHM | Full width at half maximum | Chapter 8 |
| GUI | Graphical user interface. Use it rarely: "the program" or "X-Ray Calc" reads better | Chapter 2 |

Not used in the book: MCP, TER, GIXR, GIXRR, XRD (except once, to explain that XRR is not XRD),
and nm.

## 7. Number formats

- Decimal point, never a comma.
- No e-notation (STYLE.md §6).
- **Numbers keep the precision of their source.** Do not round an angle read from the program.
  Do not add digits to a value from a paper.
- **Ranges use an en-dash with no spaces:** 0.012–0.015°, 3–5 Å.
