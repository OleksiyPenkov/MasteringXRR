import { describe, it, expect } from 'vitest';
import { renderInline } from './inline-markdown';

describe('renderInline', () => {
  it('renders emphasis', () => {
    expect(renderInline('a *and* b')).toBe('a <em>and</em> b');
  });

  it('renders strong before emphasis', () => {
    expect(renderInline('**bold** and *soft*')).toBe('<strong>bold</strong> and <em>soft</em>');
  });

  it('escapes HTML in the source', () => {
    expect(renderInline('<script>x</script>')).toBe('&lt;script&gt;x&lt;/script&gt;');
  });

  it('leaves a lone asterisk alone', () => {
    expect(renderInline('2 * 3 = 6')).toBe('2 * 3 = 6');
  });

  it('does not span across the whole caption greedily', () => {
    expect(renderInline('*a* mid *b*')).toBe('<em>a</em> mid <em>b</em>');
  });

  it('passes plain text through unchanged', () => {
    expect(renderInline('Figure 3.1 - conductance')).toBe('Figure 3.1 - conductance');
  });

  // DataTable.astro cases
  it('renders emphasis in table cells (introduction.mdx real case)', () => {
    expect(renderInline('... gravitational-wave detectors — instruments that *are* vacuum chambers.'))
      .toBe('... gravitational-wave detectors — instruments that <em>are</em> vacuum chambers.');
  });

  it('preserves em dashes and non-ASCII characters in table cells', () => {
    expect(renderInline('λ/4 — quarter wavelength')).toBe('λ/4 — quarter wavelength');
  });

  it('does not transform a bare asterisk used as multiplication or footnote marker', () => {
    expect(renderInline('voltage × current*')).toBe('voltage × current*');
  });

  // Unicode word-boundary cases: \w is ASCII-only, so an asterisk next to a
  // non-ASCII letter used to be treated as unprotected and a pair of bare
  // footnote markers either side of one would get merged into a spurious <em>.
  it('does not merge separate footnote markers flanking a Greek letter', () => {
    expect(renderInline('λ*, μ*')).toBe('λ*, μ*');
  });

  it('does not merge a footnote marker and punctuation flanking a Greek letter', () => {
    expect(renderInline('Ω*,x*')).toBe('Ω*,x*');
  });

  it('still renders real emphasis immediately after a non-ASCII letter', () => {
    expect(renderInline('λ *and* μ')).toBe('λ <em>and</em> μ');
  });

  // Script notation. These captions printed the underscore on the page.
  it('sets a subscript in a caption (Figure 2.2, the real case)', () => {
    expect(renderInline('speed in units of the most-probable speed v_p)'))
      .toBe('speed in units of the most-probable speed v<sub>p</sub>)');
  });

  it('takes the whole run as the subscript, not the first letter', () => {
    expect(renderInline('the rms speed (v_rms)')).toBe('the rms speed (v<sub>rms</sub>)');
  });

  it('returns to the baseline after the script', () => {
    expect(renderInline('the total gas load Q_total, nearly constant'))
      .toBe('the total gas load Q<sub>total</sub>, nearly constant');
  });

  it('sets a superscript', () => {
    expect(renderInline('at 10^-3 Torr')).toBe('at 10<sup>-3</sup> Torr');
  });

  it('takes a braced run when the plain one would stop too early', () => {
    expect(renderInline('P_{ult,2} falls')).toBe('P<sub>ult,2</sub> falls');
  });

  it('leaves the already-subscript digit of a formula on the baseline', () => {
    // ch6's spinning-rotor header. U+2082 is drawn low already, so M-sub-N
    // followed by a baseline "2" reads correctly without nesting scripts.
    expect(renderInline('Spinning rotor: √(M_N₂/M)'))
      .toBe('Spinning rotor: √(M<sub>N</sub>₂/M)');
  });

  it('composes with emphasis rather than fighting it', () => {
    expect(renderInline('*v_p* matters')).toBe('<em>v<sub>p</sub></em> matters');
  });

  it('does not let script notation reopen an escaped tag', () => {
    expect(renderInline('<b>x_1</b>')).toBe('&lt;b&gt;x<sub>1</sub>&lt;/b&gt;');
  });

  it('leaves prose with no script notation untouched', () => {
    expect(renderInline('a pump removes gas at speed S'))
      .toBe('a pump removes gas at speed S');
  });
});
