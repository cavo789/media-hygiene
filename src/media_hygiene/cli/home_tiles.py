"""The "where you are" tiles and what the last audit found, from the tool folders."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from media_hygiene.cli.home_tiles_clean import clean_tiles
from media_hygiene.cli.home_tiles_pages import page_tiles
from media_hygiene.cli.menu_entry import Space
from media_hygiene.cli.status_view import ago
from media_hygiene.console.formatting import human_number
from media_hygiene.i18n import _
from media_hygiene.review.home_parts import HomeTile, Pill

if TYPE_CHECKING:
    from media_hygiene.services.status import Status

_DASH: Final = "—"


def home_tiles(status: Status) -> tuple[HomeTile, ...]:
    """The tiles of the home page, each leading to its space.

    Args:
        status: What the tool folders say.

    Returns:
        Last audit, extra copies, intruder files, quarantine, NAS, sort, words,
        faces, backup, then the tiles of a page.
    """
    return (*clean_tiles(status), *_later_tiles(status), *page_tiles(status))


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
            id="sort",
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
            id="words",
            label=_("Words"),
            value=human_number(words) if words else _DASH,
            sub=_("photos have words") if words else _("tags gives them some"),
            space=Space.FIND.value,
            pill=Pill.OK if words else Pill.NONE,
            step="search" if words else "",  # the Library finds them
        ),
        HomeTile(
            id="faces",
            label=_("Faces"),
            value=human_number(faces[1]) if faces else _DASH,
            sub=_("faces found") if faces else _("Not looked for yet"),
            space=Space.SORT.value,
            pill=Pill.OK if faces else Pill.NONE,
            step="people" if faces else "",  # the page that names them
        ),
        HomeTile(
            id="backup",
            label=_("Backup"),
            value=ago(status.backed_up) if status.backed_up else _DASH,
            sub=_("Last mh push") if status.backed_up else _("mh push copies it"),
            space=Space.BACKUP.value,
            pill=Pill.OK if status.backed_up else Pill.NONE,
        ),
    )
