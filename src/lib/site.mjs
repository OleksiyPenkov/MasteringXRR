/**
 * Where the site is served from. The one place this is decided.
 *
 * astro.config.mjs (`base`), scripts/check-links.mjs, playwright.config.ts and
 * the PDF pipeline all read it from here, so a move to a different URL is a
 * one-line change. `npm run deploy` checks that its destination folder has the
 * same name.
 */
export const BASE = '/MasteringXRR';

/**
 * Port for `astro dev` and `astro preview`. Not Astro's default 4321, which the
 * Vacuum book's preview uses: when both ran, this book's preview moved to the
 * next free port and the tests waited on the wrong one.
 */
export const PORT = 4331;

/** The book's working title, shown in the top bar and the page <title>. */
export const BOOK_TITLE = 'Mastering XRR Fitting';
