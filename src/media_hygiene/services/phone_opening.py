"""The session of the page freeing a phone, opened the same way wherever it is served.

`phone-review` (its own server, `phone_review`) and the home server (`phone_here`,
0694) both open it here: the decisions file saved at once, then read back, before
the page shows a tile.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from media_hygiene.errors import MountError
from media_hygiene.i18n import _
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.review.phone_file import PHONE_DECISIONS
from media_hygiene.review.phone_session import PhonePages, PhoneSession
from media_hygiene.review.phone_tiles import TileSource
from media_hygiene.review.place import decisions_place
from media_hygiene.services.quarantines import mounted_quarantines
from media_hygiene.services.writable import ensure_writable

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.services.phone_proof import Ticked
    from media_hygiene.services.runtime import Runtime


@dataclass(frozen=True, slots=True)
class PhoneOpened:
    """The session and the previews' copies, by the rank of their file."""

    session: PhoneSession
    copies: dict[str, Path]


def open_phone_session(
    runtime: Runtime, phone: str, files: tuple[tuple[Ticked, ...], Path | None]
) -> PhoneOpened:
    """Open the session: saved once, read back from the disk.

    Args:
        runtime: Settings, mount points and output.
        phone: The phone's name.
        files: The files the PC may hold, and the import's folder in the container.

    Returns:
        The session, proven readable, and the copies the tiles show.

    Raises:
        MountError: The reports folder is not mounted: the choices would be lost.
    """
    if not runtime.persistent(MountKind.REPORTS):
        raise MountError(
            _("The decisions are saved in /reports: mount it, or they are lost.")
        )
    ensure_writable(runtime, MountKind.REPORTS)
    ticked, destination = files
    target = runtime.locations.reports_dir / PHONE_DECISIONS
    place = decisions_place(runtime.mapper, runtime.locations.reports_dir, target)
    quarantines = mounted_quarantines(runtime).folders
    tiles = TileSource(runtime.mapper, destination, quarantines)
    session = PhoneSession(PhonePages(phone, ticked, tiles, (target, place)))
    session.save()
    session.on_disk()  # proven readable before the page opens
    copies = {
        str(rank): copy
        for rank, each in enumerate(ticked)
        if (copy := tiles.preview(each)) is not None
    }
    return PhoneOpened(session, copies)
