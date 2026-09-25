"""Where the figure scripts find the files that are not in this repository.

Four inputs live outside the book:
  XRC_MCP_EXE   the command-line server that ships with X-Ray Calc (XRC_MCP.exe)
  XRC_BIN       the folder with the X-Ray Calc GUI (XRayCalc3.x64.exe), for the screenshot drivers
  XRC_DEPLOY    the X-Ray Calc install folder (its Examples and Henke subfolders)
  XRR_DEPOSIT   the fitting procedure's Zenodo deposit (its curves, fits and jobs subfolders)
and one curve that is not in the deposit:
  P2_08_CURVE   the Co film P2-08 of Chapter 21 (its points are in figures-src/ch21/curves.json)

Each is read from the environment variable of the same name, then from local-paths.json at the
repository root (not committed; a JSON object with the same keys). A script that needs a path
that is set in neither place stops and names it.
"""
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_FILE = ROOT / "local-paths.json"


def get(key):
    if os.environ.get(key):
        return Path(os.environ[key])
    if _FILE.exists():
        value = json.loads(_FILE.read_text(encoding="utf-8")).get(key)
        if value:
            return Path(value)
    raise SystemExit(f"{key} is not set: set the environment variable or add it to {_FILE}")


def deposit(*parts):
    return get("XRR_DEPOSIT").joinpath(*parts)


def deploy(*parts):
    return get("XRC_DEPLOY").joinpath(*parts)
