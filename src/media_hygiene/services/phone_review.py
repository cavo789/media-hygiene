r"""`phone-review`: the page where the user ticks what leaves the phone (0248).

`mh` pipes the plan's lines (`phone-plan`'s, a file imported by this run as
`destination`); the files the PC may hold are shown in three groups, the decisions
file is saved in `/reports` at once and after every choice. The page ends on "Delete
from the phone" (the files ticked, read back from the disk, are then printed for `mh`)
or on "Leave everything" and Ctrl+C (nothing printed: nothing deleted).
"""

from __future__ import annotations

import asyncio
import contextlib
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.errors import MountError
from media_hygiene.i18n import _
from media_hygiene.i18n.templates import translated_environment
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.review.ending import STOP_PATH, EndingDoor, serve_until_ended
from media_hygiene.review.files import FILE_PATH
from media_hygiene.review.local_app import STATE_PATH
from media_hygiene.review.phone_app import FREE_PATH, PHONE_DECIDE_PATH, PhoneApp
from media_hygiene.review.phone_file import PHONE_DECISIONS
from media_hygiene.review.phone_session import PhonePages, PhoneSession
from media_hygiene.review.phone_tiles import TileSource
from media_hygiene.review.place import decisions_place
from media_hygiene.services.quarantines import mounted_quarantines
from media_hygiene.services.reviewing import address_tip, page_url
from media_hygiene.services.writable import ensure_writable

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.review.place import DecisionsPlace
    from media_hygiene.services.phone_proof import Ticked
    from media_hygiene.services.runtime import Runtime

_TEMPLATES: Final = "media_hygiene.review"
_TEMPLATE: Final = "phone_review.html.j2"


@dataclass(frozen=True, slots=True)
class PhoneReview:
    """The phone, the files the PC may hold, the import's folder, the page's port."""

    phone: str
    files: tuple[Ticked, ...]
    destination: Path | None = None  # in the container
    port: int = 0


def serve_phone_review(runtime: Runtime, review: PhoneReview) -> tuple[str, ...]:
    """Serve the page until it ends; every choice is saved as it is made.

    Args:
        runtime: Settings, mount points and output.
        review: The phone and its files.

    Returns:
        The plan lines of the files ticked, read back from the disk, when the user
        pressed "Delete from the phone"; none otherwise.

    Raises:
        MountError: The reports folder is not mounted: the choices would be lost.
    """
    if not runtime.persistent(MountKind.REPORTS):
        raise MountError(
            _("The decisions are saved in /reports: mount it, or they are lost.")
        )
    ensure_writable(runtime, MountKind.REPORTS)
    target = runtime.locations.reports_dir / PHONE_DECISIONS
    place = decisions_place(runtime.mapper, runtime.locations.reports_dir, target)
    quarantines = mounted_quarantines(runtime).folders
    tiles = TileSource(runtime.mapper, review.destination, quarantines)
    session = PhoneSession(
        PhonePages(review.phone, review.files, tiles, (target, place))
    )
    session.save()
    session.on_disk()  # proven readable before the page opens

    def ready(port: int) -> None:
        """Tell where the page is.

        Args:
            port: The port listened on, inside the container.
        """
        runtime.output.success(
            _(
                "Page ready, open {url} in your browser. Each choice is saved at "
                "once in {place}. Nothing leaves the phone before you press Delete."
            ).format(url=page_url(port), place=place.host)
        )
        address_tip(runtime.output, port)

    with runtime.executor_factory() as executor, contextlib.suppress(KeyboardInterrupt):
        app = PhoneApp(session, _page(place), executor, runtime.previews_dir)
        door = EndingDoor(app, app.ending)
        asyncio.run(serve_until_ended(door, review.port, ready))
    return session.ticked_lines() if session.freeing else ()


def _page(place: DecisionsPlace) -> bytes:
    """Render the page.

    Args:
        place: The decisions file it writes.

    Returns:
        The page.
    """
    environment = translated_environment(_TEMPLATES, escaped=("html", "j2"))
    return (
        environment.get_template(_TEMPLATE)
        .render(
            state_path=STATE_PATH,
            decide_path=PHONE_DECIDE_PATH,
            file_path=FILE_PATH,
            free_path=FREE_PATH,
            stop_path=STOP_PATH,
            place=place.host,
        )
        .encode()
    )
