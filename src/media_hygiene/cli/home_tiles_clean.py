"""The "where you are" tiles of cleaning: audit, copies, intruders, quarantine, NAS."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from media_hygiene.cli.home_stage_lines import backup_only, extra_copies
from media_hygiene.cli.menu_entry import Space
from media_hygiene.cli.status_view import ago
from media_hygiene.console.formatting import human_number, human_size
from media_hygiene.i18n import _, ngettext
from media_hygiene.review.home_parts import HomeTile, Pill

if TYPE_CHECKING:
    from media_hygiene.report.summary import ReportSummary
    from media_hygiene.services.status import Status

_TIME: Final = "%H:%M"
_DASH: Final = "—"
INTRUDERS_STEP: Final = "review-intruders"


def clean_tiles(status: Status) -> tuple[HomeTile, ...]:
    """The tiles of the audit, the copies, the intruders, the quarantine, the NAS.

    Args:
        status: What the tool folders say.

    Returns:
        Five tiles.
    """
    summary = status.analysis.summary
    extra = extra_copies(status)
    runs = status.quarantine.runs
    nas = backup_only(status)
    audit = HomeTile(
        id="audit",
        label=_("Last audit"),
        value=ago(summary.created_at) if summary else _("Never"),
        sub=audited(summary) if summary else _("It changes nothing in your photos"),
        space=Space.CLEAN.value,
        pill=Pill.OK if summary else Pill.TODO,
    )
    copies = HomeTile(
        id="copies",
        label=_("Extra copies"),
        value=human_number(extra) if summary else _DASH,
        sub=_copies_sub(summary, extra),
        space=Space.CLEAN.value,
        pill=(Pill.TODO if extra else Pill.OK) if summary else Pill.NONE,
    )
    quarantine = HomeTile(
        id="quarantine",
        label=_("Quarantine"),
        value=human_size(status.quarantine.size) if runs else _("Empty"),
        sub=_("{count} files, since {when}").format(
            count=human_number(status.quarantine.files), when=ago(runs[-1].started)
        )
        if runs
        else _("Nothing set aside"),
        space=Space.HISTORY.value,
        pill=Pill.CHECK if runs else Pill.NONE,
    )
    only = HomeTile(
        id="nas",
        label=_("Only on the NAS"),
        value=human_number(nas) if summary else _DASH,
        sub=_("Files the PC lacks") if nas else _("The PC has it all"),
        space=Space.IMPORT.value,
        pill=Pill.TODO if nas else Pill.NONE,
    )
    return audit, copies, _intruders_tile(summary), quarantine, only


def _intruders_tile(summary: ReportSummary | None) -> HomeTile:
    """The tile of the intruder files (0515): their weight; a click opens their page.

    Args:
        summary: The last audit or clean.

    Returns:
        The tile; with none found, it leads to the Clean space (an empty page helps
        nobody).
    """
    files = summary.intruder_files if summary else 0
    if summary is None:
        value, sub = _DASH, _("The audit counts them")
    elif files:
        value = human_size(summary.intruder_bytes)
        sub = ngettext(
            "{count} file at the last audit, to set aside?",
            "{count} files at the last audit, to set aside?",
            files,
        ).format(count=human_number(files))
    else:
        value, sub = _("None"), _("Only photos and videos")
    return HomeTile(
        id="intruders",
        label=_("Intruder files"),
        value=value,
        sub=sub,
        space=Space.CLEAN.value,
        pill=Pill.TODO if files else Pill.NONE,
        step=INTRUDERS_STEP if files else "",
    )


def _copies_sub(summary: ReportSummary | None, extra: int) -> str:
    """What the tile of the extra copies says under its count.

    Args:
        summary: The last audit or clean.
        extra: The extra copies not cleaned yet.

    Returns:
        The room to free, that none is left, or that the audit counts them.
    """
    if summary is None:
        return _("The audit counts them")
    if extra:
        return _("{size} to free").format(size=human_size(summary.reclaimable_bytes))
    return _("None: it is clean")


def audited(summary: ReportSummary) -> str:
    """The files the last audit read, and when.

    Args:
        summary: The last audit or clean.

    Returns:
        E.g. "48,213 photos and videos, at 11:03".
    """
    return _("{count} photos and videos, at {time}").format(
        count=human_number(summary.files_scanned),
        time=summary.created_at.astimezone().strftime(_TIME),
    )
