/** Minimal inline Markdown for figure captions and table cells: **strong**,
 * *emphasis*, and `v_p` / `10^3` script notation.
 *
 * Figure.astro used to emit the caption prop as plain text, so an author writing
 * *and* got literal asterisks on the printed page. The same was true of the
 * script notation, one layer up: Figure 2.2's caption printed "the most-probable
 * speed v_p" with the underscore showing, and so did five other captions and
 * three table cells. A full Markdown dependency is not warranted for three
 * constructs. Everything else is escaped. */
import { splitScripts } from './script-notation';

const ESCAPES: Record<string, string> = {
  '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
};

const TAG: Record<string, string> = { sub: 'sub', sup: 'sup' };

export function renderInline(text: string): string {
  const safe = text.replace(/[&<>"']/g, (c) => ESCAPES[c]);
  // Word-boundary detection is Unicode-aware (\p{L}\p{N}_, not \w): \w is
  // ASCII-only, so an asterisk next to a Greek letter (lambda, mu, Omega -
  // this book's tables are full of them) was left unprotected and a pair of
  // bare/footnote asterisks either side of one would get merged into a single
  // spurious <em>. \p{L}/\p{N} require the /u flag on both replaces.
  const emphasised = safe
    .replace(/\*\*([^*]+)\*\*/gu, '<strong>$1</strong>')
    .replace(/(?<![*\p{L}\p{N}_])\*([^*\s][^*]*?)\*(?![\p{L}\p{N}_])/gu, '<em>$1</em>');

  // Scripts run LAST, on text that already carries <strong>/<em> tags. Running
  // them first would leave the emphasis lookarounds staring at the '>' of an
  // inserted tag instead of the character the author wrote. Splitting rather
  // than replacing keeps the tags this function has already emitted intact -
  // none of them contain an underscore or a caret.
  return splitScripts(emphasised)
    .map(({ text, script }) =>
      script === 'base' ? text : `<${TAG[script]}>${text}</${TAG[script]}>`)
    .join('');
}
