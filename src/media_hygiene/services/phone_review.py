r"""`phone-review`: the page where the user ticks what leaves the phone (0248).

`mh` pipes the plan's lines (`phone-plan`'s, a file imported by this run as
`destination`); the files the PC may hold are shown in three groups, the decisions
file is saved in `/reports` at once and after every choice. The page ends on "Delete
from the phone" (the files ticked, read back from the disk, are then printed for `mh`)
or on "Leave everything", "Back to the home page" and Ctrl+C (nothing printed:
nothing deleted, 0332). Started from the home page, the home server serves the same
page instead (`phone_here`, 0694); its paths are relative to it for that.
"""

from __future__ import annotations

import asyncio
import contextlib
from dataclasses import dataclass, replace
from functools import partial
from typing import TYPE_CHECKING, Final

from media_hygiene.constants import ExitCode
from media_hygiene.i18n import _
from media_hygiene.i18n.live import PerLocale
from media_hygiene.i18n.templates import translated_environment
from media_hygiene.person.door import with_person
from media_hygiene.review.apply_api import APPLY_PATH
from media_hygiene.review.ending import (
    STOP_PATH,
    STOPPED,
    EndingDoor,
    serve_until_ended,
)
from media_hygiene.review.files import FILE_PATH
from media_hygiene.review.home_views import UNDO_PATH
from media_hygiene.review.local_app import STATE_PATH
from media_hygiene.review.page_header import page_header
from media_hygiene.review.phone_app import FREE_PATH, PHONE_DECIDE_PATH, PhoneApp
from media_hygiene.review.presence import Presence
from media_hygiene.services.keyed_albums import keyed_albums
from media_hygiene.services.launcher_phone_free import PHONE_MB_PER_SECOND
from media_hygiene.services.phone_opening import open_phone_session
from media_hygiene.services.reviewing import address_tip, page_url
from media_hygiene.share.album_api import ALBUMS_PATH
from media_hygiene.share.album_page import TV_PAIRED_PATH

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


@dataclass(frozen=True, slots=True)
class PhoneServed:
    """The page in the home server (0694): its slideshow, its *Apply now*."""

    apply_offered: bool = False
    apply_pending: bool = False  # something waits in the decisions file


def serve_phone_review(runtime: Runtime, review: PhoneReview) -> tuple[str, ...]:
    """Serve the page until it ends; every choice is saved as it is made.

    Args:
        runtime: Settings, mount points and output.
        review: The phone and its files.

    Returns:
        The plan lines of the files ticked, read back from the disk, when the user
        pressed "Delete from the phone"; none otherwise.

    Raises:
        PageClosed: Opened from the home page, its tab was closed (0332): the loop of
            `mh` ends, as after any page; from the console, nothing is printed.
    """
    opened = open_phone_session(
        runtime, review.phone, (review.files, review.destination)
    )
    session = opened.session
    place = session.place

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
        app = PhoneApp(session, phone_page(place), executor, runtime.previews_dir)
        app = replace(app, albums=keyed_albums(runtime, opened.copies.get))  # (0657)
        door = EndingDoor(app, app.ending, Presence(app.ending, closed))
        door = with_person(door, runtime, executor)
        asyncio.run(serve_until_ended(door, review.port, ready))
    return session.ticked_lines() if session.freeing else ()


def phone_page(
    place: DecisionsPlace, served: PhoneServed | None = None
) -> PerLocale[bytes]:
    """The page, drawn in the language in use.

    Args:
        place: The decisions file it writes.
        served: Served by the home server (0694); None: by its own server.

    Returns:
        How to draw it.
    """
    return PerLocale(partial(_page, place, served))


def _relative(path: str) -> str:
    """A path of the page, relative to it: the same at `/` or under `/phone/`.

    Args:
        path: The route, from `/`.

    Returns:
        It without its first slash.
    """
    return path.removeprefix("/")


def _page(place: DecisionsPlace, served: PhoneServed | None) -> bytes:
    """Render the page.

    Args:
        place: The decisions file it writes.
        served: Served by the home server; None: by its own server.

    Returns:
        The page.
    """
    environment = translated_environment(_TEMPLATES, escaped=("html", "j2"))
    here = served or PhoneServed()
    return (
        environment.get_template(_TEMPLATE)
        .render(
            header=page_header(_TEMPLATE),
            state_path=_relative(STATE_PATH),
            decide_path=_relative(PHONE_DECIDE_PATH),
            file_path=_relative(FILE_PATH),
            free_path=_relative(FREE_PATH),
            stop_path=_relative(STOP_PATH),
            place=place.host,
            phone_speed=PHONE_MB_PER_SECOND,
            albums_path=_relative(ALBUMS_PATH),  # Add to an album (0657)
            served=served is not None,  # the tab goes home after Delete or Leave
            tv_here=served is not None,  # ▶ Slideshow ▾ (0694)
            tv_paired_path=TV_PAIRED_PATH,
            apply_offered=here.apply_offered,
            apply_path=_relative(APPLY_PATH),
            apply_pending=here.apply_pending,
            undo_path=_relative(UNDO_PATH),  # the toast after Apply now (0757)
        )
        .encode()
    )
