"""What the pages of tiles acting at once share when typed: their page, their server."""

from __future__ import annotations

import asyncio
import contextlib
from typing import TYPE_CHECKING, Final

from media_hygiene.i18n.templates import translated_environment
from media_hygiene.review.apply_api import ApplyOffer, applying_door
from media_hygiene.review.ending import serve_until_ended
from media_hygiene.review.files import FILE_PATH
from media_hygiene.review.local_app import STATE_PATH
from media_hygiene.review.page_header import headed_page
from media_hygiene.services.reviewing import address_tip, page_url

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping
    from concurrent.futures import Executor

    from media_hygiene.review.local_app import LocalApp
    from media_hygiene.services.runtime import Runtime

_TEMPLATES: Final = "media_hygiene.review"


def pick_page(template: str, paths: Mapping[str, str]) -> bytes:
    """Render a page of tiles; its paths relative to it.

    Args:
        template: Its template.
        paths: The page's own paths, by the name its template reads.

    Returns:
        The page, in the language in use.
    """
    environment = translated_environment(_TEMPLATES, escaped=("html", "j2"))
    values = {
        "state_path": STATE_PATH.removeprefix("/"),
        "file_path": FILE_PATH.removeprefix("/"),
        **{name: path.removeprefix("/") for name, path in paths.items()},
    }
    return headed_page(environment, template, values)


def serve_pick_page(
    runtime: Runtime, app_of: Callable[[Executor], LocalApp], where: tuple[int, str]
) -> int:
    """Serve a page that acts at once, nothing for *Apply now*, until it ends.

    Args:
        runtime: Settings, mount points and output.
        app_of: Builds its app on the worker pool.
        where: The port inside the container (0: any free one), and the sentence
            telling where the page is, holding `{url}`.

    Returns:
        The exit code the page ended on (0: Ctrl+C).
    """
    port, said = where

    def ready(port: int) -> None:
        """Tell where the page is.

        Args:
            port: The port listened on, inside the container.
        """
        runtime.output.success(said.format(url=page_url(port)))
        address_tip(runtime.output, port)

    code = 0
    with runtime.executor_factory() as executor, contextlib.suppress(KeyboardInterrupt):
        door = applying_door(app_of(executor), ApplyOffer(None, lambda: False))
        code = asyncio.run(serve_until_ended(door, port, ready))
    return code
