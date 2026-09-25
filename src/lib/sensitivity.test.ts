import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import {
  SENSITIVITY_PARAMS,
  baseIndex,
  buildPath,
  curvePath,
  decadeTicks,
  decodeInt16Base64,
  decodeLog10R,
  decodeSensitivity,
  downsampleMinMax,
  encodeInt16Base64,
  gridX,
  linearTicks,
  orderedSteps,
  typographicMinus,
  valueText,
  type Frame,
  type SensitivityData,
  type SensitivityParamData,
} from './sensitivity';

const DATA: SensitivityData = JSON.parse(
  readFileSync(new URL('../../public/data/ch13-sensitivity.json', import.meta.url), 'utf8'),
);
const param = (key: string) => DATA.params.find((p) => p.key === key)!;
const labels = (p: SensitivityParamData) => orderedSteps(p).map((s) => s.label);

describe('decoding', () => {
  it('round-trips int16 values through base64, little-endian', () => {
    const v = [0, 1, -1, 1000, -1000, 32767, -32768, -11986, 12345];
    expect(Array.from(decodeInt16Base64(encodeInt16Base64(v)))).toEqual(v);
    // 1 as little-endian int16 is the bytes 01 00.
    expect(encodeInt16Base64([1])).toBe(Buffer.from([1, 0]).toString('base64'));
  });

  it('matches Node’s own little-endian reading', () => {
    const buf = Buffer.alloc(6);
    buf.writeInt16LE(-5784, 0);
    buf.writeInt16LE(0, 2);
    buf.writeInt16LE(-63, 4);
    expect(Array.from(decodeInt16Base64(buf.toString('base64')))).toEqual([-5784, 0, -63]);
  });

  it('turns the stored integers into log10 R', () => {
    const y = decodeLog10R(encodeInt16Base64([0, -1000, -8000, -2500]));
    expect(Array.from(y)).toEqual([0, -1, -8, -2.5]);
  });

  it('builds the 2θ grid as start + i·step', () => {
    const x = gridX({ start_2theta: 0.002, step_2theta: 0.006, n: 4 });
    expect(x[0]).toBeCloseTo(0.002, 12);
    expect(x[3]).toBeCloseTo(0.02, 12);
    expect(x).toHaveLength(4);
  });
});

describe('the step order, with the base in its place', () => {
  it('knows the eight parameters of the data file, in the file’s order, with its labels', () => {
    expect(SENSITIVITY_PARAMS.map((p) => p.key)).toEqual(DATA.params.map((p) => p.key));
    expect(SENSITIVITY_PARAMS.map((p) => p.label)).toEqual(DATA.params.map((p) => p.label));
  });

  it('period: −2, −1, base, +1, +2 %', () => {
    expect(labels(param('period'))).toEqual(['53.61 (-2 %)', '54.15 (-1 %)', '54.70', '55.25 (+1 %)', '55.79 (+2 %)']);
  });

  it('ratio: −2, −1, base, +1, +2 Å of Co', () => {
    expect(labels(param('ratio'))).toEqual(['21.30 (-2 Å)', '22.30 (-1 Å)', '23.30', '24.30 (+1 Å)', '25.30 (+2 Å)']);
  });

  it('σ of C and σ of Co: 1, 2.5, base 4, 6, 8 Å', () => {
    expect(labels(param('sigC'))).toEqual(['1', '2.5', '4', '6', '8']);
    expect(labels(param('sigCo'))).toEqual(['1', '2.5', '4', '6', '8']);
  });

  it('ρ of C and ρ of Co: −15, −7.5, base, +7.5, +15 %', () => {
    expect(labels(param('rhoC'))).toEqual(['1.70 (-15 %)', '1.85 (-7.5 %)', '2.00', '2.15 (+7.5 %)', '2.30 (+15 %)']);
    expect(labels(param('rhoCo'))).toEqual(['6.80 (-15 %)', '7.40 (-7.5 %)', '8.00', '8.60 (+7.5 %)', '9.20 (+15 %)']);
  });

  it('surface layer: none, base, 20 Å at 1.20 g/cm³', () => {
    expect(labels(param('top'))).toEqual(['none', '15 Å, 0.90 g/cm³', '20 Å, 1.20 g/cm³']);
  });

  it('N: 10, 15, base 20, 30, 40', () => {
    expect(labels(param('N'))).toEqual(['10', '15', '20', '30', '40']);
  });

  it('marks exactly one step as the base, at baseIndex', () => {
    for (const p of DATA.params) {
      const s = orderedSteps(p);
      expect(s.filter((x) => x.isBase)).toHaveLength(1);
      expect(s[baseIndex(p.key)].isBase).toBe(true);
      expect(s[baseIndex(p.key)].log10R_milli).toBeNull();
    }
  });

  it('refuses a parameter it has no position for', () => {
    expect(() => orderedSteps({ key: 'x', label: 'x', unit: '', base_label: '0', steps: [] })).toThrow();
  });
});

describe('the readout', () => {
  it('writes a typographic minus', () => {
    expect(typographicMinus('53.61 (-2 %)')).toBe('53.61 (−2 %)');
    expect(typographicMinus('-1')).toBe('−1');
    expect(typographicMinus('a-1 range')).toBe('a-1 range');
  });

  it('puts the unit after the number and before a bracketed change', () => {
    expect(valueText('Period D', 'Å', '53.61 (-2 %)')).toBe('Period D: 53.61 Å (−2 %)');
    expect(valueText('Co thickness at the same period', 'Å', '21.30 (-2 Å)')).toBe(
      'Co thickness at the same period: 21.30 Å (−2 Å)',
    );
    expect(valueText('σ of Co', 'Å', '6')).toBe('σ of Co: 6 Å');
    expect(valueText('ρ of C', 'g/cm³', '2.00')).toBe('ρ of C: 2.00 g/cm³');
    expect(valueText('Surface layer', '', '15 Å, 0.90 g/cm³')).toBe('Surface layer: 15 Å, 0.90 g/cm³');
    expect(valueText('Number of periods N', '', '40')).toBe('Number of periods N: 40');
  });
});

describe('drawing helpers', () => {
  const F: Frame = { x0: 0, x1: 10, y0: -8, y1: 0, left: 50, right: 150, bottom: 100, top: 20 };

  it('builds a path in pixels', () => {
    expect(buildPath([0, 5, 10], [0, -4, -8], F)).toBe('M50.0 20.0 L100.0 60.0 L150.0 100.0');
  });

  it('clamps below the axis and leaves out points outside the x window', () => {
    expect(buildPath([-1, 0, 10, 11], [0, -12, 1, 0], F)).toBe('M50.0 100.0 L150.0 20.0');
  });

  it('breaks the line at a non-finite value', () => {
    expect(buildPath([0, 5, 10], [0, Number.NaN, -8], F)).toBe('M50.0 20.0 M150.0 100.0');
  });

  it('downsamples to the min and max of each bucket, keeping a narrow peak', () => {
    const xs = Array.from({ length: 1000 }, (_, i) => i);
    const ys = xs.map((i) => (i === 437 ? 5 : -Math.abs(Math.sin(i))));
    const d = downsampleMinMax(xs, ys, 50);
    expect(d.xs.length).toBeLessThanOrEqual(100);
    expect(d.ys).toContain(5);
    expect(d.xs).toContain(437);
    // order kept
    for (let i = 1; i < d.xs.length; i++) expect(d.xs[i]).toBeGreaterThan(d.xs[i - 1]);
  });

  it('leaves a short curve unchanged', () => {
    expect(downsampleMinMax([1, 2, 3], [4, 5, 6], 10)).toEqual({ xs: [1, 2, 3], ys: [4, 5, 6] });
  });

  it('curvePath keeps at most two points per pixel column', () => {
    const xs = Array.from({ length: 5000 }, (_, i) => i / 500);
    const ys = xs.map((x) => -x / 2);
    const d = curvePath(xs, ys, F);
    expect(d.startsWith('M50.0 ')).toBe(true);
    expect(d.split(/[ML]/).filter(Boolean).length).toBeLessThanOrEqual(200);
  });

  it('labels decades with superscripts, 10⁰ as 1', () => {
    expect(decadeTicks(-8, 0).map((t) => t.label)).toEqual(['10⁻⁸', '10⁻⁷', '10⁻⁶', '10⁻⁵', '10⁻⁴', '10⁻³', '10⁻²', '10⁻¹', '1']);
  });

  it('puts 2θ ticks every 2° from 0 to 14', () => {
    expect(linearTicks(0, 14, 2)).toEqual([0, 2, 4, 6, 8, 10, 12, 14]);
  });
});

describe('the real data file', () => {
  const d = decodeSensitivity(DATA);
  const n = DATA.model_grid.n;

  it('gives model_grid.n points for the base and every step', () => {
    expect(d.base).toHaveLength(n);
    expect(d.modelX).toHaveLength(n);
    for (const p of d.params) {
      expect(p.steps.length).toBe(DATA.params.find((q) => q.key === p.key)!.steps.length + 1);
      for (const s of p.steps) expect(s.y).toHaveLength(n);
    }
  });

  it('gives measured.n points for the measured curve', () => {
    expect(d.measured).toHaveLength(DATA.measured.n);
    expect(d.measuredX).toHaveLength(DATA.measured.n);
  });

  it('covers 2θ = 0–14°', () => {
    expect(d.modelX[0]).toBeLessThan(0.01);
    expect(d.modelX[n - 1]).toBeCloseTo(14, 6);
  });

  it('has the base curve near R = 1 at 2θ = 0.1–0.4°', () => {
    for (let i = 0; i < n; i++) {
      if (d.modelX[i] >= 0.1 && d.modelX[i] <= 0.4) {
        expect(d.base[i]).toBeLessThanOrEqual(0);
        expect(d.base[i]).toBeGreaterThan(-0.1);
      }
    }
  });

  it('has the measured curve normalized to 1 at its maximum', () => {
    expect(Math.max(...d.measured)).toBe(0);
  });

  it('differs from the base at every non-base step', () => {
    for (const p of d.params) {
      for (const s of p.steps) {
        if (s.isBase) continue;
        let diff = 0;
        for (let i = 0; i < n; i++) diff = Math.max(diff, Math.abs(s.y[i] - d.base[i]));
        expect(diff, `${p.key}/${s.key}`).toBeGreaterThan(0.01);
      }
    }
  });
});
