"""Turn the PDF's dead cross-references into working internal jumps.

Each section is rendered separately from the preview server, so Chrome resolves
every <a href> against that origin and the assembled book is full of links to
http://localhost:<port>/..., which lead nowhere on any reader's device.

This reads the real heading ids out of dist/ (the artifact check-links.mjs has
already validated) and rewrites those annotations into page jumps. Ported from
the Vacuum book without its two-volume logic.
"""
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import unquote, urlparse

import fitz
from bs4 import BeautifulSoup

from siteconf import BASE_PATH

HEADING_TAGS = ("h1", "h2", "h3", "h4")


def build_anchor_map(dist_dir: Path) -> dict[tuple[str, str], str]:
    """(slug, fragment-id) -> text to find on the target's page, KaTeX MathML dropped.

    Headings map to their visible text. Figures (`<figure id="fig-4-1">`, the
    cross-reference labels of STYLE.md §6) map to their caption's label,
    "Figure 4-1:", which is unique in the book where a caption's prose may not be.
    """
    anchors: dict[tuple[str, str], str] = {}
    for index in sorted(Path(dist_dir).glob("*/index.html")):
        slug = index.parent.name
        soup = BeautifulSoup(index.read_text(encoding="utf-8"), "lxml")
        for heading in soup.find_all(HEADING_TAGS, id=True):
            for mathml in heading.select(".katex-mathml"):
                mathml.decompose()
            text = " ".join(heading.get_text().split())
            if text:
                anchors[(slug, heading["id"])] = text
        for fig in soup.find_all("figure", id=True):
            label = fig.select_one("figcaption strong")
            if label and label.get_text().strip():
                anchors[(slug, fig["id"])] = " ".join(label.get_text().split())
    return anchors


def expected_internal_targets(dist_dir: Path, slugs: list[str]) -> set[tuple[str, str]]:
    """Every (slug, fragment) the rendered pages' text links to, read from dist/.

    What the reader can click in print: links inside <article> (the web chrome
    is hidden in print), outside :::web-only blocks (removed in print). The
    PDF must end up with a jump for each one. assemble.py compares against
    this, so a cross-reference lost between the browser and the merged PDF
    fails the build: the Vacuum pipeline lost same-page links this way, and
    none of its checks could see it.
    """
    wanted: set[tuple[str, str]] = set()
    for slug in slugs:
        index = Path(dist_dir) / slug / "index.html"
        if not index.exists():
            continue
        soup = BeautifulSoup(index.read_text(encoding="utf-8"), "lxml")
        for article in soup.find_all("article"):
            for a in article.find_all("a", href=True):
                if a.find_parent(class_="web-only"):
                    continue
                href = a["href"]
                if href.startswith("#"):
                    wanted.add((slug, unquote(href[1:])))
                elif href.startswith(BASE_PATH):
                    path, _, frag = href[len(BASE_PATH):].partition("#")
                    target = path.strip("/")
                    if target and "." not in target.split("/")[-1]:
                        wanted.add((target, unquote(frag)))
    return wanted


@dataclass
class LinkStats:
    # Per ANNOTATION: Chromium emits one annotation per line box, so a wrapped
    # anchor counts twice and this number moves when prose reflows.
    internal: int = 0
    # Per TARGET (slug, fragment): reflow cannot move it. Gate on this one.
    internal_targets: set = field(default_factory=set)
    external_kept: int = 0
    unresolved_slug: int = 0
    fragment_hit: int = 0
    fragment_fallback: int = 0


def format_link_summary(stats: LinkStats) -> str:
    """One line, every count with its unit word (two different units above)."""
    return (
        f"Links: {stats.internal} internal link annotation(s) "
        f"over {len(stats.internal_targets)} distinct internal target(s) "
        f"({stats.fragment_hit} to a heading or figure, {stats.fragment_fallback} to a section start), "
        f"{stats.external_kept} external kept, {stats.unresolved_slug} unresolved"
    )


def parse_internal_href(url: str) -> tuple[str, str] | None:
    """('slug', 'fragment') for a preview-server link, else None.

    Only localhost URLs under the site's base path are ours. Everything else is
    a real destination and must survive untouched.
    """
    parsed = urlparse(url)
    if parsed.hostname not in ("localhost", "127.0.0.1"):
        return None
    if not parsed.path.startswith(BASE_PATH):
        return None
    slug = parsed.path[len(BASE_PATH):].strip("/")
    if not slug:
        return None
    return slug, unquote(parsed.fragment)


# The rendered h2 is 14pt and the h3 12pt; prose is 10.5pt, the Contents rows
# 8.5pt and the running heads 8pt. A line at 11.5pt or more is a heading.
HEADING_MIN_PT = 11.5


def _heading_line_on(page, probe: str, exact: bool = False) -> bool:
    """True if a line on the page is set at heading size and starts with probe
    (or, with exact, is probe)."""
    for block in page.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            spans = line["spans"]
            if not spans or max(s["size"] for s in spans) < HEADING_MIN_PT:
                continue
            text = "".join(s["text"] for s in spans).strip()
            if text == probe if exact else text.startswith(probe):
                return True
    return False


def _page_for_heading(doc, text: str, first: int, last: int) -> int | None:
    """First page in [first, last] that carries the heading.

    A page where the heading is set as a heading wins: a line at heading size
    that starts with the text. search_for alone ignores case and matches prose,
    so Chapter 2's "In This Chapter" box ("Finding your way around the main
    window") used to beat the heading "The main window" two pages later, and the
    running heads named the wrong section. Only when no heading-sized line
    matches (a heading set in the body size, as in the unit tests) does the
    plain text search decide.

    Tries the whole heading, then a 40- and 20-character prefix, because a long
    heading wraps and an exact match then fails. A truncated probe must match
    exactly one page: sibling headings can share a prefix, and sending a reader
    to the wrong section is worse than sending them to the chapter's start.

    A heading shorter than 6 characters ("Icons") is common in this book's
    format and was simply unfindable in the Vacuum version, which skipped every
    probe that short. It is accepted here only when it is found on exactly one
    page of the range; otherwise the result is None and the caller fails loudly.
    At heading size a short heading must be the whole line: Appendix D's letter
    heading "G" otherwise matches every term heading that starts with G.
    """
    short = len(text.strip()) < 6
    probes = ((text, short), (text[:40], True), (text[:20], True))
    for styled in (True, False):
        for probe, must_be_unique in probes:
            probe = probe.strip()
            if not probe or (len(probe) < 6 and probe != text.strip()):
                continue
            hits = [n for n in range(first, last + 1)
                    if (_heading_line_on(doc[n], probe, exact=short) if styled
                        else doc[n].search_for(probe, quads=False))]
            if not hits or (must_be_unique and len(hits) > 1):
                continue
            return hits[0]
    return None


def resolve_links(doc, entries, anchor_map, front_pages: int) -> LinkStats:
    """Rewrite the merged document's localhost URIs into internal jumps.

    A link to a slug that is not in this build (entries) is counted as
    unresolved; assemble.py fails the build on it.
    """
    stats = LinkStats()
    ranges = {
        e["slug"]: (front_pages + e["start_page"] - 1,
                    front_pages + e["start_page"] - 2 + e["pages"])
        for e in entries
    }
    for page in doc:
        for link in page.get_links():
            uri = link.get("uri")
            if not uri:
                continue
            parsed = parse_internal_href(uri)
            if parsed is None:
                stats.external_kept += 1
                continue
            slug, fragment = parsed
            if slug not in ranges:
                stats.unresolved_slug += 1
                continue
            first, last = ranges[slug]
            target = first
            if fragment:
                heading = anchor_map.get((slug, fragment))
                hit = _page_for_heading(doc, heading, first, last) if heading else None
                if hit is None:
                    stats.fragment_fallback += 1
                else:
                    stats.fragment_hit += 1
                    target = hit
            page.delete_link(link)
            page.insert_link({"kind": fitz.LINK_GOTO, "from": link["from"],
                              "page": target, "to": fitz.Point(0, 0)})
            stats.internal += 1
            stats.internal_targets.add((slug, fragment))
    return stats
