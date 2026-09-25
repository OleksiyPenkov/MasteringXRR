import type { APIRoute } from 'astro';
import { getCollection } from 'astro:content';
import { buildSections } from '../lib/sections';

/**
 * Published so the print renderer (pdf-build/) reads the real page list off the
 * preview server instead of keeping a hand-written copy.
 */
export const GET: APIRoute = async () => {
  const chapters = await getCollection('chapters');
  return new Response(JSON.stringify(buildSections(chapters), null, 2), {
    headers: { 'Content-Type': 'application/json' },
  });
};
