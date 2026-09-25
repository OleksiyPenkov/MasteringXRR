import { describe, expect, it } from 'vitest';
import remarkOutputDirectives from './remark-output-directives.mjs';

// Hand-built mdast trees, shaped as remark-directive emits them, so the test does
// not depend on the parser packages Astro brings in transitively.
const run = (tree: any) => {
  remarkOutputDirectives()(tree, { path: 'test.mdx' });
  return tree;
};

const container = (name: string) => ({
  type: 'containerDirective',
  name,
  children: [{ type: 'paragraph', children: [{ type: 'text', value: 'body' }] }],
  position: { start: { line: 7 } },
});

describe('remarkOutputDirectives', () => {
  it('turns :::print-only and :::web-only into classed divs', () => {
    for (const name of ['print-only', 'web-only']) {
      const tree = run({ type: 'root', children: [container(name)] });
      expect(tree.children[0].data).toEqual({ hName: 'div', hProperties: { className: [name] } });
      expect(tree.children[0].children[0].children[0].value).toBe('body');
    }
  });

  it('fails the build on any other block name, with the line', () => {
    expect(() => run({ type: 'root', children: [container('printonly')] })).toThrow(
      /Unknown block ":::printonly" at line 7 in test\.mdx/,
    );
  });

  it('restores a stray inline directive to the text it was', () => {
    // "a ratio of 1:three" in prose parses as text "…1" + textDirective "three".
    const tree = run({
      type: 'root',
      children: [
        {
          type: 'paragraph',
          children: [
            { type: 'text', value: 'ratio 1' },
            { type: 'textDirective', name: 'three', children: [] },
          ],
        },
      ],
    });
    expect(tree.children[0].children.map((c: any) => c.value).join('')).toBe('ratio 1:three');
  });

  it('restores a leaf directive to a paragraph of literal text', () => {
    const tree = run({
      type: 'root',
      children: [{ type: 'leafDirective', name: 'note', children: [{ type: 'text', value: 'x' }] }],
    });
    expect(tree.children[0]).toEqual({
      type: 'paragraph',
      children: [{ type: 'text', value: '::note[x]' }],
    });
  });
});
