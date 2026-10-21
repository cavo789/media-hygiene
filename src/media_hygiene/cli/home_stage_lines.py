"""What the cycle says of each stage, and the count the sidebar shows next to it."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.cli.menu_entry import Space
from media_hygiene.cli.status_step import to_import
from media_hygiene.cli.status_view import ago
from media_hygiene.console.formatting import human_number, human_size
from media_hygiene.constants import RunKind
from media_hygiene.i18n import _

if TYPE_CHECKING:
    from collections.abc import Callable

    from media_hygiene.services.status import Status


def extra_copies(status: Status) -> int:
    """The extra copies the last audit found, not cleaned since.

    Args:
        status: What the tool folders say.

    Returns:
        Their count; 0 after a clean.
    """
    summary = status.analysis.summary
    if summary is None or summary.kind is not RunKind.AUDIT:
        return 0
    return summary.duplicate_files


def backup_only(status: Status) -> int:
    """The files only a backup holds, still to import.

    Args:
        status: What the tool folders say.

    Returns:
        Their count; 0 when there is nothing to import.
    """
    summary = status.analysis.summary
    return summary.backup_only if summary is not None and to_import(status) else 0


def stage_line(space: Space, status: Status) -> str:
    """What the cycle says of a stage.

    Args:
        space: The stage.
        status: What the tool folders say.

    Returns:
        One short line, translated; empty for a tool.
    """
    lines: dict[Space, Callable[[Status], str]] = {
        Space.IMPORT: _import_line,
        Space.CLEAN: _clean_line,
        Space.SORT: _sort_line,
        Space.FIND: _find_line,
        Space.BACKUP: _backup_line,
    }
    line = lines.get(space)
    return line(status) if line else ""


def stage_badge(space: Space, status: Status, *, newer: bool) -> str:
    """The sidebar's count of a space.

    Args:
        space: The space.
        status: What the tool folders say.
        newer: A newer version is published.

    Returns:
        A short text; empty for none.
    """
    counts = {
        Space.IMPORT: backup_only(status),
        Space.CLEAN: extra_copies(status),
        Space.SORT: int(status.sort.proposed is not None and not status.sort.sorted),
        Space.HISTORY: len(status.undoable),
        Space.SETTINGS: int(newer),
    }
    count = counts.get(space, 0)
    return human_number(count) if count else ""


def _backup_line(status: Status) -> str:
    """The backup stage (0264).

    Args:
        status: What the tool folders say.

    Returns:
        Its line.
    """
    if status.backed_up is None:
        return _("Not backed up yet: mh backup copies to the NAS")
    return _("Last backup: {when}").format(when=ago(status.backed_up))


def _import_line(status: Status) -> str:
    """The import stage.

    Args:
        status: What the tool folders say.

    Returns:
        Its line.
    """
    count = backup_only(status)
    if count:
        return _("{count} files to get back from the NAS").format(
            count=human_number(count)
        )
    return _("Phone, NAS: whenever you want")


def _clean_line(status: Status) -> str:
    """The clean stage.

    Args:
        status: What the tool folders say.

    Returns:
        Its line.
    """
    if not status.analysis.seen:
        return _("Start here: the audit changes nothing")
    count = extra_copies(status)
    if count:
        return _("{count} copies to set aside").format(count=human_number(count))
    if status.quarantine.runs:
        return _("{size} in the quarantine, to check").format(
            size=human_size(status.quarantine.size)
        )
    return _("All clean")


def _sort_line(status: Status) -> str:
    """The sort stage.

    Args:
        status: What the tool folders say.

    Returns:
        Its line.
    """
    if status.sort.sorted:
        return _("Sorted")
    if status.sort.proposed is not None:
        return _("A proposal to apply")
    return _("Optional, whenever you want")


def _find_line(status: Status) -> str:
    """The find stage.

    Args:
        status: What the tool folders say.

    Returns:
        Its line.
    """
    if status.tagged and status.tagged[0]:
        return _("{count} photos have words").format(
            count=human_number(status.tagged[0])
        )
    return _("Optional: give them words")
