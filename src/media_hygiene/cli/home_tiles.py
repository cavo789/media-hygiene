"""The "where you are" tiles and what the last audit found, from the tool folders."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from media_hygiene.cli.home_stage_lines import backup_only, extra_copies
from media_hygiene.cli.menu_entry import Space
from media_hygiene.cli.status_view import ago
from media_hygiene.console.formatting import human_number, human_size
from media_hygiene.i18n import _
from media_hygiene.review.home_parts import HomeTile, Pill

if TYPE_CHECKING:
    from media_hygiene.report.summary import ReportSummary
    from media_hygiene.services.status import Status

_TIME: Final = "%H:%M"
_DASH: Final = "—"


def home_tiles(status: Status) -> tuple[HomeTile, ...]:
    """The tiles of the home page, each leading to its space.

    Args:
        status: What the tool folders say.

    Returns:
        Last audit, extra copies, quarantine, NAS, sort, words, faces, backup.
    """
    return (*_clean_tiles(status), *_later_tiles(status))


def _clean_tiles(status: Status) -> tuple[HomeTile, ...]:
    """The tiles of the audit, the copies, the quarantine and the NAS.

    Args:
        status: What the tool folders say.

    Returns:
        Four tiles.
    """
    summary = status.analysis.summary
    extra = extra_copies(status)
    runs = status.quarantine.runs
    nas = backup_only(status)
    audit = HomeTile(
        label=_("Last audit"),
        value=ago(summary.created_at) if summary else _("Never"),
        sub=audited(summary) if summary else _("It changes nothing in your photos"),
        space=Space.CLEAN.value,
        pill=Pill.OK if summary else Pill.TODO,
    )
    copies = HomeTile(
        label=_("Extra copies"),
        value=human_number(extra) if summary else _DASH,
        sub=_copies_sub(summary, extra),
        space=Space.CLEAN.value,
        pill=(Pill.TODO if extra else Pill.OK) if summary else Pill.NONE,
    )
    quarantine = HomeTile(
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
        label=_("Only on the NAS"),
        value=human_number(nas) if summary else _DASH,
        sub=_("Files the PC lacks") if nas else _("The PC has it all"),
        space=Space.IMPORT.value,
        pill=Pill.TODO if nas else Pill.NONE,
    )
    return audit, copies, quarantine, only


def _later_tiles(status: Status) -> tuple[HomeTile, ...]:
    """The tiles of the sort, the words, the faces and the backup.

    Args:
        status: What the tool folders say.

    Returns:
        Four tiles.
    """
    sort = status.sort
    words = status.tagged[0] if status.tagged else 0
    faces = status.faces
    return (
        HomeTile(
            label=_("Sort"),
            value=(_("Sorted") if sort.sorted else _("To apply"))
            if sort.proposed
            else _DASH,
            sub=_("Proposed {when}").format(when=ago(sort.proposed))
            if sort.proposed
            else _("Optional: classify proposes"),
            space=Space.SORT.value,
            pill=(Pill.OK if sort.sorted else Pill.TODO)
            if sort.proposed
            else Pill.NONE,
        ),
        HomeTile(
            label=_("Words"),
            value=human_number(words) if words else _DASH,
            sub=_("photos have words") if words else _("tags gives them some"),
            space=Space.FIND.value,
            pill=Pill.OK if words else Pill.NONE,
        ),
        HomeTile(
            label=_("Faces"),
            value=human_number(faces[1]) if faces else _DASH,
            sub=_("faces found") if faces else _("Not looked for yet"),
            space=Space.SORT.value,
            pill=Pill.OK if faces else Pill.NONE,
        ),
        HomeTile(
            label=_("Backup"),
            value=_("Planned"),
            sub="mh backup",
            space=Space.BACKUP.value,
            pill=Pill.PLANNED,
        ),
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
