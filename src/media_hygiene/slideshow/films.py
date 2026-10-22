"""The videos of the show (0292): `GET /film/<key>.<ext>`, played as they are.

Never transcoded: the original is streamed piece by piece (`Range`, as `review
--near` does), a phone's `.mov` served as `video/mp4`: a Chromecast's browser offers
to download a `video/quicktime` file instead of playing it, the same H.264 file served
as `video/mp4` plays (tried by the maintainer, 2026-10-21). Only the show's videos are
served. The TV says when a video ended (`GET /api/ended/<key>`, `screen_api`);
a TV that shows photos only (a 2012 TV's own browser) says so, and once every TV paired
does, the show passes over its videos.
"""

from __future__ import annotations

import asyncio
from http import HTTPStatus
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

from media_hygiene.review.http import ContentType, FilePart, Response
from media_hygiene.review.videos import NEAR_POLICY, asked_part

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from media_hygiene.review.http import Request
    from media_hygiene.slideshow.show import Show
    from media_hygiene.slideshow.slides import Slide

FILM_PREFIX: Final = "/film/"
# Each container the TV plays, and the type that makes it play rather than download.
_PLAYED: Final = MappingProxyType(
    {
        ".mp4": ContentType.MP4,
        ".m4v": ContentType.MP4,
        ".mov": ContentType.MP4,  # QuickTime holds the same streams as MP4
        ".webm": ContentType.WEBM,
    }
)


def film_path(slide: Slide) -> str:
    """The address the TV plays a video from.

    Args:
        slide: The video.

    Returns:
        `/film/<key>.<ext>`; empty for a photo, or a video the TV cannot play.
    """
    film = slide.film
    if film is None or not film.playable:
        return ""
    return f"{FILM_PREFIX}{slide.key}{film.suffix}"


async def film_response(
    request: Request, source_of: Callable[[str], Path | None]
) -> Response:
    """Serve a video of the show, whole or the part the browser asks for.

    Args:
        request: `GET /film/<key>.<ext>`, with or without a `Range` header.
        source_of: Finds the show's file a key names, or None.

    Returns:
        200 or 206, sent in chunks; 416 for a part beyond the end; 404 for a key
        not in the show, a format the TV cannot play or a vanished file.
    """
    key = request.path.removeprefix(FILM_PREFIX).split(".", 1)[0]
    source = source_of(key)
    if source is None:
        return Response(HTTPStatus.NOT_FOUND)
    suffix = source.suffix.lower()
    if suffix not in _PLAYED or request.path != f"{FILM_PREFIX}{key}{suffix}":
        return Response(HTTPStatus.NOT_FOUND)
    try:
        size = (await asyncio.to_thread(source.stat)).st_size
    except OSError:
        return Response(HTTPStatus.NOT_FOUND)
    status, start, length = asked_part(request.headers.get("range", ""), size)
    return Response(
        status,
        content_type=_PLAYED[suffix],
        cacheable=True,
        policy=NEAR_POLICY,
        part=FilePart(source, start, length, size),
    )


def film_ended(show: Show, key: int) -> bool:
    """Move on once the TV says the video it played ended (or could not be played).

    A video ended while the show is paused stays: the phone plays the show on.

    Args:
        show: The show.
        key: The video's key.

    Returns:
        True when the show moved: that video still shown, the show playing.
    """
    current = show.current
    if current is None or current.key != key or current.film is None:
        return False
    if not show.playing:
        return False
    show.move(1)
    return True


def show_films(show: Show, *, films: bool) -> None:
    """Pass over the videos (every TV paired shows photos only), or show them again.

    Args:
        show: The show.
        films: True when a TV paired plays videos.
    """
    show.films = films
    current = show.current
    if current is None or not show.plays(current):
        show.move(1)
    else:
        show.version += 1  # the remotes say why the videos are passed over
