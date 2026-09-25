import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';
import { PART_KEYS } from './lib/parts';

const chapters = defineCollection({
  loader: glob({ pattern: '**/*.mdx', base: './src/content/chapters' }),
  schema: z.object({
    title: z.string(),
    part: z.enum(PART_KEYS),
    /** '' for the Introduction, "1".."26" for a chapter, "A".."D" for an appendix. */
    number: z.string().regex(/^(|[1-9]\d?|[A-Z])$/),
    /** Reading order across the whole book. Leave gaps (10, 20, …) for insertions. */
    order: z.number().int(),
    /**
     * The chapter-opening "In This Chapter" list (STYLE.md §3): 3–5 plain
     * phrases taken from the chapter's learning objectives in OUTLINE.md.
     */
    inThisChapter: z.array(z.string()).max(5).default([]),
  }),
});

export const collections = { chapters };
