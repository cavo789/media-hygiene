r"""What a tile of the page freeing a phone shows: the PC's copy of the file (0256).

The library's file, the import's copy, or, for a file set aside on purpose whose run's
quarantine is still there, its copy in the quarantine: the user decides on the photo
itself. Each is read only to make a thumbnail; a quarantine copy is served only when
its path, links resolved, lies in the quarantine of its run. Else a generic tile.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import TYPE_CHECKING, Final

from media_hygiene.actions.purge import run_folders
from media_hygiene.console.formatting import human_size
from media_hygiene.review.phone_views import PhoneTile, set_aside_warning
from media_hygiene.review.views import ORIGINAL_PREFIX, PREVIEW_PREFIX
from media_hygiene.services.phone_plan import AsideState, PhoneCase

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.paths.host_paths import HostPathMapper
    from media_hygiene.services.phone_proof import Ticked

_KEY_LENGTH: Final = 24
_PARENT: Final = ".."
# The fields of a set-aside's reason: the run, its state, and where the file lay.
_RUN: Final = 0
_STATE: Final = 1
_WHERE: Final = 4


@dataclass(frozen=True, slots=True)
class TileSource:
    """Where the PC's files lie: the library's, the import's folder, the quarantines."""

    mapper: HostPathMapper
    destination: Path | None = None  # the import's folder, in the container
    quarantines: tuple[Path, ...] = ()  # the default one and the drives', mounted

    def preview(self, ticked: Ticked) -> Path | None:
        """The PC file a tile shows: the library's, the import's or the quarantine's.

        Args:
            ticked: The phone file and the plan's reason.

        Returns:
            It, in the container; None for a generic tile.
        """
        held = ticked.reason[0] if ticked.reason else ""
        if ticked.case is PhoneCase.LIBRARY and held:
            return self.mapper.to_container(held)
        if ticked.case is PhoneCase.SET_ASIDE:
            return self._quarantined(ticked.reason)
        if ticked.case is not PhoneCase.DESTINATION or self.destination is None:
            return None
        relative = PurePosixPath(held)
        if not held or relative.is_absolute() or _PARENT in relative.parts:
            return None
        return self.destination.joinpath(*relative.parts)

    def _quarantined(self, reason: tuple[str, ...]) -> Path | None:
        """Find the quarantine's copy of a file set aside, while its run still has it.

        Args:
            reason: The plan's reason: the run, its state, …, where the file lay.

        Returns:
            The copy, in the container; None when purged, unknown or outside.
        """
        if len(reason) <= _WHERE or not reason[_WHERE]:
            return None
        if reason[_STATE] != AsideState.QUARANTINE.value:
            return None
        relative = self.mapper.relative(self.mapper.to_container(reason[_WHERE]))
        if relative.is_absolute() or _PARENT in relative.parts:
            return None
        for folder in run_folders(self.quarantines, reason[_RUN]):
            copy = folder / relative
            if _inside(copy, folder):
                return copy
        return None

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
        source = self.preview(ticked)
        key = preview_key(ticked)
        return PhoneTile(
            rank=rank,
            case=ticked.case,
            name=file.path.name,
            folder=file.path.parent.as_posix().removeprefix("."),
            size=file.size,
            size_text=human_size(file.size),
            taken=file.modified,
            held=ticked.reason[0] if ticked.reason else "",
            warning=set_aside_warning(ticked.reason) if aside else "",
            preview="" if source is None else f"{PREVIEW_PREFIX}{key}.jpg",
            original=""
            if source is None
            else f"{ORIGINAL_PREFIX}{key}{source.suffix.lower()}",
        )


def _inside(copy: Path, folder: Path) -> bool:
    """Tell whether a file is there, a real file in the folder once links resolved.

    Args:
        copy: The file.
        folder: The run's folder of a quarantine.

    Returns:
        True when it may be shown.
    """
    try:
        real = copy.resolve(strict=True)
        return real.is_relative_to(folder.resolve(strict=True)) and real.is_file()
    except OSError:
        return False


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
