#!/usr/bin/env python
"""Post-build integrity checks over the assembled PDF.

Checks the artifact, not the intent: everything is measured on the PDF that
assemble.py wrote. Prints every measured value and exits non-zero on any
failure, the way scripts/check-links.mjs gates the web build.

Ported from the Vacuum book's gate. One deliberate difference: that book pinned
its expected counts by hand (103 outline entries, 74 figures), because it was
finished. This one changes every week while it is drafted, so each expected
count is DERIVED from out/manifest.json and dist/, never typed in. A check that
needs body text to measure reports SKIP until there is enough of it, instead of
passing on nothing.

Usage:  python pdf-build/verify_pdf.py [path/to.pdf]
"""
import json
from collections import Counter
import re
import sys
from pathlib import Path

import fitz
from bs4 import BeautifulSoup

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from siteconf import BOOK_TITLE  # noqa: E402

DEFAULT_PDF = HERE / (BOOK_TITLE.replace(" ", "-") + ".pdf")
MANIFEST = HERE / "out" / "manifest.json"
DIST = HERE.parent / "dist"

MM = 72.0 / 25.4
A5_W, A5_H = 148.0, 210.0
SIZE_TOL_MM = 0.5

FAILURES: list[str] = []
SKIPS: list[str] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {label}{('  - ' + detail) if detail else ''}")
    if not ok:
        FAILURES.append(label)


def skip(label: str, reason: str) -> None:
    print(f"  SKIP  {label}  - {reason}")
    SKIPS.append(label)


def _ascii_safe(s: str) -> str:
    """The console may be cp1252; span text carries Greek letters and minus signs."""
    return s.encode("ascii", "backslashreplace").decode("ascii")


# ---- page geometry and structure --------------------------------------------

def check_page_size(doc: fitz.Document) -> None:
    bad = [f"p{i + 1} {p.rect.width / MM:.1f}x{p.rect.height / MM:.1f}mm"
           for i, p in enumerate(doc)
           if abs(p.rect.width / MM - A5_W) > SIZE_TOL_MM or abs(p.rect.height / MM - A5_H) > SIZE_TOL_MM]
    check(not bad, f"every page is A5 ({A5_W}x{A5_H}mm +/-{SIZE_TOL_MM})",
          f"{len(bad)} wrong: {', '.join(bad[:4])}" if bad else f"{doc.page_count} pages")


def check_metadata(doc: fitz.Document) -> None:
    """A reader's PDF viewer shows the title field, and a library indexes it."""
    meta = doc.metadata or {}
    check(meta.get("title") == BOOK_TITLE and bool(meta.get("author")), "the title and author fields are set",
          _ascii_safe(f"title '{meta.get('title')}', author '{meta.get('author')}'"))
    cover = doc[0].get_text()
    check("CC BY 4.0" in cover, "the cover states the licence")


# The outline's opening entries, each one front-matter page (Contents may run on).
FRONT = ["Cover", "Title Page", "Contents"]


def check_title_page(doc: fitz.Document) -> None:
    """The page a library or an assessor reads first: who, where, which edition, how to cite."""
    text = " ".join(doc[1].get_text().split()) if doc.page_count > 1 else ""
    wanted = {"the title": BOOK_TITLE.upper(), "the affiliation": "Zhejiang University",
              "the ORCID": "0000-0003-3675-5301", "the DOI": "10.5281/zenodo.", "the edition": "Edition ",
              "the licence": "CC BY 4.0", "a citation": "Cite as:"}
    missing = [k for k, v in wanted.items() if v not in text]
    check(not missing, "the title page names author, affiliation, edition, DOI and licence",
          f"missing {', '.join(missing)}" if missing else "")


def _chapter_starts(toc: list) -> list[tuple[int, str]]:
    """Level-1 entries after the front matter, as (0-based page, label)."""
    return [(t[2] - 1, t[1]) for t in toc[len(FRONT):] if t[0] == 1]


def _front_pages(toc: list) -> int:
    """Pages before the body (Cover + Title Page + Contents)."""
    return toc[len(FRONT)][2] - 1 if len(toc) > len(FRONT) else 0


def check_outline(doc: fitz.Document, manifest: list[dict]) -> None:
    toc = doc.get_toc()
    level1 = _chapter_starts(toc)
    check(len(level1) == len(manifest), "outline has one level-1 entry per rendered section",
          f"{len(level1)} entries for {len(manifest)} sections")
    opening = [t[1] for t in toc[:len(FRONT)]]
    check(opening == FRONT and [t[2] for t in toc[:2]] == [1, 2],
          "outline opens with Cover, Title Page and Contents", f"{opening}")


HEADER_BAND_MM = 12.0


# The running-head font (Segoe UI, assemble.py) shares one glyph between "-"
# and U+2010, and PyMuPDF writes the latter into the text layer. Map the hyphen
# and space variants back before the ASCII filter, or "X-Ray" reads "XRay".
_PLAIN = str.maketrans({"‐": "-", "‑": "-", " ": " "})


def _text_in_band(page: fitz.Page, top_mm: float, bottom_mm: float) -> str:
    return page.get_text("text", clip=fitz.Rect(0, top_mm * MM, page.rect.width, bottom_mm * MM))


def check_headers(doc: fitz.Document, sections: list[tuple[int, str]]) -> None:
    """No head on a section's first page; the page after it names the section."""
    starts = {idx for idx, _ in sections}
    on_start, missing_left, probed = [], [], 0
    for idx, label in sorted(sections):
        if any(c.isalpha() for c in _text_in_band(doc[idx], 0, HEADER_BAND_MM)):
            on_start.append(idx + 1)
        nxt = idx + 1
        if nxt < doc.page_count and nxt not in starts:
            probed += 1
            wanted = "".join(c for c in label if c.isascii()).strip()
            got = "".join(c for c in _text_in_band(doc[nxt], 0, HEADER_BAND_MM).translate(_PLAIN)
                          if c.isascii())
            if wanted and wanted not in got:
                missing_left.append(nxt + 1)
    check(not on_start, "no running head on a section's first page",
          f"head found on {on_start[:5]}" if on_start else "")
    if probed:
        check(not missing_left, "running head names its own section",
              f"missing on {missing_left[:5]}" if missing_left else f"{probed} continuation page(s)")
    else:
        skip("running head names its own section", "no section runs past its first page yet")


def check_page_numbers(doc: fitz.Document, front_pages: int) -> None:
    total = doc.page_count - front_pages
    bad = []
    for i in range(front_pages, doc.page_count):
        rect = doc[i].rect
        band = fitz.Rect(0, rect.height - 34, rect.width, rect.height - 10)
        got = " ".join(w[4] for w in doc[i].get_text("words", clip=band))
        if f"{i - front_pages + 1} / {total}" not in got:
            bad.append(i + 1)
    check(not bad, f"footer reads 'n / {total}' on every body page",
          f"{len(bad)} bad: {bad[:5]}" if bad else f"{total} body pages")


CONTENTS_TOP_MM = 12.0   # @page margin is 14mm; slack for ascenders and rounding


def check_contents_pages(doc: fitz.Document, toc: list) -> None:
    """Margin and running head on every Contents sheet, and every row linked."""
    n = len(FRONT)
    if len(toc) <= n:
        check(False, "outline reaches the first body section", f"only {len(toc)} entries")
        return
    first, end = toc[n - 1][2] - 1, toc[n][2] - 1
    thin, headless = [], []
    for i in range(first, end):
        page = doc[i]
        has_head = "Contents" in _text_in_band(page, 6.0, 11.0)
        words = page.get_text("words")
        body = [w for w in words if w[1] > 11 * MM] if has_head else words
        if body and min(w[1] for w in body) / MM < CONTENTS_TOP_MM:
            thin.append(f"p{i + 1}")
        if i > first and not has_head:
            headless.append(f"p{i + 1}")
    check(not thin, f"every contents page keeps its {CONTENTS_TOP_MM:.0f}mm top margin",
          "; ".join(thin) if thin else f"{end - first} page(s)")
    check(not headless, "contents pages after the first carry a running head",
          "; ".join(headless) if headless else f"{max(0, end - first - 1)} continuation page(s)")
    goto = [l for i in range(first, end) for l in doc[i].get_links() if l.get("kind") == fitz.LINK_GOTO]
    astray = [l["page"] + 1 for l in goto if not end <= l["page"] < doc.page_count]
    check(len(goto) >= len(toc) - n, "every contents row links to its target",
          f"{len(goto)} links for {len(toc) - n} rows")
    check(not astray, "contents links land in the body", f"{len(astray)} astray: {astray[:5]}")


# ---- type ---------------------------------------------------------------------

# The Vacuum book's floors, with their reasons: 7.9pt admits the 0.01pt of
# geometry by which a correct 8pt figure label prints small; 5.9pt is the floor
# for exponents and KaTeX's own script sizes.
MIN_TEXT_PT = 7.9
MIN_EXPONENT_PT = 5.9
ZWJ = "​"
MATH_FONTS = ("KaTeX_", "CambriaMath")
SCRIPT_BASELINE_TOL_PT = 0.5
LINE_MATE_TOUCH_PT = 1.5
CODE_FONT = "Consolas"


def _script_run(span: dict, line_spans: list) -> bool:
    """A script is both smaller than its line's body type and off its baseline."""
    body = max(s["size"] for s in line_spans)
    if span["size"] >= body:
        return False
    base_y = next(s["origin"][1] for s in line_spans if s["size"] == body)
    return abs(span["origin"][1] - base_y) > SCRIPT_BASELINE_TOL_PT


def _line_mates(span: dict, blocks: list) -> list:
    """A span alone on its PyMuPDF line borrows the spans that visually share it."""
    x0, y0, x1, y1 = span["bbox"]
    mates = [span]
    for line in (ln for b in blocks for ln in b.get("lines", [])):
        for other in line["spans"]:
            if other is span:
                continue
            ox0, oy0, ox1, oy1 = other["bbox"]
            if oy0 < y1 and oy1 > y0 and ox1 >= x0 - LINE_MATE_TOUCH_PT and ox0 <= x1 + LINE_MATE_TOUCH_PT:
                mates.append(other)
    return mates


def _visible_spans(doc: fitz.Document):
    """(page_number, size_pt, font_name, text, is_script) per printed span."""
    for i, page in enumerate(doc):
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            for line in block.get("lines", []):
                spans = line["spans"]
                for span in spans:
                    text = span["text"].strip()
                    if text and text != ZWJ:
                        mates = spans if len(spans) > 1 else _line_mates(span, blocks)
                        yield i + 1, span["size"], span["font"], text, _script_run(span, mates)


def check_no_illegible_text(doc: fitz.Document) -> None:
    bad = [(p, round(s, 1), _ascii_safe(t[:18])) for p, s, _f, t, _ in _visible_spans(doc) if s < MIN_EXPONENT_PT]
    check(not bad, f"no visible text below {MIN_EXPONENT_PT}pt", f"{len(bad)} spans: {bad[:4]}" if bad else "")


def check_labels_at_full_size(doc: fitz.Document) -> None:
    bad = [(p, round(s, 1), _ascii_safe(t[:18])) for p, s, f, t, script in _visible_spans(doc)
           if MIN_EXPONENT_PT <= s < MIN_TEXT_PT and not script
           and not t.lstrip("-−").isdigit() and not f.startswith(MATH_FONTS)]
    check(not bad, f"no non-script text between {MIN_EXPONENT_PT} and {MIN_TEXT_PT}pt",
          f"{len(bad)} spans: {bad[:4]}" if bad else "")


ENOTATION_RE = re.compile(r"(?<![A-Za-z0-9])[+-]?\d+(?:\.\d+)?[eE][+-]?\d+(?![A-Za-z0-9])")


def check_no_enotation(doc: fitz.Document) -> None:
    """House rule (STYLE.md §6): no e-notation where a reader sees it. Code-font
    spans are exempt, as <code> is on the web."""
    hits = [(p, _ascii_safe(m.group(0))) for p, _s, font, text, _ in _visible_spans(doc)
            if not font.startswith(CODE_FONT) for m in ENOTATION_RE.finditer(text)]
    check(not hits, "no reader-visible e-notation", f"{len(hits)} found: {hits[:5]}" if hits else "")


def check_no_em_dash(doc: fitz.Document, front_pages: int) -> None:
    """STYLE.md §4.2: the book uses no em-dash. The Vacuum book never had this
    gate; here it catches a dash that entered through a generated label (a
    caption prefix, a running head) as well as through prose."""
    hits = [i + 1 for i in range(front_pages, doc.page_count) if "—" in doc[i].get_text("text")]
    check(not hits, "no em-dash in the body", f"on pages {hits[:8]}" if hits else "")


def check_no_markdown_in_captions(doc: fitz.Document) -> None:
    stars = re.findall(r"\*\*?[A-Za-z][^*\n]{0,40}\*\*?", "\n".join(p.get_text() for p in doc))
    check(not stars, "no literal Markdown emphasis survives",
          f"{len(stars)} found: {[_ascii_safe(s) for s in stars[:3]]}" if stars else "")


# ---- figures ------------------------------------------------------------------

CAPTION_RE = re.compile(r"Figure (\d+-\d+[a-z]?):")
TRUNCATED_RE = re.compile(r"(?<![A-Za-z])ure (\d+-\d+[a-z]?):")


def expected_figures(dist: Path, slugs: list[str]) -> set[str]:
    """Figure numbers the rendered pages carry, read from dist/. Replaces the
    Vacuum book's hand-kept FIGURE_COUNT."""
    found: set[str] = set()
    for slug in slugs:
        index = dist / slug / "index.html"
        if index.exists():
            soup = BeautifulSoup(index.read_text(encoding="utf-8"), "lxml")
            for strong in soup.select("figure figcaption strong"):
                m = CAPTION_RE.search(strong.get_text())
                if m:
                    found.add(m.group(1))
    return found


def check_captions(doc: fitz.Document, expected: set[str]) -> None:
    """A figure pushed past the printable box loses characters silently: the
    Vacuum book printed "ure 4.6". Every expected caption must be whole."""
    text = "\n".join(p.get_text() for p in doc)
    present = set(CAPTION_RE.findall(text))
    truncated = TRUNCATED_RE.findall(text)
    if not expected:
        skip("every figure caption is present", "no numbered figures in the rendered pages")
    else:
        missing = sorted(expected - present)
        check(not missing, "every figure caption is present",
              f"{len(expected) - len(missing)} of {len(expected)}" + (f"; missing {missing[:5]}" if missing else ""))
    check(not truncated, "no caption lost its leading characters",
          f"{len(truncated)} truncated: {truncated[:4]}" if truncated else "")


# ---- text column --------------------------------------------------------------

MIN_LINES_FOR_COLUMN = 50


def column_width_mm(lines) -> float | None:
    """Width of the body text column, from (x0, x1, text[, size]) lines in points.

    The text is ragged right, so most lines stop short of the column and only
    the widest reach it: the column is the widest line, not a percentile. (The
    Vacuum book's 95th percentile passed there only because a long book has
    enough near-full lines; on the first two chapters of this one it read
    122.9mm for a column that measures 124.0.) Only lines that start at the
    column's left edge count. Figures and tables bleed 6mm into the padding
    (render-sections.mjs), so a centered caption can be wider than the column,
    and list items start indented. The edge is the leftmost x0 shared by at
    least a fifth of the full lines: a bleeding caption is centered, so its x0
    varies and never builds up that share.

    With sizes given, only lines set at the body size (the commonest size of
    the full lines) count: a centered caption (10.2pt against the prose's
    10.5pt) can start within 0.5mm of the edge by chance, as Figure 9-1's did.
    """
    lines = [ln if len(ln) == 4 else (*ln, None) for ln in lines]
    sized = [round(s, 1) for x0, x1, text, s in lines if len(text) >= 40 and s is not None]
    body = Counter(sized).most_common(1)[0][0] if sized else None
    full = [(x0, x1) for x0, x1, text, s in lines
            if len(text) >= 40 and (body is None or s is None or round(s, 1) == body)]
    if len(full) < MIN_LINES_FOR_COLUMN:
        return None
    bins = Counter(round(x0 / MM * 2) / 2 for x0, _ in full)      # 0.5mm bins
    edge = min(b for b, n in bins.items() if n >= len(full) / 5)
    return max(x1 - x0 for x0, x1 in full if abs(x0 / MM - edge) <= 0.5) / MM


def check_text_column_width(doc: fitz.Document, front_pages: int) -> None:
    """6mm page margin + 6mm .chapter padding = a 124mm column. Measured on the
    body text itself, because changing either value silently reflows the book."""
    lines = [(line["bbox"][0], line["bbox"][2], "".join(s["text"] for s in line["spans"]),
              max((s["size"] for s in line["spans"]), default=0))
             for i in range(front_pages, doc.page_count)
             for block in doc[i].get_text("dict")["blocks"]
             for line in block.get("lines", [])]
    width = column_width_mm(lines)
    if width is None:
        skip("body text column is 124mm", "too few full lines of prose to measure")
        return
    check(123.0 <= width <= 125.0, "body text column is 124mm", f"widest line at the column edge {width:.1f}mm")


# ---- links --------------------------------------------------------------------

def check_links(doc: fitz.Document) -> None:
    dead = [i + 1 for i, p in enumerate(doc) for l in p.get_links() if "localhost" in (l.get("uri") or "")
            or "127.0.0.1" in (l.get("uri") or "")]
    check(not dead, "no preview-server links survive", f"{len(dead)} on pages {dead[:5]}" if dead else "")
    targets = [l.get("page") for p in doc for l in p.get_links() if l.get("kind") == fitz.LINK_GOTO]
    out_of_range = [t for t in targets if t is None or not 0 <= t < doc.page_count]
    check(not out_of_range, "internal link targets are in range",
          f"{len(out_of_range)} out of range" if out_of_range else f"{len(targets)} internal links")


def main() -> int:
    pdf = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PDF
    if not pdf.exists():
        print(f"No such PDF: {pdf}")
        return 2
    if not MANIFEST.exists():
        print(f"No manifest at {MANIFEST}: the expected counts come from it.")
        return 2
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    doc = fitz.open(str(pdf))
    print(f"\nVerifying {pdf.name}  ({doc.page_count} pages, {len(manifest)} sections)\n")

    toc = doc.get_toc()
    front_pages = _front_pages(toc)
    check_page_size(doc)
    check_metadata(doc)
    check_title_page(doc)
    check_outline(doc, manifest)
    check_contents_pages(doc, toc)
    check_headers(doc, _chapter_starts(toc))
    check_page_numbers(doc, front_pages)
    check_no_illegible_text(doc)
    check_labels_at_full_size(doc)
    check_no_enotation(doc)
    check_no_em_dash(doc, front_pages)
    check_no_markdown_in_captions(doc)
    check_captions(doc, expected_figures(DIST, [s["slug"] for s in manifest]))
    check_text_column_width(doc, front_pages)
    check_links(doc)
    doc.close()

    print()
    if SKIPS:
        print(f"{len(SKIPS)} check(s) skipped for lack of content: {', '.join(SKIPS)}")
    if FAILURES:
        print(f"{len(FAILURES)} check(s) failed: {', '.join(FAILURES)}")
        return 1
    print("OK - all checks that could run passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
