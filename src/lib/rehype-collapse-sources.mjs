/**
 * Collapse every page's `## Sources` section on the web.
 *
 * The h2 whose text is "Sources" and everything after it, up to the next h2 or
 * the end of the page, is moved into
 *   <details class="sources-section"><summary class="sources-summary"><h2>…</h2></summary>…</details>
 * The h2 stays an h2 and keeps the id Astro gives it (`#sources`), so the link
 * check, the Contents (pdf-build/headings.py leaves it out by name) and the
 * running head still find it. The print renderer opens every <details>
 * (pdf-build/render-sections.mjs), so the PDF shows the section in full.
 */

function textOf(node) {
  if (node.type === 'text') return node.value;
  return (node.children ?? []).map(textOf).join('');
}

function isH2(node) {
  return node.type === 'element' && node.tagName === 'h2';
}

export function isSourcesHeading(node) {
  return isH2(node) && textOf(node).trim() === 'Sources';
}

/** Wrap the Sources section of a hast root in place. Returns the root. */
export function collapseSources(root) {
  const kids = root.children ?? [];
  const start = kids.findIndex(isSourcesHeading);
  if (start < 0) return root;
  let end = kids.findIndex((n, i) => i > start && isH2(n));
  if (end < 0) end = kids.length;
  const heading = kids[start];
  const body = kids.slice(start + 1, end);
  const details = {
    type: 'element',
    tagName: 'details',
    properties: { className: ['sources-section'] },
    children: [
      { type: 'element', tagName: 'summary', properties: { className: ['sources-summary'] }, children: [heading] },
      ...body,
    ],
  };
  kids.splice(start, end - start, details);
  return root;
}

export default function rehypeCollapseSources() {
  return (tree) => {
    collapseSources(tree);
  };
}
