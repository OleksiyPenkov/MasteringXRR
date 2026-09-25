/**
 * Output-conditional content (STYLE.md §6, "Web and print").
 *
 *   :::print-only
 *   A static figure and a caption that stands alone.
 *   :::
 *
 *   :::web-only
 *   <SomeLiveFigure client:visible />
 *   :::
 *
 * remark-directive parses the fences; this plugin turns the two names the book
 * uses into <div class="print-only"> / <div class="web-only">. The stylesheet
 * hides .print-only on screen, and the print renderer removes .web-only and
 * shows .print-only. That is the whole mechanism: one source, never two copies.
 *
 * The Vacuum book's Policy.md prescribed Pandoc's `::: {.print-only}`, which
 * MDX cannot parse, and the rule was never implemented there. This is the
 * implemented form.
 *
 * Two safety rules, because a directive that silently vanishes loses text:
 *  - A container directive with any other name fails the build.
 *  - Text and leaf directives are not used by the book. remark-directive still
 *    parses `:word` in running prose as one (an angle written "2θ:0.6°", a
 *    ratio "1:3"), so those are turned back into the literal text they were.
 */
import { visit } from 'unist-util-visit';

export const OUTPUT_DIRECTIVES = ['print-only', 'web-only'];

/** The literal source text of an inline or leaf directive, rebuilt. */
function literal(node, colons) {
  const label = (node.children ?? []).map((c) => c.value ?? '').join('');
  return `${colons}${node.name}${label ? `[${label}]` : ''}`;
}

export default function remarkOutputDirectives() {
  return (tree, file) => {
    visit(tree, (node, index, parent) => {
      if (node.type === 'containerDirective') {
        if (!OUTPUT_DIRECTIVES.includes(node.name)) {
          const where = node.position ? ` at line ${node.position.start.line}` : '';
          throw new Error(
            `Unknown block ":::${node.name}"${where} in ${file?.path ?? 'a chapter'}. ` +
              `Only ${OUTPUT_DIRECTIVES.map((n) => `:::${n}`).join(' and ')} exist.`,
          );
        }
        node.data = { ...(node.data ?? {}), hName: 'div', hProperties: { className: [node.name] } };
        return;
      }
      if ((node.type === 'textDirective' || node.type === 'leafDirective') && parent && index != null) {
        const text = { type: 'text', value: literal(node, node.type === 'textDirective' ? ':' : '::') };
        parent.children[index] = node.type === 'leafDirective' ? { type: 'paragraph', children: [text] } : text;
      }
    });
  };
}
