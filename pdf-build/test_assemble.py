import fitz

from assemble import (
    _two_lines, citation_meta, contents_targets, cover_html, title_page_html, fit_running_head, link_target_page, resolve_subsections, section_label, toc_html,
    toc_mark_page,
)
from headings import contents_subsections, section_headings


def test_section_label_uses_a_colon_and_leaves_the_introduction_bare():
    assert section_label({"label": "Chapter 4", "title": "X-Rays Meet a Surface"}) == "Chapter 4: X-Rays Meet a Surface"
    assert section_label({"label": "Appendix A", "title": "Notation"}) == "Appendix A: Notation"
    assert section_label({"label": "", "title": "Introduction"}) == "Introduction"
    assert "—" not in section_label({"label": "Chapter 1", "title": "T"})


def _w(s):
    return fitz.get_text_length(s, fontname="helv", fontsize=8)


def test_running_head_short_pair_is_unchanged():
    assert fit_running_head("Chapter 4: Surface", "Critical angle", 350, 17, "helv", 8) == "Critical angle"


def test_running_head_long_right_half_truncates_on_a_word_boundary():
    left = "Chapter 14: Preparing the Data: Scale, Smoothing, and Fitting Range"
    right = "Setting the floor to one count, and why a floor above the background clips the curve"
    out = fit_running_head(left, right, 351.5, 17, "helv", 8)
    assert out and out.endswith("…")
    assert right.startswith(out[:-1])
    assert right[len(out) - 1] == " "                # the cut falls at a space
    assert _w(out) <= 351.5 - _w(left) - 17


def test_running_head_returns_none_when_nothing_fits():
    assert fit_running_head("x" * 200, "Anything", 100, 17, "helv", 8) is None
    assert fit_running_head("Chapter 1", "", 350, 17, "helv", 8) is None


ENTRIES = [
    {"slug": "introduction", "number": "", "title": "Introduction", "part": "front",
     "partHeading": "Front Matter", "start_page": 1, "pages": 2},
    {"slug": "ch1", "number": "1", "title": "What XRR Fitting Is", "part": "1",
     "partHeading": "Part 1: Getting Started", "start_page": 3, "pages": 4},
]


def test_contents_groups_rows_under_their_part_heading_in_order():
    html = toc_html(ENTRIES, {"ch1": [("h", "Reading a curve", 4)]})
    assert html.index("Front Matter") < html.index("Introduction") < html.index("Part 1: Getting Started") \
        < html.index("What XRR Fitting Is") < html.index("Reading a curve")
    assert html.count('class="part"') == 2
    assert "row-sub" in html


def test_contents_emits_no_sub_row_styling_when_there_are_no_sub_rows():
    assert "row-sub" not in toc_html(ENTRIES, {})


def test_resolve_subsections_orders_same_page_ties_by_source_order():
    # Two headings on one page: source order must win over id/text order.
    doc = fitz.open()
    for _ in range(6):
        doc.new_page()
    all_subs = {"ch1": [("z-first", "Zeta heading"), ("a-second", "Alpha heading")]}
    subs, resolved, total, missing = resolve_subsections(doc, ENTRIES, all_subs, page_for_heading=lambda *_: 3)
    assert (resolved, total, missing) == (2, 2, [])
    assert [hid for hid, _t, _p in subs["ch1"]] == ["z-first", "a-second"]
    assert subs["ch1"][0][2] == 4                  # 0-based 3 -> body page 4


def test_resolve_subsections_names_what_it_could_not_find():
    doc = fitz.open()
    doc.new_page()
    _s, resolved, total, missing = resolve_subsections(
        doc, ENTRIES[:1], {"introduction": [("x", "Nowhere")]}, page_for_heading=lambda *_: None)
    assert (resolved, total) == (0, 1) and missing == ["introduction: 'Nowhere'"]


def test_contents_targets_and_page_arithmetic():
    subs = {"ch1": [("h", "Reading a curve", 4)]}
    assert contents_targets(ENTRIES, subs) == [("Introduction", 1), ("What XRR Fitting Is", 3), ("Reading a curve", 4)]
    assert toc_mark_page(2, 1) == 3           # 1-based outline page
    assert link_target_page(2, 1) == 2        # 0-based link target


def test_contents_leaves_out_sources_but_the_running_head_keeps_it(tmp_path):
    (tmp_path / "ch1").mkdir()
    (tmp_path / "ch1" / "index.html").write_text(
        '<h2 id="a">Reading a curve</h2><h2 id="sources">Sources</h2><h3 id="c">Not an h2</h3>',
        encoding="utf-8")
    assert contents_subsections(tmp_path)["ch1"] == [("a", "Reading a curve")]
    assert section_headings(tmp_path)["ch1"] == [("a", "Reading a curve"), ("sources", "Sources")]


def test_a_stamped_running_head_keeps_greek_and_the_ellipsis():
    # Built-in Helvetica has neither: "2θ or θ: the angle on your screen"
    # printed as "2· or ·: …", and every truncated head ended in "·".
    from assemble import RUNHEAD_FONT, stamp_text
    doc = fitz.open()
    page = doc.new_page(width=420, height=595)
    stamp_text(page, (30, 30), "2θ or θ: the angle…", 8, (0.4, 0.4, 0.4))
    assert "2θ or θ: the angle…" in page.get_text()
    assert fit_running_head("Chapter 2", "2θ or θ: the angle on your screen", 350, 17, RUNHEAD_FONT, 8) \
        == "2θ or θ: the angle on your screen"


def test_title_breaks_into_two_balanced_lines():
    assert _two_lines("Mastering XRR Fitting") == "Mastering<br>XRR Fitting"
    assert _two_lines("Single") == "Single"


def test_cover_inlines_the_hero_with_its_colors_filled():
    html = cover_html()
    assert '<svg class="hero"' in html
    assert "{accent}" not in html and "{tint}" not in html and "{data}" not in html


def test_citation_meta_reads_the_top_level_keys_only():
    cff = ('version: 1.0.2\ndate-released: 2026-09-25\ndoi: 10.5281/zenodo.1\nurl: "https://x.org/b/"\n'
           'preferred-citation:\n  doi: 10.9999/wrong\n  url: "https://wrong/"\n')
    assert citation_meta(cff) == {"version": "1.0.2", "doi": "10.5281/zenodo.1", "url": "https://x.org/b/",
                                  "year": "2026"}


def test_title_page_carries_affiliation_orcid_edition_and_citation():
    html = title_page_html({"version": "1.0.2", "doi": "10.5281/zenodo.1", "url": "https://x.org/b/", "year": "2026"})
    for s in ("Zhejiang University", "0000-0003-3675-5301", "Edition 1.0.2", "https://doi.org/10.5281/zenodo.1",
              "CC BY 4.0", "Penkov, O. V. (2026)."):
        assert s in html
