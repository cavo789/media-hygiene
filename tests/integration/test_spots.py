"""Each located photo's landmark and town, stored once in the index (0545)."""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from typing import TYPE_CHECKING, Final

import pytest

from media_hygiene.errors import MountError
from media_hygiene.geo.distance import Point
from media_hygiene.geo.towns_once import shared_towns
from media_hygiene.index.schema import MOVE, prepare
from media_hygiene.index.spot_rows import SpotSource, spot_figures, spots_by_key
from media_hygiene.search.fts import SearchIndex
from media_hygiene.search.query import SearchQuery, parse_terms
from media_hygiene.search.spot_label import SpotNames, spot_labels
from media_hygiene.services import slideshow_places, spot_fill
from media_hygiene.services.place_names import PLACE_NAMES_FILE, spot_key
from media_hygiene.services.slideshow_places import Places
from media_hygiene.services.spot_fill import fill_spots
from media_hygiene.services.spot_scan import scan_spots
from media_hygiene.slideshow.chapters import Chapter
from tests.support.runtime import make_locations, make_runtime

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.scan.progress import Step
    from media_hygiene.services.runtime import Runtime

_EIFFEL: Final = (48.8584, 2.2945)
_COLMAR: Final = (48.0815, 7.3550)
_SEA: Final = (45.0, -30.0)
_INSERT: Final = (
    "INSERT INTO files (path, size, mtime_ns, latitude, longitude)"
    " VALUES (?, 1, 1, ?, ?)"
)
_HOME: Final = {
    "name": "Home",
    "latitude": 48.0815,
    "longitude": 7.355,
    "radius_m": 500,
}


class _Sink:
    """Counts the progress reported."""

    def __init__(self) -> None:
        """Nothing reported yet."""
        self.total: int | None = None
        self.done = 0

    def start(self, step: Step, total: int | None) -> None:
        """Keep the total."""
        assert step.title
        self.total = total

    def advance(self, weight: int = 1) -> None:
        """Count."""
        self.done += weight

    def current(self, text: str) -> None:
        """Say something."""
        assert text

    def stop(self) -> None:
        """Nothing to end."""


def _index(runtime: Runtime) -> sqlite3.Connection:
    assert runtime.index_file is not None
    runtime.index_file.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(runtime.index_file)
    prepare(connection)
    return connection


def _located(connection: sqlite3.Connection, **photos: tuple[float, float]) -> None:
    connection.executemany(
        _INSERT, [(f"/data/c/{name}.jpg", *where) for name, where in photos.items()]
    )
    connection.commit()


def _row(connection: sqlite3.Connection, name: str) -> dict[str, str]:
    connection.row_factory = sqlite3.Row
    with closing(connection.cursor()) as cursor:
        row = cursor.execute(
            "SELECT * FROM spots WHERE path = ?", (f"/data/c/{name}.jpg",)
        ).fetchone()
    connection.row_factory = None
    return dict(row) if row else {}


@pytest.fixture
def runtime(tmp_path: Path) -> Runtime:
    """A runtime with its cache."""
    return make_runtime(make_locations(tmp_path))


def test_a_photo_gets_its_landmark_town_and_regions(runtime: Runtime) -> None:
    """Colmar: town, admin1, admin2; the Eiffel Tower by GeoNames; each stored once."""
    with closing(_index(runtime)) as connection:
        _located(connection, eiffel=_EIFFEL, colmar=_COLMAR)
        sink = _Sink()
        assert fill_spots(runtime, connection, sink) == 2
        assert (sink.total, sink.done) == (2, 2)
        eiffel, colmar = _row(connection, "eiffel"), _row(connection, "colmar")
    assert eiffel["landmark"] == "Tour Eiffel"
    assert eiffel["source"] == SpotSource.GEONAMES
    assert eiffel["country"] == "FR"
    assert colmar["town"] == "Colmar"
    assert colmar["region"] == "Grand Est"
    assert colmar["district"] == "Haut-Rhin"
    assert "Haut-Rhin" in colmar["words"]
    assert "Allemagne" not in colmar["words"]


def test_the_second_run_writes_nothing_and_reads_no_snapshot(
    runtime: Runtime, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scanned once: nothing to name, the towns are not even read."""
    with closing(_index(runtime)) as connection:
        _located(connection, eiffel=_EIFFEL)
        fill_spots(runtime, connection, _Sink())

        def never() -> None:
            raise AssertionError

        monkeypatch.setattr(spot_fill, "shared_towns", never)
        assert fill_spots(runtime, connection, _Sink()) == 0


def test_far_from_any_town_no_town_is_named(runtime: Runtime) -> None:
    """Out at sea: past `[tags] town_km`, nothing to search by."""
    with closing(_index(runtime)) as connection:
        _located(connection, sea=_SEA)
        fill_spots(runtime, connection, _Sink())
        sea = _row(connection, "sea")
    assert (sea["town"], sea["words"]) == ("", "")


def test_a_move_keeps_the_row(runtime: Runtime) -> None:
    """`sort`/`undo` (`MOVE`): the row follows, nothing to name again."""
    with closing(_index(runtime)) as connection:
        _located(connection, eiffel=_EIFFEL)
        fill_spots(runtime, connection, _Sink())
        for statement in MOVE:
            connection.execute(statement, ("/data/c/moved.jpg", "/data/c/eiffel.jpg"))
        connection.commit()
        assert _row(connection, "moved")["landmark"] == "Tour Eiffel"
        assert fill_spots(runtime, connection, _Sink()) == 0


def test_a_user_rename_outside_the_tool_names_the_new_path(runtime: Runtime) -> None:
    """Renamed in Explorer: the audit sees a new file, named anew; old row gone."""
    with closing(_index(runtime)) as connection:
        _located(connection, eiffel=_EIFFEL)
        fill_spots(runtime, connection, _Sink())
        connection.execute("DELETE FROM files WHERE path LIKE '%eiffel%'")
        _located(connection, renamed=_EIFFEL)
        assert fill_spots(runtime, connection, _Sink()) == 1
        assert not _row(connection, "eiffel")
        assert _row(connection, "renamed")["landmark"] == "Tour Eiffel"


def test_a_file_rewritten_elsewhere_or_without_gps(runtime: Runtime) -> None:
    """Another position: named again, unseen until then; no position: row dropped."""
    with closing(_index(runtime)) as connection:
        _located(connection, one=_EIFFEL, two=_EIFFEL)
        fill_spots(runtime, connection, _Sink())
        key = connection.execute(
            "SELECT rowid FROM files WHERE path LIKE '%one%'"
        ).fetchone()[0]
        connection.execute(
            "UPDATE files SET latitude = ?, longitude = ? WHERE path LIKE '%one%'",
            _COLMAR,
        )
        assert spots_by_key(connection, json.dumps([key])) == {}  # never the old name
        connection.execute(
            "UPDATE files SET latitude = NULL, longitude = NULL WHERE path LIKE '%two%'"
        )
        assert fill_spots(runtime, connection, _Sink()) == 1
        assert _row(connection, "one")["town"] == "Colmar"
        assert not _row(connection, "two")


def test_a_name_typed_by_hand_is_never_replaced(runtime: Runtime) -> None:
    """Source `user` (0489 writes it): kept when the row is refilled."""
    with closing(_index(runtime)) as connection:
        _located(connection, eiffel=_EIFFEL)
        fill_spots(runtime, connection, _Sink())
        connection.execute(
            "UPDATE spots SET landmark = 'Mine', source = 'user', stamp = 'old'"
        )
        assert fill_spots(runtime, connection, _Sink()) == 1
        eiffel = _row(connection, "eiffel")
    assert (eiffel["landmark"], eiffel["source"]) == ("Mine", "user")
    assert "Mine" in eiffel["words"]


def test_an_online_name_said_yes_to_later_reaches_the_row(runtime: Runtime) -> None:
    """The name kept in the cache beats GeoNames at the next run; nothing is sent."""
    with closing(_index(runtime)) as connection:
        _located(connection, eiffel=_EIFFEL)
        fill_spots(runtime, connection, _Sink())
        names = {spot_key((48.858, 2.295)): "OSM name"}
        (runtime.locations.cache_dir / PLACE_NAMES_FILE).write_text(json.dumps(names))
        written = fill_spots(runtime, connection, _Sink())
        eiffel = _row(connection, "eiffel")
    assert written == 1
    assert (eiffel["landmark"], eiffel["source"]) == ("OSM name", "osm")


def test_search_finds_by_landmark_town_district_not_by_stale_position(
    runtime: Runtime,
) -> None:
    """The words are searchable; `tags` has not run; accents do not matter."""
    with closing(_index(runtime)) as connection:
        _located(connection, eiffel=_EIFFEL, colmar=_COLMAR)
        fill_spots(runtime, connection, _Sink())
    assert runtime.index_file is not None
    with SearchIndex.open(runtime.index_file) as search:
        for words, name in (
            ("tour eiffel", "eiffel"),
            ("colmar", "colmar"),
            ("haut-rhin", "colmar"),
            ("grand est", "colmar"),
        ):
            found = search.find(SearchQuery(parse_terms(words)), 5)
            assert [hit.photo.path.stem for hit in found.hits] == [name]


def test_an_index_older_than_the_rows_still_searches(tmp_path: Path) -> None:
    """Opened read-only before any audit upgraded it: no table, no failure."""
    index = tmp_path / "old.sqlite"
    with closing(sqlite3.connect(index)) as connection:
        prepare(connection)
        connection.execute("DROP TABLE spots")
        connection.commit()
    with SearchIndex.open(index) as search:
        assert search.find(SearchQuery(()), 1).total == 0
        assert spot_labels(search.connection, [1], SpotNames()) == {}


def test_the_label_is_the_user_s_place_else_the_town(runtime: Runtime) -> None:
    """Landmark, then the place; a place drawn today applies; renames at show time."""
    with closing(_index(runtime)) as connection:
        _located(connection, eiffel=_EIFFEL, colmar=_COLMAR)
        fill_spots(runtime, connection, _Sink())
        keys = [
            row[0]
            for row in connection.execute("SELECT rowid FROM files ORDER BY path DESC")
        ]
        plain = spot_labels(connection, keys, SpotNames())
        assert plain[keys[1]] == ("Colmar", "")
        assert "Tour Eiffel" not in plain[keys[0]][0]  # the chip shows it, not the line
        assert plain[keys[0]][0]  # the town stays
        assert plain[keys[0]][1] == "Tour Eiffel"  # the tile's 📍 chip (0651)
        renamed = spot_labels(connection, keys, SpotNames(renames={"Colmar": "Kolmar"}))
        assert renamed[keys[1]][0] == "Kolmar"
        with_home = make_runtime(
            make_locations(runtime.locations.cache_dir.parent),
            {"classify": {"places": [_HOME]}},
        )
        names = SpotNames.of(with_home.settings.classify)
        assert spot_labels(connection, keys, names)[keys[1]][0] == "Home"


def test_the_slideshow_reads_the_row_without_the_landmarks(
    runtime: Runtime, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Stored: the landmarks' snapshot is never read; a missing row still works."""
    called: list[object] = []

    def counting(cells: object) -> object:
        called.append(cells)
        raise AssertionError

    monkeypatch.setattr(slideshow_places, "shared_landmarks", counting)
    with closing(_index(runtime)) as connection:
        _located(connection, eiffel=_EIFFEL)
        fill_spots(runtime, connection, _Sink())
        stored = spots_by_key(connection, "[1]")[1]
    places = Places(runtime, shared_towns(), [Point(*_EIFFEL)])
    event = Chapter(1, "Walk", "", "")
    assert places.spot(Point(*_EIFFEL), event, stored) == "Tour Eiffel"
    assert not called
    with pytest.raises(AssertionError):
        places.spot(Point(*_EIFFEL), event)
    assert called


def test_scan_reads_back_and_refuses_without_an_index(runtime: Runtime) -> None:
    """`spots`: the figures come from the index; no index: a sentence, no traceback."""
    with pytest.raises(MountError):
        scan_spots(runtime, _Sink())
    with closing(_index(runtime)) as connection:
        _located(connection, eiffel=_EIFFEL, colmar=_COLMAR)
    scan = scan_spots(runtime, _Sink())
    assert scan.written == 2
    assert (scan.figures.stored, scan.figures.towns) == (2, 2)
    with closing(sqlite3.connect(str(runtime.index_file))) as connection:
        assert spot_figures(connection).landmarks >= 1
