r"""What the page freeing a phone receives: three groups of tiles, ticked or not (0248).

Already in the library and imported by `mh phone`: ticked for the user. Set aside
before on purpose: never ticked for the user, its warning on each tile, dated once
its quarantine is purged (0256). What a tile shows: `phone_tiles`.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Final

from pydantic import BaseModel, ConfigDict

from media_hygiene.i18n import _
from media_hygiene.services.phone_plan import AsideState, PhoneCase
from media_hygiene.services.phone_proof import AsideWhen, aside_warning

if TYPE_CHECKING:
    from media_hygiene.services.phone_proof import Ticked

_FROZEN = ConfigDict(frozen=True, extra="forbid")
_ASIDE_FIELDS: Final = 3  # run, state, date (then the kind, where, the purge date)
_PURGED: Final = 5  # the purge date's field in the reason
# The groups, in the page's order.
GROUPS: Final = (PhoneCase.LIBRARY, PhoneCase.DESTINATION, PhoneCase.SET_ASIDE)


class PhoneTile(BaseModel):
    """One file of the phone as the page shows it."""

    model_config = _FROZEN

    rank: int
    name: str
    folder: str  # below DCIM
    size: int
    size_text: str
    taken: str  # the phone's date, ISO 8601
    held: str  # the PC's file, the import's copy, or the run that set it aside
    warning: str = ""  # a file set aside before: recoverable, or lost for good
    preview: str = ""  # empty: a generic tile
    ticked: bool = False


class PhoneGroup(BaseModel):
    """One group of the page: its case, title, explanation and files."""

    model_config = _FROZEN

    case: PhoneCase
    title: str
    help: str
    files: tuple[int, ...]


class PhoneReviewState(BaseModel):
    """Everything the page needs: `GET /api/state`."""

    model_config = _FROZEN

    phone: str
    decisions_place: str
    tiles: tuple[PhoneTile, ...]
    groups: tuple[PhoneGroup, ...]


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


def phone_groups(files: tuple[Ticked, ...]) -> tuple[PhoneGroup, ...]:
    """Put the files in their groups, the empty groups left out.

    Args:
        files: The files of the page, in rank order.

    Returns:
        The groups, in the page's order.
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
    groups = []
    for case in GROUPS:
        ranks = tuple(r for r, ticked in enumerate(files) if ticked.case is case)
        if ranks:
            title, help_text = texts[case]
            groups.append(
                PhoneGroup(case=case, title=title, help=help_text, files=ranks)
            )
    return tuple(groups)
