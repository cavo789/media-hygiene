"""Serve the page of `shrink --try` until it closes, or asks to lighten (0307).

The same server as the other pages: loopback `Host`, JSON-only `POST`, `/api/stop` and
the presence that ends the page once no tab shows it. Ctrl+C ends it as closing it.
"""

from __future__ import annotations

import asyncio
import contextlib
from functools import partial
from typing import TYPE_CHECKING, Final

from media_hygiene.constants import ExitCode
from media_hygiene.i18n import _
from media_hygiene.i18n.templates import translated_environment
from media_hygiene.review.ending import Ending, EndingDoor, serve_until_ended
from media_hygiene.review.local_app import STATE_PATH
from media_hygiene.review.page_header import headed_page
from media_hygiene.review.presence import Presence
from media_hygiene.review.shrink_app import (
    CHOOSE_PATH,
    LIGHTEN_PATH,
    ShrinkDesk,
    ShrinkTryApp,
)
from media_hygiene.services.reviewing import address_tip, page_url

if TYPE_CHECKING:
    from media_hygiene.services.runtime import Runtime
    from media_hygiene.services.shrink_try import Trial

PAGE_TEMPLATE: Final = "shrink.html.j2"
_TEMPLATES: Final = "media_hygiene.review"


def try_page() -> bytes:
    """Render the page of the try.

    Returns:
        The page, in the language in use.
    """
    environment = translated_environment(_TEMPLATES, escaped=("html", "j2"))
    paths = {
        "state_path": STATE_PATH,
        "choose_path": CHOOSE_PATH,
        "lighten_path": LIGHTEN_PATH,
    }
    return headed_page(environment, PAGE_TEMPLATE, paths)


def serve_try(runtime: Runtime, trial: Trial) -> int:
    """Serve the page until it closes, Ctrl+C, or it asks to lighten.

    Args:
        runtime: Settings, mount points and output.
        trial: The try, its drafts encoding.

    Returns:
        `LIGHTEN_CODE` when the page asked to lighten the videos chosen; 0 otherwise.

    Raises:
        PageClosed: The page's tab was closed and none came back.
    """
    ending = Ending()
    app = ShrinkTryApp(try_page(), ShrinkDesk(trial, runtime.mapper, ending))
    door = EndingDoor(app, ending, Presence(ending, ExitCode.PAGE_CLOSED))
    code = 0
    with contextlib.suppress(KeyboardInterrupt):
        port = runtime.settings.review.port
        code = asyncio.run(serve_until_ended(door, port, partial(_ready, runtime)))
    return code


def _ready(runtime: Runtime, port: int) -> None:
    """Say where the page is and how to open it from the host.

    Args:
        runtime: Settings, mount points and output.
        port: The port listened on, inside the container.
    """
    said = _(
        "Try ready, open {url} in your browser: each draft shows there as soon as "
        "it is encoded. Ctrl+C stops the try; its drafts are removed."
    )
    runtime.output.success(said.format(url=page_url(port)))
    address_tip(runtime.output, port)
