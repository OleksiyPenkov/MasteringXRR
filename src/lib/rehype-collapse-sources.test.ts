import { describe, expect, it } from 'vitest';
import { collapseSources, isSourcesHeading } from './rehype-collapse-sources.mjs';

const text = (value: string) => ({ type: 'text', value });
const el = (tagName: string, children: any[] = [], properties: any = {}) =>
  ({ type: 'element', tagName, properties, children });

describe('collapseSources', () => {
  it('wraps the Sources heading and everything after it in a closed <details>', () => {
    const root = { type: 'root', children: [
      el('h2', [text('Reading a curve')]), el('p', [text('body')]),
      el('h2', [text('Sources')]), el('ul', [el('li', [text('Parratt (1954)')])]), el('p', [text('Cross-references')]),
    ] };
    collapseSources(root);
    expect(root.children).toHaveLength(3);
    const details: any = root.children[2];
    expect(details.tagName).toBe('details');
    expect(details.properties.className).toEqual(['sources-section']);
    expect(details.properties.open).toBeUndefined();
    const summary = details.children[0];
    expect(summary.tagName).toBe('summary');
    expect(summary.children[0].tagName).toBe('h2');
    expect(details.children.map((c: any) => c.tagName)).toEqual(['summary', 'ul', 'p']);
  });

  it('stops at the next h2', () => {
    const root = { type: 'root', children: [
      el('h2', [text('Sources')]), el('p', [text('a')]), el('h2', [text('After')]),
    ] };
    collapseSources(root);
    expect(root.children.map((c: any) => c.tagName)).toEqual(['details', 'h2']);
  });

  it('leaves a page without Sources alone, and ignores an h3 named Sources', () => {
    const children = [el('h2', [text('Other')]), el('h3', [text('Sources')])];
    const root = { type: 'root', children: [...children] };
    collapseSources(root);
    expect(root.children).toEqual(children);
  });

  it('reads the heading text through nested elements', () => {
    expect(isSourcesHeading(el('h2', [el('span', [text(' Sources ')])]))).toBe(true);
    expect(isSourcesHeading(el('h2', [text('Sources of error')]))).toBe(false);
  });
});
