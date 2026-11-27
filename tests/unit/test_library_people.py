"""The library stays when only faces were named; built again for anything else."""

from __future__ import annotations

from dataclasses import dataclass, replace
from types import SimpleNamespace
from typing import TYPE_CHECKING, cast

from media_hygiene.config.people_settings import Person
from media_hygiene.search.meaning_index import MeaningIndex
from media_hygiene.services.library_people import faces_only, follow_faces
from tests.support.runtime import make_locations, make_runtime

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.search.app import SearchApp
    from media_hygiene.services.runtime import Runtime


def _with(runtime: Runtime, *people: Person) -> Runtime:
    """The runtime, `[people]` replaced."""
    settings = runtime.settings
    named = settings.model_copy(
        update={"people": settings.people.model_copy(update={"person": people})}
    )
    return replace(runtime, loaded=replace(runtime.loaded, settings=named))


def test_faces_added_to_known_people_keep_the_library(tmp_path: Path) -> None:
    """Same names, more faces: kept; a new name, or another setting: built again."""
    base = make_runtime(make_locations(tmp_path))
    before = _with(base, Person(name="Lisa", faces=("/a.jpg#0",)))
    more = _with(base, Person(name="Lisa", faces=("/a.jpg#0", "/b.jpg#0")))
    other = _with(base, Person(name="Lisa"), Person(name="Manon"))
    assert faces_only(before, more)
    assert not faces_only(before, other)
    review = before.settings.review.model_copy(update={"port": 8199})
    moved = replace(
        before,
        loaded=replace(
            before.loaded,
            settings=before.settings.model_copy(update={"review": review}),
        ),
    )
    assert not faces_only(before, moved)


@dataclass(frozen=True)
class _Place:
    """The people desk's place: only its settings matter here."""

    settings: object


def test_the_names_are_read_again_and_the_desk_forgets(tmp_path: Path) -> None:
    """The search gets the names anew; the people desk reads its faces again."""
    locations = make_locations(tmp_path)
    locations.index_file.parent.mkdir(parents=True, exist_ok=True)
    locations.index_file.touch()
    runtime = _with(make_runtime(locations), Person(name="Lisa", faces=("/a#0",)))
    given: list[object] = []
    search = object.__new__(MeaningIndex)
    search.name_people_soon = given.append  # type: ignore[method-assign,assignment]
    desk = SimpleNamespace(place=_Place(settings=None), seen="kept")
    place = SimpleNamespace(index=search, names=desk)
    follow_faces(cast("SearchApp", SimpleNamespace(place=place)), runtime)
    assert len(given) == 1
    assert desk.seen is None
    assert desk.place.settings == runtime.settings.people
