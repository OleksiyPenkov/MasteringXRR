// Renders a local HTML file to PDF via Chromium. Used for the generated cover
// and table-of-contents pages (no server needed: loaded over file://).
//
// Usage: node render-html.mjs <input.html> <output.pdf>

import { chromium } from '@playwright/test';
import { pathToFileURL } from 'node:url';
import { resolve } from 'node:path';

const input = resolve(process.argv[2]);
const output = resolve(process.argv[3]);

const browser = await chromium.launch();
const page = await browser.newPage({ deviceScaleFactor: 2 });
await page.goto(pathToFileURL(input).href, { waitUntil: 'networkidle' });
await page.evaluate(() => document.fonts && document.fonts.ready);
await page.pdf({
  path: output,
  format: 'A5',
  printBackground: true,
  margin: { top: '0mm', bottom: '0mm', left: '0mm', right: '0mm' },
});
await browser.close();
console.log(`Rendered ${input} -> ${output}`);
