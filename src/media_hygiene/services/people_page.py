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
from typing import TYPE_CHECKING

from media_hygiene.i18n import _
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.paths.mounts import is_writable
from media_hygiene.person.door import with_person
from media_hygiene.review.apply_api import ApplyOffer, applying_door
from media_hygiene.review.ending import serve_until_ended
from media_hygiene.services.people_app_build import PeopleBuild, people_app
from media_hygiene.services.reviewing import address_tip, page_url

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from media_hygiene.people.roster import Roster
    from media_hygiene.review.apply_api import ApplyStep
    from media_hygiene.services.people_names import PeopleResult
    from media_hygiene.services.runtime import Runtime


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
    code = 0
    with runtime.executor_factory() as executor:
        build = PeopleBuild(executor, _names_file(runtime), start.apply is not None)
        app, aside = people_app(runtime, result, build)
        offer = ApplyOffer(start.apply, lambda: bool(aside.paths()))
        roster = app.roster
        door = applying_door(app, offer, runtime.locations.reports_dir)
        door = with_person(door, runtime, executor)
        with contextlib.suppress(KeyboardInterrupt):
            code = asyncio.run(
                serve_until_ended(door, start.port, partial(_announce, runtime, roster))
            )
    return PeopleServed(len(aside.paths()), code)


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
