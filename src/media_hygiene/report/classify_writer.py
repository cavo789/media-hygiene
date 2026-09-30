"""Write the classify report: an index page, one page per year, the previews.

70,000 thumbnails do not fit one page: each year has its own, and each group shows at
most 8 previews. Links open the files themselves (`file:///C:/Photos/...`).
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Final
from urllib.parse import quote

from media_hygiene.classify.layout import month_name
from media_hygiene.classify.names import lost_line
from media_hygiene.classify.worklist import work_list
from media_hygiene.constants import REPORT_FILE_NAME
from media_hygiene.report.classify_tree import proposed_tree
from media_hygiene.report.classify_views import work_left, year_groups
from media_hygiene.report.environment import make_environment
from media_hygiene.report.thumbnails import (
    PREVIEWABLE,
    ThumbnailJob,
    make_thumbnails,
    preview_name,
)
from media_hygiene.scan.filters import media_kind

if TYPE_CHECKING:
    from concurrent.futures import Executor
    from pathlib import Path

    from media_hygiene.classify.plan_file import ClassifyPlan, PlanRow
    from media_hygiene.paths.host_paths import HostPathMapper
    from media_hygiene.report.classify_views import GroupView

_INDEX_TEMPLATE: Final = "classify.html.j2"
_YEAR_TEMPLATE: Final = "classify_year.html.j2"
_TOP_EVENTS: Final = 20


def year_page(year: int) -> str:
    """The file name of a year's page.

    Args:
        year: The year; 0 for the undated files.

    Returns:
        `2016.html`, or `undated.html`.
    """
    return f"{year}.html" if year else "undated.html"


def file_url(host_path: str) -> str:
    """A link that opens a file from the report, on the host.

    Args:
        host_path: A Windows or a Linux host path.

    Returns:
        A `file://` URL.
    """
    path = host_path.replace("\\", "/")
    return "file://" + quote(path if path.startswith("/") else "/" + path)


@dataclass(frozen=True, slots=True)
class ClassifyReportWriter:
    """Writes the report of a classify run into its folder."""

    folder: Path
    mapper: HostPathMapper
    executor: Executor

    def write(self, plan: ClassifyPlan) -> Path:
        """Write the report of a plan.

        Args:
            plan: The plan.

        Returns:
            Path of its `report.html`.
        """
        years = year_groups(plan)
        previews = self._previews(
            [
                row
                for groups in years.values()
                for group in groups
                for row in group.shown
            ]
        )
        environment = make_environment()
        environment.filters["file_url"] = file_url
        environment.globals["year_page"] = year_page
        page = environment.get_template(_YEAR_TEMPLATE)
        for year, groups in years.items():
            (self.folder / year_page(year)).write_text(
                page.render(year=year, groups=groups, previews=previews),
                encoding="utf-8",
            )
        first = {group.key: year for year, groups in years.items() for group in groups}
        target = self.folder / REPORT_FILE_NAME
        target.write_text(
            environment.get_template(_INDEX_TEMPLATE).render(
                plan=plan,
                left=work_left(plan),
                in_place=sum(1 for row in plan.rows if row.in_place),
                years={year: _counts(groups) for year, groups in years.items()},
                top=[(item, first[item.event.id]) for item in work_list(plan)][
                    :_TOP_EVENTS
                ],
                tree=proposed_tree(plan),
                saved=_saved(plan),
                lost=[lost_line(lost) for lost in plan.carried.lost]
                if plan.carried
                else [],
            ),
            encoding="utf-8",
        )
        return target

    def _previews(self, rows: list[PlanRow]) -> dict[str, str]:
        """Render the previews of the rows shown.

        Args:
            rows: The rows shown in the pages.

        Returns:
            Row id → preview, relative to the report folder.
        """
        jobs: dict[str, ThumbnailJob] = {}
        for row in rows:
            source = self.mapper.to_container(row.path)
            if media_kind(source) in PREVIEWABLE:
                jobs[row.id] = ThumbnailJob(source, self.folder / preview_name(source))
        written = asyncio.run(make_thumbnails(list(jobs.values()), self.executor))
        return {
            row_id: preview_name(job.source)
            for row_id, job in jobs.items()
            if job.target in written
        }


def _saved(plan: ClassifyPlan) -> str:
    """When the workbook carried over was saved, as people write it.

    Args:
        plan: The plan.

    Returns:
        `2 October 2026, 14:32`, or empty when nothing was carried.
    """
    if plan.carried is None:
        return ""
    saved = datetime.fromisoformat(plan.carried.saved_at)
    return f"{saved.day} {month_name(saved.month)} {saved.year}, {saved:%H:%M}"


def _counts(groups: list[GroupView]) -> tuple[int, int, int]:
    """Files, groups and files left of one year.

    Args:
        groups: Its groups.

    Returns:
        The three counts.
    """
    return (
        sum(len(group.rows) for group in groups),
        len(groups),
        sum(group.undecided for group in groups),
    )
