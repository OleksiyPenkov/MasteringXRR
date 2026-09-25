import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import verify_pdf  # noqa: E402


@pytest.fixture(autouse=True)
def _clean_verify_state():
    """verify_pdf keeps module-level FAILURES/SKIPS lists that check() and
    skip() append to; a test calling a check directly would leave them dirty."""
    verify_pdf.FAILURES.clear()
    verify_pdf.SKIPS.clear()
    yield
    verify_pdf.FAILURES.clear()
    verify_pdf.SKIPS.clear()
