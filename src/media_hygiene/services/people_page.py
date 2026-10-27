"""Serve the people page until Ctrl+C: the groups of faces alike, and their names.

The faces are cut from their photos on request in the worker pool and never written
anywhere; the page is served like `review` and `places`, on the loopback only. The
names are saved into `config.toml` (`[[people.person]]`), when `/config` is mounted
and writable; otherwise the page shows the groups and the names already given. The
photos of a group can be set aside in the decisions file, as on the search page;
opened from the home page, *Apply now* hands `mh` the step that quarantines them.
"""

from __future__ import annotations

import asyncio
import contextlib
from dataclasses import dataclass
from functools import partial
from typing import TYPE_CHECKING, Final

from media_hygiene.i18n import _
from media_hygiene.i18n.templates import translated_environment
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.paths.mounts import is_writable
from media_hygiene.people.alike import AlikeFinder
from media_hygiene.people.app import (
    CHANGE_PATH,
    GROUPS_PATH,
    SAMPLE_PREFIX,
    SECTION_PREFIX,
    PeopleApp,
)
from media_hygiene.people.aside import ASIDE_PATH, AsideDesk
from media_hygiene.people.board import PeopleBoard
from media_hygiene.people.pictures import FACE_PREFIX, PHOTO_PREFIX
from media_hygiene.people.remembered import AsideMemory
from media_hygiene.people.roster import NamesFile, Roster
from media_hygiene.people.views import STRIP
from media_hygiene.person.door import with_person
from media_hygiene.review.apply_api import APPLY_PATH, ApplyOffer, applying_door
from media_hygiene.review.ending import serve_until_ended
from media_hygiene.review.page_header import page_header
from media_hygiene.services.chosen_place import chosen_store, reports_ready
from media_hygiene.services.reviewing import address_tip, page_url

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from media_hygiene.review.apply_api import ApplyStep
    from media_hygiene.services.people_names import PeopleResult
    from media_hygiene.services.runtime import Runtime

_PACKAGE: Final = "media_hygiene.people"
_PAGE_TEMPLATE: Final = "people.html.j2"


@dataclass(frozen=True, slots=True)
class PeopleStart:
    """The port of the page, and the step its *Apply now* ends on (None: no button)."""

    port: int
    apply: Callable[[], ApplyStep | None] | None = None


@dataclass(frozen=True, slots=True)
class PeopleServed:
    """How the page ended: the files set aside, and the exit code asked for."""

    chosen: int  # read from the disk
    code: int = 0  # `STEP_EXIT_BASE + n`: *Apply now* chose step `n`


def serve_people(
    runtime: Runtime, result: PeopleResult, start: PeopleStart
) -> PeopleServed:
    """Serve the groups until Ctrl+C or *Apply now*; each choice is saved at once.

    Args:
        runtime: Settings, mount points and output.
        result: The groups to show, and every face of the index.
        start: The port (0: any free one) and the step *Apply now* ends on.

    Returns:
        How many files are set aside when the page stops, read from the disk, and
        the exit code the page asked for.
    """
    environment = translated_environment(_PACKAGE, escaped=("html", "j2"))
    page = environment.get_template(_PAGE_TEMPLATE).render(
        header=page_header(_PAGE_TEMPLATE),
        groups_path=GROUPS_PATH,
        section_prefix=SECTION_PREFIX,
        sample_prefix=SAMPLE_PREFIX,
        strip=STRIP,
        change_path=CHANGE_PATH,
        aside_path=ASIDE_PATH,
        face_prefix=FACE_PREFIX,
        photo_prefix=PHOTO_PREFIX,
        apply_path=APPLY_PATH,
        apply_offered=start.apply is not None,
    )
    names = NamesFile(_names_file(runtime), runtime.settings.people, result.moves)
    board = PeopleBoard.of(result.groups, result.every)
    roster = Roster(board, result.every, names)
    aside, alike = _aside_desks(runtime, board)
    offer = ApplyOffer(start.apply, lambda: bool(aside.paths()))
    code = 0
    with runtime.executor_factory() as executor, contextlib.suppress(KeyboardInterrupt):
        app = PeopleApp(
            roster,
            runtime.mapper,
            page.encode(),
            executor,
            runtime.previews_dir,
            aside,
            alike,
        )
        door = applying_door(app, offer, runtime.locations.reports_dir)
        door = with_person(door, runtime, executor)
        code = asyncio.run(
            serve_until_ended(door, start.port, partial(_announce, runtime, roster))
        )
    return PeopleServed(len(aside.paths()), code)


def _aside_desks(
    runtime: Runtime, board: PeopleBoard
) -> tuple[AsideDesk, AlikeFinder | None]:
    """Where the photos set aside go, and who looks like the people set aside.

    Args:
        runtime: Mount points.
        board: Every face of the page.

    Returns:
        The desk saving the photos and remembering the faces; the finder of the
        faces like theirs, None without a persistent cache.
    """
    memory = AsideMemory.of(runtime)
    ready = partial(reports_ready, runtime)
    aside = AsideDesk(chosen_store(runtime), ready, memory)
    return aside, None if memory is None else AlikeFinder(board, memory)


def names_file(runtime: Runtime) -> Path | None:
    """The `config.toml` the names go to; None when it cannot be written.

    Args:
        runtime: Mount points.

    Returns:
        The file, or None.
    """
    config = runtime.locations.config_file
    if runtime.persistent(MountKind.CONFIG) and is_writable(config.parent):
        return config
    return None


def _names_file(runtime: Runtime) -> Path | None:
    """The `config.toml` the names go to; None when it cannot be written.

    Args:
        runtime: Mount points and output.

    Returns:
        The file, or None after saying why names cannot be saved.
    """
    config = names_file(runtime)
    if config is not None:
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
