# Mastering XRR Fitting

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22959661.svg)](https://doi.org/10.5281/zenodo.22959661)

A free book on fitting an X-ray reflectivity (XRR) curve, from reading the raw curve to reporting
the fit. It is written for a graduate student or engineer who has an XRR curve and has never fitted
one, and it is built around one program, [X-Ray Calc 3](https://github.com/OleksiyPenkov/X-RayCalc3).
Every step is something you do in that program.

**Read it online:** https://oleksiypenkov.github.io/MasteringXRR/

**Download the PDF:** [Mastering-XRR-Fitting.pdf](https://github.com/OleksiyPenkov/MasteringXRR/releases/latest/download/Mastering-XRR-Fitting.pdf)
(the latest release; earlier editions are on the [Releases](https://github.com/OleksiyPenkov/MasteringXRR/releases) page)

The book is written for X-Ray Calc 3.9.4. Its fitting method is the laboratory procedure described in
Penkov, Peng & Fu, *Teaching an LLM agent to fit XRR curves with X-Ray Calc 3*,
[arXiv:2609.28926](https://arxiv.org/abs/2609.28926); the procedure and its data are deposited at
[doi:10.5281/zenodo.22851595](https://doi.org/10.5281/zenodo.22851595).

## How to cite

> Penkov, O. (2026). *Mastering XRR Fitting: Fitting X-Ray Reflectivity Curves with X-Ray Calc 3*.
> https://doi.org/10.5281/zenodo.22959661

This DOI always resolves to the latest edition. To cite one edition (for a page or figure number),
use that version's DOI from the [Zenodo record](https://doi.org/10.5281/zenodo.22959661).

## What is in this repository

- `src/content/chapters/`: the chapters, one MDX file each. This is the only source of the text.
- `src/components/`, `src/layouts/`, `src/lib/`: the site (Astro, with KaTeX for the equations) and
  the few calculations it shows, with their unit tests.
- `public/figures/`: the figures as the book shows them. `figures-src/` holds the data behind them,
  and `scripts/figures/` the scripts that computed and drew them.
- `pdf-build/`: the print edition, rendered from the running site.

## Build the web edition

Node 20.19 or newer.

```sh
npm ci
npm run dev          # http://localhost:4331/MasteringXRR/
npm test             # unit tests
npm run build        # static site in dist/
npm run check:links  # every internal link and #fragment in dist/
```

## Build the PDF

With `npm run preview` running (Python 3 with PyMuPDF, pypdf and BeautifulSoup, and a Playwright Chromium):

```sh
npm run pdf:render
npm run pdf:assemble
npm run pdf:verify
```

`pdf-build/README.md` describes the stages and the checks.

## Rerun the figure scripts

The scripts in `scripts/figures/` call the command-line server that ships with X-Ray Calc 3 and read
the measured curves from the procedure's Zenodo deposit. Tell them where these are, either with
environment variables or with a `local-paths.json` at the repository root (not committed):

```json
{
  "XRC_MCP_EXE": "C:/path/to/a/copy/of/X-Ray Calc 3/XRC_MCP.exe",
  "XRC_DEPLOY": "C:/path/to/X-Ray Calc 3",
  "XRR_DEPOSIT": "C:/path/to/the/unzipped/deposit"
}
```

`scripts/figures/local_paths.py` lists every key. The outputs the book uses are already in
`figures-src/` and `public/figures/`, so the site builds without any of this.

## Licence

The text, figures and data are under [CC BY 4.0](LICENSE-CONTENT.md); the code is under the
[MIT licence](LICENSE).
