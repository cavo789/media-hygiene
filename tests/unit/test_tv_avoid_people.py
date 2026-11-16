"""0825: the people a phone asks to keep off the TV, for one show."""

from __future__ import annotations

import json
import sqlite3
import tomllib
from contextlib import closing
from http import HTTPStatus
from pathlib import Path
from typing import TYPE_CHECKING, Final, cast

import numpy as np
import pytest

from media_hygiene.faces.models import FaceBox
from media_hygiene.index.face_rows import StoredFace
from media_hygiene.person.likeness import stacked
from media_hygiene.review.http import Request
from media_hygiene.services import slideshow_avoid
from media_hygiene.services.slideshow_avoid import PersonPhotos, paths_by_name
from tests.support.indexed_photos import indexed_photos
from tests.support.runtime import make_locations, make_runtime
from tests.support.slideshow_serving import HOST, ask, choose, search_in, slideshow_of

if TYPE_CHECKING:
    from collections.abc import Iterator

    from media_hygiene.services.runtime import Runtime
    from media_hygiene.services.slideshow_here import SlideshowHere

_PHOTOS: Final = 4  # IMG_0 named Antoine, IMG_1 looks like him, IMG_2 someone else
_BOX: Final = FaceBox(0, 0, 60, 60)


def _vector(*values: float) -> bytes:
    vector = np.zeros(128, dtype=np.float32)
    vector[: len(values)] = values
    return (vector / np.linalg.norm(vector)).astype("<f4").tobytes()


class _Faces:
    """The faces of the index, without reading one."""

    def __init__(self, every: tuple[StoredFace, ...]) -> None:
        self.every = every
        self.vectors = stacked(every)


def _faces(trip: Path) -> tuple[StoredFace, ...]:
    shapes = ((1.0, 0.0), (0.98, 0.2), (0.0, 1.0))
    return tuple(
        StoredFace(trip / f"IMG_{n}.jpg", 0, _BOX, 0.9, 99.0, _vector(*shape))
        for n, shape in enumerate(shapes)
    )


@pytest.fixture
def runtime(tmp_path: Path) -> Runtime:
    """Antoine named on IMG_0's face; Léa named, her faces not in the index."""
    locations = make_locations(tmp_path)
    trip = locations.data_dir / "c" / "Trip"
    locations.config_file.parent.mkdir(parents=True, exist_ok=True)
    locations.config_file.write_text(
        "[[people.person]]\nname = 'Antoine'\n"
        f"faces = ['{trip / 'IMG_0.jpg'}#0']\n"
        "[[people.person]]\nname = 'Léa'\n",
        "utf-8",
    )
    return make_runtime(locations)


@pytest.fixture
def here(
    runtime: Runtime, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Iterator[SlideshowHere]:
    """The home slideshow over Trip: four dated camera photos, three with a face."""
    trip = runtime.locations.data_dir / "c" / "Trip"
    index = tmp_path / "index.sqlite"
    indexed_photos(index, trip, _PHOTOS)
    with closing(sqlite3.connect(index)) as connection:
        connection.execute(
            "UPDATE files SET media_date = '2025:11:03 10:00:00', metadata = ?",
            ('{"make": "Canon"}',),
        )
        connection.commit()
    every = _faces(trip)
    monkeypatch.setattr(slideshow_avoid, "FaceIndex", lambda _file: _Faces(every))
    search_in(monkeypatch, index)
    yield from slideshow_of(runtime)


def test_the_home_choices_carry_no_people_any_more(here: SlideshowHere) -> None:
    """The home's TV block is gone: people are avoided on the remote it opens."""
    lists = json.loads(ask(here, Request("GET", "/slideshow/choices", HOST)).body)
    assert "people" not in lists
    answer = choose(here, {"first": "2025-11-01", "avoid": ["Antoine"]})
    assert answer.status is HTTPStatus.BAD_REQUEST
    script = (
        Path(__file__).resolve().parents[2]
        / "src/media_hygiene/review/templates/home_tv.js.j2"
    ).read_text("utf-8")
    assert "tvAvoid" not in script


def test_the_named_and_the_look_alike_photos_are_theirs(runtime: Runtime) -> None:
    """IMG_0 named Antoine (✓), IMG_1 close to his mean (≈); IMG_2 someone else."""
    trip = runtime.locations.data_dir / "c" / "Trip"
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(slideshow_avoid, "FaceIndex", lambda _f: _Faces(_faces(trip)))
        found = paths_by_name(runtime, ["antoine", "Zoé"])
    assert found == {
        "Antoine": PersonPhotos(
            frozenset({trip / "IMG_0.jpg"}), frozenset({trip / "IMG_1.jpg"})
        )
    }


def test_a_person_without_faces_has_no_photo(
    runtime: Runtime, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Léa has no face in the index: named, nothing of hers."""
    monkeypatch.setattr(slideshow_avoid, "FaceIndex", lambda _file: _Faces(()))
    assert paths_by_name(runtime, ["Léa"]) == {"Léa": PersonPhotos()}


def test_the_remote_offers_only_the_people_on_the_show(here: SlideshowHere) -> None:
    """Antoine named on IMG_0, guessed on IMG_1, Léa on none: only Antoine."""
    answer = choose(here, {"first": "2025-11-01", "last": "2025-11-30"})
    assert answer.status is HTTPStatus.OK
    view = json.loads(ask(here, Request("GET", "/slideshow/api/avoid", HOST)).body)
    assert view["people"] == [{"name": "Antoine", "sure": 1, "guessed": 1}]
    payload = json.dumps({"names": ["Antoine"]}).encode()
    ticked = ask(here, Request("POST", "/slideshow/api/avoid", HOST, payload))
    assert json.loads(ticked.body)["out"] == 2


def _avoid_view(here: SlideshowHere) -> dict[str, object]:
    view: dict[str, object] = json.loads(
        ask(here, Request("GET", "/slideshow/api/avoid", HOST)).body
    )
    return view


def _remembered_on_disk(runtime: Runtime) -> object:
    return tomllib.loads(runtime.locations.config_file.read_text("utf-8"))["slideshow"][
        "avoid"
    ]


def test_a_tick_on_the_pc_is_remembered_for_the_next_show(
    here: SlideshowHere, runtime: Runtime
) -> None:
    """0834: the tick is written, read back; a new show starts with it set out."""
    month = {"first": "2025-11-01", "last": "2025-11-30"}
    choose(here, month)
    payload = json.dumps({"names": ["Antoine"]}).encode()
    ticked = ask(here, Request("POST", "/slideshow/api/avoid", HOST, payload))
    assert json.loads(ticked.body)["remembered"] == ["Antoine"]
    assert _remembered_on_disk(runtime) == ["Antoine"]
    choose(here, month)
    view = _avoid_view(here)
    assert (view["ticked"], view["out"], view["phone"]) == (["Antoine"], 2, False)


def test_unticking_on_the_pc_removes_the_name_from_the_file(
    here: SlideshowHere, runtime: Runtime
) -> None:
    """0834: an untick takes the name out of `[slideshow] avoid`."""
    choose(here, {"first": "2025-11-01", "last": "2025-11-30"})
    for names in (["Antoine"], []):
        payload = json.dumps({"names": names}).encode()
        ask(here, Request("POST", "/slideshow/api/avoid", HOST, payload))
    assert _remembered_on_disk(runtime) == []


def test_a_remembered_person_on_no_photo_is_listed_and_ticked(
    runtime: Runtime, here: SlideshowHere
) -> None:
    """0834: Léa, on none of the photos, is offered ticked; a renamed one ignored."""
    config = runtime.locations.config_file
    config.write_text(
        config.read_text("utf-8") + "[slideshow]\navoid = ['Léa', 'Gone']\n",
        "utf-8",
    )
    choose(here, {"first": "2025-11-01", "last": "2025-11-30"})
    view = _avoid_view(here)
    assert {"name": "Léa", "sure": 0, "guessed": 0} in cast(
        "list[object]", view["people"]
    )
    assert (view["ticked"], view["remembered"]) == (["Léa"], ["Léa"])
    payload = json.dumps({"names": ["Léa", "Antoine"]}).encode()
    ask(here, Request("POST", "/slideshow/api/avoid", HOST, payload))
    assert _remembered_on_disk(runtime) == ["Gone", "Antoine", "Léa"]
