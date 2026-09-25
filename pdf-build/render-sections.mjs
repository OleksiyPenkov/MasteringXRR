// Renders each page of the book from the running `astro preview` server to a
// print-ready, single-section PDF. Ported from the Vacuum book's renderer and
// trimmed: that book's quizzes, YouTube embeds and two-volume split are gone.
// What it does to each page before printing:
//   - removes the web chrome (top bar, sidebar nav, prev/next footer)
//   - removes every :::web-only block and shows every :::print-only block
//     (src/lib/remark-output-directives.mjs), then ASSERTS both, so a change
//     to the mechanism cannot silently print the wrong half
//   - opens every <details> (Going Deeper collapses on the web)
//   - keeps interactive widgets that draw a plot as static snapshots, and
//     drops pure control->readout widgets, which mean nothing on paper
//   - shrinks a table's type (never below 8pt) only when its columns cannot
//     fit the page, and reports every such table
//
// Usage: node pdf-build/render-sections.mjs [baseUrl] [outDir] [slug,slug,...]
//   baseUrl defaults to the preview server from src/lib/site.mjs.
//   The slug list renders a subset. `sampler` (src/pages/sampler.mdx, not part
//   of the book) may be named there to test the pipeline on every component.
//
// Emits <outDir>/manifest.json describing the sections rendered, in order.

import { chromium } from '@playwright/test';
import { mkdirSync, readdirSync, writeFileSync, rmSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';
import { collectPrintBoxCandidates, judgePrintBox } from './print-box.mjs';
import { BASE, PORT } from '../src/lib/site.mjs';

const __dirname = dirname(fileURLToPath(import.meta.url));

const baseUrl = (process.argv[2] || `http://localhost:${PORT}${BASE}`).replace(/\/$/, '');
const outDir = resolve(process.argv[3] || resolve(__dirname, 'out'));
mkdirSync(outDir, { recursive: true });

// The one non-book page the renderer knows. Rendered only when asked for.
const SAMPLER = { slug: 'sampler', title: 'Component sampler', number: '', label: '', order: 999, part: 'back', partHeading: 'Test page' };

// The printed content box, in CSS pixels, measured in the Vacuum book: a
// `width:100%` bar printed to A5 with these margins is 386.25pt, and
// 386.25 / 0.75 = 515. (Chrome quantises the 6mm margin to 23 CSS px.)
// transform() sizes tables against it and assertFitsPrintBox() gates on it.
const PRINT_BOX_PX = 515;

// Injected into every page, regardless of media, so it also governs the PDF pass.
// Every rule here is a Vacuum-book rule that fixed a defect it actually shipped;
// the reasons are kept short. pdf-build/README.md points at the long versions.
const PRINT_CSS = `
  @page { size: A5; margin: 12mm 6mm; }
  html, body { background: #fff !important; }
  .topbar, .sidebar, .chapter-footer { display: none !important; }
  .shell { display: block !important; }
  .chapter { max-width: none !important; padding: 0 6mm !important; line-height: 1.35 !important; }
  /* Print body in the site's own face, pure black, 10.5pt (the Vacuum book's
     e-ink reading call). Heading sizes are absolute by design. */
  body { font-size: 10.5pt; line-height: 1.35; font-family: 'Segoe UI', Arial, sans-serif; font-weight: 400; color: #000; }
  .chapter h1 { font-size: 18pt; }
  .chapter h2 { font-size: 14pt; }
  .chapter h3 { font-size: 12pt; }

  /* One source, two outputs. transform() also removes .web-only outright. */
  .print-only { display: block !important; }
  span.print-only { display: inline !important; }
  .web-only { display: none !important; }

  /* Atomic blocks. Figures stay whole: breaking them was tried in the Vacuum
     book and orphaned five captions. */
  figure, .in-this-chapter { break-inside: avoid; page-break-inside: avoid; }
  h1, h2, h3 { break-after: avoid; page-break-after: avoid; }
  /* A tall callout may break (kept whole, it strands its lead-in sentence and
     leaves half a page blank); its title may not be separated from its body. */
  .box { break-inside: auto; page-break-inside: auto; }
  .box .box-title { break-after: avoid; page-break-after: avoid; }
  /* A display equation is atomic wherever it appears. */
  .katex-display, .katex-display > .katex { break-inside: avoid; page-break-inside: avoid; }
  .chapter p, .box p, .box li { orphans: 2; widows: 2; }
  /* Tables break between rows, with the header repeated; a row never splits. */
  .chapter table, .data-table { break-inside: auto; page-break-inside: auto; }
  .chapter thead, .data-table thead {
    display: table-header-group;
    break-inside: avoid; page-break-inside: avoid; break-after: avoid; page-break-after: avoid;
  }
  .chapter tr, .data-table tr { break-inside: avoid; page-break-inside: avoid; }

  /* Figures and tables bleed into the .chapter padding: 136mm against the
     124mm text column, still inside the printable box. */
  .figure-svg svg { max-width: 136mm !important; }
  .figure { margin-left: -6mm !important; margin-right: -6mm !important; }
  .chapter table, .data-table {
    width: 136mm !important; max-width: 136mm !important;
    margin-left: -6mm !important; margin-right: -6mm !important;
  }
  /* ...except inside a callout, where the bleed would run past the page box. */
  .box table, .box .data-table {
    width: 100% !important; max-width: 100% !important;
    margin-left: 0 !important; margin-right: 0 !important;
  }
  img, svg, canvas { max-width: 100% !important; }
  /* KaTeX sets display math nowrap, which overflows the page and makes Chrome
     shrink the whole section. Let it break where KaTeX already splits it. */
  .katex-display > .katex { white-space: normal !important; }
  a { color: #1a5276; }

  /* Collapsibles are forced open; drop the web disclosure arrow. */
  .box-collapsible > summary.box-title { cursor: auto; }
  .box-collapsible > summary.box-title::after { content: none !important; }
  .box-collapsible[open] > summary.box-title { margin-bottom: .4rem; }
  /* The Sources section is a <details> on the web (rehype-collapse-sources). */
  .sources-section > summary { cursor: auto; }
  .sources-section > summary > h2::after { content: none !important; }
  /* The figure viewer never prints. */
  dialog.figzoom { display: none !important; }

  /* Inline code: no padding or background in print (it pushed punctuation
     away from the span), and a long URL may wrap rather than overflow. */
  code { background: none; padding: 0; border-radius: 0; overflow-wrap: anywhere; word-break: break-word; }
`;

async function autoScroll(page) {
  // Walk the page top to bottom so client:visible islands hydrate and draw.
  await page.evaluate(async () => {
    await new Promise((res) => {
      let y = 0;
      const timer = setInterval(() => {
        window.scrollTo(0, y);
        y += 400;
        if (y >= document.body.scrollHeight + window.innerHeight) {
          clearInterval(timer);
          res();
        }
      }, 60);
    });
    window.scrollTo(0, 0);
  });
}

/** In-place print transform. Returns { shrunkTables, output } for the caller. */
async function transform(page) {
  return page.evaluate(({ PRINT_BOX_PX }) => {
    // 1) One source, two outputs: the web half goes, the print half shows.
    const webOnly = document.querySelectorAll('.web-only').length;
    document.querySelectorAll('.web-only').forEach((el) => el.remove());

    // 1b) Same-page links ("see Figure 4-1", href="#fig-4-1"). Chrome prints them
    //     as named-destination links, and the page merge in assemble.py drops
    //     named destinations - so every in-chapter reference vanished from the
    //     book with nothing failing. Rewritten as URLs they print as URI links,
    //     which links.py resolves to a page like any cross-chapter reference.
    //     The `?xref` is required, measured: Chrome recognises an absolute URL
    //     to the SAME document and still emits a named destination for it.
    //     links.py ignores the query.
    document.querySelectorAll('article a[href^="#"]').forEach((a) => {
      a.setAttribute('href', `${location.origin}${location.pathname}?xref${a.getAttribute('href')}`);
    });

    // 2) Every <details> open: a closed one hides its body on paper.
    document.querySelectorAll('details').forEach((d) => { d.open = true; });

    // 3) Widgets: keep a drawn plot, drop dead controls; drop a widget that is
    //    only controls and readouts.
    document.querySelectorAll('.widget').forEach((w) => {
      if (w.querySelector('canvas, svg')) {
        w.querySelectorAll('label.slider, input, select, button').forEach((el) => el.remove());
      } else {
        (w.closest('astro-island') || w).remove();
      }
    });

    // 4) Tables whose columns cannot fit: first drop cell padding, then step the
    //    type down, never below 8pt. Never word-break, which splits words.
    const MM_PX = 96 / 25.4;
    const FLOOR_PX = 8 / 0.75;
    const shrunkTables = [];
    document.querySelectorAll('.chapter table, .data-table').forEach((t) => {
      let avail;
      if (t.closest('.box')) {
        let inset = 0;
        for (let p = t.parentElement; p; p = p.parentElement) {
          const cs = getComputedStyle(p);
          inset += parseFloat(cs.paddingLeft) + parseFloat(cs.paddingRight)
                 + parseFloat(cs.borderLeftWidth) + parseFloat(cs.borderRightWidth);
          if (p.classList.contains('chapter')) break;
        }
        avail = PRINT_BOX_PX - inset;
      } else {
        avail = 136 * MM_PX;
      }
      // The print CSS pins width with !important, so the probe must too.
      const minWidth = () => {
        const w = t.style.getPropertyValue('width'), wp = t.style.getPropertyPriority('width');
        const m = t.style.getPropertyValue('max-width'), mp = t.style.getPropertyPriority('max-width');
        t.style.setProperty('width', 'min-content', 'important');
        t.style.setProperty('max-width', 'none', 'important');
        const px = t.getBoundingClientRect().width;
        t.style.removeProperty('width');
        t.style.removeProperty('max-width');
        if (w) t.style.setProperty('width', w, wp);
        if (m) t.style.setProperty('max-width', m, mp);
        return px;
      };
      const naturalMin = minWidth();
      if (naturalMin <= avail) return;
      const cells = [...t.querySelectorAll('th, td')];
      cells.forEach((c) => { c.style.paddingLeft = '4px'; c.style.paddingRight = '4px'; });
      const base = cells.map((c) => parseFloat(getComputedStyle(c).fontSize));
      const smallest = Math.min(...base);
      let k = 1;
      for (let i = 0; i < 12; i++) {
        const min = minWidth();
        if (min <= avail) break;
        const next = k * Math.min(0.98, avail / min);
        if (smallest * next < FLOOR_PX) break;
        k = next;
        cells.forEach((c, j) => { c.style.fontSize = `${base[j] * k}px`; });
      }
      if (k < 1) {
        const head = (t.querySelector('tr')?.textContent || '').replace(/\s+/g, ' ').trim();
        shrunkTables.push({ min: naturalMin, avail, pt: smallest * k * 0.75, head: head.slice(0, 50) });
      }
    });

    // 5) What the output-conditional content looks like now, for the gate.
    const printOnly = [...document.querySelectorAll('.print-only')];
    const output = {
      webOnlyRemoved: webOnly,
      webOnlyLeft: document.querySelectorAll('.web-only').length,
      printOnly: printOnly.length,
      printOnlyHidden: printOnly.filter((el) => getComputedStyle(el).display === 'none').length,
    };
    return { shrunkTables, output };
  }, { PRINT_BOX_PX });
}

// Gate: no section may be wider than the printed content box. Chrome's
// printToPDF shrink-to-fits a WHOLE section the moment one element overflows,
// so one wide table reprints every label in that chapter smaller - a defect the
// Vacuum book shipped in 23 of 30 sections before this existed. Run AFTER
// page.pdf(): the measurement resizes the viewport.
async function assertFitsPrintBox(page, slug) {
  await page.setViewportSize({ width: PRINT_BOX_PX, height: 1400 });
  await page.emulateMedia({ media: 'print' });
  await page.waitForTimeout(250);
  const measured = await page.evaluate(collectPrintBoxCandidates, PRINT_BOX_PX);
  await page.setViewportSize({ width: 1100, height: 1400 });
  await page.emulateMedia({ media: null });
  const verdict = judgePrintBox({ boxPx: PRINT_BOX_PX, ...measured });
  return verdict.ok ? null : { slug, ...verdict };
}

async function main() {
  const secRes = await fetch(`${baseUrl}/sections.json`).catch((e) => {
    throw new Error(`Cannot reach ${baseUrl}/sections.json (${e.cause?.code ?? e.message}). Is \`npm run preview\` running?`);
  });
  if (!secRes.ok) throw new Error(`Cannot fetch ${baseUrl}/sections.json (HTTP ${secRes.status}).`);
  const ALL_SECTIONS = await secRes.json();

  // A slug list renders a subset. An unknown slug is fatal: a typo would
  // otherwise silently produce a shorter book than asked for.
  const wanted = (process.argv[4] || '').split(',').map((t) => t.trim()).filter(Boolean);
  const known = new Map([...ALL_SECTIONS, SAMPLER].map((s) => [s.slug, s]));
  const missing = wanted.filter((t) => !known.has(t));
  if (missing.length) {
    throw new Error(`Unknown slug(s): ${missing.join(', ')}\nKnown: ${[...known.keys()].join(', ')}`);
  }
  const SECTIONS = wanted.length ? wanted.map((t) => known.get(t)).sort((a, b) => a.order - b.order) : ALL_SECTIONS;
  console.log(wanted.length
    ? `Subset: ${SECTIONS.length} page(s) (${wanted.join(', ')})`
    : `Whole book: ${SECTIONS.length} page(s)`);

  // A stale manifest is a loaded gun: assemble.py after a FAILED render would
  // find the previous run's manifest and build a book from it. Remove it now,
  // write it only when every section has passed.
  const manifestPath = resolve(outDir, 'manifest.json');
  rmSync(manifestPath, { force: true });
  // Old section PDFs go too, so out/ only ever holds this run's pages.
  for (const f of readdirSync(outDir)) {
    if (/^\d{3}-.+\.pdf$/.test(f)) rmSync(resolve(outDir, f), { force: true });
  }

  const browser = await chromium.launch();
  const context = await browser.newContext({ viewport: { width: 1100, height: 1400 }, deviceScaleFactor: 2 });
  const page = await context.newPage();

  // Hermetic: every request that leaves the preview server is aborted, so the
  // PDF never depends on a third party being reachable.
  const host = new URL(baseUrl).host;
  await page.route('**/*', (route) =>
    (new URL(route.request().url()).host === host ? route.continue() : route.abort()));

  const manifest = [];
  const overflows = [];
  const outputFaults = [];
  for (const sec of SECTIONS) {
    process.stdout.write(`Rendering ${sec.slug} ... `);
    await page.goto(`${baseUrl}/${sec.slug}/`, { waitUntil: 'networkidle', timeout: 60000 });
    await autoScroll(page);
    await page.evaluate(() => document.fonts && document.fonts.ready);
    await page.waitForTimeout(500);
    await page.addStyleTag({ content: PRINT_CSS });
    const { shrunkTables, output } = await transform(page);
    await page.waitForTimeout(200);

    if (output.webOnlyLeft || output.printOnlyHidden) {
      outputFaults.push(`${sec.slug}: ${output.webOnlyLeft} web-only left, ${output.printOnlyHidden} print-only hidden`);
    }

    const file = `${String(sec.order).padStart(3, '0')}-${sec.slug}.pdf`;
    await page.pdf({
      path: resolve(outDir, file),
      format: 'A5',
      printBackground: true,
      margin: { top: '12mm', bottom: '12mm', left: '6mm', right: '6mm' },
    });
    manifest.push({ ...sec, file });

    const over = await assertFitsPrintBox(page, sec.slug);
    if (over) {
      overflows.push(over);
      const w = over.worst;
      process.stdout.write(
        `${over.clipped.length ? 'CLIPPED OVERFLOW' : 'OVERFLOW'} ${over.scrollWidth}px vs ${PRINT_BOX_PX}px `
        + `(would print at scale ${over.scale.toFixed(4)})\n`
        + (w ? `      widest: ${w.chain}  right=${w.right}px  "${w.text}"\n` : ''));
    } else {
      process.stdout.write(`ok (web-only removed: ${output.webOnlyRemoved}, print-only shown: ${output.printOnly})\n`);
    }
    for (const t of shrunkTables) {
      console.warn(`      note: table type reduced to ${t.pt.toFixed(1)}pt to fit ${t.avail.toFixed(0)}px `
        + `(min-content was ${t.min.toFixed(0)}px) - "${t.head}"`);
    }
  }
  await browser.close();

  // Every section is measured before anything is reported, so one run names
  // all the offenders.
  let failed = false;
  if (outputFaults.length) {
    failed = true;
    console.error(`\nThe print/web split did not apply:\n  ${outputFaults.join('\n  ')}`);
  }
  if (overflows.length) {
    failed = true;
    console.error(`\n${overflows.length} of ${manifest.length} sections do not fit the ${PRINT_BOX_PX}px print box.\n`
      + 'Unclipped overflow shrinks that whole section; clipped overflow cuts text off at the margin.\n'
      + 'Fix the elements named above. Do not hide them behind overflow:hidden.\n  '
      + overflows.map((o) => `${o.slug}: ${o.scrollWidth}px, scale ${o.scale.toFixed(4)}`).join('\n  '));
  }
  if (failed) {
    console.error('\nNo manifest.json was written, so assemble.py cannot build a book from this run.');
    process.exit(1);
  }
  writeFileSync(manifestPath, JSON.stringify(manifest, null, 2));
  console.log(`\nRendered ${manifest.length} page(s) to ${outDir}; all fit the print box (scale 1.000).`);
}

main().catch((e) => { console.error(e.message ?? e); process.exit(1); });
