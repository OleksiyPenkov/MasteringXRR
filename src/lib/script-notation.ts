/** The book's one definition of what `v_p` and `10^3` mean in authored text.
 *
 * Two renderers need it and they must not drift apart: figure labels become SVG
 * `<tspan>`s with an explicit size and baseline shift (see figure-helpers), and
 * caption and table prose becomes HTML `<sub>` / `<sup>` (see inline-markdown).
 * The same caption string is often set both ways - "the most-probable speed
 * v_p" appears in Figure 2.2's caption and, as a label, inside the figure - so a
 * notation that meant one thing in one place and another in the other would be
 * worse than no notation at all.
 *
 * Pure - no DOM, no Astro, no tokens.
 */

export type ScriptKind = 'base' | 'sub' | 'sup';

export interface ScriptPart { text: string; script: ScriptKind; }

/** `_x` / `^x` for a single alphanumeric run, `_{...}` / `^{...}` for anything
 * else. An unbraced run stops at punctuation and whitespace, so `P_ult'` keeps
 * its prime on the baseline and `Q_total = Σ (sources)` returns to the baseline
 * at the space.
 *
 * A leading sign is part of the run - `10^-3` is the way anyone writes a
 * negative exponent, and requiring `10^{-3}` for it would be a trap. Both the
 * hyphen-minus an author types and the real U+2212 the book prefers are
 * accepted; the sign still has to be followed by an alphanumeric, so a stray
 * `^ -` in prose matches nothing.
 *
 * Deliberately NOT anchored to a word boundary on the left: the only underscores
 * in the book's captions and tables are this notation (audited - six captions
 * and three table cells, every one of them a subscript that was printing as a
 * literal). Anything that must keep a real underscore, such as a filename or a
 * code identifier, is already set in a `<code>` span, which never reaches
 * either renderer. */
export const scriptPattern = () => /([_^])(?:\{([^}]*)\}|([-−]?[A-Za-z0-9]+))/g;

/** Split authored text into baseline runs and script runs, in order. */
export function splitScripts(text: string): ScriptPart[] {
  const parts: ScriptPart[] = [];
  const re = scriptPattern();
  let cursor = 0;

  const push = (t: string, script: ScriptKind) => {
    if (t) parts.push({ text: t, script });
  };

  for (let m = re.exec(text); m; m = re.exec(text)) {
    push(text.slice(cursor, m.index), 'base');
    push(m[2] ?? m[3], m[1] === '_' ? 'sub' : 'sup');
    cursor = m.index + m[0].length;
  }
  push(text.slice(cursor), 'base');

  return parts;
}

/** True when `text` carries any script notation at all. */
export const hasScripts = (text: string): boolean => scriptPattern().test(text);
