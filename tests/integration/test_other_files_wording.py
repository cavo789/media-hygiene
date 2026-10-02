"""Copies of other files than media read "moved to the quarantine", not "deleted"."""

from __future__ import annotations

import io
from typing import TYPE_CHECKING

from rich.console import Console

from media_hygiene.console.tables import folder_pairs_view
from media_hygiene.constants import RunKind
from media_hygiene.report.views import ReportRecord
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.audit import AuditService
from media_hygiene.services.reporting import write_report
from tests.support.runtime import make_runtime

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.config.layers import Layer
    from media_hygiene.paths.locations import Locations
    from tests.support.media import MediaFactory

_ASKED: Layer = {"scan": {"extensions": ["pdf", "jpg"]}}


def _document(path: Path, content: bytes) -> None:
    """Write a small document, creating its folder."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def test_a_pdf_pair_reads_moved_to_the_quarantine(
    locations: Locations,
    media: MediaFactory,
) -> None:
    r"""C:\Docs\old loses a PDF (moved), C:\Photos\old a photo (deleted)."""
    data = locations.data_dir
    _document(data / "c/Docs/Contract.pdf", b"%PDF-1.7 contract")
    _document(data / "c/Docs/old/Contract.pdf", b"%PDF-1.7 contract")
    photo = media.image("c/Photos/IMG_1.jpg", seed=1)
    media.copy(photo, "c/Photos/old/IMG_1.jpg")
    runtime = make_runtime(locations, _ASKED)
    findings = AuditService(runtime, NullProgress()).run()
    buffer = io.StringIO()
    Console(file=buffer, width=300).print(folder_pairs_view(findings, runtime.mapper))
    console = buffer.getvalue()
    assert "C:\\Docs\\old (moved to the quarantine)" in console
    assert "C:\\Photos\\old (deleted)" in console
    report = write_report(runtime, ReportRecord(RunKind.AUDIT, findings))
    assert report is not None
    html = report.read_text()
    assert "Will be deleted or moved to the quarantine from" in html
    assert "📦 C:\\Docs\\old\\Contract.pdf" in html
    assert "🗑️ C:\\Photos\\old\\IMG_1.jpg" in html
    pages = {
        page.read_text().count("Will be moved to the quarantine from")
        for page in (report.parent / "pairs").glob("pair-*.html")
    }
    assert pages == {0, 1}
