"""A file the disk could not read once is listed, left alone, then read again (0222)."""

from __future__ import annotations

import errno
import os
from typing import TYPE_CHECKING

from media_hygiene.console.unread_view import SHOWN_FIRST, show_unread
from media_hygiene.constants import MediaKind, RunKind
from media_hygiene.index.repository import FactsRepository
from media_hygiene.report.views import ReportRecord
from media_hygiene.scan import image_check
from media_hygiene.scan.models import MediaFile
from media_hygiene.scan.progress import NullProgress
from media_hygiene.scan.read_errors import UnreadFile
from media_hygiene.scan.whole_read import read_whole
from media_hygiene.services.audit import AuditService
from media_hygiene.services.clean import CleanService
from media_hygiene.services.reporting import write_report
from tests.support.media import MediaFactory
from tests.support.runtime import make_runtime, output_of

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    import pytest

    from media_hygiene.paths.locations import Locations
    from media_hygiene.plan.models import AuditFindings


def audit(locations: Locations) -> AuditFindings:
    """Run a complete audit of the data mount point."""
    return AuditService(make_runtime(locations), NullProgress()).run()


def unplugged(target: Path) -> Callable[[Path, int], bytes | None]:
    """A `read_whole` whose disk fails on `target` only."""

    def read(path: Path, limit: int) -> bytes | None:
        if path == target:
            raise OSError(errno.EIO, os.strerror(errno.EIO), str(path))
        return read_whole(path, limit)

    return read


def test_unread_file_is_left_then_read_again(
    locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Listed, never broken nor in the plan; clean leaves it; then read healthy."""
    media = MediaFactory(locations.data_dir / "c" / "Photos")
    original = media.image("a.jpg", seed=3)
    copy = media.copy(original, "a (1).jpg")
    monkeypatch.setattr(image_check, "read_whole", unplugged(copy))

    first = audit(locations)
    assert [item.file.path for item in first.unread] == [copy]
    assert "Input/output error" in first.unread[0].detail
    assert not first.plan.broken
    assert copy not in first.plan.removed
    assert first.plan.is_empty  # its copy has nothing to pair with this time
    report = write_report(make_runtime(locations), ReportRecord(RunKind.AUDIT, first))
    assert report is not None
    html = report.read_text(encoding="utf-8")
    assert 'id="unread"' in html
    assert "a (1).jpg" in html

    runtime = make_runtime(locations)
    service = CleanService(runtime, NullProgress())
    service.ensure_ready()
    service.execute(service.feasible(first.plan))
    assert copy.is_file()
    assert original.is_file()

    monkeypatch.undo()  # the disk is back
    second = audit(locations)
    assert not second.unread
    assert not second.plan.broken
    assert copy in second.plan.removed or original in second.plan.removed
    with FactsRepository.open(runtime.index_file) as repository:
        assert repository.get(_listed(second, copy)).integrity_checked


def _listed(findings: AuditFindings, path: Path) -> MediaFile:
    """The file the audit listed at `path`."""
    return next(
        file for group in findings.groups for file in group.files if file.path == path
    )


def test_console_names_the_first_ones(locations: Locations) -> None:
    """The console names a few files, then how many more the report lists."""
    runtime = make_runtime(locations)
    show_unread(runtime, ())
    assert not output_of(runtime)
    unread = tuple(
        UnreadFile(
            MediaFile(locations.data_dir / "c" / f"{n}.jpg", 1, 1, MediaKind.IMAGE)
        )
        for n in range(SHOWN_FIRST + 2)
    )
    show_unread(runtime, unread)
    text = output_of(runtime)
    assert "7 files could not be read this time" in text
    assert "4.jpg" in text
    assert "5.jpg" not in text
    assert "2 more" in text
