"""Serve the people page until Ctrl+C: the groups of faces alike, and their names.

The faces are cut from their photos on request in the worker pool and never written
anywhere; the page is served like `review` and `places`, on the loopback only. The
names are saved into `config.toml` (`[[people.person]]`), when `/config` is mounted
and writable; otherwise the page shows the groups and the names already given.
"""

from __future__ import annotations

import asyncio
import contextlib
from functools import partial
from typing import TYPE_CHECKING, Final

from media_hygiene.i18n import _
from media_hygiene.i18n.templates import translated_environment
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.paths.mounts import is_writable
from media_hygiene.people.app import (
    CHANGE_PATH,
    FACE_PREFIX,
    GROUPS_PATH,
    PHOTO_PREFIX,
    PeopleApp,
)
from media_hygiene.people.board import PeopleBoard
from media_hygiene.people.roster import NamesFile, Roster
from media_hygiene.services.reviewing import address_tip, page_url, run_server

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.services.people_names import PeopleResult
    from media_hygiene.services.runtime import Runtime

_PACKAGE: Final = "media_hygiene.people"
_PAGE_TEMPLATE: Final = "people.html.j2"


def serve_people(runtime: Runtime, result: PeopleResult, port: int) -> None:
    """Serve the groups until Ctrl+C; each name is saved as it is given.

    Args:
        runtime: Settings, mount points and output.
        result: The groups to show, and every face of the index.
        port: The port to listen on, inside the container (0: any free one).
    """
    environment = translated_environment(_PACKAGE, escaped=("html", "j2"))
    page = environment.get_template(_PAGE_TEMPLATE).render(
        groups_path=GROUPS_PATH,
        change_path=CHANGE_PATH,
        face_prefix=FACE_PREFIX,
        photo_prefix=PHOTO_PREFIX,
    )
    names = NamesFile(_names_file(runtime), runtime.settings.people)
    roster = Roster(PeopleBoard.of(result.groups), result.every, names)
    with runtime.executor_factory() as executor, contextlib.suppress(KeyboardInterrupt):
        app = PeopleApp(roster, runtime.mapper, page.encode(), executor)
        asyncio.run(run_server(app, port, partial(_announce, runtime, roster)))


def _names_file(runtime: Runtime) -> Path | None:
    """The `config.toml` the names go to; None when it cannot be written.

    Args:
        runtime: Mount points and output.

    Returns:
        The file, or None after saying why names cannot be saved.
    """
    config = runtime.locations.config_file
    if runtime.persistent(MountKind.CONFIG) and is_writable(config.parent):
        return config
    runtime.output.info(
        _(
            "Names are saved in config.toml: mount a writable folder of yours on "
            "/config to name the groups. The page shows them meanwhile."
        )
    )
    return None


def _announce(runtime: Runtime, roster: Roster, port: int) -> None:
    """Tell where the page is and how to open it from the host.

    Args:
        runtime: Settings, mount points and output.
        roster: The page's state: can it save names?
        port: The port listened on, inside the container.
    """
    url = page_url(port)
    if roster.writable:
        line = _(
            "Faces ready, open {url} in your browser to name them; each name is "
            "saved at once in config.toml. Ctrl+C stops it; the photos are not "
            "changed."
        )
    else:
        line = _(
            "Faces ready, open {url} in your browser. Ctrl+C stops it; nothing is "
            "changed."
        )
    runtime.output.success(line.format(url=url))
    address_tip(runtime.output, port)
