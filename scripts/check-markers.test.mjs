import { describe, expect, it } from 'vitest';
import { findMarkers, MARKERS } from './check-markers.mjs';

describe('findMarkers', () => {
  it('finds each marker (STYLE.md §5 plus LINK NEEDED), with its line', () => {
    const text = MARKERS.map((m) => `text [${m}] text`).join('\n');
    expect(findMarkers(text)).toEqual(MARKERS.map((marker, i) => ({ line: i + 1, marker })));
  });

  it('finds two markers on one line', () => {
    expect(findMarkers('[NUMBER NEEDED] and [SOURCE NEEDED]')).toHaveLength(2);
  });

  it('finds a LINK NEEDED marker inside an MDX comment', () => {
    expect(findMarkers('Chapter 10: Is This Curve Worth Fitting? {/* [LINK NEEDED] */}')).toEqual([
      { line: 1, marker: 'LINK NEEDED' },
    ]);
  });

  it('ignores the words without brackets, and unknown bracketed text', () => {
    expect(findMarkers('a number needed here, [TODO], [NUMBER]')).toEqual([]);
  });
});
