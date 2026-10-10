"""Before `clean --tier near` asks: the report that shows every near duplicate it moves.

Near duplicates are not identical files: a person should see them before answering. The
report of the clean is written after the clean, too late for that; this one is written
before the question, from the same audit, and its page of near duplicates alone is
linked in the line above it.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.cli.context import warn
from media_hygiene.console.links import file_link
from media_hygiene.constants import NEAR_FILE_NAME, RunKind
from media_hygiene.errors import MountError
from media_hygiene.i18n import _, ngettext
from media_hygiene.report.views import ReportRecord
from media_hygiene.services.reporting import write_report

if TYPE_CHECKING:
    from media_hygiene.plan.models import AuditFindings
    from media_hygiene.services.runtime import Runtime


def show_near_first(runtime: Runtime, findings: AuditFindings, *, yes: bool) -> None:
    """Write the report of the audit and link it, when near duplicates are to be moved.

    Nothing is written when nobody is asked: `--yes` or `[clean] confirm = false`.

    Args:
        runtime: Settings, mount points and output.
        findings: The audit, its plan as the clean will execute it.
        yes: `--yes` was given.
    """
    if not findings.plan.near or yes or not runtime.settings.clean.confirm:
        return
    output = runtime.output
    working = output.console.status(_("Writing the HTML report and its previews…"))
    try:
        with working:
            report = write_report(runtime, ReportRecord(RunKind.AUDIT, findings))
    except MountError as exc:
        warn(output, exc)
        return
    if report is None:
        output.tip(
            _(
                'Add -v "<a folder of yours>:/reports" to see the near duplicates '
                "in an HTML report before answering."
            )
        )
        return
    page = report.parent / NEAR_FILE_NAME
    line = _(
        "👀 Not identical files: look at them before answering, every one on a "
        "single page: {path} (Ctrl+click opens it)."
    )
    output.info(line.format(path=file_link(runtime.mapper.to_host(page))))


def near_waiting(count: int) -> str:
    """Say that decisions on near duplicates wait for a near tier.

    Args:
        count: The groups decided in `review --near`.

    Returns:
        The translated line.
    """
    message = ngettext(
        "{count} near-duplicate group decided in 'review --near' waits for "
        "--tier near: nothing of it moves without it.",
        "{count} near-duplicate groups decided in 'review --near' wait for "
        "--tier near: nothing of them moves without it.",
        count,
    )
    return message.format(count=count)
