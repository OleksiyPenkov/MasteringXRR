#!/usr/bin/env node
/**
 * Post-build integrity checks over `dist/`.
 *
 * Copied from the Vacuum book, where it was reimplemented three times before
 * being committed. It exists because three defect classes are invisible to the
 * build:
 *
 *  1. An internal link to a page that does not exist, or — far more common — a
 *     `#fragment` that matches no `id` on the destination page. Astro's heading
 *     slugs are generated, and KaTeX inside a heading mangles them, so a
 *     hand-written fragment is a guess until something checks it. The reader
 *     lands at the top of an 800-line page and nothing anywhere reports it.
 *  2. A literal `$$` surviving into the HTML, or a display equation that never
 *     became `.katex-display`. A single-line `$$…$$` is parsed as *inline* math:
 *     it typesets, the build says Complete, and the equation sits in the middle
 *     of its paragraph.
 *  3. Reader-visible e-notation (`1.4e-5`), which the house style forbids.
 *     `<code>`, `<script>` and `<style>` are stripped first: island props and
 *     inline CSS hex colors are not reader-visible numbers.
 *
 * Usage:  node scripts/check-links.mjs [distDir]
 * Exits non-zero on any failure, and prints the counts the handoff gates on.
 */
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join, relative, resolve } from 'node:path';
import { BASE } from '../src/lib/site.mjs';

const DIST = resolve(process.argv[2] ?? 'dist');

function htmlFiles(dir) {
  const out = [];
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry);
    if (statSync(full).isDirectory()) out.push(...htmlFiles(full));
    else if (entry.endsWith('.html')) out.push(full);
  }
  return out;
}

/** `dist/ch4-.../index.html` -> `${BASE}/ch4-.../` */
function routeOf(file) {
  const rel = relative(DIST, file).split(/[\\/]/).join('/');
  const withoutIndex = rel.replace(/(^|\/)index\.html$/, '$1');
  return `${BASE}/${withoutIndex}`.replace(/\/+$/, '/');
}

/** Normalize a route for comparison: always exactly one trailing slash. */
const norm = (r) => (r.endsWith('/') ? r : `${r}/`);

const files = htmlFiles(DIST);
if (files.length === 0) {
  console.error(`No HTML found under ${DIST}. Run \`npm run build\` first.`);
  process.exit(1);
}

// ── Pass 1: what exists ────────────────────────────────────────────────────
const idsByRoute = new Map();
for (const file of files) {
  const html = readFileSync(file, 'utf8');
  const ids = new Set();
  for (const m of html.matchAll(/\sid="([^"]+)"/g)) ids.add(m[1]);
  idsByRoute.set(norm(routeOf(file)), ids);
}

// ── Pass 2: every internal link resolves, fragment included ────────────────
const failures = [];
let linkCount = 0;

for (const file of files) {
  const html = readFileSync(file, 'utf8');
  const here = norm(routeOf(file));

  for (const m of html.matchAll(/\shref="([^"]+)"/g)) {
    const href = m[1];
    if (/^(https?:|mailto:|tel:|data:|#)/.test(href)) {
      // Same-page fragment: still checkable.
      if (href.startsWith('#')) {
        linkCount++;
        const id = decodeURIComponent(href.slice(1));
        if (id && !idsByRoute.get(here)?.has(id)) {
          failures.push(`${here} -> ${href} : no element with that id on this page`);
        }
      }
      continue;
    }
    if (!href.startsWith(BASE)) continue; // off-site or non-base path
    // An asset reference (`…/_astro/textbook.D90JqVj6.css`), not a page route.
    if (/\.[a-z0-9]+$/i.test(href.split('#')[0])) continue;

    linkCount++;
    const [pathPart, fragment] = href.split('#');
    const target = norm(pathPart);
    const ids = idsByRoute.get(target);
    if (!ids) {
      failures.push(`${here} -> ${href} : no such page in dist`);
      continue;
    }
    if (fragment && !ids.has(decodeURIComponent(fragment))) {
      failures.push(`${here} -> ${href} : page exists but has no id="${fragment}"`);
    }
  }
}

// ── Pass 3: display math and number format ────────────────────────────────
const stripped = (html) =>
  html
    .replace(/<script[\s\S]*?<\/script>/g, '')
    .replace(/<style[\s\S]*?<\/style>/g, '')
    .replace(/<code[\s\S]*?<\/code>/g, '')
    // Svelte island hydration props are data the component reads, never text a
    // reader sees, and may correctly hold JS literals such as `1e-7`.
    .replace(/<astro-island[\s\S]*?>/g, '');

let katexDisplay = 0;
const dollarPages = [];
const enotationHits = [];

for (const file of files) {
  const html = readFileSync(file, 'utf8');
  katexDisplay += (html.match(/katex-display/g) ?? []).length;

  const text = stripped(html);
  if (text.includes('$$')) dollarPages.push(routeOf(file));

  // A digit, optional decimals, then e/E with a signed exponent — the house
  // style forbids this anywhere a reader sees it.
  for (const m of text.matchAll(/\b\d+(?:\.\d+)?[eE][-+]?\d+\b/g)) {
    enotationHits.push(`${routeOf(file)} : ${m[0]}`);
  }
}

// ── Report ────────────────────────────────────────────────────────────────
console.log(`pages:            ${files.length}`);
console.log(`internal links:   ${linkCount}`);
console.log(`katex-display:    ${katexDisplay}`);
console.log(`literal $$:       ${dollarPages.length} page(s)`);
console.log(`e-notation:       ${enotationHits.length} hit(s)`);

let failed = false;
if (failures.length) {
  failed = true;
  console.error(`\n${failures.length} broken internal link(s):`);
  for (const f of failures) console.error(`  ${f}`);
}
if (dollarPages.length) {
  failed = true;
  console.error(`\nLiteral $$ survived into HTML on:`);
  for (const p of dollarPages) console.error(`  ${p}`);
}
if (enotationHits.length) {
  failed = true;
  console.error(`\nReader-visible e-notation:`);
  for (const h of enotationHits) console.error(`  ${h}`);
}

if (failed) process.exit(1);
console.log('\nOK — every internal link and fragment resolves, no literal $$, no e-notation.');
