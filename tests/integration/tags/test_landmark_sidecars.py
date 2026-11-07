"""0649: the landmark typed in the large view: sidecar first, index second, moves."""

from __future__ import annotations

import asyncio
import json
import sqlite3
from contextlib import closing
from typing import TYPE_CHECKING, Final, cast

from media_hygiene.index.schema import MOVE, prepare
from media_hygiene.index.spot_rows import SpotSource
from media_hygiene.search.landmark_desk import LandmarkDesk
from media_hygiene.services.landmark_sidecars import (
    LandmarkWriter,
    sidecar_landmark,
)
from media_hygiene.services.spot_fill import fill_spots
from media_hygiene.tags.xmp_doc import parse
from media_hygiene.tags.xmp_landmark import landmark_in, with_landmark, with_rejected
from media_hygiene.tags.xmp_merge import XmpValues, new_document
from tests.support.cli import run
from tests.support.runtime import make_runtime

if TYPE_CHECKING:
    from pathlib import Path

    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations
    from media_hygiene.search.fts import SearchIndex
    from media_hygiene.services.runtime import Runtime

_EIFFEL: Final = (48.8584, 2.2945)
_TOOL: Final = "media-hygiene test"


class _Version:
    """A file found by its key."""

    def __init__(self, path: Path) -> None:
        self.path = path


class _Index:
    """The two things the desk reads of the search index."""

    def __init__(self, connection: sqlite3.Connection, photo: Path) -> None:
        self.connection = connection
        self._photo = photo

    def source_of(self, key: int) -> _Version | None:
        """The photo, under key 1 only."""
        return _Version(self._photo) if key == 1 else None


class _Sink:
    def start(self, step: object, total: int | None) -> None:
        """Nothing."""

    def advance(self, weight: int = 1) -> None:
        """Nothing."""

    def current(self, text: str) -> None:
        """Nothing."""

    def stop(self) -> None:
        """Nothing."""


def _index(runtime: Runtime, *photos: Path) -> sqlite3.Connection:
    assert runtime.index_file is not None
    runtime.index_file.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(runtime.index_file)
    prepare(connection)
    connection.executemany(
        "INSERT INTO files (path, size, mtime_ns, latitude, longitude)"
        " VALUES (?, 1, 1, ?, ?) ON CONFLICT(path) DO UPDATE"
        " SET latitude = excluded.latitude, longitude = excluded.longitude",
        [(str(photo), *_EIFFEL) for photo in photos],
    )
    connection.commit()
    return connection


def _spot(connection: sqlite3.Connection, photo: Path) -> tuple[str, str]:
    row = connection.execute(
        "SELECT landmark, source FROM spots WHERE path = ?", (str(photo),)
    ).fetchone()
    return (row[0], row[1]) if row else ("", "")


def _sidecar(photo: Path, doc_bytes: bytes) -> None:
    photo.with_name(photo.name + ".xmp").write_bytes(doc_bytes)


def test_xmp_name_ownership_and_rejection() -> None:
    """Ours is written and read back; another's is kept; a rejection takes ours off."""
    doc = with_landmark(None, "Champ de Mars", _TOOL)
    assert doc is not None
    read = landmark_in(parse(doc.to_bytes()))
    assert (read.name, read.ours) == ("Champ de Mars", True)
    theirs = parse(doc.to_bytes().replace(b">Champ de Mars</mh:", b">Ours</mh:"))
    assert with_landmark(theirs, "Other", _TOOL) is None
    rejected = with_rejected(parse(doc.to_bytes()), "champ de mars", _TOOL)
    rejected = with_rejected(rejected, "Champ de Mars", _TOOL)
    read = landmark_in(parse(rejected.to_bytes()))
    assert (read.name, read.rejected) == ("", ("champ de mars",))


def test_written_journaled_read_back_then_undone(
    cli: CliRunner, locations: Locations
) -> None:
    """The desk writes the sidecar, caches it as `user`; `undo` removes the sidecar."""
    photo = next((locations.data_dir / "c" / "Photos" / "DCIM").glob("*.jpg"))
    before = photo.read_bytes()
    runtime = make_runtime(locations)
    with closing(_index(runtime, photo)) as connection:
        desk = LandmarkDesk(
            cast("SearchIndex", _Index(connection, photo)),
            LandmarkWriter(runtime),
            locations.cache_dir,
        )
        body = {"action": "set", "key": 1, "name": "  Champ   de Mars "}
        answer = asyncio.run(desk.answer(json.dumps(body).encode()))
        said = json.loads(answer.body)
        assert said["name"] == "Champ de Mars"
        assert said["run"] in said["saved"]
        assert _spot(connection, photo) == ("Champ de Mars", SpotSource.USER)
        assert sidecar_landmark(photo).name == "Champ de Mars"
        proposed = desk.proposals(photo)
        assert proposed["name"] == "Champ de Mars"
        assert any(each["name"] == "Tour Eiffel" for each in proposed["near"])  # type: ignore[attr-defined]
        undone = run(cli, "undo", said["run"])
    assert undone.exit_code == 0, undone.output
    assert not photo.with_name(photo.name + ".xmp").exists()
    assert photo.read_bytes() == before


def test_a_rejected_name_is_never_proposed_nor_filled(
    locations: Locations, tmp_path: Path
) -> None:
    """Rejected in the sidecar: left out of the proposals and of the audit's row."""
    folder = tmp_path / "pics"
    folder.mkdir()
    photo = folder / "eiffel.jpg"
    photo.write_bytes(b"x")
    _sidecar(photo, with_rejected(None, "Tour Eiffel", _TOOL).to_bytes())
    runtime = make_runtime(locations)
    with closing(_index(runtime, photo)) as connection:
        fill_spots(runtime, connection, _Sink())
        assert _spot(connection, photo) == ("", SpotSource.USER)
        desk = LandmarkDesk(
            cast("SearchIndex", _Index(connection, photo)),
            LandmarkWriter(runtime),
            locations.cache_dir,
        )
        names = [each["name"] for each in desk.proposals(photo)["near"]]  # type: ignore[attr-defined]
    assert "Tour Eiffel" not in names


def test_the_sidecar_wins_after_a_move_or_a_rebuilt_index(
    locations: Locations, tmp_path: Path
) -> None:
    """Explorer rename of the folder, an index rebuilt: the name comes back from XMP."""
    folder = tmp_path / "Paris"
    folder.mkdir()
    photo = folder / "eiffel.jpg"
    photo.write_bytes(b"x")
    doc = with_landmark(new_document(XmpValues(()), _TOOL), "Champ de Mars", _TOOL)
    assert doc is not None
    _sidecar(photo, doc.to_bytes())
    renamed = folder.rename(tmp_path / "Paris 2019") / photo.name
    runtime = make_runtime(locations)
    with closing(_index(runtime, renamed)) as connection:
        fill_spots(runtime, connection, _Sink())
        assert _spot(connection, renamed) == ("Champ de Mars", SpotSource.USER)
        moved = renamed.with_name("sorted.jpg")
        for statement in MOVE:  # `sort` and `undo` move the row with the photo
            connection.execute(statement, (str(moved), str(renamed)))
        connection.commit()
        assert _spot(connection, moved) == ("Champ de Mars", SpotSource.USER)
