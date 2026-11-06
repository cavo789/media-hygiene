"""The people page's app, for its own server (`people_page`) or the home's (0600).

Under the home server the page answers below `/people/`: its paths are then given
without their leading `/`, relative to the page, as the other pages served there.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import partial
from typing import TYPE_CHECKING, Final

from media_hygiene.i18n.templates import translated_environment
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
from media_hygiene.review.apply_api import APPLY_PATH
from media_hygiene.review.home_tags_api import PEOPLE_PATH
from media_hygiene.review.home_views import UNDO_PATH
from media_hygiene.review.page_header import page_header
from media_hygiene.services.chosen_place import chosen_store, reports_ready

if TYPE_CHECKING:
    from concurrent.futures import Executor
    from pathlib import Path

    from media_hygiene.services.people_names import PeopleResult
    from media_hygiene.services.runtime import Runtime

_PACKAGE: Final = "media_hygiene.people"
_PAGE_TEMPLATE: Final = "people.html.j2"


@dataclass(frozen=True, slots=True)
class PeopleBuild:
    """The pool, where the names go, and how the page is served."""

    executor: Executor
    names: Path | None  # `config.toml`, None when it cannot be written
    apply_offered: bool = False  # *Apply now*: opened from the home page
    relative: bool = False  # under a prefix of the home server (0600)
    new: int = 0  # photos not analysed yet, which the page analyses itself (0588)


def people_page(build: PeopleBuild) -> bytes:
    """Render the page.

    Args:
        build: Whether *Apply now* shows, whether its paths are relative.

    Returns:
        The HTML.
    """
    paths = {
        "groups_path": GROUPS_PATH,
        "section_prefix": SECTION_PREFIX,
        "sample_prefix": SAMPLE_PREFIX,
        "change_path": CHANGE_PATH,
        "aside_path": ASIDE_PATH,
        "face_prefix": FACE_PREFIX,
        "photo_prefix": PHOTO_PREFIX,
        "apply_path": APPLY_PATH,
        "undo_path": UNDO_PATH,
    }
    if build.relative:
        paths = {name: path.removeprefix("/") for name, path in paths.items()}
    environment = translated_environment(_PACKAGE, escaped=("html", "j2"))
    return (
        environment.get_template(_PAGE_TEMPLATE)
        .render(
            header=page_header(_PAGE_TEMPLATE),
            strip=STRIP,
            apply_offered=build.apply_offered,
            new_photos=build.new,
            scan_path=PEOPLE_PATH,
            **paths,
        )
        .encode()
    )


def people_app(
    runtime: Runtime, result: PeopleResult, build: PeopleBuild
) -> tuple[PeopleApp, AsideDesk]:
    """Build the page's app on the groups found.

    Args:
        runtime: Settings, mount points.
        result: The groups to show, and every face of the index.
        build: The pool, the names file, how the page is served.

    Returns:
        The app, and the desk of the photos set aside.
    """
    names = NamesFile(build.names, runtime.settings.people, result.moves)
    board = PeopleBoard.of(result.groups, result.every)
    roster = Roster(board, result.every, names)
    memory = AsideMemory.of(runtime)
    aside = AsideDesk(chosen_store(runtime), partial(reports_ready, runtime), memory)
    alike = None if memory is None else AlikeFinder(board, memory)
    app = PeopleApp(
        roster,
        runtime.mapper,
        people_page(build),
        build.executor,
        runtime.previews_dir,
        aside,
        alike,
    )
    return app, aside
