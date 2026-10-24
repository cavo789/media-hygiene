r"""What the page freeing a phone receives: its tiles, ticked or not, by phone folder.

One group per folder of the phone (0312), in the order of their names: the user sorted
the phone into folders and thinks in them. Why the PC holds a file is a badge on its
tile, explained once in a legend (0248): already in the library and imported by `mh
phone`, ticked for the user; set aside before on purpose, never ticked for the user,
its warning on each tile, dated once its quarantine is purged (0256). What a tile
shows: `phone_tiles`.
"""

from __future__ import annotations

from datetime import datetime
from typing import Final

from pydantic import BaseModel, ConfigDict

from media_hygiene.i18n import _
from media_hygiene.services.phone_plan import AsideState, PhoneCase
from media_hygiene.services.phone_proof import AsideWhen, aside_warning

_FROZEN = ConfigDict(frozen=True, extra="forbid")
_ASIDE_FIELDS: Final = 3  # run, state, date (then the kind, where, the purge date)
_PURGED: Final = 5  # the purge date's field in the reason
# Why the PC holds a file, in the legend's order.
REASONS: Final = (PhoneCase.LIBRARY, PhoneCase.DESTINATION, PhoneCase.SET_ASIDE)


class PhoneTile(BaseModel):
    """One file of the phone as the page shows it."""

    model_config = _FROZEN

    rank: int
    case: PhoneCase  # why the PC holds it: its badge
    name: str
    folder: str  # below DCIM
    size: int
    size_text: str
    taken: str  # the phone's date, ISO 8601
    held: str  # the PC's file, the import's copy, or the run that set it aside
    warning: str = ""  # a file set aside before: recoverable, or lost for good
    preview: str = ""  # empty: a generic tile
    original: str = ""  # the PC's file untouched, for the large view
    ticked: bool = False


class PhoneReason(BaseModel):
    """One line of the legend: why the PC holds a file, its badge and explanation."""

    model_config = _FROZEN

    case: PhoneCase
    badge: str
    help: str


class PhoneGroup(BaseModel):
    """One folder of the phone: its files, and how many of them were set aside."""

    model_config = _FROZEN

    folder: str  # below DCIM; empty: DCIM itself
    files: tuple[int, ...]
    aside: int  # never ticked by the folder's box


class PhoneReviewState(BaseModel):
    """Everything the page needs: `GET /api/state`."""

    model_config = _FROZEN

    phone: str
    decisions_place: str
    tiles: tuple[PhoneTile, ...]
    groups: tuple[PhoneGroup, ...]
    reasons: tuple[PhoneReason, ...]


def set_aside_warning(reason: tuple[str, ...]) -> str:
    """The warning of a file set aside before, from the plan's reason.

    Args:
        reason: The run, the quarantine state, the date, the kind, where it lay,
            when it was purged (empty: not recorded, 0256).

    Returns:
        The translated warning; lost for good when the plan says too little.
    """
    now = datetime.now().astimezone()
    if len(reason) < _ASIDE_FIELDS:
        return aside_warning(AsideWhen("", now, quarantined=False))
    run_id, state, at = reason[:_ASIDE_FIELDS]
    quarantined = state == AsideState.QUARANTINE.value
    purged = _moment(reason[_PURGED]) if len(reason) > _PURGED else None
    when = AsideWhen(run_id, _moment(at) or now, quarantined, purged)
    return aside_warning(when)


def _moment(text: str) -> datetime | None:
    """Read a moment of the plan's reason.

    Args:
        text: An ISO 8601 moment, or empty.

    Returns:
        It; None when empty or unreadable.
    """
    try:
        return datetime.fromisoformat(text) if text else None
    except ValueError:
        return None


def phone_groups(tiles: tuple[PhoneTile, ...]) -> tuple[PhoneGroup, ...]:
    """Put the files in the phone's folders, in the order of their names.

    Args:
        tiles: The files of the page, in rank order.

    Returns:
        One group per folder holding files.
    """
    folders: dict[str, list[PhoneTile]] = {}
    for tile in tiles:
        folders.setdefault(tile.folder, []).append(tile)
    return tuple(
        PhoneGroup(
            folder=folder,
            files=tuple(tile.rank for tile in shown),
            aside=sum(tile.case is PhoneCase.SET_ASIDE for tile in shown),
        )
        for folder, shown in sorted(
            folders.items(), key=lambda item: item[0].casefold()
        )
    )


def phone_reasons(tiles: tuple[PhoneTile, ...]) -> tuple[PhoneReason, ...]:
    """The legend: why the PC holds the files, for the reasons the page shows.

    Args:
        tiles: The files of the page.

    Returns:
        One line per reason shown, in the legend's order.
    """
    texts = {
        PhoneCase.LIBRARY: (
            "📚 " + _("Already in your library"),
            _("A file of your library has the same name and size."),
        ),
        PhoneCase.DESTINATION: (
            "📥 " + _("Copied by mh phone"),
            _("The copy of the import has the same name and size."),
        ),
        PhoneCase.SET_ASIDE: (
            "⚠️ " + _("Set aside before, on purpose"),
            _(
                "Not in your library: you set them aside (a burst shot, a near copy, "
                "an unwanted photo). Never ticked for you: read the warning first."
            ),
        ),
    }
    shown = {tile.case for tile in tiles}
    return tuple(
        PhoneReason(case=case, badge=texts[case][0], help=texts[case][1])
        for case in REASONS
        if case in shown
    )


def phone_state(
    phone: str, place: str, tiles: tuple[PhoneTile, ...]
) -> PhoneReviewState:
    """Everything the page needs: the tiles, the phone's folders, the legend.

    Args:
        phone: The phone's name.
        place: The decisions file, on the host.
        tiles: The files of the page, ticked or not, in rank order.

    Returns:
        The state.
    """
    return PhoneReviewState(
        phone=phone,
        decisions_place=place,
        tiles=tiles,
        groups=phone_groups(tiles),
        reasons=phone_reasons(tiles),
    )
