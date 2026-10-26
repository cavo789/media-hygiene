"""Give a page's server the person page (`/person`, TODO 0351): one call per page.

Every page that shows photos adds it to its door, so that "set this person aside"
works from any of them: the index read-only, the decisions file of the reports, the
face models of the cache for a second look (never downloaded from here).
"""

from __future__ import annotations

import dataclasses
from functools import partial
from typing import TYPE_CHECKING, Final

from media_hygiene.faces.worker import OnnxRecipe
from media_hygiene.i18n.templates import translated_environment
from media_hygiene.people.aside import AsideDesk
from media_hygiene.people.remembered import AsideMemory
from media_hygiene.person import routes
from media_hygiene.person.app import PersonApp
from media_hygiene.person.finding import PersonFinder, PhotoPlace
from media_hygiene.person.lookup import FaceIndex
from media_hygiene.person.second_look import LOOSE_SCORE
from media_hygiene.person.shelf import FaceShelf
from media_hygiene.review.apply_api import ApplyDesk, ApplyingApp
from media_hygiene.review.page_header import page_header
from media_hygiene.search.app import SearchApp
from media_hygiene.services import people_models
from media_hygiene.services.chosen_place import chosen_store, reports_ready

if TYPE_CHECKING:
    from concurrent.futures import Executor

    from media_hygiene.faces.worker import FinderRecipe
    from media_hygiene.review.ending import EndingDoor
    from media_hygiene.services.runtime import Runtime

_PACKAGE: Final = "media_hygiene.person"
_PAGE_TEMPLATE: Final = "person.html.j2"
_PATHS: Final = {
    "photo": routes.PHOTO_PATH,
    "look": routes.LOOK_PATH,
    "like": routes.LIKE_PATH,
    "aside": routes.ASIDE_PATH,
}


def with_person(door: EndingDoor, runtime: Runtime, executor: Executor) -> EndingDoor:
    """The same door, answering `/person` too, with the page's *Apply now* if it has it.

    Args:
        door: A page's door.
        runtime: Settings, mount points and output.
        executor: The page's worker pool.

    Returns:
        The door with its person page.
    """
    person = person_app(runtime, executor, host_apply(door))
    return dataclasses.replace(door, person=person)


def host_apply(door: EndingDoor) -> ApplyDesk | None:
    """The *Apply now* of the page serving `/person`: a review's, or the search's.

    Args:
        door: The page's door.

    Returns:
        Its desk; None for a page without one (the phone page).
    """
    app = door.app
    if isinstance(app, ApplyingApp):
        return app.desk
    if isinstance(app, SearchApp):
        return app.place.apply
    return None


def person_app(
    runtime: Runtime, executor: Executor, host: ApplyDesk | None = None
) -> PersonApp:
    """The person page of a run.

    Args:
        runtime: Settings, mount points and output.
        executor: The worker pool.
        host: The *Apply now* of the page serving it: the same step, ended the same
            way, offered when something is set aside in the decisions file.

    Returns:
        It.
    """
    ready = partial(reports_ready, runtime)
    aside = AsideDesk(chosen_store(runtime), ready, AsideMemory.of(runtime))
    apply = None
    if host is not None and host.offered:
        offer = dataclasses.replace(host.offer, pending=lambda: bool(aside.paths()))
        apply = dataclasses.replace(host, offer=offer)
    environment = translated_environment(_PACKAGE, escaped=("html", "j2"))
    page = environment.get_template(_PAGE_TEMPLATE).render(
        header=page_header(_PAGE_TEMPLATE),
        paths=_PATHS,
        apply_offered=apply is not None,
        apply_path=routes.APPLY_PATH,
    )
    place = PhotoPlace(runtime.mapper, runtime.locations.data_dir)
    finder = PersonFinder(place, FaceIndex(runtime.index_file), FaceShelf())
    recipe = partial(loose_recipe, runtime)
    return PersonApp(
        page.encode(), finder, executor, recipe, aside, runtime.previews_dir, apply
    )


def loose_recipe(runtime: Runtime) -> FinderRecipe | None:
    """The face finder of a second look: the cache's models, less strict.

    Args:
        runtime: Mount points.

    Returns:
        Its recipe; None when the models are not in the cache (never downloaded here).
    """
    if not people_models.models_present(runtime):
        return None
    recipe = people_models.face_recipe(runtime)
    if isinstance(recipe, OnnxRecipe):
        return dataclasses.replace(recipe, least=LOOSE_SCORE)
    return recipe
