"""A second report decodes no picture: its previews come from the cache."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.constants import RunKind
from media_hygiene.report import preview_cache, thumbnails
from media_hygiene.report.views import ReportRecord
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.audit import AuditService
from media_hygiene.services.reporting import write_report
from tests.support.demo import build_demo
from tests.support.runtime import make_runtime

if TYPE_CHECKING:
    from pathlib import Path

    import pytest

    from media_hygiene.paths.locations import Locations


def test_a_second_report_decodes_no_picture(
    locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The first report renders and keeps its previews; the second copies them."""
    build_demo(locations.data_dir)
    runtime = make_runtime(locations)
    real = thumbnails.jpeg_preview
    decoded: list[Path] = []

    def counted(source: Path, edge: int) -> bytes | None:
        decoded.append(source)
        return real(source, edge)

    monkeypatch.setattr(preview_cache, "jpeg_preview", counted)
    findings = AuditService(runtime, NullProgress()).run()
    first = write_report(runtime, ReportRecord(RunKind.AUDIT, findings))
    assert decoded, "the demo report shows previews"
    decoded.clear()
    second = write_report(runtime, ReportRecord(RunKind.AUDIT, findings))
    assert not decoded
    assert first is not None
    assert second is not None
    assert first.parent != second.parent
    assert any((second.parent / "thumbs").iterdir())
    assert any((locations.cache_dir / "previews").iterdir())
