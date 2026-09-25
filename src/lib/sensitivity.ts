/**
 * The sensitivity check of Chapter 13: the CoC4 starting model with one
 * parameter changed at a time.
 *
 * X-Ray Calc computed every curve in advance (scripts/figures/ch13_engine_data.py,
 * pack()). The widget SensitivityCheck.svelte fetches public/data/ch13-sensitivity.json
 * and only draws what these functions return. Pure functions, no DOM.
 *
 * Data format: every curve is log10 R × 1000, rounded, stored as little-endian
 * int16 and then base64. The model curves share one 2θ grid (model_grid); the
 * measured curve has its own.
 */

import { superscript } from './format';

export interface Grid2Theta {
  /** First 2θ, degrees. */
  start_2theta: number;
  /** Step in 2θ, degrees. */
  step_2theta: number;
  /** Number of points. */
  n: number;
}

export interface SensitivityStepData {
  key: string;
  label: string;
  log10R_milli: string;
}

export interface SensitivityParamData {
  key: string;
  label: string;
  unit: string;
  base_label: string;
  steps: SensitivityStepData[];
}

export interface SensitivityData {
  source?: string;
  lambda_A?: number;
  delta_theta_deg?: number;
  model_grid: Grid2Theta;
  measured: Grid2Theta & { log10R_milli: string; name: string };
  base: string;
  params: SensitivityParamData[];
}

/**
 * The eight parameters in the order the widget lists them, and where the
 * starting model (the base) belongs among each parameter's steps. The steps in
 * the data file are ordered by value and leave the base out; `basePosition` is
 * the index at which the base is inserted. Explicit, so nothing depends on
 * parsing the step labels:
 *   period, ratio, ρ of C, ρ of Co   −2, −1, [0], +1, +2 (or −15, −7.5, [0], +7.5, +15 %)
 *   σ of C, σ of Co                  1, 2.5, [4], 6, 8 Å
 *   surface layer                    none, [15 Å at 0.90 g/cm³], 20 Å at 1.20 g/cm³
 *   N                                10, 15, [20], 30, 40
 * The labels are the data file's labels, repeated here so that the controls
 * can be drawn before the file arrives. A unit test checks both against the file.
 */
export const SENSITIVITY_PARAMS: readonly { key: string; label: string; basePosition: number }[] = Object.freeze([
  { key: 'period', label: 'Period D', basePosition: 2 },
  { key: 'ratio', label: 'Co thickness at the same period', basePosition: 2 },
  { key: 'sigC', label: 'σ of C', basePosition: 2 },
  { key: 'sigCo', label: 'σ of Co', basePosition: 2 },
  { key: 'rhoC', label: 'ρ of C', basePosition: 2 },
  { key: 'rhoCo', label: 'ρ of Co', basePosition: 2 },
  { key: 'top', label: 'Surface layer', basePosition: 1 },
  { key: 'N', label: 'Number of periods N', basePosition: 2 },
]);

/** One position of the slider: a precomputed step, or the base (the starting model). */
export interface OrderedStep {
  /** The step key from the data file, or 'base'. */
  key: string;
  /** The value as the data file writes it (base_label for the base). */
  label: string;
  isBase: boolean;
  /** The encoded curve; null for the base, whose curve is SensitivityData.base. */
  log10R_milli: string | null;
}

/**
 * The slider positions of one parameter: its steps with the base inserted at
 * the position that SENSITIVITY_PARAMS gives. Throws for a parameter that the
 * table does not know or a position outside the steps, because either means the
 * data file and the table disagree.
 */
export function orderedSteps(param: SensitivityParamData): OrderedStep[] {
  const entry = SENSITIVITY_PARAMS.find((p) => p.key === param.key);
  if (!entry) throw new Error(`No base position for parameter "${param.key}".`);
  const pos = entry.basePosition;
  if (!Number.isInteger(pos) || pos < 0 || pos > param.steps.length) {
    throw new Error(`Base position ${pos} is outside the ${param.steps.length} steps of "${param.key}".`);
  }
  const steps: OrderedStep[] = param.steps.map((s) => ({
    key: s.key,
    label: s.label,
    isBase: false,
    log10R_milli: s.log10R_milli,
  }));
  steps.splice(pos, 0, { key: 'base', label: param.base_label, isBase: true, log10R_milli: null });
  return steps;
}

/** The index of the base among orderedSteps(param). */
export function baseIndex(key: string): number {
  const entry = SENSITIVITY_PARAMS.find((p) => p.key === key);
  if (!entry) throw new Error(`No base position for parameter "${key}".`);
  return entry.basePosition;
}

/** Hyphen-minus before a digit becomes a typographic minus (U+2212): "(-2 %)" → "(−2 %)". */
export function typographicMinus(s: string): string {
  return s.replace(/(^|[\s(])-(?=\d)/g, '$1−');
}

/**
 * The readout for one step: "<label>: <value> <unit>". When the value has a
 * bracketed change after it, the unit goes after the number and before the
 * bracket: "Period D: 53.61 Å (−2 %)". A parameter without a unit (the surface
 * layer, N) shows the value alone.
 */
export function valueText(paramLabel: string, unit: string, stepLabel: string): string {
  let v = typographicMinus(stepLabel);
  if (unit) {
    const i = v.indexOf(' (');
    v = i >= 0 ? `${v.slice(0, i)} ${unit}${v.slice(i)}` : `${v} ${unit}`;
  }
  return `${paramLabel}: ${v}`;
}

// ---- decoding -------------------------------------------------------------

/** Base64 of little-endian int16 values → the integers. */
export function decodeInt16Base64(b64: string): Int16Array {
  const bin = atob(b64);
  if (bin.length % 2 !== 0) throw new Error('The encoded curve has an odd number of bytes.');
  const view = new DataView(new ArrayBuffer(bin.length));
  for (let i = 0; i < bin.length; i++) view.setUint8(i, bin.charCodeAt(i));
  const out = new Int16Array(bin.length / 2);
  for (let i = 0; i < out.length; i++) out[i] = view.getInt16(2 * i, true);
  return out;
}

/** The integers → base64 of little-endian int16. The inverse of decodeInt16Base64. */
export function encodeInt16Base64(values: ArrayLike<number>): string {
  const view = new DataView(new ArrayBuffer(values.length * 2));
  for (let i = 0; i < values.length; i++) view.setInt16(2 * i, values[i], true);
  let bin = '';
  for (let i = 0; i < view.byteLength; i++) bin += String.fromCharCode(view.getUint8(i));
  return btoa(bin);
}

/** An encoded curve → log10 R (value / 1000). */
export function decodeLog10R(b64: string): Float64Array {
  const ints = decodeInt16Base64(b64);
  const out = new Float64Array(ints.length);
  for (let i = 0; i < ints.length; i++) out[i] = ints[i] / 1000;
  return out;
}

/** The 2θ values of a grid: start + i·step, degrees. */
export function gridX(g: Grid2Theta): Float64Array {
  const out = new Float64Array(g.n);
  for (let i = 0; i < g.n; i++) out[i] = g.start_2theta + i * g.step_2theta;
  return out;
}

// ---- drawing --------------------------------------------------------------

/** A plot frame: the data window and where it lands in SVG pixels. */
export interface Frame {
  x0: number; // data x at the left edge (2θ, degrees)
  x1: number; // data x at the right edge
  y0: number; // data y at the bottom edge (log10 R)
  y1: number; // data y at the top edge
  left: number; // pixel x of x0
  right: number; // pixel x of x1
  bottom: number; // pixel y of y0
  top: number; // pixel y of y1
}

export const scaleX = (f: Frame, x: number) => f.left + ((x - f.x0) / (f.x1 - f.x0)) * (f.right - f.left);
export const scaleY = (f: Frame, y: number) => f.bottom + ((y - f.y0) / (f.y1 - f.y0)) * (f.top - f.bottom);

/**
 * Min-max downsampling: split the points into `buckets` equal runs and keep
 * the lowest and the highest point of each, in their original order. A narrow
 * Bragg peak keeps its top. Returns the input unchanged when it already has
 * no more than 2 × buckets points.
 */
export function downsampleMinMax(
  xs: ArrayLike<number>,
  ys: ArrayLike<number>,
  buckets: number,
): { xs: number[]; ys: number[] } {
  const n = Math.min(xs.length, ys.length);
  if (buckets < 1 || n <= 2 * buckets) return { xs: Array.from(xs).slice(0, n), ys: Array.from(ys).slice(0, n) };
  const ox: number[] = [];
  const oy: number[] = [];
  for (let b = 0; b < buckets; b++) {
    const i0 = Math.floor((b * n) / buckets);
    const i1 = Math.floor(((b + 1) * n) / buckets);
    if (i1 <= i0) continue;
    let iMin = i0;
    let iMax = i0;
    for (let i = i0 + 1; i < i1; i++) {
      if (ys[i] < ys[iMin]) iMin = i;
      if (ys[i] > ys[iMax]) iMax = i;
    }
    const first = Math.min(iMin, iMax);
    const second = Math.max(iMin, iMax);
    ox.push(xs[first]);
    oy.push(ys[first]);
    if (second !== first) {
      ox.push(xs[second]);
      oy.push(ys[second]);
    }
  }
  return { xs: ox, ys: oy };
}

/**
 * An SVG path "M x y L x y …" through the points, in pixels, one decimal.
 * Points outside [x0, x1] are left out. y is clamped to [y0, y1], so a curve
 * that falls below the axis runs along it (the chart clips it there). A
 * non-finite y breaks the line.
 */
export function buildPath(xs: ArrayLike<number>, ys: ArrayLike<number>, f: Frame): string {
  const n = Math.min(xs.length, ys.length);
  const lo = Math.min(f.y0, f.y1);
  const hi = Math.max(f.y0, f.y1);
  const xlo = Math.min(f.x0, f.x1);
  const xhi = Math.max(f.x0, f.x1);
  const parts: string[] = [];
  let pen = false;
  for (let i = 0; i < n; i++) {
    const x = xs[i];
    const y = ys[i];
    if (!Number.isFinite(x) || x < xlo || x > xhi || !Number.isFinite(y)) {
      pen = false;
      continue;
    }
    const px = scaleX(f, x).toFixed(1);
    const py = scaleY(f, Math.min(hi, Math.max(lo, y))).toFixed(1);
    parts.push(`${pen ? 'L' : 'M'}${px} ${py}`);
    pen = true;
  }
  return parts.join(' ');
}

/**
 * The path of one curve in a frame: trim to the x window, then min-max
 * downsample to about one point pair per pixel column, then build the path.
 */
export function curvePath(xs: ArrayLike<number>, ys: ArrayLike<number>, f: Frame): string {
  const n = Math.min(xs.length, ys.length);
  const tx: number[] = [];
  const ty: number[] = [];
  for (let i = 0; i < n; i++) {
    if (xs[i] >= f.x0 && xs[i] <= f.x1) {
      tx.push(xs[i]);
      ty.push(ys[i]);
    }
  }
  const cols = Math.max(1, Math.round(Math.abs(f.right - f.left)));
  const s = downsampleMinMax(tx, ty, cols);
  return buildPath(s.xs, s.ys, f);
}

/** Decade ticks of a log axis from 10^lo to 10^hi, labeled with Unicode superscripts; 10⁰ is written 1. */
export function decadeTicks(lo: number, hi: number): { exp: number; label: string }[] {
  const out: { exp: number; label: string }[] = [];
  for (let e = Math.ceil(lo); e <= Math.floor(hi); e++) {
    out.push({ exp: e, label: e === 0 ? '1' : `10${superscript(e)}` });
  }
  return out;
}

/** Linear ticks from lo to hi every `step`. */
export function linearTicks(lo: number, hi: number, step: number): number[] {
  const out: number[] = [];
  const n = Math.floor((hi - lo) / step + 1e-9);
  for (let i = 0; i <= n; i++) out.push(Number((lo + i * step).toFixed(10)));
  return out;
}

// ---- the decoded data set --------------------------------------------------

export interface DecodedParam {
  key: string;
  label: string;
  unit: string;
  steps: (OrderedStep & { y: Float64Array })[];
}

export interface DecodedSensitivity {
  modelX: Float64Array;
  base: Float64Array;
  measuredX: Float64Array;
  measured: Float64Array;
  measuredName: string;
  params: DecodedParam[];
}

/**
 * Decode the whole file once. Checks that every model curve has model_grid.n
 * points and the measured curve measured.n, and that the file has exactly the
 * parameters of SENSITIVITY_PARAMS, in that order. Throws on any mismatch.
 */
export function decodeSensitivity(data: SensitivityData): DecodedSensitivity {
  const n = data.model_grid.n;
  const check = (y: Float64Array, what: string, want: number) => {
    if (y.length !== want) throw new Error(`${what} has ${y.length} points, expected ${want}.`);
    return y;
  };
  const keys = data.params.map((p) => p.key).join(',');
  const want = SENSITIVITY_PARAMS.map((p) => p.key).join(',');
  if (keys !== want) throw new Error(`The file's parameters (${keys}) differ from the widget's (${want}).`);
  const base = check(decodeLog10R(data.base), 'The base curve', n);
  return {
    modelX: gridX(data.model_grid),
    base,
    measuredX: gridX(data.measured),
    measured: check(decodeLog10R(data.measured.log10R_milli), 'The measured curve', data.measured.n),
    measuredName: data.measured.name,
    params: data.params.map((p) => ({
      key: p.key,
      label: p.label,
      unit: p.unit,
      steps: orderedSteps(p).map((s) => ({
        ...s,
        y: s.isBase ? base : check(decodeLog10R(s.log10R_milli!), `Step ${p.key}/${s.key}`, n),
      })),
    })),
  };
}
