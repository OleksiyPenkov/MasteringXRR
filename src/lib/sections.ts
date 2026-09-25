import { partHeading, pageLabel } from './parts';

/** One page of the book as the PDF pipeline consumes it, in reading order. */
export interface SectionDescriptor {
  slug: string;
  title: string;
  /** '' for the Introduction, digits for a chapter, a letter for an appendix. */
  number: string;
  /** "Chapter 4" | "Appendix B" | "" */
  label: string;
  order: number;
  part: string;
  partHeading: string;
}

/** Minimal shape of a content-collection entry, so this stays unit-testable. */
export interface ChapterLike {
  id: string;
  data: { title: string; number: string; order: number; part: string };
}

/**
 * Turn content-collection entries into the ordered page list that
 * src/pages/sections.json.ts publishes for the print renderer. Resolving the
 * labels here means the Python side never keeps its own copy of the Part names.
 */
export function buildSections(chapters: ChapterLike[]): SectionDescriptor[] {
  return [...chapters]
    .sort((a, b) => a.data.order - b.data.order)
    .map((c) => ({
      slug: c.id,
      title: c.data.title,
      number: c.data.number,
      label: pageLabel(c.data.number),
      order: c.data.order,
      part: c.data.part,
      partHeading: partHeading(c.data.part),
    }));
}
