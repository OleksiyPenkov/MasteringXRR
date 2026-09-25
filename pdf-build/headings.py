"""Ordered h2 headings per page, for the Contents and the running head.

links.build_anchor_map returns a dict and so loses document order, which both
consumers need. This reads the same dist/ artifact and keeps the order.

The Vacuum book listed only numbered headings ("6.1 ...") in its Contents,
filtering its boilerplate out with a positive number pattern. This book's
headings are unnumbered, in the "... for Dummies" format, so the Contents
lists every h2 except the ones every page carries (EXCLUDED_FROM_CONTENTS).
"""
from pathlib import Path

from bs4 import BeautifulSoup

# Headings every content page ends with (STYLE.md §7). They carry no locator
# information, so they stay out of the Contents; they still count for the
# running head, where "Sources" is exactly what the page shows.
EXCLUDED_FROM_CONTENTS = frozenset({"Sources"})


def section_headings(dist_dir: Path) -> dict[str, list[tuple[str, str]]]:
    """{slug: [(heading_id, visible_text)]} for every h2 with an id, in order."""
    out: dict[str, list[tuple[str, str]]] = {}
    for index in sorted(Path(dist_dir).glob("*/index.html")):
        slug = index.parent.name
        soup = BeautifulSoup(index.read_text(encoding="utf-8"), "lxml")
        items = []
        for h in soup.find_all("h2", id=True):
            # KaTeX renders twice (MathML + HTML); the PDF text layer has only
            # the HTML copy, so the MathML one must go or no heading matches.
            for mathml in h.select(".katex-mathml"):
                mathml.decompose()
            text = " ".join(h.get_text().split())
            if text:
                items.append((h["id"], text))
        out[slug] = items
    return out


def contents_subsections(dist_dir: Path) -> dict[str, list[tuple[str, str]]]:
    """section_headings(), minus the per-page boilerplate, order kept."""
    return {
        slug: [(hid, text) for hid, text in items if text not in EXCLUDED_FROM_CONTENTS]
        for slug, items in section_headings(dist_dir).items()
    }
