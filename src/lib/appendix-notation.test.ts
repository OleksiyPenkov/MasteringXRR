import { describe, it, expect } from 'vitest';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

// Appendix A is written from NOTATION.md §3, which stays canonical. This test fails when a
// symbol is added to NOTATION §3 and not to the appendix (scripts/appendix/make_appendix_a.py).

const root = resolve(__dirname, '..', '..');
const notation = readFileSync(resolve(root, 'NOTATION.md'), 'utf-8');
const appendix = readFileSync(resolve(root, 'src/content/chapters/appendix-a-notation.mdx'), 'utf-8')
  .replace(/<sub>(.*?)<\/sub>/g, '_$1');

function section3Symbols(md: string): string[] {
  const start = md.indexOf('## 3. Symbols');
  const end = md.indexOf('## 4.', start);
  const rows = md.slice(start, end).split('\n').filter((l) => l.startsWith('| ') && !l.startsWith('| Symbol'));
  const out: string[] = [];
  for (const row of rows) {
    const first = row.split('|')[1].trim().replace(/\*\*/g, '');
    for (const piece of first.split(', ')) {
      const p = piece.trim();
      if (p && p !== '…' && !/^-+$/.test(p)) out.push(p);
    }
  }
  return out;
}

describe('Appendix A against NOTATION.md §3', () => {
  const symbols = section3Symbols(notation);

  it('finds the symbols of NOTATION §3', () => {
    expect(symbols.length).toBeGreaterThan(50);
  });

  it.each(symbols)('has %s', (s) => {
    expect(appendix.includes(`<td>${s}`) || appendix.includes(`, ${s}`)).toBe(true);
  });
});
