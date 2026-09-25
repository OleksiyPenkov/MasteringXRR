import { defineConfig } from 'astro/config';
import svelte from '@astrojs/svelte';
import mdx from '@astrojs/mdx';
import { unified } from '@astrojs/markdown-remark';
import remarkMath from 'remark-math';
import remarkDirective from 'remark-directive';
import rehypeKatex from 'rehype-katex';
import remarkOutputDirectives from './src/lib/remark-output-directives.mjs';
import rehypeCollapseSources from './src/lib/rehype-collapse-sources.mjs';
import { KATEX_MACROS } from './src/lib/katex-macros.mjs';
import { BASE, PORT } from './src/lib/site.mjs';

// Astro 7.3 form: one unified() processor, which the MDX integration inherits.
// (Plugins passed to mdx({...}) or markdown.remarkPlugins are deprecated.)
const processor = unified({
  // remark-math before remark-directive, so `$…:…$` stays math.
  remarkPlugins: [remarkMath, remarkDirective, remarkOutputDirectives],
  // throwOnError / strict: an unknown macro or bad TeX fails the build instead
  // of printing red TeX into the page.
  // rehype-collapse-sources folds each page's Sources section into a <details>
  // on the web; the print renderer opens every <details>.
  rehypePlugins: [
    [rehypeKatex, { macros: KATEX_MACROS, throwOnError: true, strict: 'error' }],
    rehypeCollapseSources,
  ],
});

export default defineConfig({
  base: BASE,
  server: { port: PORT },
  markdown: { processor },
  integrations: [svelte(), mdx()],
});
