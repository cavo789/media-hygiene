"""The parts of `phone_here` (0694): the end written for `mh`, Leave, the page's app."""

from __future__ import annotations

import asyncio
import dataclasses
import json
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from media_hygiene.cli.home_pending import home_pending
from media_hygiene.i18n import _
from media_hygiene.review.apply_api import ApplyDesk, ApplyingApp, ApplyOffer
from media_hygiene.review.apply_relay import home_relay
from media_hygiene.review.home_fields import write_whole
from media_hygiene.review.http import Response, is_local
from media_hygiene.review.phone_app import PhoneApp
from media_hygiene.review.serving import json_response, refused_post
from media_hygiene.review.step_files import WATCH
from media_hygiene.services.keyed_albums import keyed_albums
from media_hygiene.services.page_undo import PageUndo
from media_hygiene.services.phone_review import PhoneServed, phone_page

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.review.http import Request
    from media_hygiene.services.home_pages import HomeServer
    from media_hygiene.services.phone_opening import PhoneOpened
    from media_hygiene.services.runtime import Runtime

ENCODING: Final = "utf-8-sig"  # Windows PowerShell 5.1 may write a byte order mark
_POST: Final = "POST"


def not_told() -> str:
    """The sentence of a page that could not tell `mh` what to delete.

    Returns:
        It, translated.
    """
    return _("The page could not tell mh what to delete: try again.")


def write_ended(folder: Path, lines: tuple[str, ...]) -> bool:
    """Write what the page ended on, then read it back.

    Args:
        folder: The reports folder.
        lines: The plan lines of the files to delete; none: nothing leaves.

    Returns:
        True once the file read back holds exactly these lines.
    """
    target = folder / WATCH.phone_ended
    write_whole(target, json.dumps({"lines": list(lines)}, ensure_ascii=False) + "\n")
    try:
        read = json.loads(target.read_text(ENCODING))
    except OSError, ValueError:
        return False
    return isinstance(read, dict) and read.get("lines") == list(lines)


async def leave(request: Request, folder: Path) -> Response:
    """Leave everything on the phone: nothing leaves it, the home server stays up.

    Args:
        request: `POST /api/stop`, under the prefix.
        folder: The reports folder.

    Returns:
        An empty answer once `mh` can read that nothing is deleted.
    """
    if not is_local(request):
        return Response(HTTPStatus.FORBIDDEN)
    if request.method != _POST:
        return Response(HTTPStatus.METHOD_NOT_ALLOWED)
    refused = refused_post(request)
    if refused is not None:
        return refused
    if not await asyncio.to_thread(write_ended, folder, ()):
        return json_response(HTTPStatus.CONFLICT, {"error": not_told()})
    return json_response(HTTPStatus.OK, {})


def phone_here_app(
    runtime: Runtime, opened: PhoneOpened, server: HomeServer
) -> ApplyingApp:
    """The page's app: its albums on the home server's TV, *Apply now*.

    Args:
        runtime: Settings, mount points and output.
        opened: The session.
        server: The home server's *Apply now*, end, pool and TV.

    Returns:
        The app.
    """
    reports = runtime.locations.reports_dir
    served = PhoneServed(server.apply is not None, home_pending(reports) is not None)
    app = PhoneApp(
        opened.session,
        phone_page(opened.session.place, served),
        server.executor,
        runtime.previews_dir,
    )
    albums = keyed_albums(runtime, opened.copies.get, server.tv)
    app = dataclasses.replace(app, albums=albums)
    offer = ApplyOffer(
        server.apply, lambda: home_pending(reports) is not None, PageUndo(runtime)
    )
    return ApplyingApp(app, ApplyDesk(offer, server.ending, home_relay(reports)))
