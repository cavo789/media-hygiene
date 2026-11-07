"""The events and trips other grouping values would make, unsaved (0643, 0646)."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from http import HTTPStatus
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from media_hygiene.classify.engine import Scope, classify
from media_hygiene.classify.grouping_preview import previewed
from media_hygiene.classify.grouping_trips import Tried
from media_hygiene.classify.models import MediaInput
from media_hygiene.config.classify_places import PersonalPlace
from media_hygiene.config.classify_settings import ClassifySettings
from media_hygiene.geo.gazetteer import Gazetteer
from media_hygiene.scan.metadata import MediaMetadata
from media_hygiene.scan.models import VisualFacts
from media_hygiene.search.grouping_desk import GroupingPreview

if TYPE_CHECKING:
    from collections.abc import Mapping

_START = datetime(2024, 5, 1, 10, tzinfo=UTC)
_ROOT = Path("/data/c/Photos")
_HOME = (50.45, 3.95)  # Mons
_FAR = (48.85, 2.35)  # Paris: about 250 km from home
_NEAR = (50.47, 4.87)  # Namur: about 65 km from home


def _file(
    number: int, hours: float, place: tuple[float, float] | None = None
) -> MediaInput:
    """A photo taken that many hours after the start."""
    taken = (_START + timedelta(hours=hours)).strftime("%Y:%m:%d %H:%M:%S")
    return MediaInput(
        path=_ROOT / f"p{number:03d}.jpg",
        root=_ROOT,
        size=10,
        mtime_ns=1,
        visual=VisualFacts(0, 0, 10, 10, 1.0, taken_at=taken),
        metadata=(
            MediaMetadata(latitude=place[0], longitude=place[1]) if place else None
        ),
    )


def _settings(**values: float) -> ClassifySettings:
    """`[classify]` with a home, the session gap short."""
    home = PersonalPlace(name="Home", latitude=_HOME[0], longitude=_HOME[1], home=True)
    return ClassifySettings(
        session_gap_hours=4,
        places=(home,),
        **values,  # type: ignore[arg-type]
    )


def _preview(
    files: list[MediaInput], now: ClassifySettings, asked: ClassifySettings
) -> Mapping[str, object]:
    """The preview, the towns loaded."""
    return previewed(files, Tried(now, asked), Scope(towns=Gazetteer.load()))


def _hours(*hours: float) -> list[MediaInput]:
    """Photos without a position."""
    return [_file(number, hour) for number, hour in enumerate(hours)]


def test_events_follow_the_gap_and_the_minimum() -> None:
    """A longer gap merges, a shorter one splits, the minimum decides."""
    files = _hours(0, 1, 2, 30, 31, 32, 100, 101)
    now = _settings(merge_gap_hours=12, min_event_size=3)
    merged = _preview(files, now, _settings(merge_gap_hours=48, min_event_size=3))
    assert merged["before"] == {"events": 2, "files": 6}
    assert merged["after"] == {"events": 1, "files": 6}
    assert merged["merged"] == {
        "count": 1,
        "listed": [
            {
                "first": _START.replace(tzinfo=None).isoformat(),
                "last": (_START + timedelta(hours=32)).replace(tzinfo=None).isoformat(),
                "files": 6,
                "parts": 2,
            }
        ],
    }
    split = _preview(files, _settings(merge_gap_hours=48, min_event_size=3), now)
    assert split["split"]["count"] == 1  # type: ignore[index]
    smaller = _preview(files, now, _settings(merge_gap_hours=12, min_event_size=2))
    assert smaller["new"]["count"] == 1  # type: ignore[index]
    larger = _preview(files, now, _settings(merge_gap_hours=12, min_event_size=4))
    assert larger["gone"]["count"] == 2  # type: ignore[index]


def test_trips_appear_and_go_with_the_distance() -> None:
    """A trip shorter than the distance asked goes; a longer one stays."""
    files = [
        *(_file(number, number, _FAR) for number in range(3)),
        *(_file(number + 10, 200 + number, _NEAR) for number in range(3)),
    ]
    now = _settings(merge_gap_hours=12, min_event_size=3, trip_min_km=100)
    wider = _settings(merge_gap_hours=12, min_event_size=3, trip_min_km=50)
    longer = _preview(files, now, wider)["trips"]
    assert longer["known"] is True  # type: ignore[index]
    assert (longer["before"], longer["after"]) == (1, 2)  # type: ignore[index]
    new = longer["new"]  # type: ignore[index]
    assert new["count"] == 1
    assert new["listed"][0]["files"] == 3
    assert new["listed"][0]["town"]
    gone = _preview(files, wider, now)["trips"]["gone"]  # type: ignore[index]
    assert gone["count"] == 1


def test_no_trips_without_a_home_or_a_rule() -> None:
    """Trips need a home and the towns of a `trip` rule: the answer says so."""
    files = _hours(0, 1, 2)
    settings = _settings(merge_gap_hours=12, min_event_size=3)
    answer = previewed(files, Tried(settings, settings), Scope())
    assert answer["trips"] == {"known": False}


def test_the_preview_counts_what_classify_groups() -> None:
    """Undated-by-EXIF files, received pictures: the same events as the real run."""
    files = [
        *_hours(0, 1, 2, 30, 31),
        MediaInput(
            path=_ROOT / "IMG-20240501-WA0003.jpg", root=_ROOT, size=1, mtime_ns=1
        ),
        MediaInput(path=_ROOT / "no-date.jpg", root=_ROOT, size=1, mtime_ns=1),
    ]
    settings = _settings(merge_gap_hours=8, min_event_size=2)
    answer = previewed(files, Tried(settings, settings), Scope())
    real = classify(files, settings, Scope()).events
    assert answer["after"] == {
        "events": len(real),
        "files": sum(len(event.paths) for event in real),
    }


@pytest.fixture
def desk(tmp_path: Path) -> GroupingPreview:
    """A desk over `[classify]` written, comparing nothing but its arguments."""
    config = tmp_path / "config.toml"
    config.write_text(
        "[classify]\nmerge_gap_hours = 4.0\nmin_event_size = 2\n", encoding="utf-8"
    )
    return GroupingPreview(config, lambda now, asked: {"now": now, "asked": asked})


def test_the_route_compares_without_writing(desk: GroupingPreview) -> None:
    """The kept values against the typed ones; the file untouched."""
    before = desk.config_file.read_bytes()
    body = {"merge_gap_hours": 48.0, "min_event_size": 2, "trip_min_km": 100.0}
    answer = desk.answer(json.dumps(body).encode())
    assert answer.status == HTTPStatus.OK
    shown = json.loads(answer.body)
    assert shown["asked"] == body
    assert shown["now"]["merge_gap_hours"] == pytest.approx(4.0)
    assert desk.config_file.read_bytes() == before


def test_the_route_refuses_what_the_save_would(desk: GroupingPreview) -> None:
    """A body the save would refuse is refused here too."""
    for body in (
        b"[]",
        b"{}",
        b"not json",
        json.dumps(
            {"merge_gap_hours": -1, "min_event_size": 2, "trip_min_km": 100}
        ).encode(),
    ):
        assert desk.answer(body).status == HTTPStatus.BAD_REQUEST
