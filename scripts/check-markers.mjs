#!/usr/bin/env node
/**
 * Release gate: no author-gap marker may remain in the manuscript.
 *
 * STYLE.md §5: a missing number, cause, mechanism or source is marked, never
 * filled - [NUMBER NEEDED], [INTERPRETATION NEEDED], [MECHANISM NEEDED],
 * [SOURCE NEEDED]. The markers are how a draft stays honest, so they must be
 * allowed while drafting; this check is therefore NOT part of `npm run build`.
 * Run it before a release: `npm run check:markers`. It lists every marker with
 * its file and line, and exits 1 if there are any.
 *
 * Usage: node scripts/check-markers.mjs [contentDir]
 */
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

// LINK NEEDED marks a cross-reference to a chapter that is not written yet. It
// sits in an MDX comment ({/* [LINK NEEDED] */}) after the plain-text chapter
// title, so the reader sees no marker while the release gate still finds it.
export const MARKERS = ['NUMBER NEEDED', 'INTERPRETATION NEEDED', 'MECHANISM NEEDED', 'SOURCE NEEDED', 'LINK NEEDED'];
const MARKER_RE = new RegExp(`\\[(${MARKERS.join('|')})\\]`, 'g');

/** Every marker in one file's text, as { line, marker }. Pure, for the test. */
export function findMarkers(text) {
  const hits = [];
  text.split(/\r?\n/).forEach((line, i) => {
    for (const m of line.matchAll(MARKER_RE)) hits.push({ line: i + 1, marker: m[1] });
  });
  return hits;
}

function mdxFiles(dir) {
  const out = [];
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry);
    if (statSync(full).isDirectory()) out.push(...mdxFiles(full));
    else if (/\.mdx?$/.test(entry)) out.push(full);
  }
  return out;
}

function main() {
  const dir = resolve(process.argv[2] ?? 'src/content/chapters');
  let total = 0;
  for (const file of mdxFiles(dir)) {
    for (const { line, marker } of findMarkers(readFileSync(file, 'utf8'))) {
      console.log(`${relative(process.cwd(), file)}:${line}  [${marker}]`);
      total++;
    }
  }
  console.log(`\n${total} marker(s) left.`);
  if (total > 0) process.exit(1);
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main();
