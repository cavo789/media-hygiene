"""Write one report folder: previews, report and pair pages, `summary.json`, index."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Final

from media_hygiene.constants import (
    NEAR_FILE_NAME,
    PLAN_CSV_FILE_NAME,
    REPORT_FILE_NAME,
    SUMMARY_FILE_NAME,
)
from media_hygiene.report.backup_views import (
    backup_only,
    backup_section,
    write_backup_csvs,
)
from media_hygiene.report.builder import ReportBuilder
from media_hygiene.report.clean_done import asked_flags
from media_hygiene.report.csv_export import write_plan_csv
from media_hygiene.report.environment import make_environment
from media_hygiene.report.index_page import write_index
from media_hygiene.report.thumbnail_jobs import make_thumbnails

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.paths.host_paths import HostPathMapper
    from media_hygiene.report.preview_cache import PreviewPool
    from media_hygiene.report.views import ReportRecord

_STAMP_FORMAT: Final = "%Y%m%d-%H%M%S"
_REPORT_TEMPLATE: Final = "report.html.j2"
_PAIR_TEMPLATE: Final = "pair.html.j2"
_NEAR_TEMPLATE: Final = "near.html.j2"


@dataclass(frozen=True, slots=True)
class ReportWriter:
    """Writes reports below the reports mount point."""

    reports_dir: Path
    mapper: HostPathMapper
    pool: PreviewPool  # renders previews, and keeps them in the cache

    def write(self, record: ReportRecord) -> Path:
        """Write the report of an audit or a clean, and its near-duplicates page.

        Args:
            record: What to report.

        Returns:
            Path of `report.html`.
        """
        folder = self._new_folder(record)
        builder = ReportBuilder(self.mapper, folder)
        previews = asyncio.run(
            make_thumbnails(builder.thumbnail_jobs(record), self.pool)
        )
        view = builder.view(record, previews)
        backups = backup_section(record.findings.backups, self.mapper)  # 0204
        environment = make_environment()
        target = folder / REPORT_FILE_NAME
        page = environment.get_template(_REPORT_TEMPLATE)
        target.write_text(page.render(report=view, backups=backups), encoding="utf-8")
        if view.similar.near or view.similar.videos.groups:
            near_page = environment.get_template(_NEAR_TEMPLATE)
            (folder / NEAR_FILE_NAME).write_text(
                near_page.render(report=view), encoding="utf-8"
            )
        pair_page = environment.get_template(_PAIR_TEMPLATE)
        for name, pair_view in builder.pair_pages(record, previews):
            (folder / name).parent.mkdir(exist_ok=True)
            (folder / name).write_text(
                pair_page.render(page=pair_view), encoding="utf-8"
            )
        write_plan_csv(folder / PLAN_CSV_FILE_NAME, record.findings, self.mapper)
        write_backup_csvs(folder, record.findings.backups, self.mapper)
        # What only a backup holds: `mh menu` then proposes `import` (0265).
        summary = view.header.summary.model_copy(
            update={
                "backup_only": backup_only(record.findings.backups),
                **asked_flags(record.asked),  # 0309
            }
        )
        (folder / SUMMARY_FILE_NAME).write_text(
            summary.model_dump_json(indent=2), encoding="utf-8"
        )
        write_index(self.reports_dir)
        return target

    def _new_folder(self, record: ReportRecord) -> Path:
        stamp = record.run_id or datetime.now().astimezone().strftime(_STAMP_FORMAT)
        base = f"{stamp}-{record.kind.value}"
        folder, suffix = self.reports_dir / base, 1
        while folder.exists():
            suffix += 1
            folder = self.reports_dir / f"{base}-{suffix}"
        folder.mkdir(parents=True)
        return folder
