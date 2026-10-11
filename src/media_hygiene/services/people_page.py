"""Serve the people page until Ctrl+C: the groups of faces alike, read-only.

The faces are cut from their photos on request in the worker pool and never written
anywhere; the page is served like `review` and `search`, on the loopback only.
"""

from __future__ import annotations

import asyncio
import contextlib
from functools import partial
from typing import TYPE_CHECKING, Final

from media_hygiene.i18n import _
from media_hygiene.i18n.templates import translated_environment
from media_hygiene.people.app import (
    FACE_PREFIX,
    GROUPS_PATH,
    PHOTO_PREFIX,
    PeopleApp,
)
from media_hygiene.people.board import PeopleBoard
from media_hygiene.services.reviewing import address_tip, page_url, run_server

if TYPE_CHECKING:
    from media_hygiene.services.people_groups import PeopleGroups
    from media_hygiene.services.runtime import Runtime

_PACKAGE: Final = "media_hygiene.people"
_PAGE_TEMPLATE: Final = "people.html.j2"


def serve_people(runtime: Runtime, groups: PeopleGroups, port: int) -> None:
    """Serve the groups until Ctrl+C.

    Args:
        runtime: Settings, mount points and output.
        groups: The groups to show.
        port: The port to listen on, inside the container (0: any free one).
    """
    environment = translated_environment(_PACKAGE, escaped=("html", "j2"))
    page = environment.get_template(_PAGE_TEMPLATE).render(
        groups_path=GROUPS_PATH, face_prefix=FACE_PREFIX, photo_prefix=PHOTO_PREFIX
    )
    board = PeopleBoard.of(groups)
    with runtime.executor_factory() as executor, contextlib.suppress(KeyboardInterrupt):
        app = PeopleApp(board, runtime.mapper, page.encode(), executor)
        asyncio.run(run_server(app, port, partial(_announce, runtime)))


def _announce(runtime: Runtime, port: int) -> None:
    """Tell where the page is and how to open it from the host.

    Args:
        runtime: Settings, mount points and output.
        port: The port listened on, inside the container.
    """
    runtime.output.success(
        _(
            "Faces ready, open {url} in your browser. Ctrl+C stops it; nothing is "
            "changed."
        ).format(url=page_url(port))
    )
    address_tip(runtime.output, port)
