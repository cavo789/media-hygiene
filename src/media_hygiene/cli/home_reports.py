"""The reports the home page links to."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.cli.status_view import when
from media_hygiene.constants import REPORT_FILE_NAME, RunKind
from media_hygiene.i18n import _
from media_hygiene.review.home_parts import HomeReport
from media_hygiene.review.home_views import REPORTS_PREFIX

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from media_hygiene.report.summary import ReportSummary


def latest_reports(
    folders: Sequence[tuple[ReportSummary, Path]],
) -> tuple[HomeReport, ...]:
    """The newest audit and the newest clean, each linked to its report.

    Args:
        folders: Every report read, newest first, with its folder (`Status.reports`).

    Returns:
        At most one report of each kind, newest first.
    """
    labels = {RunKind.AUDIT: _("Last audit"), RunKind.CLEAN: _("Last clean")}
    found: dict[RunKind, HomeReport] = {}
    for summary, folder in folders:
        if summary.kind in found or not (folder / REPORT_FILE_NAME).is_file():
            continue
        found[summary.kind] = HomeReport(
            label=labels[summary.kind],
            when=when(summary.created_at),
            url=f"{REPORTS_PREFIX}{folder.name}/{REPORT_FILE_NAME}",
        )
    return tuple(found.values())
