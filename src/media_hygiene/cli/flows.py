"""Steps shared by several commands: audit and display, report, confirmation."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.cli.context import warn
from media_hygiene.console.crosscheck_outdated import show_outdated
from media_hygiene.console.crosscheck_view import show_cross_check
from media_hygiene.console.inventory_view import inventory_table
from media_hygiene.console.links import file_link
from media_hygiene.console.progress import RichProgress
from media_hygiene.console.tables import findings_table, folder_pairs_view
from media_hygiene.constants import REPORT_INDEX_FILE_NAME
from media_hygiene.errors import CrossCheckError, MediaHygieneError, MountError
from media_hygiene.i18n import _
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.services.audit import AuditService
from media_hygiene.services.crosscheck import cross_check, czkawka_refresh
from media_hygiene.services.reporting import write_report
from media_hygiene.services.writable import ensure_writable

if TYPE_CHECKING:
    from pathlib import Path
    from typing import TextIO

    from media_hygiene.console.output import Output
    from media_hygiene.crosscheck.compare import CrossCheckResult
    from media_hygiene.plan.models import AuditFindings
    from media_hygiene.report.views import ReportRecord
    from media_hygiene.services.runtime import Runtime


def audit_and_show(runtime: Runtime) -> AuditFindings:
    """Run the audit with progress bars, then print its summary.

    Args:
        runtime: Settings, mount points and output.

    Returns:
        The findings.

    Raises:
        MountError: The index or the report could not be written (checked first).
    """
    ensure_writable(runtime, MountKind.CACHE, MountKind.REPORTS)
    output = runtime.output
    output.title(_("Audit"))
    with RichProgress(output.console) as progress:
        findings = AuditService(runtime, progress).run()
    output.show(findings_table(findings))
    output.blank()
    inventory = inventory_table(findings.inventory)
    if inventory is not None:
        output.show(inventory)
        output.blank()
    show_pairs(runtime, findings)
    return findings


def show_pairs(runtime: Runtime, findings: AuditFindings) -> None:
    """Print the folder pairs freeing the most space, when there are any.

    Args:
        runtime: Settings, mount points and output.
        findings: The audit, or the plan once reviewed.
    """
    pairs = folder_pairs_view(findings, runtime.mapper)
    if pairs is not None:
        runtime.output.show(pairs)
        runtime.output.blank()


def show_second_opinion(
    runtime: Runtime, findings: AuditFindings
) -> CrossCheckResult | None:
    """Show Czkawka's verdict on this audit, or say it was not cross-checked.

    Information only: unusable Czkawka results are a warning, never an error.

    Args:
        runtime: Settings, mount points and output.
        findings: The audit just run.

    Returns:
        The comparison, or None without Czkawka results.
    """
    try:
        result = cross_check(runtime, findings)
    except CrossCheckError as exc:  # information only: never blocks a clean
        runtime.output.warning(exc.message)
        return None
    if result is None:
        runtime.output.tip(
            _("For a second opinion, run 'crosscheck' (same -v options).")
        )
        return None
    result = show_verdict(runtime, result)
    runtime.output.blank()
    return result


def show_verdict(runtime: Runtime, result: CrossCheckResult) -> CrossCheckResult | None:
    """Show Czkawka's verdict, or why its outdated results are ignored.

    Args:
        runtime: Settings, mount points and output.
        result: The comparison.

    Returns:
        The comparison, or None when Czkawka ran before files were removed.
    """
    if result.outdated:
        show_outdated(runtime.output, result.results_date, czkawka_refresh(runtime))
        return None
    show_cross_check(runtime.output, result, runtime.mapper)
    return result


def report_and_announce(runtime: Runtime, record: ReportRecord) -> None:
    """Write the HTML report and tell the user where it is.

    A report that cannot be written is only a warning: the results are on screen.

    Args:
        runtime: Settings, mount points and output.
        record: What to report.
    """
    output = runtime.output
    # Previews of thousands of photos take seconds: a spinner says the tool works.
    working = output.console.status(_("Writing the HTML report and its previews…"))
    try:
        with working:
            report = write_report(runtime, record)
    except MountError as exc:
        warn(output, exc)
        return
    if report is None:
        output.tip(_('Add -v "<a folder of yours>:/reports" to get HTML reports.'))
        return
    mapper = runtime.mapper
    index = runtime.locations.reports_dir / REPORT_INDEX_FILE_NAME
    index_on_host = mapper.to_host(index)
    if index_on_host == str(index):  # the host folder behind /reports is unknown
        _announce_in_container(output, report)
        return
    output.success(
        _("HTML report: {path}").format(path=file_link(mapper.to_host(report)))
    )
    output.tip(
        _("Every report is listed in {path} (Ctrl+click opens it).").format(
            path=file_link(index_on_host)
        )
    )


def _announce_in_container(output: Output, report: Path) -> None:
    """Name the report by its container path: its host folder is unknown.

    Args:
        output: Where to print.
        report: The report written.
    """
    output.success(_("HTML report: {path}").format(path=report))
    output.tip(
        _("Open index.html in the folder mounted on /reports: it lists every report."),
    )


def require_terminal(stdin: TextIO) -> None:
    """Refuse to ask a question without a terminal to answer it in.

    Args:
        stdin: The standard input.

    Raises:
        MediaHygieneError: There is no interactive terminal.
    """
    if not stdin.isatty():
        raise MediaHygieneError(
            _("Cannot ask for confirmation without an interactive terminal."),
            _("Run docker with -it, or add --yes."),
        )
