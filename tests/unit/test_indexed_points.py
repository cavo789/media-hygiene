"""The library's positions: the file's own, else its Takeout `.json`'s, never 0, 0."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, cast

from media_hygiene.geo.distance import Point
from media_hygiene.scan.metadata import MediaMetadata
from media_hygiene.scan.takeout_facts import TakeoutFacts
from media_hygiene.services import indexed_points as module

if TYPE_CHECKING:
    import sqlite3

    import pytest

_PARIS = (48.85, 2.35)
_LYON = (45.76, 4.84)


def _gps(latitude: float, longitude: float) -> MediaMetadata:
    return MediaMetadata(latitude=latitude, longitude=longitude)


def _takeout(latitude: float | None, longitude: float | None) -> TakeoutFacts:
    return TakeoutFacts(None, latitude, longitude, "")


def test_own_position_first_then_the_takeout_one(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Each case of `with_takeout` then `located_point`, in one pass."""
    files = {
        "own.jpg": _gps(*_PARIS),  # its GPS, though a .json says Lyon
        "zero.jpg": _gps(0, 0),  # a receiver without a fix: the .json is not read
        "takeout.jpg": None,  # no GPS: the .json's position
        "takeout_zero.jpg": None,  # the .json at 0, 0: nowhere
        "takeout_none.jpg": MediaMetadata(),  # the .json without a position
        "nothing.jpg": None,  # no GPS, no .json
    }
    takeouts = {
        Path("own.jpg"): _takeout(*_LYON),
        Path("zero.jpg"): _takeout(*_LYON),
        Path("takeout.jpg"): _takeout(*_LYON),
        Path("takeout_zero.jpg"): _takeout(0, 0),
        Path("takeout_none.jpg"): _takeout(None, None),
    }
    rows = [
        SimpleNamespace(path=Path(name), facts=SimpleNamespace(metadata=metadata))
        for name, metadata in files.items()
    ]
    monkeypatch.setattr(module, "indexed_files", lambda _connection: iter(rows))
    monkeypatch.setattr(module, "takeout_facts", lambda _connection: takeouts)
    points = module.indexed_points(cast("sqlite3.Connection", None))
    assert points == {
        Path("own.jpg"): Point(*_PARIS),
        Path("takeout.jpg"): Point(*_LYON),
    }
