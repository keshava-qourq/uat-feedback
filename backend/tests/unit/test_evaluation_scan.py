"""AC-009: ground truth is reachable from the evaluation module and nowhere else.

A source scan over `backend/app/`: neither the evaluation-only accessor
`evaluation_labels` nor the `patient_labels` table name may appear in any
module outside `app/labels.py` (the store itself) and `app/evaluation.py`
(the one component permitted to read ground truth). A hit fails naming the
offending file and line.

Comments and docstrings are stripped before the scan: prose that explains the
rule is not a read of ground truth, executable code is.
"""

from __future__ import annotations

import io
import tokenize
from pathlib import Path

APP = Path(__file__).resolve().parents[2] / "app"

#: The names no module outside the two allowed ones may mention in code.
FORBIDDEN = ("evaluation_labels", "patient_labels")

#: The store, and the one component permitted to read through it.
ALLOWED = {APP / "labels.py", APP / "evaluation.py"}


def _code_lines(path: Path) -> list[tuple[int, str]]:
    """Each line of `path` with its comments and string literals removed."""
    source = path.read_text()
    lines = source.splitlines()
    blanked = {}
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
    except tokenize.TokenError:  # pragma: no cover -- app sources always tokenise
        return list(enumerate(lines, start=1))
    for token in tokens:
        if token.type in (tokenize.COMMENT, tokenize.STRING):
            for number in range(token.start[0], token.end[0] + 1):
                blanked[number] = ""
    return [(number, blanked.get(number, line)) for number, line in enumerate(lines, start=1)]


def _hits() -> list[str]:
    found: list[str] = []
    for path in sorted(APP.rglob("*.py")):
        if path in ALLOWED:
            continue
        for number, line in _code_lines(path):
            for name in FORBIDDEN:
                if name in line:
                    found.append(
                        f"{path.relative_to(APP.parent)}:{number}: '{name}' -- {line.strip()}"
                    )
    return found


def test_ac009_ground_truth_is_read_only_by_the_labels_store_and_the_evaluation_module():
    hits = _hits()
    assert not hits, (
        "AC-009: only app/labels.py and app/evaluation.py may name the "
        "evaluation-only accessor or the patient_labels table:\n" + "\n".join(hits)
    )


def test_ac009_the_scan_reports_the_file_and_line_of_a_hit(tmp_path, monkeypatch):
    """The scan is not vacuous: a planted read is reported with its location."""
    offender = APP / "_scan_probe_tmp.py"
    offender.write_text("from app.labels import evaluation_labels\n")
    try:
        hits = _hits()
    finally:
        offender.unlink()
    assert any("_scan_probe_tmp.py:1" in hit and "evaluation_labels" in hit for hit in hits)


def test_ac009_both_allowed_modules_do_name_the_accessor():
    assert "evaluation_labels" in (APP / "labels.py").read_text()
    assert "evaluation_labels" in (APP / "evaluation.py").read_text()
