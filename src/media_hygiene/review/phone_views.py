r"""What the page freeing a phone receives: three groups of tiles, ticked or not (0248).

Already in the library and imported by `mh phone`: ticked for the user. Set aside
before on purpose: never ticked for the user, its warning on each tile. A tile shows
the PC's file (the library's, the import's copy), else a generic tile.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime
from pathlib import PurePosixPath
from typing import TYPE_CHECKING, Final

from pydantic import BaseModel, ConfigDict

from media_hygiene.console.formatting import human_size
from media_hygiene.i18n import _
from media_hygiene.review.views import PREVIEW_PREFIX
from media_hygiene.services.phone_plan import AsideState, PhoneCase
from media_hygiene.services.phone_proof import aside_warning

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.paths.host_paths import HostPathMapper
    from media_hygiene.services.phone_proof import Ticked

_FROZEN = ConfigDict(frozen=True, extra="forbid")
_KEY_LENGTH: Final = 24
_PARENT: Final = ".."
_ASIDE_FIELDS: Final = 3  # run, state, date (then the kind)
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


@dataclass(frozen=True, slots=True)
class TileSource:
    """Where the PC's files lie: the library's by host path, the import's folder."""

    mapper: HostPathMapper
    destination: Path | None = None  # the import's folder, in the container

    def preview(self, ticked: Ticked) -> Path | None:
        """The PC file a tile shows: the library's, or the import's copy.

        Args:
            ticked: The phone file and the plan's reason.

        Returns:
            It, in the container; None for a generic tile.
        """
        held = ticked.reason[0] if ticked.reason else ""
        if ticked.case is PhoneCase.LIBRARY and held:
            return self.mapper.to_container(held)
        relative = PurePosixPath(held)
        if ticked.case is not PhoneCase.DESTINATION or self.destination is None:
            return None
        if not held or relative.is_absolute() or _PARENT in relative.parts:
            return None
        return self.destination.joinpath(*relative.parts)

    def tile(self, rank: int, ticked: Ticked) -> PhoneTile:
        """Describe one file, unticked.

        Args:
            rank: Its rank in the page.
            ticked: The phone file and the plan's reason.

        Returns:
            Its tile.
        """
        file = ticked.file
        aside = ticked.case is PhoneCase.SET_ASIDE
        return PhoneTile(
            rank=rank,
            name=file.path.name,
            folder=file.path.parent.as_posix().removeprefix("."),
            size=file.size,
            size_text=human_size(file.size),
            taken=file.modified,
            held=ticked.reason[0] if ticked.reason else "",
            warning=set_aside_warning(ticked.reason) if aside else "",
            preview=f"{PREVIEW_PREFIX}{preview_key(ticked)}.jpg"
            if self.preview(ticked) is not None
            else "",
        )


def preview_key(ticked: Ticked) -> str:
    """Name a tile's preview: stable for one file of the phone.

    Args:
        ticked: The phone file.

    Returns:
        A key, safe in a URL.
    """
    file = ticked.file
    identity = f"{ticked.case.value}\0{file.path.as_posix()}\0{file.size}"
    return hashlib.sha256(identity.encode()).hexdigest()[:_KEY_LENGTH]


def set_aside_warning(reason: tuple[str, ...]) -> str:
    """The warning of a file set aside before, from the plan's reason.

    Args:
        reason: The run, the quarantine state, the date, the kind.

    Returns:
        The translated warning; lost for good when the plan says too little.
    """
    if len(reason) < _ASIDE_FIELDS:
        return aside_warning("", datetime.now().astimezone(), quarantined=False)
    run_id, state, at = reason[:_ASIDE_FIELDS]
    try:
        when = datetime.fromisoformat(at)
    except ValueError:
        when = datetime.now().astimezone()
    quarantined = state == AsideState.QUARANTINE.value
    return aside_warning(run_id, when, quarantined=quarantined)


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
