"""The site constants, read from src/lib/site.mjs. (Not named site.py: that
would shadow the stdlib module Python imports at startup.)

site.mjs is the one place the base path, port and title are decided (the Vacuum
book hard-coded '/VacuumTextbook' in four files, two of them Python). Python
cannot import an ES module, so this reads the three string/number literals out
of it. A missing constant is a hard error: a guessed base path would make every
cross-reference in the PDF silently fail to resolve.
"""
import re
from pathlib import Path

SITE_MJS = Path(__file__).resolve().parent.parent / "src" / "lib" / "site.mjs"


def _read(name: str, text: str) -> str:
    m = re.search(rf"export const {name} = (['\"]?)([^'\";\n]+)\1;", text)
    if not m:
        raise SystemExit(f"{SITE_MJS}: no `export const {name} = ...;` found")
    return m.group(2)


_TEXT = SITE_MJS.read_text(encoding="utf-8")
BASE = _read("BASE", _TEXT)            # '/MasteringXRR'
PORT = int(_read("PORT", _TEXT))       # 4331
BOOK_TITLE = _read("BOOK_TITLE", _TEXT)
BASE_PATH = BASE.rstrip("/") + "/"     # '/MasteringXRR/', the prefix links carry
