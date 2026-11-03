"""Serve the page of `undo --pick` (0525) until Ctrl+C, its tab closed, or home."""

from __future__ import annotations

import asyncio
import contextlib
from typing import TYPE_CHECKING, Final

from media_hygiene.i18n import _
from media_hygiene.i18n.templates import translated_environment
from media_hygiene.review.apply_api import ApplyOffer, applying_door
from media_hygiene.review.ending import serve_until_ended
from media_hygiene.review.files import FILE_PATH
from media_hygiene.review.local_app import STATE_PATH
from media_hygiene.review.page_header import headed_page
from media_hygiene.review.quarantine_app import RESTORE_PATH, QuarantineApp
from media_hygiene.services.reviewing import address_tip, page_url

if TYPE_CHECKING:
    from media_hygiene.services.runtime import Runtime

PAGE_TEMPLATE: Final = "quarantine.html.j2"
_TEMPLATES: Final = "media_hygiene.review"


def quarantine_page() -> bytes:
    """Render the page; its paths relative to it.

    Returns:
        The page, in the language in use.
    """
    environment = translated_environment(_TEMPLATES, escaped=("html", "j2"))
    values = {
        "state_path": STATE_PATH.removeprefix("/"),
        "file_path": FILE_PATH.removeprefix("/"),
        "restore_path": RESTORE_PATH.removeprefix("/"),
    }
    return headed_page(environment, PAGE_TEMPLATE, values)


def serve_quarantine(runtime: Runtime, port: int) -> int:
    """Serve the quarantine's page; each *Restore* acts at once, journaled.

    Args:
        runtime: Settings, mount points and output.
        port: The port to listen on, inside the container (0: any free one).

    Returns:
        The exit code the page ended on (0: Ctrl+C).
    """

    def ready(port: int) -> None:
        """Tell where the page is.

        Args:
            port: The port listened on, inside the container.
        """
        runtime.output.success(
            _(
                "The quarantine is ready, open {url} in your browser. Each photo "
                "restored goes back at once, journaled. Ctrl+C stops the page."
            ).format(url=page_url(port))
        )
        address_tip(runtime.output, port)

    page = quarantine_page()
    code = 0
    with runtime.executor_factory() as executor, contextlib.suppress(KeyboardInterrupt):
        app = QuarantineApp(runtime, page, executor)
        door = applying_door(app, ApplyOffer(None, _nothing))
        code = asyncio.run(serve_until_ended(door, port, ready))
    return code


def _nothing() -> bool:
    """Nothing to apply: *Restore* acts at once.

    Returns:
        False.
    """
    return False
