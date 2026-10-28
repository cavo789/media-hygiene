"""`slideshow`: the photos of a folder, a search or an album, on the TV.

The index is read, never written; the photos are never changed. One server until
Ctrl+C (or *Back to the home page*): the remote at `/` on the PC (its browser opens
there) and on the phones paired by `mh --lan`'s code, the screen at `/screen` on the
TV. No presence: the PC's tab may close while the family watches.
"""

from __future__ import annotations

import asyncio
import contextlib
from dataclasses import dataclass
from functools import partial
from typing import TYPE_CHECKING

from media_hygiene.errors import MediaHygieneError
from media_hygiene.i18n import _, ngettext
from media_hygiene.review.ending import Ending, EndingDoor, serve_until_ended
from media_hygiene.review.lan import lan_access
from media_hygiene.review.lan_phones import phone_book
from media_hygiene.services.search import open_search
from media_hygiene.services.slideshow_build import Serving, show_app
from media_hygiene.services.slideshow_pick import Pick, Picked, picked_slides
from media_hygiene.services.slideshow_say import announce_slideshow
from media_hygiene.slideshow.desk import Changes, Desk
from media_hygiene.slideshow.door import Door
from media_hygiene.slideshow.screens import Screens
from media_hygiene.slideshow.show import Show
from media_hygiene.slideshow.slides import Timing
from media_hygiene.slideshow.tv_door import TvDoor

if TYPE_CHECKING:
    from media_hygiene.search.fts import SearchIndex
    from media_hygiene.services.runtime import Runtime


@dataclass(frozen=True, slots=True)
class ShowStart:
    """What to show, and the port of the pages (fixed: the TV keeps a bookmark)."""

    pick: Pick
    port: int


def serve_slideshow(runtime: Runtime, start: ShowStart) -> int:
    """Serve the slideshow until Ctrl+C or *Back to the home page*.

    Args:
        runtime: Settings, mount points and output.
        start: What to show, and the port.

    Returns:
        How many photos the show held.

    Raises:
        MediaHygieneError: Nothing to show.
    """
    with open_search(runtime, words=False) as search:
        picked = shown_slides(runtime, search, start.pick)
        settings = runtime.settings.slideshow
        show = Show(picked.slides, Timing(settings.interval_seconds))
        with runtime.executor_factory() as executor:
            lan = lan_access(start.port) if start.port else None  # `mh --lan`
            secure = lan is not None and lan.secure  # phones paired for good (0431)
            door = Door(lan, Screens(), phones=phone_book(secure=secure))
            desk = Desk(show, door.screens, Changes())
            app = show_app(runtime, desk, Serving(search, executor, door))
            ready = partial(announce_slideshow, runtime, app.door)
            with contextlib.suppress(KeyboardInterrupt):
                ending = Ending()
                asyncio.run(
                    serve_until_ended(
                        EndingDoor(app, ending, plain=TvDoor(app).handle),
                        start.port,
                        ready,
                    )
                )
    return len(picked.slides)


def shown_slides(runtime: Runtime, search: SearchIndex, pick: Pick) -> Picked:
    """The photos of the show; what was cut or is missing said in the console.

    Args:
        runtime: Settings, mount points and output.
        search: The open index.
        pick: The folder, the words, or the album.

    Returns:
        The photos.

    Raises:
        MediaHygieneError: Nothing to show.
    """
    picked = picked_slides(runtime, search, pick)
    if not picked.slides:
        raise MediaHygieneError(
            _("No photo or video to show: nothing the last audit saw matches."),
            _(
                "Check the folder as the Explorer shows it, under one of your "
                "photo folders; a search needs 'tags' first."
            ),
        )
    if picked.found > len(picked.slides):
        runtime.output.warning(
            _(
                "{found} photos and videos found: the first {shown} by date are shown."
            ).format(found=picked.found, shown=len(picked.slides))
        )
    if picked.missing:
        runtime.output.warning(
            ngettext(
                "{n} file of the album is missing (moved out of the folders "
                "analysed, or deleted): not shown.",
                "{n} files of the album are missing (moved out of the folders "
                "analysed, or deleted): not shown.",
                picked.missing,
            ).format(n=picked.missing)
        )
    return picked
