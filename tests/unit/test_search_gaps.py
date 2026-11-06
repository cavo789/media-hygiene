"""0531, 0553: a day given to a group, read back from its sidecars; my places."""

from __future__ import annotations

import asyncio
import json
import sqlite3
import tomllib
from contextlib import closing
from datetime import date
from http import HTTPStatus
from pathlib import Path
from typing import TYPE_CHECKING, cast

from media_hygiene.actions.xmp_write import XmpJob
from media_hygiene.config.classify_places import PersonalPlace
from media_hygiene.geo.point import Point
from media_hygiene.index.schema import prepare
from media_hygiene.paths.host_paths import HostPathMapper
from media_hygiene.places.config_file import PlaceEdit, save_places
from media_hygiene.search import tag_cap
from media_hygiene.search.date_desk import DateDesk
from media_hygiene.search.date_propose import folder_day, proposals
from media_hygiene.search.hand_index import HandIndex
from media_hygiene.search.place_book import PlaceBook
from media_hygiene.search.place_desk import PlaceDesk
from media_hygiene.search.place_neighbours import among, neighbours
from media_hygiene.search.query import Filters, Order, SearchQuery
from media_hygiene.search.sidecar_days import days_of, undated_days
from media_hygiene.search.views import SearchAsked
from media_hygiene.services.date_sidecars import DateJobs, DatesWritten
from media_hygiene.tags.xmp_date import sidecar_day, with_day

if TYPE_CHECKING:
    import pytest

    from media_hygiene.services.date_sidecars import DateWriter

_TOOL = "media-hygiene 9.9"
_THEIRS = (
    b'<x:xmpmeta xmlns:x="adobe:ns:meta/"><rdf:RDF'
    b' xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'
    b'<rdf:Description xmlns:photoshop="http://ns.adobe.com/photoshop/1.0/"'
    b' photoshop:DateCreated="2001-02-03T10:00:00"/></rdf:RDF></x:xmpmeta>'
)


def _index(tmp_path: Path) -> tuple[HandIndex, Path]:
    """Three photos of `2019-07 Trip`, two undated; one at Durbuy."""
    folder = tmp_path / "2019-07 Trip"
    folder.mkdir()
    file = tmp_path / "index.sqlite"
    with closing(sqlite3.connect(file)) as connection:
        prepare(connection)
        for rank, (name, taken) in enumerate(
            (("a1.jpg", None), ("a2.jpg", "2019:07:14 10:00:00"), ("a3.jpg", None)),
            start=1,
        ):
            path = folder / name
            path.write_bytes(name.encode())
            connection.execute(
                "INSERT INTO files (rowid, path, size, mtime_ns, media_date,"
                " full_digest, partial_digest) VALUES (?, ?, ?, 1, ?, ?, '')",
                (rank, str(path), len(name), taken, f"{rank:x}" * 64),
            )
        connection.commit()
    return HandIndex.open(file), folder


class _Writer:
    """The sidecars written, without a journal or a mount check."""

    def ensure_ready(self) -> None:
        """Nothing to refuse here."""

    def jobs(self, photos: tuple[Path, ...], day: str) -> DateJobs:
        """Decide as the real writer does, without its settings."""
        written = []
        for photo in photos:
            sidecar = photo.with_name(photo.name + ".xmp")
            previous = sidecar.read_bytes() if sidecar.is_file() else None
            content = with_day(previous, day, _TOOL)
            assert content is not None
            written.append(XmpJob(photo, sidecar, content, previous))
        return DateJobs(tuple(written))

    def write(self, asked: DateJobs) -> DatesWritten:
        """Write them; no run."""
        for job in asked.jobs:
            job.sidecar.write_bytes(job.content)
        return DatesWritten("", 0, asked)


def _desk(index: HandIndex, tmp_path: Path) -> DateDesk:
    """The desk, nothing set aside."""
    writer = cast("DateWriter", _Writer())
    return DateDesk(index, HostPathMapper(tmp_path), writer, frozenset)


def _undated(index: HandIndex) -> tuple[int, list[str]]:
    """The filter's count, and the names found."""
    query = SearchQuery((), Filters(undated=True, order=Order.NAME))
    found = index.find(query, 10)
    return found.total, [hit.photo.path.name for hit in found.hits]


def test_a_day_set_on_a_group_is_read_back_and_the_count_drops(tmp_path: Path) -> None:
    """Done when of 0531: read from the sidecars, shown on the hit, the filter drops."""
    index, folder = _index(tmp_path)
    assert _undated(index) == (2, ["a1.jpg", "a3.jpg"])
    desk = _desk(index, tmp_path)
    body = json.dumps({"action": "set", "keys": [1], "day": "2019-07-15"}).encode()
    answer = asyncio.run(desk.answer(body))
    assert answer.status is HTTPStatus.OK
    assert json.loads(answer.body)["count"] == 1
    assert (folder / "a1.jpg").read_bytes() == b"a1.jpg"  # never the photo
    assert sidecar_day((folder / "a1.jpg.xmp").read_bytes()) == "2019-07-15"
    assert _undated(index) == (1, ["a3.jpg"])
    hit = index.find(SearchQuery((), Filters(order=Order.NAME)), 1).hits[0]
    assert hit.date == "2019-07-15"
    within = Filters(days=(date(2019, 7, 15), date(2019, 7, 15)))
    assert index.find(SearchQuery((), within), 5).total == 1
    index.connection.close()


def test_the_days_are_those_of_the_disk(tmp_path: Path) -> None:
    """A sidecar there gives its day at each reading; once gone (`undo`): undated."""
    index, folder = _index(tmp_path)
    sidecar = folder / "a1.jpg.xmp"
    sidecar.write_bytes(cast("bytes", with_day(None, "2019-07-15", _TOOL)))
    photo = folder / "a1.jpg"
    assert undated_days(index.connection) == {photo: "2019-07-15"}
    moved = tmp_path / "moved"  # `sort`, or Explorer: the sidecar goes with the photo
    moved.mkdir()
    index.connection.close()
    assert not days_of((moved / "a1.jpg",))
    photo.rename(moved / "a1.jpg")
    sidecar.rename(moved / "a1.jpg.xmp")
    assert days_of((moved / "a1.jpg",)) == {moved / "a1.jpg": "2019-07-15"}
    (moved / "a1.jpg.xmp").unlink()  # `undo`
    assert not days_of((moved / "a1.jpg",))


def test_an_own_date_and_another_application_s_date_are_kept(tmp_path: Path) -> None:
    """A file dated by itself is left; another application's date is never replaced."""
    index, folder = _index(tmp_path)
    desk = _desk(index, tmp_path)
    body = json.dumps({"action": "set", "keys": [2], "day": "2020-01-01"}).encode()
    told = json.loads(asyncio.run(desk.answer(body)).body)
    assert told["count"] == 0
    assert not (folder / "a2.jpg.xmp").exists()
    assert with_day(_THEIRS, "2020-01-01", _TOOL) is None
    assert sidecar_day(_THEIRS) == "2001-02-03"
    ours = cast("bytes", with_day(None, "2020-01-01", _TOOL))
    assert (
        sidecar_day(cast("bytes", with_day(ours, "2020-01-02", _TOOL))) == "2020-01-02"
    )
    index.connection.close()


def test_the_days_proposed(tmp_path: Path) -> None:
    """The folder's name first, then the neighbours; a body refused."""
    index, folder = _index(tmp_path)
    assert folder_day(folder) == "2019-07-01"
    assert folder_day(Path("/data/Photos/misc")) is None
    assert folder_day(Path("/data/20190714 feast")) == "2019-07-14"
    days = proposals(index.connection, (folder / "a3.jpg",))
    assert days == ["2019-07-01", "2019-07-14"]
    desk = _desk(index, tmp_path)
    asked = json.dumps({"action": "propose", "keys": [3]}).encode()
    assert json.loads(asyncio.run(desk.answer(asked)).body)["days"] == days
    assert asyncio.run(desk.answer(b"{")).status is HTTPStatus.BAD_REQUEST
    index.connection.close()


def test_the_page_s_fields_reach_the_query() -> None:
    """*Without a date* is a filter of the query, so *Pick all N found* keeps it."""
    assert SearchAsked(missing="date").query().filters.undated
    assert not SearchAsked(missing="place").query().filters.undated


def _places(tmp_path: Path, index: HandIndex, folder: Path) -> PlaceDesk:
    """Durbuy holds a2 by its GPS; a3 is elsewhere; a1 has no position."""
    config = tmp_path / "config.toml"
    durbuy = PersonalPlace(name="Durbuy", latitude=50.35, longitude=5.45, radius_m=500)
    save_places(config, [PlaceEdit(None, durbuy)])
    points = {folder / "a2.jpg": Point(50.35, 5.45), folder / "a3.jpg": Point(1.0, 1.0)}
    book = PlaceBook(index.connection, config, lambda: points)
    return PlaceDesk(index, HostPathMapper(tmp_path), book, True, frozenset)  # noqa: FBT003


def _names(desk: PlaceDesk, place: str, *, unplaced: bool) -> list[str]:
    """The names a search narrowed so finds."""
    index = desk.index
    query = desk.narrow(SearchQuery(()), place, unplaced=unplaced)
    return sorted(hit.photo.path.name for hit in index.find(query, 10).hits)


def test_the_place_filter_lists_by_gps_and_by_hand(tmp_path: Path) -> None:
    """Counts, filter, the file read back, a photo by its GPS never written."""
    index, folder = _index(tmp_path)
    desk = _places(tmp_path, index, folder)
    listed = json.loads(desk.answer(b"{}").body)
    assert listed["places"] == [{"name": "Durbuy", "count": 1}]
    assert _names(desk, "durbuy", unplaced=False) == ["a2.jpg"]
    assert _names(desk, "", unplaced=True) == ["a1.jpg"]
    body = {"action": "give", "keys": [1, 2], "place": "DURBUY"}
    told = json.loads(desk.answer(json.dumps(body).encode()).body)
    assert "1 " in told["saved"]
    assert told["places"] == [{"name": "Durbuy", "count": 2}]
    linked = tomllib.loads((tmp_path / "places" / "Durbuy.toml").read_text("utf-8"))
    assert [Path(p["path"]).name for p in linked["photos"]] == ["a1.jpg"]
    assert _names(desk, "Durbuy", unplaced=False) == ["a1.jpg", "a2.jpg"]
    assert _names(desk, "", unplaced=True) == []
    index.connection.close()


def test_a_place_refused(tmp_path: Path) -> None:
    """An unknown place, a read-only `/config`, a bad body."""
    index, folder = _index(tmp_path)
    desk = _places(tmp_path, index, folder)
    body = json.dumps({"action": "give", "keys": [1], "place": "Nowhere"}).encode()
    assert desk.answer(body).status is not HTTPStatus.OK
    assert desk.answer(b"{").status is HTTPStatus.BAD_REQUEST
    closed = PlaceDesk(index, desk.mapper, desk.book, False, frozenset)  # noqa: FBT003
    good = json.dumps({"action": "give", "keys": [1], "place": "Durbuy"}).encode()
    assert closed.answer(good).status is HTTPStatus.CONFLICT
    index.connection.close()


def _neighbours_index(tmp_path: Path) -> tuple[HandIndex, Path]:
    """`a1`-`a3` of one day and folder (`a3` by its sidecar), `b` another day."""
    folder = tmp_path / "Trip"
    folder.mkdir()
    day = "2019:07:14 10:00:00"
    rows = (("a1.jpg", day), ("a2.jpg", day), ("a3.jpg", None), ("b.jpg", "2019:07:15"))
    file = tmp_path / "index.sqlite"
    with closing(sqlite3.connect(file)) as connection:
        prepare(connection)
        for rank, (name, taken) in enumerate(rows, start=1):
            path = folder / name
            path.write_bytes(name.encode())
            connection.execute(
                "INSERT INTO files (rowid, path, size, mtime_ns, media_date,"
                " full_digest, partial_digest) VALUES (?, ?, ?, 1, ?, ?, '')",
                (rank, str(path), len(name), taken, f"{rank:x}" * 64),
            )
        connection.commit()
    content = with_day(None, "2019-07-14", _TOOL)
    assert content is not None
    (folder / "a3.jpg.xmp").write_bytes(content)
    return HandIndex.open(file), folder


def test_the_same_day_and_folder_only_never_placed_nor_set_aside(
    tmp_path: Path,
) -> None:
    """0554: named, not written; a located, placed or undated one is not proposed."""
    index, folder = _neighbours_index(tmp_path)
    connection = index.connection
    given = [folder / "a1.jpg"]
    assert neighbours(connection, given, frozenset(given)) == {
        folder / "a2.jpg": 2,
        folder / "a3.jpg": 3,
    }
    out = frozenset({*given, folder / "a2.jpg"})
    assert neighbours(connection, given, out) == {folder / "a3.jpg": 3}
    (folder / "a3.jpg.xmp").unlink()
    assert not neighbours(connection, [folder / "a3.jpg"], frozenset())
    connection.close()


def test_the_answer_offers_them_and_writes_only_those_given(tmp_path: Path) -> None:
    """The give names the others; the file holds the photo picked, then the Yes."""
    index, folder = _index(tmp_path)  # a1, a3 undated: their day by the sidecars
    config = tmp_path / "config.toml"
    durbuy = PersonalPlace(name="Durbuy", latitude=50.35, longitude=5.45, radius_m=500)
    save_places(config, [PlaceEdit(None, durbuy)])
    points = {folder / "a2.jpg": Point(50.35, 5.45)}
    book = PlaceBook(index.connection, config, lambda: points)
    desk = PlaceDesk(index, HostPathMapper(tmp_path), book, True, frozenset)  # noqa: FBT003
    content = with_day(None, "2019-07-14", _TOOL)
    assert content is not None
    (folder / "a1.jpg.xmp").write_bytes(content)
    (folder / "a3.jpg.xmp").write_bytes(content)
    body = {"action": "give", "keys": [1], "place": "Durbuy"}
    told = json.loads(desk.answer(json.dumps(body).encode()).body)
    assert told["near"] == [3]  # a2 lies in Durbuy by its GPS
    linked = tomllib.loads((tmp_path / "places" / "Durbuy.toml").read_text("utf-8"))
    assert [Path(p["path"]).name for p in linked["photos"]] == ["a1.jpg"]
    aside = PlaceDesk(
        index, desk.mapper, desk.book, True,  # noqa: FBT003
        lambda: frozenset({desk.mapper.to_host(folder / "a3.jpg")}),
    )  # fmt: skip
    body["keys"] = [2]
    assert json.loads(aside.answer(json.dumps(body).encode()).body)["near"] == []
    index.connection.close()


def test_a_search_among_the_keys_lists_them_alone(tmp_path: Path) -> None:
    """The tiles of the offer: these photos, whatever else is in the index."""
    index, folder = _index(tmp_path)
    query = among(index, SearchQuery((), Filters(order=Order.NAME)), (1, 3))
    assert [hit.photo.path for hit in index.find(query, 10).hits] == [
        folder / "a1.jpg",
        folder / "a3.jpg",
    ]
    index.connection.close()


def test_a_place_over_the_cap_of_unread_photos_is_refused_at_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """0571: the place given by hand refuses as Tag does, saying how many."""
    index, folder = _index(tmp_path)
    desk = _places(tmp_path, index, folder)
    monkeypatch.setattr(tag_cap, "MOST_UNREAD", 0)
    with closing(sqlite3.connect(tmp_path / "index.sqlite")) as writer:
        writer.execute("UPDATE files SET full_digest = '' WHERE rowid = 1")
        writer.commit()
    body = json.dumps({"action": "give", "keys": [1], "place": "Durbuy"}).encode()
    answer = desk.answer(body)
    assert answer.status is HTTPStatus.UNPROCESSABLE_ENTITY
    assert "1 photo not analysed yet" in json.loads(answer.body)["error"]
    assert not (tmp_path / "places" / "Durbuy.toml").exists()
    index.connection.close()
