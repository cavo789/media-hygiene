"""The end of an audit names its report the way the user can open it."""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

from media_hygiene.cli.flows import report_and_announce
from media_hygiene.constants import RunKind
from media_hygiene.paths.mounts import MountTable
from media_hygiene.report.views import ReportRecord
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.audit import AuditService
from tests.support.runtime import make_runtime, output_of

if TYPE_CHECKING:
    from media_hygiene.paths.locations import Locations

_HOST_REPORTS = r"C:\Users\John Doe\media-hygiene\reports"


def test_windows_folder_of_the_reports_is_shown(locations: Locations) -> None:
    """Docker Desktop tells the Windows folder: full paths, no `/reports`.

    Args:
        locations: Mount points in a temporary directory.
    """
    (locations.data_dir / "c").mkdir()
    runtime = make_runtime(locations)
    sources = ((locations.reports_dir, _HOST_REPORTS),)
    runtime = replace(runtime, mounts=MountTable(frozenset(), host_sources=sources))
    findings = AuditService(runtime, NullProgress()).run()
    report_and_announce(runtime, ReportRecord(RunKind.AUDIT, findings))
    runtime.output.finish()  # the closing advice
    printed = output_of(runtime)
    assert f"{_HOST_REPORTS}\\" in printed
    assert "-audit\\report.html" in printed
    assert f"{_HOST_REPORTS}\\index.html (Ctrl+click opens it)" in printed


def test_unknown_folder_keeps_the_mount_point(locations: Locations) -> None:
    """Without Docker Desktop, the container path and the general tip remain.

    Args:
        locations: Mount points in a temporary directory.
    """
    (locations.data_dir / "c").mkdir()
    runtime = make_runtime(locations)
    findings = AuditService(runtime, NullProgress()).run()
    report_and_announce(runtime, ReportRecord(RunKind.AUDIT, findings))
    runtime.output.finish()  # the closing advice
    printed = output_of(runtime)
    assert f"{locations.reports_dir}/" in printed
    assert "Open index.html in the folder mounted on /reports" in printed
