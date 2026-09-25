/**
 * The book's Parts: the one place they are named. OUTLINE.md is the source; a
 * Part renamed there is renamed here, and the nav, the home page, the chapter
 * eyebrow and the PDF contents all follow.
 *
 * `front` (the Introduction) and `back` (the appendices) are not numbered
 * Parts, and display without a "Part N" prefix.
 */
export const PART_KEYS = ['front', '1', '2', '3', '4', '5', 'back'] as const;
export type PartKey = (typeof PART_KEYS)[number];

export interface Part {
  key: PartKey;
  name: string;
  numbered: boolean;
}

export const PARTS: Part[] = [
  { key: 'front', name: 'Front Matter', numbered: false },
  { key: '1', name: 'Getting Started', numbered: true },
  { key: '2', name: 'The Physics You Need, and No More', numbered: true },
  { key: '3', name: 'The Fitting Workflow, Step by Step', numbered: true },
  { key: '4', name: 'Special Cases and Reporting', numbered: true },
  { key: '5', name: 'The Part of Tens', numbered: true },
  { key: 'back', name: 'Appendices', numbered: false },
];

export function getPart(key: string): Part | undefined {
  return PARTS.find((p) => p.key === key);
}

/** Home page and PDF contents: "Part 2: The Physics You Need, and No More" | "Appendices". */
export function partHeading(key: string): string {
  const p = getPart(key);
  if (!p) return key;
  return p.numbered ? `Part ${p.key}: ${p.name}` : p.name;
}

/** Sidebar group label: "Part 2" | "Appendices". */
export function partNavLabel(key: string): string {
  const p = getPart(key);
  if (!p) return key;
  return p.numbered ? `Part ${p.key}` : p.name;
}

/**
 * How a page is labeled in front of its title: "Chapter 4", "Appendix B", or
 * nothing for the Introduction. `number` is the frontmatter field: '' for an
 * unnumbered page, digits for a chapter, a capital letter for an appendix.
 */
export function pageLabel(number: string): string {
  if (number === '') return '';
  return /^[A-Z]$/.test(number) ? `Appendix ${number}` : `Chapter ${number}`;
}

/** Chapter-header eyebrow: "Part 2 · Chapter 4" | "Appendices · Appendix B" | "Front Matter". */
export function pageEyebrow(part: string, number: string): string {
  const label = pageLabel(number);
  return label ? `${partNavLabel(part)} · ${label}` : partNavLabel(part);
}
