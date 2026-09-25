/**
 * The shared KaTeX preamble (STYLE.md §6, "Mathematics"). Chapters may use
 * these macros and KaTeX built-ins, nothing else. The web build
 * (astro.config.mjs) and the print renderer read this one object, so a formula
 * cannot typeset on one output and fail on the other.
 *
 * Add a macro here only when a symbol in NOTATION.md needs one, and add the
 * NOTATION.md entry in the same pass.
 */
export const KATEX_MACROS = {
  // Ångström as a unit after a number: $35\,\Ang$. KaTeX's own \AA is text-mode
  // only, so a math-mode unit needs this wrapper.
  '\\Ang': '\\text{\\AA}',
  // Period-averaged refractive decrement, NOTATION.md §3 (Structure).
  '\\dbar': '\\bar{\\delta}',
};
