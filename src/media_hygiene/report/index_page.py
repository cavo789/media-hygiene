"""The report catalogue: `index.html`, listing, pruning."""

from __future__ import annotations

import logging
import re
import shutil
from typing import TYPE_CHECKING, Final

from pydantic import ValidationError

from media_hygiene.constants import REPORT_INDEX_FILE_NAME, SUMMARY_FILE_NAME
from media_hygiene.report.environment import make_environment
from media_hygiene.report.summary import ReportSummary

if TYPE_CHECKING:
    from pathlib import Path

_LOGGER = logging.getLogger(__name__)
_INDEX_TEMPLATE = "index.html.j2"
# `<run or stamp>-<kind>`, with a number when two reports share a second.
_REPORT_FOLDER: Final = re.compile(r"\d{8}-\d{6}(?:-\d+)?-[a-z]+(?:-\d+)?")


def load_summaries(reports_dir: Path) -> list[ReportSummary]:
    """Read the summary of every report, newest first; unreadable ones are skipped.

    Args:
        reports_dir: Reports mount point.

    Returns:
        The summaries.
    """
    return [summary for summary, _folder in _reports(reports_dir)]


def _reports(reports_dir: Path) -> list[tuple[ReportSummary, Path]]:
    """Read every report: its summary and the folder holding it, newest first.

    Args:
        reports_dir: Reports mount point.

    Returns:
        The summaries, each with the folder its `summary.json` was found in.
    """
    found: list[tuple[ReportSummary, Path]] = []
    for file in reports_dir.glob(f"*/{SUMMARY_FILE_NAME}"):
        try:
            summary = ReportSummary.model_validate_json(file.read_text("utf-8"))
        except OSError, ValidationError:
            _LOGGER.warning("Skipping unreadable report summary %s", file)
            continue
        found.append((summary, file.parent))
    return sorted(found, key=lambda item: item[0].created_at, reverse=True)


def write_index(reports_dir: Path) -> Path:
    """(Re)generate `index.html`, the entry page listing every report.

    Args:
        reports_dir: Reports mount point.

    Returns:
        Path of the index page.
    """
    page = make_environment().get_template(_INDEX_TEMPLATE)
    target = reports_dir / REPORT_INDEX_FILE_NAME
    target.write_text(
        page.render(summaries=load_summaries(reports_dir)), encoding="utf-8"
    )
    return target


def prune_reports(reports_dir: Path, keep: int) -> list[str]:
    """Delete every report but the `keep` most recent ones, then refresh the index.

    Only a report the tool wrote is deleted: a real folder, directly in `reports_dir`,
    named like a report (`20260925-183015-audit`), holding its `summary.json`. The
    folder is the one the summary was found in, never a name read from the file.

    Args:
        reports_dir: Reports mount point.
        keep: How many reports to keep.

    Returns:
        The folders deleted.
    """
    removed = [
        folder
        for _summary, folder in _reports(reports_dir)[keep:]
        if _REPORT_FOLDER.fullmatch(folder.name) and not folder.is_symlink()
    ]
    for folder in removed:
        shutil.rmtree(folder)
    write_index(reports_dir)
    return [folder.name for folder in removed]
