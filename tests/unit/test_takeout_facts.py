"""What a Takeout `.json` says, kept in the index, used for dates and places (0217)."""

from __future__ import annotations

import json
import os
import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from media_hygiene.actions.sort_names import SourceSidecars, owners
from media_hygiene.actions.sort_plan import Move, MoveGroup
from media_hygiene.classify.dates import takeout_date
from media_hygiene.classify.models import Band, MediaInput
from media_hygiene.constants import MediaKind
from media_hygiene.index.schema import prepare
from media_hygiene.index.takeout_rows import (
    remember_takeout,
    takeout_facts,
    takeout_of,
)
from media_hygiene.plan.keeper import KeepPolicy
from media_hygiene.plan.near import near_decisions
from media_hygiene.scan.metadata import MediaMetadata
from media_hygiene.scan.models import MediaFile, VisualFacts
from media_hygiene.scan.sidecars import Sidecar, companions_of, is_sidecar_of
from media_hygiene.scan.takeout_facts import TakeoutFacts, facts_of, read_takeout
from media_hygiene.services.classify_inputs import with_takeout

_STAMP = 1_560_340_800  # 2019-06-12 12:00:00 UTC
_HASH = 0x0F0F_3C3C_5A5A_6969


def listed(path: Path, kind: MediaKind = MediaKind.IMAGE) -> MediaFile:
    """The file as the walk lists it."""
    stat = path.stat()
    return MediaFile(path, stat.st_size, stat.st_mtime_ns, kind)


def write(path: Path, document: object) -> Path:
    """Write a `.json` document."""
    path.write_text(json.dumps(document), encoding="utf-8")
    return path


@pytest.mark.parametrize(
    ("document", "expected"),
    [
        (
            {
                "photoTakenTime": {"timestamp": str(_STAMP)},
                "geoData": {"latitude": 50.5, "longitude": 4.25},
                "description": " Plage ",
            },
            TakeoutFacts(_STAMP, 50.5, 4.25, "Plage"),
        ),
        (
            {"photoTakenTime": {"timestamp": _STAMP}, "description": ""},
            TakeoutFacts(_STAMP),
        ),
        ({"geoData": {"latitude": 0.0, "longitude": 0.0}}, TakeoutFacts()),
        (
            {"geoData": {"latitude": 0.0, "longitude": 12.5}},
            TakeoutFacts(None, 0.0, 12.5),
        ),
        ({"geoData": {"latitude": 91, "longitude": 4}}, TakeoutFacts()),
        ({"geoData": {"latitude": True, "longitude": 4}}, TakeoutFacts()),
        ({"photoTakenTime": {"timestamp": "soon"}}, TakeoutFacts()),
        ({"photoTakenTime": {"timestamp": "0"}}, TakeoutFacts()),
        ({"photoTakenTime": "2019", "geoData": []}, TakeoutFacts()),
    ],
)
def test_fields(document: dict[str, object], expected: TakeoutFacts) -> None:
    """Date, place and description; odd or unknown values are left out."""
    assert facts_of(document) == expected


def test_reading(tmp_path: Path) -> None:
    """A file that is no Takeout document, or cannot be read, gives nothing."""
    assert read_takeout(write(tmp_path / "a.json", {"description": "x"})) == (
        TakeoutFacts(description="x")
    )
    assert read_takeout(write(tmp_path / "b.json", [1, 2])) is None
    (tmp_path / "c.json").write_text("{not json", encoding="utf-8")
    assert read_takeout(tmp_path / "c.json") is None
    assert read_takeout(tmp_path / "missing.json") is None
    big = tmp_path / "big.json"
    big.write_text(" " * 1_000_001, encoding="utf-8")
    assert read_takeout(big) is None


def test_dates_in_local_time() -> None:
    """Unix seconds become the photo's local time; none, odd or too old: no date."""
    brussels = datetime(2019, 6, 12, 14)  # noqa: DTZ001 - naive local time
    assert takeout_date(_STAMP, ZoneInfo("Europe/Brussels")) == brussels
    assert takeout_date(None, UTC) is None
    assert takeout_date(86_400, UTC) is None
    assert takeout_date(10**20, UTC) is None


def test_rows_follow_each_version(tmp_path: Path) -> None:
    """Read once per version; forgotten when the `.json` goes or is no document."""
    photo = tmp_path / "IMG_1.jpg"
    photo.write_bytes(b"jpeg")
    sidecar_path = write(
        tmp_path / "IMG_1.jpg.json", {"photoTakenTime": {"timestamp": str(_STAMP)}}
    )
    sidecar = Sidecar(listed(sidecar_path, MediaKind.SIDECAR), frozenset({photo.name}))
    with closing(sqlite3.connect(":memory:")) as connection:
        prepare(connection)
        assert remember_takeout(connection, [sidecar], [photo]) == 1
        assert takeout_of(connection, photo) == TakeoutFacts(_STAMP)
        assert remember_takeout(connection, [sidecar], [photo]) == 0
        write(sidecar_path, {"description": "Mer"})
        os.utime(sidecar_path, ns=(1, 1))
        changed = Sidecar(listed(sidecar_path, MediaKind.SIDECAR), sidecar.companions)
        assert remember_takeout(connection, [changed], [photo]) == 1
        assert takeout_facts(connection) == {photo: TakeoutFacts(description="Mer")}
        sidecar_path.write_text("[]", encoding="utf-8")
        broken = Sidecar(listed(sidecar_path, MediaKind.SIDECAR), sidecar.companions)
        remember_takeout(connection, [broken], [photo])
        assert takeout_of(connection, photo) is None
        remember_takeout(connection, [changed], [photo])
        remember_takeout(connection, [], [photo])
        assert takeout_of(connection, photo) is None


def test_position_stands_for_a_missing_gps() -> None:
    """The `.json` place fills a file without GPS; a file's own GPS stays."""
    bare = MediaInput(Path("/data/c/a.png"), Path("/data/c"), 1, 1)
    facts = TakeoutFacts(_STAMP, 50.5, 4.25)
    completed = with_takeout(bare, facts)
    assert completed.takeout == facts
    assert completed.metadata is not None
    assert (completed.metadata.latitude, completed.metadata.longitude) == (50.5, 4.25)
    own = MediaMetadata(latitude=1.0, longitude=2.0)
    located = with_takeout(MediaInput(bare.path, bare.root, 1, 1, metadata=own), facts)
    assert located.metadata == own
    assert with_takeout(bare, None) is bare


def test_sidecar_recognition(tmp_path: Path) -> None:
    """A `.json` is a sidecar only when it describes a file of its folder."""
    names = ["IMG_1.jpg", "IMG_1.jpg.json", "IMG_1.xmp", "notes.json"]
    assert is_sidecar_of("IMG_1.jpg.json", names)
    assert is_sidecar_of("IMG_1.xmp", names)
    assert not is_sidecar_of("notes.json", names)
    assert not is_sidecar_of("IMG_1.jpg", names)
    assert companions_of(tmp_path / "IMG_1.jpg.json", names) == {"IMG_1.jpg"}


def test_sort_carries_the_json(tmp_path: Path) -> None:
    """`sort` hands the `.json` to its photo's group once, the original first."""
    for name in ("IMG_1.jpg", "IMG_1-edited.jpg", "IMG_1.jpg.json", "x.json"):
        (tmp_path / name).write_bytes(b"x")
    assert owners("IMG_1.jpg.json", ["IMG_1.jpg", "IMG_1-edited.jpg"]) == [
        "IMG_1-edited.jpg",
        "IMG_1.jpg",
    ]
    sidecars = SourceSidecars()
    out = tmp_path / "out"
    edited = MoveGroup(out, out, (_move(tmp_path / "IMG_1-edited.jpg"),))
    original = MoveGroup(out, out, (_move(tmp_path / "IMG_1.jpg"),))
    assert sidecars.take(edited) == []
    assert sidecars.take(original) == [tmp_path / "IMG_1.jpg.json"]


def _move(source: Path) -> Move:
    """A move of one file, as `sort` plans it."""
    return Move(source.name, source, 1, 0, Band.SURE)


def test_an_edit_is_never_a_near_duplicate_of_its_original() -> None:
    """`IMG_1-edited.jpg` looks like `IMG_1.jpg`: both stay, as an edit is a choice."""
    data = Path("/data/c")
    files = [
        MediaFile(data / name, 100, 0, MediaKind.IMAGE)
        for name in ("IMG_1.jpg", "IMG_1-edited.jpg")
    ]
    visuals = {
        file.path: VisualFacts(_HASH, _HASH, 400 + index, 300, 100.0)
        for index, file in enumerate(files)
    }
    assert not near_decisions(files, visuals, KeepPolicy())
