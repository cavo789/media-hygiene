"""After an import: the new places named online, only after an explicit Yes (0474)."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Final

import typer

from media_hygiene.cli.import_places import offer_place_names
from media_hygiene.geo.distance import Point
from media_hygiene.geo.reverse import Pace
from media_hygiene.geo.towns_once import shared_towns
from media_hygiene.services.place_names import PLACE_NAMES_FILE, read_names
from media_hygiene.services.slideshow_places import Places
from media_hygiene.slideshow.chapters import Chapter
from tests.support.runtime import make_locations, make_runtime
from tests.support.scenes import Shot, write_shot

if TYPE_CHECKING:
    import urllib.request
    from collections.abc import Mapping
    from pathlib import Path

    import pytest

    from media_hygiene.services.runtime import Runtime

_EIFFEL: Final = (48.8584, 2.2945)
_NEAR_EIFFEL: Final = (48.85842, 2.29452)  # the same spot, rounded
_LIEGE: Final = (50.6326, 5.5797)


class _FakeServer:
    """Answers as Nominatim would, and counts what it was sent."""

    def __init__(self, *, down: bool = False) -> None:
        self.asked: list[str] = []
        self.down = down
        self.slept: list[float] = []

    def fetch(self, request: urllib.request.Request, _timeout: float) -> bytes:
        """Answer a reverse lookup, or fail when down."""
        self.asked.append(request.full_url)
        if self.down:
            message = "unreachable"
            raise OSError(message)
        return json.dumps({"name": f"Spot {len(self.asked)}"}).encode()

    def pace(self) -> Pace:
        """The transport sending to this server, never waiting for real."""
        return Pace(self.fetch, clock=lambda: 0.0, sleep=self.slept.append)


def _photos(tmp_path: Path) -> list[Path]:
    places = (_EIFFEL, _NEAR_EIFFEL, _LIEGE)
    return [
        write_shot(tmp_path / "in" / f"{i}.jpg", Shot(seed=i), gps=place)
        for i, place in enumerate(places)
    ] + [write_shot(tmp_path / "in" / "none.jpg", Shot(seed=9))]


def _runtime(tmp_path: Path, places: Mapping[str, object] | None = None) -> Runtime:
    locations = make_locations(tmp_path)
    locations.cache_dir.mkdir(parents=True, exist_ok=True)
    return make_runtime(locations, {"places": dict(places or {})})


def _answer(monkeypatch: pytest.MonkeyPatch, *, yes: bool | None) -> list[str]:
    asked: list[str] = []

    def confirm(question: str, *, default: bool) -> bool:
        asked.append(question)
        assert default is False
        if yes is None:
            raise typer.Abort
        return yes

    monkeypatch.setattr(typer, "confirm", confirm)
    return asked


def test_no_or_no_terminal_sends_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Answer No, or no one to answer: not one request."""
    server, runtime, photos = _FakeServer(), _runtime(tmp_path), _photos(tmp_path)
    for answer in (False, None):
        asked = _answer(monkeypatch, yes=answer)
        offer_place_names(runtime, photos, server.pace())
        assert "2 new places" in asked[0]
    assert not server.asked
    assert not (runtime.locations.cache_dir / PLACE_NAMES_FILE).exists()


def test_never_or_no_address_does_not_even_ask(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`never` and an empty `nominatim_url`: no question, no request."""
    server, photos = _FakeServer(), _photos(tmp_path)
    asked = _answer(monkeypatch, yes=True)
    for places in ({"reverse_lookup": "never"}, {"nominatim_url": ""}):
        offer_place_names(_runtime(tmp_path, places), photos, server.pace())
    assert not asked
    assert not server.asked


def test_yes_asks_once_per_spot_then_never_again(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Two photos at the Eiffel Tower, one in Liège: two rounded requests, kept."""
    server, runtime, photos = _FakeServer(), _runtime(tmp_path), _photos(tmp_path)
    _answer(monkeypatch, yes=True)
    offer_place_names(runtime, photos, server.pace())
    assert len(server.asked) == 2
    assert "lat=48.858&lon=2.295" in server.asked[0]
    assert server.slept == [1.0]  # one request per second
    names = read_names(runtime.locations.cache_dir)
    assert names == {"48.858,2.295": "Spot 1", "50.633,5.58": "Spot 2"}
    asked = _answer(monkeypatch, yes=True)
    offer_place_names(runtime, photos, server.pace())
    assert not asked
    assert len(server.asked) == 2


def test_always_needs_no_question_and_a_place_of_the_user_is_not_sent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`always`: no question; the Eiffel Tower inside a place of the user: not sent."""
    eiffel = {"name": "Trip", "latitude": _EIFFEL[0], "longitude": _EIFFEL[1]}
    locations = make_locations(tmp_path)
    locations.cache_dir.mkdir(parents=True, exist_ok=True)
    layer: dict[str, dict[str, object]] = {
        "places": {"reverse_lookup": "always"},
        "classify": {"places": [eiffel]},
    }
    runtime = make_runtime(locations, layer)
    server = _FakeServer()
    asked = _answer(monkeypatch, yes=False)
    offer_place_names(runtime, _photos(tmp_path), server.pace())
    assert not asked
    assert len(server.asked) == 1
    assert "lat=50.633" in server.asked[0]


def test_an_unreachable_server_is_said_and_keeps_nothing_wrong(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No network: one line, the spot is not cached (asked again next time)."""
    server, runtime = _FakeServer(down=True), _runtime(tmp_path)
    _answer(monkeypatch, yes=True)
    offer_place_names(runtime, _photos(tmp_path), server.pace())
    assert len(server.asked) == 1
    assert read_names(runtime.locations.cache_dir) == {}


def test_the_slideshow_tells_the_name_found(tmp_path: Path) -> None:
    """A spot named online wins over the landmark and the town."""
    runtime = _runtime(tmp_path)
    (runtime.locations.cache_dir / PLACE_NAMES_FILE).write_text(
        json.dumps({"48.858,2.295": "Tour Eiffel (OSM)"}), "utf-8"
    )
    places = Places(runtime, shared_towns(), [Point(*_EIFFEL)])
    assert places.spot(Point(*_EIFFEL), Chapter(1, "Paris")) == "Tour Eiffel (OSM)"
