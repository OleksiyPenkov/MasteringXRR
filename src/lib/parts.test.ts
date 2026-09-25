import { describe, expect, it } from 'vitest';
import { PART_KEYS, PARTS, pageEyebrow, pageLabel, partHeading, partNavLabel } from './parts';

describe('parts', () => {
  it('names every key exactly once, in reading order', () => {
    expect(PARTS.map((p) => p.key)).toEqual([...PART_KEYS]);
  });

  it('prefixes numbered Parts and leaves front and back matter bare', () => {
    expect(partHeading('3')).toBe('Part 3: The Fitting Workflow, Step by Step');
    expect(partHeading('back')).toBe('Appendices');
    expect(partNavLabel('5')).toBe('Part 5');
    expect(partNavLabel('front')).toBe('Front Matter');
  });

  it('labels chapters by number and appendices by letter', () => {
    expect(pageLabel('')).toBe('');
    expect(pageLabel('12')).toBe('Chapter 12');
    expect(pageLabel('B')).toBe('Appendix B');
  });

  it('builds the eyebrow from both', () => {
    expect(pageEyebrow('2', '4')).toBe('Part 2 · Chapter 4');
    expect(pageEyebrow('back', 'A')).toBe('Appendices · Appendix A');
    expect(pageEyebrow('front', '')).toBe('Front Matter');
  });

  it('uses no em-dash, which the house style bans (STYLE.md §4.2)', () => {
    for (const p of PARTS) expect(partHeading(p.key)).not.toContain('—');
  });
});
