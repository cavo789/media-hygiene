"""What the last audit or clean found, each finding with the action it calls for."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.cli.home_stage_lines import backup_only, extra_copies
from media_hygiene.cli.home_tiles import audited
from media_hygiene.cli.status_view import ago
from media_hygiene.console.formatting import human_number, human_size
from media_hygiene.constants import RunKind
from media_hygiene.i18n import _
from media_hygiene.review.home_parts import HomeFinding, HomeFindings

if TYPE_CHECKING:
    from media_hygiene.report.summary import ReportSummary
    from media_hygiene.services.status import Status


def home_findings(status: Status, *, backups: bool) -> HomeFindings | None:
    """What the last audit or clean found, each finding with its action.

    Args:
        status: What the tool folders say.
        backups: A backup folder is compared.

    Returns:
        The findings; None before any report.
    """
    summary = status.analysis.summary
    if summary is None:
        return None
    rows = [_copies(status, summary)]
    if summary.broken_files:
        rows.append(
            HomeFinding(
                icon="broken",
                title=_("{count} unreadable files").format(
                    count=human_number(summary.broken_files)
                ),
                sub=_("Damaged or incomplete: the report says which."),
                action="open",
            )
        )
    nas = backup_only(status)
    if nas:
        rows.append(
            HomeFinding(
                icon="nas",
                title=_("{count} files only on the NAS").format(
                    count=human_number(nas)
                ),
                sub=_("The PC lacks them; never those you set aside on purpose."),
                action="import",
            )
        )
    elif backups:
        rows.append(
            HomeFinding(
                icon="check",
                title=_("The PC has all the NAS keeps"),
                sub=_("Nothing to get back."),
                ok=True,
            )
        )
    audit = summary.kind is RunKind.AUDIT
    return HomeFindings(
        title=_("What the last audit found")
        if audit
        else _("What the last clean left"),
        note=f"{ago(summary.created_at)} · {audited(summary)}",
        rows=tuple(rows),
    )


def _copies(status: Status, summary: ReportSummary) -> HomeFinding:
    """The finding of the exact copies: to set aside, in the quarantine, or none.

    Args:
        status: What the tool folders say.
        summary: The last audit or clean.

    Returns:
        The finding.
    """
    extra = extra_copies(status)
    if extra:
        return HomeFinding(
            icon="copy",
            title=_("{count} identical copies").format(count=human_number(extra)),
            sub=_("{size} · no risk: one command, undoable.").format(
                size=human_size(summary.reclaimable_bytes)
            ),
            action="clean",
        )
    if status.quarantine.runs:
        return HomeFinding(
            icon="check",
            title=_("The identical copies are set aside"),
            sub=_("{count} files in the quarantine: check, then free the room.").format(
                count=human_number(status.quarantine.files)
            ),
            action="purge",
        )
    return HomeFinding(
        icon="check",
        title=_("No identical copy"),
        sub=_("Your folders are clean."),
        ok=True,
    )
