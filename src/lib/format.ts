/**
 * Number formatting for display.
 *
 * House rule: a number shown to a reader never appears in e-notation.
 * 1.4e-5 is how a machine writes it; the book writes 1.4 × 10⁻⁵.
 *
 * These return plain Unicode rather than LaTeX so the same string is safe in
 * an SVG <text> label, a plain-text component prop, and prose alike. Where a
 * context actually renders KaTeX (MDX body, Quiz strings), write $…$ by hand
 * instead — see the chapters.
 */

const SUPERSCRIPTS: Record<string, string> = {
  '0': '⁰',
  '1': '¹',
  '2': '²',
  '3': '³',
  '4': '⁴',
  '5': '⁵',
  '6': '⁶',
  '7': '⁷',
  '8': '⁸',
  '9': '⁹',
  '-': '⁻',
};

/** Render an integer exponent with Unicode superscript glyphs: -5 -> ⁻⁵ */
export function superscript(exponent: number | string): string {
  return String(exponent)
    .split('')
    .map((ch) => SUPERSCRIPTS[ch] ?? ch)
    .join('');
}

/** Turn a JS exponential string ("1.30e-8", "6.2e+15") into 1.30 × 10⁻⁸. */
function fromExponentialString(s: string): string {
  const m = /^(-?[\d.]+)e([-+]?)(\d+)$/i.exec(s);
  if (!m) return s;
  const [, mantissa, sign, digits] = m;
  const exponent = (sign === '-' ? '-' : '') + String(Number(digits));
  return `${mantissa} × 10${superscript(exponent)}`;
}

/**
 * Always-exponential display: sci(1.4e-5) -> "1.40 × 10⁻⁵".
 * `digits` is digits after the decimal point, as in Number#toExponential.
 * An exponent of zero collapses to the plain mantissa, so sci(2) -> "2.00".
 */
export function sci(value: number, digits = 2): string {
  if (!Number.isFinite(value)) return '—';
  if (value === 0) return (0).toFixed(digits);
  const s = value.toExponential(digits);
  const exponent = Number(s.slice(s.indexOf('e') + 1));
  if (exponent === 0) return value.toFixed(digits);
  return fromExponentialString(s);
}

/**
 * The one to reach for in a live readout: plain where a plain number reads
 * better, house exponential only where it doesn't.
 *
 *   readable(10)     -> "10"          (not "1.00 × 10¹")
 *   readable(0.5)    -> "0.5"
 *   readable(1e-5)   -> "1.0 × 10⁻⁵"
 *
 * Inside [0.01, 10⁶) the value is shown plainly, rounded to `digits + 1`
 * significant figures with trailing zeros dropped, so a slider reads "10"
 * rather than "10.0". Outside that window the digits get hard to count and
 * it falls back to sci().
 */
export function readable(value: number, digits = 2): string {
  if (!Number.isFinite(value)) return '—';
  if (value === 0) return '0';
  const magnitude = Math.abs(value);
  if (magnitude >= 0.01 && magnitude < 1e6) {
    return String(Number(value.toPrecision(digits + 1)));
  }
  return sci(value, digits);
}

/**
 * A stored number as a reader should see it, with no invented precision:
 * 60000 -> "60000", 0.002 -> "0.002", 1e-7 -> "1 × 10⁻⁷".
 *
 * Everyday magnitudes stay plain; only values that JS would print in
 * e-notation get the × 10ⁿ treatment. Used for the ADS fact values.
 */
export function displayNumber(value: number): string {
  if (!Number.isFinite(value)) return '—';
  if (value === 0) return '0';
  const magnitude = Math.abs(value);
  if (magnitude >= 1e-3 && magnitude < 1e6) return String(value);
  return fromExponentialString(value.toExponential());
}

/**
 * Like Number#toPrecision, but never leaks e-notation:
 * precise(1.3e-8, 2) -> "1.3 × 10⁻⁸", precise(2.5, 2) -> "2.5".
 */
export function precise(value: number, digits = 3): string {
  if (!Number.isFinite(value)) return '—';
  const s = value.toPrecision(digits);
  return s.includes('e') ? fromExponentialString(s) : s;
}
