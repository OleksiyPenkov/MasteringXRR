import fitz

import verify_pdf
from verify_pdf import CAPTION_RE, ENOTATION_RE, TRUNCATED_RE, expected_figures


def _doc(texts):
    # insert_htmlbox, not insert_text: the built-in Helvetica of insert_text
    # prints an em-dash as a middle dot, so the dash never reaches the text layer.
    doc = fitz.open()
    for t in texts:
        doc.new_page(width=420, height=595).insert_htmlbox(fitz.Rect(40, 60, 380, 200), t)
    return doc


def test_caption_pattern_matches_the_house_label_and_its_truncation():
    assert CAPTION_RE.findall("Figure 4-1: A caption. Figure 12-3b: another") == ["4-1", "12-3b"]
    assert TRUNCATED_RE.findall("ure 4-1: lost its Fig") == ["4-1"]
    assert TRUNCATED_RE.findall("Figure 4-1: whole") == []


def test_expected_figures_come_from_the_rendered_pages_in_dist(tmp_path):
    (tmp_path / "ch4").mkdir()
    (tmp_path / "ch4" / "index.html").write_text(
        '<figure><figcaption><strong>Figure 4-1:</strong> a</figcaption></figure>'
        '<figure><figcaption>unnumbered</figcaption></figure>', encoding="utf-8")
    (tmp_path / "ch5").mkdir()
    (tmp_path / "ch5" / "index.html").write_text(
        '<figure><figcaption><strong>Figure 5-1:</strong> b</figcaption></figure>', encoding="utf-8")
    assert expected_figures(tmp_path, ["ch4"]) == {"4-1"}   # ch5 was not rendered


def test_a_missing_caption_fails_and_no_figures_skips():
    verify_pdf.check_captions(_doc(["Figure 4-1: here"]), {"4-1", "4-2"})
    assert verify_pdf.FAILURES == ["every figure caption is present"]
    verify_pdf.FAILURES.clear()
    verify_pdf.check_captions(_doc(["no figures"]), set())
    assert verify_pdf.FAILURES == [] and verify_pdf.SKIPS == ["every figure caption is present"]


def test_em_dash_in_the_body_fails_but_front_matter_is_not_checked():
    doc = _doc(["Cover — title", "body text — aside"])
    verify_pdf.check_no_em_dash(doc, front_pages=1)
    assert verify_pdf.FAILURES == ["no em-dash in the body"]
    verify_pdf.FAILURES.clear()
    verify_pdf.check_no_em_dash(_doc(["Cover —", "clean body, 0.012–0.015"]), front_pages=1)
    assert verify_pdf.FAILURES == []                          # an en-dash range is fine


def test_enotation_pattern():
    assert ENOTATION_RE.findall("a floor of 1e-7 and 1.4E+05") == ["1e-7", "1.4E+05"]
    assert ENOTATION_RE.findall("Figure 3e, 12398.6, B4C") == []


def test_text_column_skips_on_too_little_prose():
    verify_pdf.check_text_column_width(_doc(["short"]), front_pages=0)
    assert verify_pdf.SKIPS == ["body text column is 124mm"] and verify_pdf.FAILURES == []


def _col(x0_mm, width_mm, n=1, text="x" * 60):
    mm = verify_pdf.MM
    return [(x0_mm * mm, (x0_mm + width_mm) * mm, text)] * n


def test_column_is_the_widest_line_that_starts_at_the_column_edge():
    # Ragged-right prose: most lines stop short of the column, the widest reach it.
    lines = _col(12.1, 118.0, 40) + _col(12.1, 121.5, 15) + _col(12.1, 124.0, 2)
    assert round(verify_pdf.column_width_mm(lines), 1) == 124.0


def test_column_ignores_figures_that_bleed_into_the_padding_and_indented_lists():
    lines = (_col(12.1, 120.0, 40) + _col(12.1, 124.0, 3)
             + _col(8.7, 131.1, 3)      # centered caption of a bleeding figure
             + _col(22.7, 113.0, 30))   # list items, indented
    assert round(verify_pdf.column_width_mm(lines), 1) == 124.0


def test_column_ignores_a_caption_line_that_happens_to_start_at_the_edge():
    # Figure 9-1's centered caption bleeds into the padding; one of its lines
    # started within 0.5mm of the column edge and read 125.2mm. Captions are set
    # at 10.2pt and prose at 10.5pt, so only lines at the body size count.
    mm = verify_pdf.MM
    lines = ([(x0, x1, t, 10.5) for x0, x1, t in _col(12.1, 120.0, 50) + _col(12.1, 124.0, 3)]
             + [(11.6 * mm, 136.8 * mm, "x" * 60, 10.2)])
    assert round(verify_pdf.column_width_mm(lines), 1) == 124.0


def test_column_ignores_short_lines_and_skips_on_too_little_prose():
    assert verify_pdf.column_width_mm(_col(12.1, 124.0, 10, text="short")) is None


def test_a_running_head_stamped_with_unicode_hyphen_and_spaces_still_names_its_section():
    # Segoe UI, the running-head font, maps "-" and U+2010 to one glyph, so the
    # head "Chapter 2: Meet X-Ray Calc 3" extracts as "X\u2010Ray". Dropping the
    # non-ASCII character used to leave "XRay", and the check failed.
    doc = fitz.open()
    doc.new_page(width=420, height=595)                     # the section's first page
    p = doc.new_page(width=420, height=595)
    p.insert_htmlbox(fitz.Rect(34, 12, 380, 30), "Chapter 2: Meet X\u2010Ray\u00a0Calc 3")
    verify_pdf.check_headers(doc, [(0, "Chapter 2: Meet X-Ray Calc 3")])
    assert "running head names its own section" not in verify_pdf.FAILURES
