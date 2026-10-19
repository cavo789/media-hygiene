"""The audit the home page runs: the same checks, settings and report as `audit`.

Started from the page, the audit sees the folders and the settings of the `home`
command (those of `mh audit`); its report and what it lets the user do are those
`audit` would write and print.
"""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

from media_hygiene.cli.audit_actions import action_list
from media_hygiene.cli.status_view import status_lines
from media_hygiene.console.stage_times import stages_line
from media_hygiene.constants import RunKind
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.report.views import ReportRecord
from media_hygiene.review.home_views import REPORTS_PREFIX
from media_hygiene.services.audit import AuditService
from media_hygiene.services.data_checks import refuse_empty_data
from media_hygiene.services.home_audit import AuditResult
from media_hygiene.services.reporting import write_report
from media_hygiene.services.status import read_status
from media_hygiene.services.writable import ensure_writable

if TYPE_CHECKING:
    from collections.abc import Callable

    from media_hygiene.console.page_progress import PageProgress
    from media_hygiene.services.runtime import Runtime


def page_audit(runtime: Runtime) -> Callable[[PageProgress], AuditResult]:
    """The audit of the home page, on the folders and settings of `home`.

    Args:
        runtime: Settings, mount points and output.

    Returns:
        Runs it, reporting to the progress given.
    """
    return partial(_audit, runtime)


def _audit(runtime: Runtime, progress: PageProgress) -> AuditResult:
    """Audit, write the report, then say what was found and what to do.

    Args:
        runtime: Settings, mount points and output.
        progress: Where each step reports.

    Returns:
        The first line of `status` (the audit's figures), the actions, the report,
        and the time of each step, as the console's `Time per step` line.
    """
    refuse_empty_data(runtime, "audit")
    ensure_writable(runtime, MountKind.CACHE, MountKind.REPORTS)
    service = AuditService(runtime, progress)
    findings = service.run()
    service.guide.close()
    actions = action_list(runtime, findings)
    report = write_report(
        runtime, ReportRecord(RunKind.AUDIT, findings, actions=actions)
    )
    return AuditResult(
        lines=status_lines(read_status(runtime))[:1],
        actions=tuple(f"{action.icon} {action.text}" for action in actions),
        report=None
        if report is None
        else f"{REPORTS_PREFIX}{report.parent.name}/{report.name}",
        timed=stages_line(findings.stages),
    )
