import { describe, expect, it } from 'vitest';
import { displayNumber, precise, readable, sci, superscript } from './format';

describe('superscript', () => {
  it('maps digits and the minus sign', () => {
    expect(superscript(-5)).toBe('⁻⁵');
    expect(superscript(22)).toBe('²²');
    expect(superscript(0)).toBe('⁰');
  });
});

describe('sci', () => {
  it('writes the house form, never e-notation', () => {
    expect(sci(1.4e-5)).toBe('1.40 × 10⁻⁵');
    expect(sci(1e-7, 1)).toBe('1.0 × 10⁻⁷');
    expect(sci(6.24e15)).toBe('6.24 × 10¹⁵');
  });

  it('never emits an "e"', () => {
    for (const v of [1e-13, 3.513e22, 760, 0.0005, 1.380649e-23]) {
      expect(sci(v)).not.toMatch(/e/i);
    }
  });

  it('collapses a zero exponent to a plain mantissa', () => {
    expect(sci(2)).toBe('2.00');
    expect(sci(9.5, 1)).toBe('9.5');
  });

  it('handles zero and non-finite input', () => {
    expect(sci(0)).toBe('0.00');
    expect(sci(Number.NaN)).toBe('—');
    expect(sci(Number.POSITIVE_INFINITY)).toBe('—');
  });

  it('keeps the sign of a negative value', () => {
    expect(sci(-2.5e-3)).toBe('-2.50 × 10⁻³');
  });
});

describe('readable', () => {
  it('prefers a plain number and drops trailing zeros', () => {
    expect(readable(10)).toBe('10');
    expect(readable(0.5)).toBe('0.5');
    expect(readable(2)).toBe('2');
    expect(readable(760)).toBe('760');
  });

  it('falls back to the house exponential outside the plain window', () => {
    expect(readable(1e-5, 1)).toBe('1.0 × 10⁻⁵');
    expect(readable(2.15e-7)).toBe('2.15 × 10⁻⁷');
    expect(readable(5e7)).toBe('5.00 × 10⁷');
  });

  it('rounds to digits + 1 significant figures', () => {
    expect(readable(1.23456, 2)).toBe('1.23');
    expect(readable(1.23456, 1)).toBe('1.2');
  });

  it('never emits an "e"', () => {
    for (const v of [1e-13, 3.513e22, 760, 0.0005, 10, 49529]) {
      expect(readable(v)).not.toMatch(/e/i);
    }
  });

  it('handles zero and non-finite input', () => {
    expect(readable(0)).toBe('0');
    expect(readable(Number.NaN)).toBe('—');
  });
});

describe('displayNumber', () => {
  it('keeps everyday magnitudes plain and adds no precision', () => {
    expect(displayNumber(60000)).toBe('60000');
    expect(displayNumber(750)).toBe('750');
    expect(displayNumber(0.002)).toBe('0.002');
    expect(displayNumber(0.05)).toBe('0.05');
  });

  it('uses the house form where JS would print e-notation', () => {
    expect(displayNumber(1e-7)).toBe('1 × 10⁻⁷');
    expect(displayNumber(1e-6)).toBe('1 × 10⁻⁶');
  });

  it('renders the magnitudes an XRR fit produces without e-notation', () => {
    // The reflectivity floor (Help: Min limit, default 1E-7), the engine's hc in
    // eV·Å, a Cu Kα wavelength in Å, and a resolution in degrees.
    for (const value of [1e-7, 12398.6, 1.5406, 0.012]) {
      expect(displayNumber(value)).not.toMatch(/e/i);
    }
  });

  it('handles zero and non-finite input', () => {
    expect(displayNumber(0)).toBe('0');
    expect(displayNumber(Number.NaN)).toBe('—');
  });
});

describe('precise', () => {
  it('converts only when toPrecision would use e-notation', () => {
    expect(precise(1.3e-8, 2)).toBe('1.3 × 10⁻⁸');
    expect(precise(2.5, 2)).toBe('2.5');
    expect(precise(760, 3)).toBe('760');
  });

  it('never emits an "e"', () => {
    for (const v of [1.78e15, 5e-9, 0.13]) {
      expect(precise(v, 3)).not.toMatch(/e/i);
    }
  });

  it('handles non-finite input', () => {
    expect(precise(Number.NaN)).toBe('—');
  });
});
