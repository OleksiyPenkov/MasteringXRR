import { describe, expect, it } from 'vitest';
import { buildSections } from './sections';

const entry = (id: string, order: number, part: string, number: string) => ({
  id,
  data: { title: id.toUpperCase(), number, order, part },
});

describe('buildSections', () => {
  it('sorts by order and resolves labels and Part headings', () => {
    const out = buildSections([
      entry('ch4', 40, '2', '4'),
      entry('introduction', 0, 'front', ''),
      entry('appendix-a', 900, 'back', 'A'),
    ]);
    expect(out.map((s) => s.slug)).toEqual(['introduction', 'ch4', 'appendix-a']);
    expect(out[0]).toMatchObject({ label: '', partHeading: 'Front Matter' });
    expect(out[1]).toMatchObject({ label: 'Chapter 4', partHeading: 'Part 2: The Physics You Need, and No More' });
    expect(out[2]).toMatchObject({ label: 'Appendix A', partHeading: 'Appendices' });
  });

  it('does not mutate its input', () => {
    const input = [entry('b', 2, '1', '2'), entry('a', 1, '1', '1')];
    buildSections(input);
    expect(input.map((e) => e.id)).toEqual(['b', 'a']);
  });
});
