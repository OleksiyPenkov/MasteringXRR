/**
 * The period and the refraction term from the measured Bragg orders.
 *
 * X-Ray Calc has no tool that fits the order positions, so the book does it
 * with a straight line (procedure §1.5 and §6.6; NOTATION.md, "The Bragg law
 * with refraction"):
 *
 *   sin²θ_m = (mλ / 2D)² + 2δ̄
 *
 * An ordinary least-squares line of y = sin²θ_m against x = m² has slope
 * a = (λ / 2D)² and intercept b = 2δ̄. So D = λ / (2√a), 2δ̄ = b and, when
 * b > 0, θc = √(2δ̄) in radians.
 *
 * Angles come in as 2θ in degrees, the chart's axis. The physics uses θ.
 * Pure functions, no DOM: the widget PeriodFromOrders.svelte only displays
 * what these return.
 */

import { superscript } from './format';

export interface MeasuredOrder {
  /** Bragg order number, 1, 2, 3, … */
  m: number;
  /** Measured peak position, 2θ in degrees. */
  twoThetaDeg: number;
}

export interface OrdersFit {
  ok: true;
  /** Number of orders in the fit. */
  n: number;
  /** Period D, Å. */
  D: number;
  /** Standard error of D, Å. Null with fewer than 3 orders. */
  sigmaD: number | null;
  /** The intercept 2δ̄ (dimensionless). */
  twoDelta: number;
  /** Standard error of 2δ̄. Null with fewer than 3 orders. */
  sigmaTwoDelta: number | null;
  /** Critical angle 2θc = 2√(2δ̄) in degrees. Null when 2δ̄ ≤ 0. */
  twoThetaC: number | null;
  /** Standard error of 2θc, degrees. Null when 2θc is null or with fewer than 3 orders. */
  sigmaTwoThetaC: number | null;
  /** Per order, in input order: the 2θ that the fitted line predicts, degrees (null if none exists). */
  predicted: (number | null)[];
  /** Per order, in input order: measured 2θ minus predicted 2θ, degrees (null if no prediction). */
  residuals: (number | null)[];
  /** Root-mean-square residual of the line, in sin²θ. */
  rmsSin2: number;
}

export interface OrdersError {
  ok: false;
  /** A plain-English sentence for the reader. */
  message: string;
}

export type OrdersResult = OrdersFit | OrdersError;

const DEG = Math.PI / 180;

const fail = (message: string): OrdersError => ({ ok: false, message });

/**
 * The 2θ (degrees) at which order m appears for period D (Å), refraction term
 * 2δ̄ and wavelength λ (Å). Null when sin²θ falls outside (0, 1]: the order
 * does not exist for these values.
 */
export function predictTwoTheta(m: number, D: number, twoDelta: number, lambdaA: number): number | null {
  if (!(D > 0) || !(lambdaA > 0) || !Number.isFinite(m) || !Number.isFinite(twoDelta)) return null;
  const s2 = ((m * lambdaA) / (2 * D)) ** 2 + twoDelta;
  if (!(s2 > 0) || s2 > 1) return null;
  return (2 * Math.asin(Math.sqrt(s2))) / DEG;
}

/** The naive guess that the orders are evenly spaced: order m at m·2θ₁. */
export function evenTwoTheta(m: number, twoTheta1: number): number {
  return m * twoTheta1;
}

/** Check the inputs. Returns a message for the reader, or null when they are usable. */
function validate(lambdaA: number, orders: MeasuredOrder[]): string | null {
  if (typeof lambdaA !== 'number' || !Number.isFinite(lambdaA)) return 'The wavelength λ is not a number.';
  if (lambdaA <= 0) return 'The wavelength λ must be larger than 0 Å.';
  const seen = new Set<number>();
  for (const o of orders) {
    const { m, twoThetaDeg } = o;
    if (typeof m !== 'number' || !Number.isFinite(m)) return 'An order number m is not a number.';
    if (!Number.isInteger(m) || m < 1) return `Order number ${m} is not allowed. Each m must be a whole number of 1 or more.`;
    if (typeof twoThetaDeg !== 'number' || !Number.isFinite(twoThetaDeg)) return `The measured 2θ of order ${m} is not a number.`;
    if (twoThetaDeg <= 0) return `The measured 2θ of order ${m} must be larger than 0°.`;
    if (twoThetaDeg >= 180) return `The measured 2θ of order ${m} must be smaller than 180°.`;
    if (seen.has(m)) return `Order ${m} is entered twice. Each order number may appear only once.`;
    seen.add(m);
  }
  if (orders.length < 2) return 'Enter at least two orders. A straight line needs two points.';
  return null;
}

/**
 * Fit the straight line sin²θ_m = a·m² + b to the measured orders.
 *
 * Standard errors come from the ordinary least-squares covariance with n − 2
 * degrees of freedom and are propagated as σD = (D/2)·σa/a and
 * σ(2θc) = (2θc/2)·σb/b. With exactly two orders the line passes through both
 * points, so there are no standard errors.
 */
export function fitOrders(lambdaA: number, orders: MeasuredOrder[]): OrdersResult {
  const problem = validate(lambdaA, orders);
  if (problem) return fail(problem);

  const n = orders.length;
  const xs = orders.map((o) => o.m * o.m);
  const ys = orders.map((o) => Math.sin((o.twoThetaDeg / 2) * DEG) ** 2);
  const xbar = xs.reduce((s, x) => s + x, 0) / n;
  const ybar = ys.reduce((s, y) => s + y, 0) / n;
  let sxx = 0;
  let sxy = 0;
  for (let i = 0; i < n; i++) {
    sxx += (xs[i] - xbar) ** 2;
    sxy += (xs[i] - xbar) * (ys[i] - ybar);
  }
  const a = sxy / sxx;
  const b = ybar - a * xbar;
  if (!(a > 0)) {
    return fail('The angles do not grow with the order number, so no period can be found. Check the order numbers and the angles.');
  }

  let sse = 0;
  for (let i = 0; i < n; i++) sse += (ys[i] - (a * xs[i] + b)) ** 2;
  const rmsSin2 = Math.sqrt(sse / n);

  const D = lambdaA / (2 * Math.sqrt(a));
  const twoDelta = b;
  const twoThetaC = b > 0 ? (2 * Math.sqrt(b)) / DEG : null;

  let sigmaD: number | null = null;
  let sigmaTwoDelta: number | null = null;
  let sigmaTwoThetaC: number | null = null;
  if (n >= 3) {
    const s2 = sse / (n - 2);
    const sigmaA = Math.sqrt(s2 / sxx);
    const sigmaB = Math.sqrt(s2 * (1 / n + (xbar * xbar) / sxx));
    sigmaD = (D / 2) * (sigmaA / a);
    sigmaTwoDelta = sigmaB;
    if (twoThetaC !== null) sigmaTwoThetaC = (twoThetaC / 2) * (sigmaB / b);
  }

  const predicted = orders.map((o) => predictTwoTheta(o.m, D, twoDelta, lambdaA));
  const residuals = orders.map((o, i) => {
    const p = predicted[i];
    return p === null ? null : o.twoThetaDeg - p;
  });

  return { ok: true, n, D, sigmaD, twoDelta, sigmaTwoDelta, twoThetaC, sigmaTwoThetaC, predicted, residuals, rmsSin2 };
}

/**
 * The CoC4 example of Chapter 11: the measured Co/C multilayer at
 * λ = 1.541874 Å, its six clear orders. The chapter seeds the period from
 * these six and then finds orders 7 and 8 where the seed predicts them.
 */
export const COC4_LAMBDA_A = 1.541874;
export const COC4_ORDERS: readonly MeasuredOrder[] = Object.freeze([
  { m: 1, twoThetaDeg: 1.6975 },
  { m: 2, twoThetaDeg: 3.2695 },
  { m: 3, twoThetaDeg: 4.8775 },
  { m: 4, twoThetaDeg: 6.4825 },
  { m: 5, twoThetaDeg: 8.1025 },
  { m: 6, twoThetaDeg: 9.7135 },
]);

/** A typographic minus sign (U+2212) for a displayed negative number. */
export const withMinus = (s: string) => s.replace(/^-/, '−');

/**
 * A small value and its standard error in one power of ten, never in
 * e-notation: (2.08e-5, 1.1e-7) → "(2.08 ± 0.01) × 10⁻⁵". Without a sigma:
 * "2.08 × 10⁻⁵". The power of ten is taken from the value.
 */
export function formatScaled(value: number, sigma: number | null, digits = 2): string {
  if (!Number.isFinite(value)) return '';
  let k = value === 0 ? 0 : Math.floor(Math.log10(Math.abs(value)));
  // Rounding can carry the mantissa to 10.00; move one power up.
  if (Math.abs(Number((value / 10 ** k).toFixed(digits))) >= 10) k += 1;
  const scale = 10 ** k;
  const mant = withMinus((value / scale).toFixed(digits));
  const tail = k === 0 ? '' : ` × 10${superscript(k)}`;
  if (sigma === null || !Number.isFinite(sigma)) return `${mant}${tail}`;
  const sig = (sigma / scale).toFixed(digits);
  return k === 0 ? `${mant} ± ${sig}` : `(${mant} ± ${sig})${tail}`;
}
