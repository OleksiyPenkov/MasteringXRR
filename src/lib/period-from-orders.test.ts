import { describe, expect, it } from 'vitest';
import {
  COC4_LAMBDA_A,
  COC4_ORDERS,
  evenTwoTheta,
  fitOrders,
  formatScaled,
  predictTwoTheta,
  type MeasuredOrder,
  type OrdersFit,
} from './period-from-orders';

// CoC4, the measured Co/C multilayer of Chapter 11 (OUTLINE.md, Chapter 11 §4–5),
// at λ = 1.541874 Å. Orders 1–7 as measured on the chart, 2θ in degrees.
const L = COC4_LAMBDA_A;
const ANGLES = [1.698, 3.269, 4.878, 6.482, 8.102, 9.713, 11.336];
const numbered = (angles: number[], first: number): MeasuredOrder[] =>
  angles.map((twoThetaDeg, i) => ({ m: first + i, twoThetaDeg }));

function ok(r: ReturnType<typeof fitOrders>): OrdersFit {
  if (!r.ok) throw new Error(`expected a fit, got: ${r.message}`);
  return r;
}

describe('fitOrders: CoC4, orders 1–7 (the reference case)', () => {
  const r = ok(fitOrders(L, numbered(ANGLES, 1)));

  it('gives D = 54.70 Å with σD ≈ 0.010 Å', () => {
    expect(r.n).toBe(7);
    expect(Math.abs(r.D - 54.7025)).toBeLessThan(0.0005);
    expect(r.sigmaD).not.toBeNull();
    expect(r.sigmaD!).toBeCloseTo(0.010, 3);
  });

  it('gives 2δ̄ ≈ 2.08 × 10⁻⁵', () => {
    expect(r.twoDelta).toBeGreaterThan(2.077e-5);
    expect(r.twoDelta).toBeLessThan(2.086e-5);
    expect(r.sigmaTwoDelta).not.toBeNull();
  });

  it('gives 2θc ≈ 0.523° with σ ≈ 0.024°', () => {
    expect(r.twoThetaC).not.toBeNull();
    expect(r.twoThetaC!).toBeCloseTo(0.523, 3);
    expect(r.sigmaTwoThetaC!).toBeCloseTo(0.024, 3);
  });

  it('predicts every order within 0.004° of the measured 2θ', () => {
    expect(r.residuals).toHaveLength(7);
    for (const d of r.residuals) {
      expect(d).not.toBeNull();
      expect(Math.abs(d!)).toBeLessThan(0.004);
    }
    // residual = measured − predicted
    expect(r.residuals[6]!).toBeCloseTo(ANGLES[6] - r.predicted[6]!, 12);
  });

  it('reports the rms residual in sin²θ', () => {
    expect(r.rmsSin2).toBeGreaterThan(0);
    expect(r.rmsSin2).toBeLessThan(1e-5);
  });
});

describe('fitOrders: CoC4, the six clear orders (the widget example)', () => {
  const r = ok(fitOrders(L, [...COC4_ORDERS]));

  it('is the six clear orders as the import gives them (the 0.003° grid of the scan)', () => {
    expect(COC4_ORDERS.map((o) => o.twoThetaDeg)).toEqual([1.6975, 3.2695, 4.8775, 6.4825, 8.1025, 9.7135]);
    expect(COC4_ORDERS.map((o) => o.m)).toEqual([1, 2, 3, 4, 5, 6]);
  });

  it('gives the chapter’s seed: D = 54.70 Å, 2δ̄ = 2.12 × 10⁻⁵, 2θc = 0.527°', () => {
    // figures-src/ch11/numbers.txt (scripts/figures/fig_11_figures.py, numpy least squares):
    // D = 54.7045 ± 0.0152 Å, 2δ̄ = 2.1162e-5 ± 2.15e-6, 2θc = 0.5271 ± 0.0268°.
    expect(Math.abs(r.D - 54.7045)).toBeLessThan(0.0005);
    expect(Math.abs(r.sigmaD! - 0.0152)).toBeLessThan(0.0005);
    expect(Math.abs(r.twoDelta - 2.1162e-5)).toBeLessThan(0.0005e-5);
    expect(Math.abs(r.twoThetaC! - 0.5271)).toBeLessThan(0.0005);
    expect(Math.abs(r.sigmaTwoThetaC! - 0.0268)).toBeLessThan(0.0005);
  });

  it('predicts orders 7 and 8 where the chapter finds them (11.3365° and 12.9595° measured)', () => {
    const p7 = predictTwoTheta(7, r.D, r.twoDelta, L)!;
    const p8 = predictTwoTheta(8, r.D, r.twoDelta, L)!;
    expect(p7).toBeCloseTo(11.3351, 3);
    expect(p8).toBeCloseTo(12.9576, 3);
    expect(Math.abs(p7 - 11.3365)).toBeLessThan(0.002);
    expect(Math.abs(p8 - 12.9595)).toBeLessThan(0.002);
  });
});

describe('fitOrders: wrong numbering shows in the result', () => {
  it('numbered from 2 (shifted by one): D ≈ 60.94 Å and a negative 2δ̄', () => {
    const r = ok(fitOrders(L, numbered(ANGLES, 2)));
    expect(r.D).toBeCloseTo(60.94, 2);
    expect(r.twoDelta).toBeLessThan(0);
    expect(r.twoThetaC).toBeNull();
    expect(r.sigmaTwoThetaC).toBeNull();
  });

  it('the weak second order missed: D ≈ 47.59 Å and 2θc ≈ 2.67°', () => {
    const skipped = [1.698, 4.878, 6.482, 8.102, 9.713, 11.336];
    const r = ok(fitOrders(L, numbered(skipped, 1)));
    expect(r.D).toBeCloseTo(47.59, 2);
    expect(r.twoThetaC!).toBeCloseTo(2.67, 2);
    // 2θc above the lowest measured order: the widget's cue that the numbering is wrong.
    expect(r.twoThetaC!).toBeGreaterThan(skipped[0]);
  });
});

describe('fitOrders: exact synthetic data are recovered', () => {
  it('D = 50 Å, 2δ̄ = 2.6 × 10⁻⁵, m = 1..5', () => {
    const D = 50;
    const twoDelta = 2.6e-5;
    const orders = [1, 2, 3, 4, 5].map((m) => ({ m, twoThetaDeg: predictTwoTheta(m, D, twoDelta, L)! }));
    const r = ok(fitOrders(L, orders));
    expect(Math.abs(r.D / D - 1)).toBeLessThan(1e-6);
    expect(Math.abs(r.twoDelta / twoDelta - 1)).toBeLessThan(1e-6);
    expect(r.twoThetaC!).toBeCloseTo((2 * Math.sqrt(twoDelta) * 180) / Math.PI, 6);
    for (const d of r.residuals) expect(Math.abs(d!)).toBeLessThan(1e-9);
    expect(r.sigmaD!).toBeLessThan(1e-6);
  });
});

describe('fitOrders: two orders', () => {
  it('gives D and 2δ̄ but no standard errors', () => {
    const r = ok(fitOrders(L, numbered(ANGLES.slice(0, 2), 1)));
    expect(r.D).toBeGreaterThan(50);
    expect(Number.isFinite(r.twoDelta)).toBe(true);
    expect(r.sigmaD).toBeNull();
    expect(r.sigmaTwoDelta).toBeNull();
    expect(r.sigmaTwoThetaC).toBeNull();
  });

  it('does not need the orders sorted', () => {
    const a = ok(fitOrders(L, numbered(ANGLES, 1)));
    const b = ok(fitOrders(L, numbered(ANGLES, 1).reverse()));
    expect(b.D).toBeCloseTo(a.D, 10);
    expect(b.residuals[0]).toBeCloseTo(a.residuals[6]!, 10);
  });
});

describe('fitOrders: errors come back as plain sentences', () => {
  const two = numbered(ANGLES.slice(0, 2), 1);
  const cases: [string, number, MeasuredOrder[], RegExp][] = [
    ['λ = 0', 0, two, /wavelength/],
    ['negative λ', -1.54, two, /wavelength/],
    ['λ not a number', Number.NaN, two, /wavelength .* not a number/],
    ['one order', L, two.slice(0, 1), /at least two orders/],
    ['no orders', L, [], /at least two orders/],
    ['duplicate m', L, [{ m: 1, twoThetaDeg: 1.698 }, { m: 1, twoThetaDeg: 3.269 }], /entered twice/],
    ['m = 0', L, [{ m: 0, twoThetaDeg: 1.698 }, { m: 1, twoThetaDeg: 3.269 }], /whole number of 1 or more/],
    ['m = 1.5', L, [{ m: 1.5, twoThetaDeg: 1.698 }, { m: 2, twoThetaDeg: 3.269 }], /whole number/],
    ['m not a number', L, [{ m: Number.NaN, twoThetaDeg: 1.698 }, { m: 2, twoThetaDeg: 3.269 }], /not a number/],
    ['2θ = 0', L, [{ m: 1, twoThetaDeg: 0 }, { m: 2, twoThetaDeg: 3.269 }], /larger than 0°/],
    ['2θ negative', L, [{ m: 1, twoThetaDeg: -1 }, { m: 2, twoThetaDeg: 3.269 }], /larger than 0°/],
    ['2θ not a number', L, [{ m: 1, twoThetaDeg: Number.NaN }, { m: 2, twoThetaDeg: 3.269 }], /2θ of order 1 is not a number/],
    ['angles fall with m', L, [{ m: 1, twoThetaDeg: 3.269 }, { m: 2, twoThetaDeg: 1.698 }], /do not grow/],
  ];
  for (const [name, lambda, orders, re] of cases) {
    it(name, () => {
      const r = fitOrders(lambda, orders);
      expect(r.ok).toBe(false);
      if (!r.ok) {
        expect(r.message).toMatch(re);
        expect(r.message).not.toMatch(/—/);
      }
    });
  }
});

describe('predictTwoTheta', () => {
  it('reduces to the plain Bragg law when 2δ̄ = 0', () => {
    // mλ = 2D sin θ
    const tt = predictTwoTheta(1, 50, 0, L)!;
    expect(Math.sin(((tt / 2) * Math.PI) / 180)).toBeCloseTo(L / 100, 12);
  });

  it('puts a refracted order above the plain Bragg angle', () => {
    expect(predictTwoTheta(1, 50, 2.6e-5, L)!).toBeGreaterThan(predictTwoTheta(1, 50, 0, L)!);
  });

  it('returns null when sin²θ is outside (0, 1]', () => {
    expect(predictTwoTheta(1, 60.94, -6.5e-4, L)).toBeNull(); // negative sin²θ
    expect(predictTwoTheta(100, 10, 0, L)).toBeNull(); // sin θ > 1
    expect(predictTwoTheta(1, 0, 0, L)).toBeNull();
    expect(predictTwoTheta(1, 50, 0, 0)).toBeNull();
  });
});

describe('evenTwoTheta', () => {
  it('is m times the first-order 2θ', () => {
    expect(evenTwoTheta(7, 1.698)).toBeCloseTo(11.886, 12);
    expect(evenTwoTheta(1, 1.698)).toBe(1.698);
  });
});

describe('formatScaled', () => {
  it('writes a small value in the × 10ⁿ form, never e-notation', () => {
    expect(formatScaled(2.0851e-5, null)).toBe('2.09 × 10⁻⁵');
    expect(formatScaled(2.0851e-5, 1.9e-6)).toBe('(2.09 ± 0.19) × 10⁻⁵');
    expect(formatScaled(-6.48e-4, 1.06e-4)).toBe('(−6.48 ± 1.06) × 10⁻⁴');
    for (const v of [1e-9, 2.6e-5, -3e-7, 9.999e-6]) expect(formatScaled(v, v / 10)).not.toMatch(/e/i);
  });

  it('carries a rounded 10.00 up one power', () => {
    expect(formatScaled(9.999e-6, null)).toBe('1.00 × 10⁻⁵');
  });

  it('drops the power for values between 1 and 10', () => {
    expect(formatScaled(2.5, 0.1)).toBe('2.50 ± 0.10');
  });
});
