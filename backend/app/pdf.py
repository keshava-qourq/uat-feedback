"""A very small PDF writer for the exported documents.

WeasyPrint is the project's renderer for rich documents, but it needs the
native Pango stack; the export here is a few lines of text per page, so the
bytes are written directly. Each page is drawn with the base-14 Helvetica
font, which needs no embedded font file, and the synthetic-data notice is
drawn as the last line of every page (AC-120).
"""

from __future__ import annotations

import io

from app.notice import SYNTHETIC_DATA_NOTICE


def _escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _content(lines: list[str]) -> bytes:
    parts = ["BT", "/F1 11 Tf", "1 0 0 1 56 760 Tm", "14 TL"]
    for line in lines:
        parts.append(f"({_escape(line)}) Tj")
        parts.append("T*")
    parts.append("ET")
    return "\n".join(parts).encode("latin-1", "replace")


def render_pdf(pages: list[list[str]]) -> bytes:
    """A PDF of `pages`, each a list of text lines, each ending in the notice."""
    pages = pages or [[]]
    objects: list[bytes] = []

    def add(body: bytes) -> int:
        objects.append(body)
        return len(objects)

    content_ids = []
    for lines in pages:
        stream = _content([*lines, "", SYNTHETIC_DATA_NOTICE])
        body = b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream"
        content_ids.append(add(body))
    font_id = add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    pages_id = len(objects) + len(pages) + 1
    page_ids = [
        add(
            b"<< /Type /Page /Parent %d 0 R /MediaBox [0 0 595 842] "
            b"/Resources << /Font << /F1 %d 0 R >> >> /Contents %d 0 R >>"
            % (pages_id, font_id, content_id)
        )
        for content_id in content_ids
    ]
    kids = b" ".join(b"%d 0 R" % page_id for page_id in page_ids)
    add(b"<< /Type /Pages /Count %d /Kids [%s] >>" % (len(page_ids), kids))
    root_id = add(b"<< /Type /Catalog /Pages %d 0 R >>" % pages_id)

    out = io.BytesIO()
    out.write(b"%PDF-1.4\n")
    offsets = []
    for number, body in enumerate(objects, start=1):
        offsets.append(out.tell())
        out.write(b"%d 0 obj\n" % number + body + b"\nendobj\n")
    xref = out.tell()
    out.write(b"xref\n0 %d\n" % (len(objects) + 1))
    out.write(b"0000000000 65535 f \n")
    for offset in offsets:
        out.write(b"%010d 00000 n \n" % offset)
    out.write(
        b"trailer\n<< /Size %d /Root %d 0 R >>\nstartxref\n%d\n%%%%EOF\n"
        % (len(objects) + 1, root_id, xref)
    )
    return out.getvalue()
