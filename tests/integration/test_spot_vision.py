"""🤖 `spots --vision`: a local model picks the landmark a photo shows (0589)."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from typing import TYPE_CHECKING, Final

import pytest
from PIL import Image

from media_hygiene.classify.ai.landmark_prompt import read_landmark
from media_hygiene.errors import AiError
from media_hygiene.geo.distance import Point
from media_hygiene.geo.landmarks import shared_landmarks
from media_hygiene.index.schema import prepare
from media_hygiene.search.fts import SearchIndex
from media_hygiene.search.query import SearchQuery, parse_terms
from media_hygiene.services import spot_fill
from media_hygiene.services.spot_fill import fill_spots
from media_hygiene.services.spot_vision import pick_landmarks
from tests.support.cli import run
from tests.support.runtime import make_locations, make_runtime
from tests.support.tagging import write_tags_config

if TYPE_CHECKING:
    from pathlib import Path

    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations
    from media_hygiene.scan.progress import Step
    from media_hygiene.services.runtime import Runtime
    from tests.support.fake_ollama import FakeOllama

_EIFFEL: Final = (48.8584, 2.2945)
_SEA: Final = (45.0, -30.0)
_INSERT: Final = (
    "INSERT INTO files (path, size, mtime_ns, latitude, longitude)"
    " VALUES (?, 1, 1, ?, ?)"
)


class _Sink:
    """Accepts the progress reported."""

    def start(self, step: Step, total: int | None) -> None:
        """Nothing to show."""
        assert step.title
        assert total

    def advance(self, weight: int = 1) -> None:
        """Nothing to count."""
        assert weight

    def current(self, text: str) -> None:
        """Nothing to say."""
        assert text

    def stop(self) -> None:
        """Nothing to end."""


def _runtime(tmp_path: Path, url: str, model: str = "vision-model") -> Runtime:
    ai: dict[str, object] = {"url": url, "model": model, "retries": 0}
    layer: dict[str, dict[str, object]] = {"classify": {"ai": ai}}
    return make_runtime(make_locations(tmp_path), layer)


def _photos(runtime: Runtime, tmp_path: Path, **where: tuple[float, float]) -> None:
    """Real pictures, indexed with their position, their spots filled."""
    assert runtime.index_file is not None
    runtime.index_file.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(runtime.index_file)) as connection:
        prepare(connection)
        for name, point in where.items():
            path = tmp_path / f"{name}.jpg"
            Image.new("RGB", (64, 48), "gray").save(path)
            connection.execute(_INSERT, (str(path), *point))
        connection.commit()
        fill_spots(runtime, connection, _Sink())


def _row(runtime: Runtime, tmp_path: Path, name: str) -> tuple[str, str]:
    assert runtime.index_file is not None
    with closing(sqlite3.connect(runtime.index_file)) as connection:
        row = connection.execute(
            "SELECT landmark, source FROM spots WHERE path = ?",
            (str(tmp_path / f"{name}.jpg"),),
        ).fetchone()
    return (str(row[0]), str(row[1]))


def _found(runtime: Runtime, words: str) -> list[str]:
    assert runtime.index_file is not None
    with SearchIndex.open(runtime.index_file) as search:
        hits = search.find(SearchQuery(parse_terms(words)), 5).hits
    return [hit.photo.path.stem for hit in hits]


def _second() -> str:
    """The second landmark nearest the Eiffel Tower, the one the fake picks."""
    return shared_landmarks(None).around(Point(*_EIFFEL), 1000.0)[1]


def test_the_pick_is_stored_with_its_source_and_found(
    tmp_path: Path, fake: FakeOllama
) -> None:
    """Choice 2 among the nearest landmarks: stored, searched; asked once only."""
    fake.answer = lambda _body: {"choice": 2}
    runtime = _runtime(tmp_path, fake.url)
    _photos(runtime, tmp_path, eiffel=_EIFFEL, sea=_SEA)
    assert _row(runtime, tmp_path, "eiffel") == ("Tour Eiffel", "geonames")
    picks = pick_landmarks(runtime, _Sink())
    assert (picks.asked, picks.picked) == (1, 1)  # out at sea: nothing around
    second = _second()
    assert _row(runtime, tmp_path, "eiffel") == (second, "vision")
    assert _found(runtime, second) == ["eiffel"]
    assert _found(runtime, "tour eiffel") == []
    asked = fake.described()
    assert pick_landmarks(runtime, _Sink()).asked == 0
    assert fake.described() == asked
    body = fake.calls[-1][1]
    assert "1. Tour Eiffel" in str(body["messages"])


def test_none_shown_clears_and_a_refill_keeps_the_pick(
    tmp_path: Path, fake: FakeOllama, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Facing away: no landmark; a later refill (new stamp) does not bring it back."""
    fake.answer = lambda _body: {"choice": 0}
    runtime = _runtime(tmp_path, fake.url)
    _photos(runtime, tmp_path, eiffel=_EIFFEL)
    assert pick_landmarks(runtime, _Sink()).none == 1
    monkeypatch.setattr(spot_fill, "_FORMAT", 99)
    assert runtime.index_file is not None
    with closing(sqlite3.connect(runtime.index_file)) as connection:
        assert fill_spots(runtime, connection, _Sink()) == 1
    assert _row(runtime, tmp_path, "eiffel") == ("", "vision")


def test_a_name_typed_by_hand_is_never_asked_about(
    tmp_path: Path, fake: FakeOllama
) -> None:
    """Source `user` (0489): no photo sent, the name stays."""
    fake.answer = lambda _body: {"choice": 2}
    runtime = _runtime(tmp_path, fake.url)
    _photos(runtime, tmp_path, eiffel=_EIFFEL)
    assert runtime.index_file is not None
    with closing(sqlite3.connect(runtime.index_file)) as connection:
        connection.execute("UPDATE spots SET landmark = 'Mine', source = 'user'")
        connection.commit()
    assert pick_landmarks(runtime, _Sink()).asked == 0
    assert fake.described() == 0
    assert _row(runtime, tmp_path, "eiffel") == ("Mine", "user")


def test_an_answer_outside_the_list_changes_nothing(
    tmp_path: Path, fake: FakeOllama
) -> None:
    """A number past the list: unclear, the GeoNames name stays."""
    fake.answer = lambda _body: {"choice": 99}
    runtime = _runtime(tmp_path, fake.url)
    _photos(runtime, tmp_path, eiffel=_EIFFEL)
    assert pick_landmarks(runtime, _Sink()).unclear == 1
    assert _row(runtime, tmp_path, "eiffel") == ("Tour Eiffel", "geonames")


@pytest.mark.parametrize("model", ["", "vision-model"])
def test_without_a_model_nothing_changes(tmp_path: Path, model: str) -> None:
    """No model set, or no server answering: an error, the rows as they were."""
    runtime = _runtime(tmp_path, "http://127.0.0.1:9", model)
    _photos(runtime, tmp_path, eiffel=_EIFFEL)
    with pytest.raises(AiError):
        pick_landmarks(runtime, _Sink())
    assert _row(runtime, tmp_path, "eiffel") == ("Tour Eiffel", "geonames")


@pytest.mark.parametrize(
    ("content", "expected"),
    [
        ('{"choice": 1}', "A"),
        ('{"choice": 0}', ""),
        ('{"choice": 3}', None),
        ('{"choice": true}', None),
        ("nonsense", None),
    ],
)
def test_the_answer_is_read_from_the_list_only(
    content: str, expected: str | None
) -> None:
    """A number of the list, 0 for none; anything else is no answer."""
    assert read_landmark(content, ("A", "B")) == expected


def test_the_command_says_how_it_went(
    cli: CliRunner, fake: FakeOllama, locations: Locations
) -> None:
    """`spots --vision`: no model, an error; the fake model, the figures read back."""
    assert run(cli, "audit").exit_code == 0
    refused = run(cli, "spots", "--vision")
    assert refused.exit_code == 1
    assert "No local vision model" in refused.output
    write_tags_config(locations.config_dir, fake.url)
    result = run(cli, "spots", "--vision")
    assert result.exit_code == 0, result.output
    assert "shown to the model" in result.output
