"""AC-021 / NFR-019: no axSpA identifier is hard-coded outside the condition pack.

An automated scan of `backend/app/`, excluding `backend/app/pack/packs/`, for
condition-specific identifiers: the marker and criteria-set names the product
names explicitly, and every code-list value the pack file itself carries -- the
forbidden list is derived from the pack, so it stays true as the pack changes.
A hit fails the scan naming the file and the line.

(This scan reads files rather than the API; it lives here only because this
ticket's writable scope is backend/tests/integration/.)
"""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any

import yaml

APP = Path(__file__).resolve().parents[2] / "app"
PACK_DIR = APP / "pack" / "packs"
PACK_FILE = PACK_DIR / "axspa.yaml"

#: Condition-specific identifiers the requirement names outright.
NAMED_IDENTIFIERS = ("HLA-B27", "HLAB27", "SPARTAN", "ASAS", "axSpA")

#: A short token (three characters or fewer) is not a usable identifier to scan for.
MIN_VALUE_LENGTH = 4


def _pack_config() -> dict:
    assert PACK_FILE.exists(), (
        f"the condition pack file is not at {PACK_FILE.relative_to(APP.parent)}: all "
        "condition logic must live in the pack"
    )
    return yaml.safe_load(PACK_FILE.read_text()) or {}


def _code_values(payload: Any) -> set[str]:
    """Every code-list-ish string value anywhere in the pack configuration."""
    found: set[str] = set()
    if isinstance(payload, str):
        if len(payload.strip()) >= MIN_VALUE_LENGTH:
            found.add(payload.strip())
    elif isinstance(payload, dict):
        for value in payload.values():
            found |= _code_values(value)
    elif isinstance(payload, list):
        for item in payload:
            found |= _code_values(item)
    return found


def _code_list_values(config: dict) -> set[str]:
    """The pack's code-list values -- the condition codes no code may hard-code."""
    for name in ("code_lists", "codes", "code_sets", "codelists"):
        section = config.get(name)
        if section:
            return _code_values(section)
    return set()


def _scanned_files() -> list[Path]:
    return sorted(path for path in APP.rglob("*.py") if PACK_DIR not in path.parents)


def _docstring_lines(source: str) -> set[int]:
    """The line numbers covered by docstrings: prose, not hard-coded logic."""
    lines: set[int] = set()
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return lines
    for node in ast.walk(tree):
        if not isinstance(node, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        body = getattr(node, "body", [])
        if (
            body
            and isinstance(body[0], ast.Expr)
            and isinstance(body[0].value, ast.Constant)
            and isinstance(body[0].value.value, str)
        ):
            first = body[0]
            lines.update(range(first.lineno, (first.end_lineno or first.lineno) + 1))
    return lines


def _code_lines(path: Path) -> list[tuple[int, str]]:
    """Executable lines of a module: comments and docstrings stripped, so the
    scan judges code rather than prose."""
    source = path.read_text()
    skip = _docstring_lines(source)
    out: list[tuple[int, str]] = []
    for number, line in enumerate(source.splitlines(), start=1):
        if number in skip:
            continue
        code = line.split("#", 1)[0]
        if code.strip():
            out.append((number, code))
    return out


def _hits(needle: str) -> list[str]:
    """`file:line` for every line of scanned application code containing `needle`."""
    pattern = re.compile(re.escape(needle), re.IGNORECASE)
    found: list[str] = []
    for path in _scanned_files():
        for number, line in _code_lines(path):
            if pattern.search(line):
                found.append(f"{path.relative_to(APP.parent)}:{number}: {line.strip()[:120]}")
    return found


def test_ac021_nfr019_no_named_axspa_identifier_is_hard_coded_outside_the_pack() -> None:
    """AC-021: the scan finds no 'HLA-B27', 'SPARTAN', 'ASAS' or 'axSpA' anywhere
    in backend/app/ outside backend/app/pack/packs/, and names file and line when
    it does."""
    offenders: dict[str, list[str]] = {}
    for identifier in NAMED_IDENTIFIERS:
        hits = _hits(identifier)
        if hits:
            offenders[identifier] = hits
    assert not offenders, (
        "these condition-specific identifiers are hard-coded outside the condition "
        f"pack: {offenders}"
    )


def test_ac021_nfr019_no_pack_code_list_value_is_hard_coded_outside_the_pack() -> None:
    """AC-021: the forbidden list is derived from the pack file itself -- none of
    the pack's own code-list values appears in application code."""
    values = _code_list_values(_pack_config())
    assert values, (
        "the condition pack carries no code lists, so the scan has nothing derived "
        "from the pack to look for"
    )

    offenders = {value: _hits(value) for value in sorted(values)}
    offenders = {value: hits for value, hits in offenders.items() if hits}
    assert not offenders, (
        "these code-list values from the condition pack are hard-coded in "
        f"application code outside the pack: {offenders}"
    )


def test_ac021_the_scan_reports_the_file_and_line_of_a_hit() -> None:
    """AC-021: the scan is useful -- when an identifier is present it names the
    file and the line, proven against a string that certainly is in the code."""
    hits = _hits("def ")
    assert hits, "the scan found no application code to scan at all"
    for hit in hits[:5]:
        parts = hit.split(":")
        assert parts[0].endswith(".py"), f"the scan does not name a file: {hit}"
        assert parts[1].isdigit(), f"the scan does not name a line number: {hit}"


def test_ac021_the_pack_directory_itself_is_excluded_from_the_scan() -> None:
    """AC-021: the pack's own file is where these identifiers belong, so it must
    not be part of the scanned set."""
    scanned = {str(path) for path in _scanned_files()}
    inside_pack = {path for path in scanned if str(PACK_DIR) in path}
    assert not inside_pack, f"the scan includes the pack's own files: {sorted(inside_pack)}"
