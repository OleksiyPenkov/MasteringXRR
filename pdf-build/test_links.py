import fitz
import pytest

import siteconf
from links import (
    _page_for_heading, build_anchor_map, expected_internal_targets, parse_internal_href, resolve_links,
)

B = siteconf.BASE_PATH  # '/MasteringXRR/'


def test_siteconf_reads_the_constants_from_site_mjs():
    assert siteconf.BASE.startswith("/") and not siteconf.BASE.endswith("/")
    assert siteconf.BASE_PATH == siteconf.BASE + "/"
    assert isinstance(siteconf.PORT, int)
    assert siteconf.BOOK_TITLE


PAGE = f"""<html><body>
<nav><a href="{B}introduction/">nav link, hidden in print</a></nav>
<article>
  <h2 id="finding-the-edge">Finding the <span class="katex"><span class="katex-mathml">theta</span><span>θ</span></span> edge</h2>
  <h2 id="no-text"></h2>
  <figure id="fig-4-1"><svg></svg><figcaption><strong>Figure 4-1:</strong> A caption.</figcaption></figure>
  <p><a href="#fig-4-1">Figure 4-1</a>, <a href="{B}ch5-one-film/#kiessig">Chapter 5</a>,
     <a href="{B}ch6/">Chapter 6</a>, <a href="{B}_astro/x.css">asset</a>,
     <a href="https://example.org/">external</a></p>
  <div class="web-only"><a href="#web-only-target">web only</a></div>
</article></body></html>"""


@pytest.fixture
def dist(tmp_path):
    (tmp_path / "ch4").mkdir()
    (tmp_path / "ch4" / "index.html").write_text(PAGE, encoding="utf-8")
    return tmp_path


def test_anchor_map_has_headings_without_mathml_and_figures_by_label(dist):
    anchors = build_anchor_map(dist)
    assert anchors[("ch4", "finding-the-edge")] == "Finding the θ edge"
    assert anchors[("ch4", "fig-4-1")] == "Figure 4-1:"
    assert ("ch4", "no-text") not in anchors


def test_expected_targets_are_the_article_links_a_print_reader_can_click(dist):
    assert expected_internal_targets(dist, ["ch4"]) == {
        ("ch4", "fig-4-1"),          # same-page fragment
        ("ch5-one-film", "kiessig"),  # cross-page with fragment
        ("ch6", ""),                  # cross-page, no fragment
    }                                 # not: nav, asset, external, web-only


@pytest.mark.parametrize("url,expected", [
    (f"http://localhost:4331{B}ch4/#fig-4-1", ("ch4", "fig-4-1")),
    (f"http://localhost:4331{B}ch4/?xref#fig-4-1", ("ch4", "fig-4-1")),  # the renderer's same-page form
    (f"http://127.0.0.1:4331{B}ch5/", ("ch5", "")),
    (f"http://localhost:4331{B}ch6/#a%20b", ("ch6", "a b")),
])
def test_parses_preview_links(url, expected):
    assert parse_internal_href(url) == expected


@pytest.mark.parametrize("url", [
    "https://example.org/MasteringXRR/ch4/",       # right path, wrong host
    "http://localhost:4331/OtherBook/ch4/",         # right host, wrong base
    f"http://localhost:4331{B}",                    # the home page, no slug
])
def test_leaves_everything_else_alone(url):
    assert parse_internal_href(url) is None


def _doc(pages):
    doc = fitz.open()
    for lines in pages:
        page = doc.new_page(width=420, height=595)
        for i, line in enumerate(lines):
            page.insert_text((40, 60 + 20 * i), line, fontsize=10)
    return doc


def test_a_short_heading_resolves_when_it_is_on_one_page_only():
    doc = _doc([["Intro text"], ["Icons", "body"], ["other"]])
    assert _page_for_heading(doc, "Icons", 0, 2) == 1


def test_a_short_heading_on_two_pages_is_refused_not_guessed():
    doc = _doc([["Icons"], ["Icons again"]])
    assert _page_for_heading(doc, "Icons", 0, 1) is None


def test_an_ambiguous_truncated_probe_returns_none_not_a_sibling():
    a = "Setting the fitting range: where it starts"
    b = "Setting the fitting range: where it ends"
    doc = _doc([[a[:30]], [b[:30]]])  # both pages carry only the shared prefix
    assert _page_for_heading(doc, a, 0, 1) is None


def test_resolve_links_rewrites_to_the_heading_page_and_counts_targets():
    doc = _doc([["Chapter start"], ["Finding the edge", "text"], ["Chapter 5"]])
    doc[0].insert_link({"kind": fitz.LINK_URI, "from": fitz.Rect(40, 40, 200, 70),
                        "uri": f"http://localhost:4331{B}ch4/?xref#finding-the-edge"})
    doc[0].insert_link({"kind": fitz.LINK_URI, "from": fitz.Rect(40, 80, 200, 100),
                        "uri": f"http://localhost:4331{B}missing/"})
    doc[0].insert_link({"kind": fitz.LINK_URI, "from": fitz.Rect(40, 110, 200, 130),
                        "uri": "https://example.org/"})
    entries = [{"slug": "ch4", "start_page": 1, "pages": 2}, {"slug": "ch5", "start_page": 3, "pages": 1}]
    stats = resolve_links(doc, entries, {("ch4", "finding-the-edge"): "Finding the edge"}, 0)
    assert stats.internal_targets == {("ch4", "finding-the-edge")}
    assert (stats.fragment_hit, stats.unresolved_slug, stats.external_kept) == (1, 1, 1)
    goto = [l for l in doc[0].get_links() if l["kind"] == fitz.LINK_GOTO]
    assert [l["page"] for l in goto] == [1]


def _styled_doc(pages):
    """Pages of (text, fontsize) lines, so a heading can be set larger than prose."""
    doc = fitz.open()
    for lines in pages:
        page = doc.new_page(width=420, height=595)
        for i, (line, size) in enumerate(lines):
            page.insert_text((40, 60 + 24 * i), line, fontsize=size)
    return doc


def test_a_heading_wins_over_the_same_words_earlier_in_the_prose():
    # Chapter 2's "In This Chapter" box says "Finding your way around the main
    # window" two pages before the heading "The main window". search_for ignores
    # case, so the box used to win and the running head named the wrong section.
    doc = _styled_doc([
        [("Finding your way around the main window", 10.5)],
        [("32-bit or 64-bit?", 14), ("body", 10.5)],
        [("The main window", 14), ("The main window has three columns", 10.5)],
    ])
    assert _page_for_heading(doc, "The main window", 0, 2) == 2


def test_a_heading_wins_over_a_prose_link_that_quotes_it():
    doc = _styled_doc([
        [("the settings. Your first calculation goes through them.", 10.5)],
        [("Your first calculation", 14)],
    ])
    assert _page_for_heading(doc, "Your first calculation", 0, 1) == 1


def test_a_letter_heading_is_found_among_terms_that_start_with_it():
    # Appendix D sets each letter as an h2 and each term as a heading-sized
    # line too; "G" starts "Graded multilayer" on the same and the next page,
    # so a prefix match never found a unique page and the build failed.
    doc = _styled_doc([
        [("F", 14), ("Fringe", 12), ("body", 10.5)],
        [("G", 14), ("Graded multilayer", 12), ("body", 10.5)],
        [("Grazing angle", 12), ("body", 10.5)],
    ])
    assert _page_for_heading(doc, "G", 0, 2) == 1
