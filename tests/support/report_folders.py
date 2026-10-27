"""A report folder holding only its `summary.json`, for tests of the catalogue."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Final

from media_hygiene.constants import SUMMARY_FILE_NAME, RunKind
from media_hygiene.report.summary import ReportSummary

if TYPE_CHECKING:
    from pathlib import Path

MINIMAL: Final = {
    "files_scanned": 1,
    "duplicate_groups": 0,
    "duplicate_files": 0,
    "reclaimable_bytes": 0,
    "broken_files": 0,
}


def write_summary(where: Path, **fields: Any) -> ReportSummary:  # noqa: ANN401
    """Write a report folder with a minimal audit summary.

    Args:
        where: The report folder to create.
        **fields: The summary fields to set (`folder`, `kind`, `created_at`, `roots`).

    Returns:
        The summary written.
    """
    where.mkdir(parents=True)
    summary = ReportSummary(
        **{
            "folder": where.name,
            "kind": RunKind.AUDIT,
            **MINIMAL,
            **fields,
        }
    )
    (where / SUMMARY_FILE_NAME).write_text(summary.model_dump_json())
    return summary
