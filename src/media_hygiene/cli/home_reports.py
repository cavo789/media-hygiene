"""The reports the home page links to, and the previews of the last audit."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from media_hygiene.cli.status_view import when
from media_hygiene.constants import REPORT_FILE_NAME, THUMBNAILS_DIR_NAME, RunKind
from media_hygiene.i18n import _
from media_hygiene.report.index_page import report_folders
from media_hygiene.review.home_parts import HomeReport
from media_hygiene.review.home_views import REPORTS_PREFIX

if TYPE_CHECKING:
    from pathlib import Path

_PREVIEWS: Final = 8  # thumbnails of the last audit shown on the home page


def latest_reports(reports: Path) -> tuple[HomeReport, ...]:
    """The newest audit and the newest clean, each linked to its report.

    Args:
        reports: The reports folder.

    Returns:
        At most one report of each kind, newest first.
    """
    labels = {RunKind.AUDIT: _("Last audit"), RunKind.CLEAN: _("Last clean")}
    found: dict[RunKind, HomeReport] = {}
    for summary, folder in report_folders(reports):
        if summary.kind in found or not (folder / REPORT_FILE_NAME).is_file():
            continue
        found[summary.kind] = HomeReport(
            label=labels[summary.kind],
            when=when(summary.created_at),
            url=f"{REPORTS_PREFIX}{folder.name}/{REPORT_FILE_NAME}",
        )
    return tuple(found.values())


def audit_previews(reports: Path) -> tuple[str, ...]:
    """A few thumbnails of the newest audit's report: what it found.

    Args:
        reports: The reports folder.

    Returns:
        Their addresses on the page, at most `_PREVIEWS`.
    """
    folders = (
        folder
        for summary, folder in report_folders(reports)
        if summary.kind is RunKind.AUDIT
    )
    folder = next(folders, None)
    if folder is None:
        return ()
    thumbs = sorted((folder / THUMBNAILS_DIR_NAME).glob("*.jpg"))[:_PREVIEWS]
    return tuple(
        f"{REPORTS_PREFIX}{folder.name}/{THUMBNAILS_DIR_NAME}/{thumb.name}"
        for thumb in thumbs
    )
