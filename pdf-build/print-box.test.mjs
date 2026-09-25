import { describe, it, expect } from 'vitest';
import { judgePrintBox, OVERFLOW_EPS } from './print-box.mjs';

const BOX = 515;

/** A measured box, with sane defaults so each test states only what it is about. */
function box(over) {
  return {
    tag: 'div', right: BOX, width: 100, height: 20,
    clipped: false, katexGlyph: false, depth: 5, chain: 'div', text: '',
    ...over,
  };
}

const judge = (candidates, scrollWidth = BOX) =>
  judgePrintBox({ boxPx: BOX, scrollWidth, candidates });

describe('judgePrintBox', () => {
  it('passes a section whose content fits', () => {
    const r = judge([box({ right: 400 }), box({ right: 515 })]);
    expect(r.ok).toBe(true);
    expect(r.scale).toBe(1);
    expect(r.worst).toBeNull();
  });

  it('fails when the document scrolls wider than the box', () => {
    const r = judge([box({ right: 636, text: 'a long equation' })], 636);
    expect(r.ok).toBe(false);
    expect(r.scale).toBeCloseTo(515 / 636, 6);
    expect(r.visible).toHaveLength(1);
    expect(r.worst.text).toBe('a long equation');
  });

  it('reports the scale Chrome would apply, which is what corrupts the type size', () => {
    // 515/851 was Appendix A before the fix: 11pt body printed at 6.7pt.
    expect(judge([], 851).scale).toBeCloseTo(0.6052, 4);
  });

  it('never reports a scale above 1 for a section that under-fills the box', () => {
    expect(judge([], 300).scale).toBe(1);
  });

  // --- the hole this function was extracted to close ------------------------

  it('FAILS a clipped element that overflows, even though scrollWidth is clean', () => {
    // `.katex-display { overflow-x: hidden }` removes the overflow from
    // scrollWidth while the equation still prints truncated at the margin.
    // Before this, the gate said "all 30 sections fit" in exactly that case.
    const r = judge([box({ right: 851, clipped: true, text: 'truncated equation' })], BOX);
    expect(r.ok).toBe(false);
    expect(r.clipped).toHaveLength(1);
    expect(r.visible).toHaveLength(0);
    expect(r.worst.text).toBe('truncated equation');
  });

  it('separates clipped from unclipped overflow, because the fixes differ', () => {
    const r = judge([
      box({ right: 600, text: 'pushes the page' }),
      box({ right: 700, clipped: true, text: 'silently cut off' }),
    ], 600);
    expect(r.visible.map((c) => c.text)).toEqual(['pushes the page']);
    expect(r.clipped.map((c) => c.text)).toEqual(['silently cut off']);
    expect(r.ok).toBe(false);
  });

  it('still fails on clipped overflow when nothing is visibly overflowing', () => {
    const r = judge([box({ right: 2000, clipped: true })], BOX);
    expect(r.ok).toBe(false);
  });

  // --- the one deliberate exemption ----------------------------------------

  it('exempts KaTeX stretchy glyphs, which are meant to be cropped', () => {
    const r = judge([box({ right: 7320, clipped: true, katexGlyph: true, tag: 'svg' })], BOX);
    expect(r.ok).toBe(true);
    expect(r.clipped).toHaveLength(0);
    expect(r.visible).toHaveLength(0);
  });

  it('does not let the KaTeX exemption cover an unclipped overflow either', () => {
    // Belt and braces: the exemption is about a known-cropped glyph, so it
    // applies whether or not the crop is detected.
    const r = judge([box({ right: 900, katexGlyph: true, tag: 'svg' })], BOX);
    expect(r.visible).toHaveLength(0);
  });

  it('does not exempt an ordinary svg that overflows', () => {
    // A figure is an <svg> too. Exempting by tag rather than by KaTeX ancestry
    // would blind the gate to every figure in the book.
    const r = judge([box({ right: 900, tag: 'svg', text: '' })], 900);
    expect(r.ok).toBe(false);
    expect(r.visible).toHaveLength(1);
  });

  // --- thresholds and ordering ---------------------------------------------

  it('tolerates sub-pixel overshoot rather than reporting rounding', () => {
    expect(judge([box({ right: BOX + OVERFLOW_EPS })]).visible).toHaveLength(0);
    expect(judge([box({ right: BOX + OVERFLOW_EPS + 0.1 })]).visible).toHaveLength(1);
  });

  it('ignores zero-area boxes', () => {
    expect(judge([box({ right: 900, width: 0 })]).visible).toHaveLength(0);
    expect(judge([box({ right: 900, height: 0 })]).visible).toHaveLength(0);
  });

  it('names the widest offender first', () => {
    const r = judge([
      box({ right: 560, text: 'narrower' }),
      box({ right: 680, text: 'widest' }),
    ], 680);
    expect(r.worst.text).toBe('widest');
  });

  it('names the deepest element when two share a right edge', () => {
    // An overflowing leaf drags its ancestors' right edges with it; the leaf is
    // the thing to fix, so it must win the tie.
    const r = judge([
      box({ right: 636, depth: 3, text: 'ancestor' }),
      box({ right: 636, depth: 9, text: 'the actual leaf' }),
    ], 636);
    expect(r.worst.text).toBe('the actual leaf');
  });
});
