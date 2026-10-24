r"""`phone-review`: the page where the user ticks what leaves the phone (0248).

`mh` pipes the plan's lines (`phone-plan`'s, a file imported by this run as
`destination`); the files the PC may hold are shown in three groups, the decisions
file is saved in `/reports` at once and after every choice. The page ends on "Delete
from the phone" (the files ticked, read back from the disk, are then printed for `mh`)
or on "Leave everything", "Back to the home page" and Ctrl+C (nothing printed:
nothing deleted, 0332).
"""

from __future__ import annotations

import asyncio
import contextlib
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.constants import ExitCode
from media_hygiene.errors import MountError
from media_hygiene.i18n import _
from media_hygiene.i18n.templates import translated_environment
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.person.door import with_person
from media_hygiene.review.ending import (
    STOP_PATH,
    STOPPED,
    EndingDoor,
    serve_until_ended,
)
from media_hygiene.review.files import FILE_PATH
from media_hygiene.review.local_app import STATE_PATH
from media_hygiene.review.page_header import page_header
from media_hygiene.review.phone_app import FREE_PATH, PHONE_DECIDE_PATH, PhoneApp
from media_hygiene.review.phone_file import PHONE_DECISIONS
from media_hygiene.review.phone_session import PhonePages, PhoneSession
from media_hygiene.review.phone_tiles import TileSource
from media_hygiene.review.place import decisions_place
from media_hygiene.review.presence import Presence
from media_hygiene.services.launcher_phone_free import PHONE_MB_PER_SECOND
from media_hygiene.services.quarantines import mounted_quarantines
from media_hygiene.services.reviewing import address_tip, page_url
from media_hygiene.services.writable import ensure_writable

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.review.page_header import PageHeader
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
        PageClosed: Opened from the home page, its tab was closed (0332): the loop of
            `mh` ends, as after any page; from the console, nothing is printed.
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

    header = page_header(_TEMPLATE)
    # Its tab closed: as Stop, nothing deleted; mh reads the page's lines (0262). From
    # the home page, the loop of mh ends instead, as after any page's tab (0332).
    closed = ExitCode.PAGE_CLOSED if header.home else STOPPED
    with runtime.executor_factory() as executor, contextlib.suppress(KeyboardInterrupt):
        app = PhoneApp(session, _page(place, header), executor, runtime.previews_dir)
        door = EndingDoor(app, app.ending, Presence(app.ending, closed))
        door = with_person(door, runtime, executor)
        asyncio.run(serve_until_ended(door, review.port, ready))
    return session.ticked_lines() if session.freeing else ()


def _page(place: DecisionsPlace, header: PageHeader) -> bytes:
    """Render the page.

    Args:
        place: The decisions file it writes.
        header: Its bar.

    Returns:
        The page.
    """
    environment = translated_environment(_TEMPLATES, escaped=("html", "j2"))
    return (
        environment.get_template(_TEMPLATE)
        .render(
            header=header,
            state_path=STATE_PATH,
            decide_path=PHONE_DECIDE_PATH,
            file_path=FILE_PATH,
            free_path=FREE_PATH,
            stop_path=STOP_PATH,
            place=place.host,
            phone_speed=PHONE_MB_PER_SECOND,
        )
        .encode()
    )
