/** Deciding whether a rendered section fits the printed content box.
 *
 * Split out of render-sections.mjs so the decision can be tested. The rule it
 * enforces exists because Chrome's printToPDF shrink-to-fits an ENTIRE rendered
 * section by box/contentWidth the moment one element overflows, and this
 * pipeline renders one section per PDF - so a single over-wide table in
 * Chapter 2 reprinted every figure label in that chapter at 6.46pt while the
 * identical authored 8pt token in Chapter 1 printed at 7.75pt.
 *
 * The two halves are deliberately separate:
 *
 *   collectPrintBoxCandidates  runs inside the browser and only measures.
 *   judgePrintBox              is pure, and holds every decision.
 *
 * Everything that could be got wrong - what counts as an overflow, what is
 * exempt, whether a clipped element still fails - lives in the pure half.
 */

/** Sub-pixel slack. Layout arithmetic lands a hair over the box often enough
 * that a bare `>` would report rounding as a defect. */
export const OVERFLOW_EPS = 0.5;

/**
 * @typedef {object} PrintBoxCandidate
 * @property {string} tag        lowercase tag name
 * @property {number} right      right edge, CSS px from the viewport origin
 * @property {number} width
 * @property {number} height
 * @property {boolean} clipped   an ancestor between it and the root clips overflow
 * @property {boolean} katexGlyph  part of a KaTeX stretchy glyph (see below)
 * @property {number} depth      distance from the root, for tie-breaking
 * @property {string} chain      ancestor chain, for the failure message
 * @property {string} text
 */

/**
 * Decide whether a section fits, and say what is at fault if it does not.
 *
 * `scrollWidth` alone is NOT sufficient, and that was a real hole in the first
 * version of this gate: the document's scroll width excludes anything clipped
 * by an intermediate `overflow: hidden`, so adding one line of CSS -
 * `.katex-display { overflow-x: hidden }`, the first thing anyone reaches for
 * when an equation is too wide - made the gate report "all 30 sections fit"
 * while Appendix A's equations printed truncated at the right margin. Nothing
 * else in the pipeline looks at clipped text. So clipped overflow fails too,
 * and it is reported separately because the fix is different: unclipped
 * overflow shrinks the page, clipped overflow silently deletes content.
 *
 * @param {{boxPx: number, scrollWidth: number, candidates: PrintBoxCandidate[]}} input
 */
export function judgePrintBox({ boxPx, scrollWidth, candidates }) {
  const over = candidates.filter(
    (c) => c.width > 0 && c.height > 0 && !c.katexGlyph && c.right > boxPx + OVERFLOW_EPS,
  );
  // Widest first, then deepest: the leaf is the culprit and its ancestors are
  // only carrying it, so the deepest element at a given right edge is the one
  // worth naming.
  const rank = (a, b) => b.right - a.right || b.depth - a.depth;
  const visible = over.filter((c) => !c.clipped).sort(rank);
  const clipped = over.filter((c) => c.clipped).sort(rank);

  return {
    ok: scrollWidth <= boxPx && clipped.length === 0,
    scrollWidth,
    scale: Math.min(1, boxPx / scrollWidth),
    visible,
    clipped,
    worst: visible[0] || clipped[0] || null,
  };
}

/**
 * Measure every laid-out box on the page. Runs in the browser via
 * page.evaluate, so it must not reference anything outside itself.
 *
 * @param {number} boxPx
 * @returns {{scrollWidth: number, candidates: PrintBoxCandidate[]}}
 */
export function collectPrintBoxCandidates(boxPx) {
  // An <svg> lays out as a box in the surrounding flow; the shapes inside it do
  // not, they are painted in the SVG's own coordinate system and their
  // client rects can be wildly larger than the box that clips them. So consider
  // HTML elements and outermost <svg> elements, and nothing below an <svg>.
  //
  // (The first version of this test was `el instanceof HTMLElement`, which threw
  // away the <svg> box itself along with its contents - so every figure in the
  // book was invisible to the gate that is meant to protect the figures.)
  const outermostSvg = (el) => el.tagName.toLowerCase() === 'svg' && !el.ownerSVGElement;
  const isLayoutBox = (el) => el instanceof HTMLElement || outermostSvg(el);

  // The one deliberate exemption. KaTeX draws \sqrt rules and stretchy
  // delimiters as <svg>s hundreds of ems wide, sized to be cropped by a wrapper
  // with overflow:hidden - the overflow is the mechanism, not a defect. This is
  // matched narrowly, on being (or being inside) an <svg> that sits inside a
  // .katex, rather than by the old blanket "is clipped" test, because that
  // blanket test is exactly what let genuine clipped overflow through.
  const isKatexGlyph = (el) => {
    const svg = outermostSvg(el) ? el : el.ownerSVGElement;
    return !!(svg && svg.closest('.katex'));
  };

  const isClipped = (el) => {
    for (let p = el.parentElement; p && p !== document.documentElement; p = p.parentElement) {
      const cs = getComputedStyle(p);
      if (cs.overflowX !== 'visible' || cs.overflowY !== 'visible') return true;
    }
    return false;
  };

  // Content deliberately removed from the visual flow (screen-reader text, the
  // MathML KaTeX keeps beside its HTML) is clipped on purpose and prints
  // nothing, so it cannot be truncated in any sense a reader would notice.
  const isVisuallyHidden = (el) => {
    for (let p = el; p && p !== document.documentElement; p = p.parentElement) {
      const cs = getComputedStyle(p);
      if (cs.visibility !== 'visible' || cs.opacity === '0') return true;
      if (cs.clip !== 'auto' && cs.clip !== '') return true;      // clip: rect(1px,1px,1px,1px)
      if (cs.clipPath && cs.clipPath !== 'none') return true;
    }
    return false;
  };

  const chain = (el) => {
    const out = [];
    for (let p = el; p && p !== document.body; p = p.parentElement) {
      const cls = (typeof p.className === 'string' ? p.className : '').trim().split(/\s+/)[0] || '';
      out.push(p.tagName.toLowerCase() + (cls ? '.' + cls : ''));
    }
    return out.slice(0, 5).join(' < ');
  };

  const candidates = [];
  for (const el of document.querySelectorAll('body *')) {
    if (!isLayoutBox(el)) continue;
    const r = el.getBoundingClientRect();
    if (r.width <= 0 || r.height <= 0) continue;
    if (r.right <= boxPx + 0.5) continue;
    if (isVisuallyHidden(el)) continue;
    let depth = 0;
    for (let p = el; p.parentElement; p = p.parentElement) depth++;
    candidates.push({
      tag: el.tagName.toLowerCase(),
      right: +r.right.toFixed(1),
      width: +r.width.toFixed(1),
      height: +r.height.toFixed(1),
      clipped: isClipped(el),
      katexGlyph: isKatexGlyph(el),
      depth,
      chain: chain(el),
      text: (el.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 60),
    });
  }
  return { scrollWidth: document.documentElement.scrollWidth, candidates };
}
