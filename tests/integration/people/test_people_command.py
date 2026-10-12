"""`people`: find once, group, show; --sample, --path, --forget, refusals, status."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from typing import TYPE_CHECKING

from tests.support.cli import run

if TYPE_CHECKING:
    import pytest
    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations


def face_rows(locations: Locations) -> int:
    """Count the faces of the index file, straight from SQLite."""
    with closing(sqlite3.connect(locations.cache_dir / "index.sqlite")) as connection:
        return int(connection.execute("SELECT COUNT(*) FROM faces").fetchone()[0])


def flat(text: str) -> str:
    """The output on one line, as the console wraps it."""
    return " ".join(text.split())


def test_find_group_and_show_then_nothing_new(
    cli: CliRunner, apps: list[object], locations: Locations
) -> None:
    """Eight faces of three people; the page shows the two seen more than once."""
    first = run(cli, "people")
    assert first.exit_code == 0, first.output
    output = flat(first.output)
    assert "nothing is sent anywhere" in output
    assert "10 photos of 10 to analyse" in output
    assert "10 photos analysed: 8 faces" in output
    assert (
        "8 faces in 10 photos: 2 groups of faces alike, the largest 4, 3; 1 seen once"
        in output
    )
    assert "Faces ready, open http://127.0.0.1:8766/" in output
    assert "Page stopped; nothing was changed." in output
    assert face_rows(locations) == 8
    again = run(cli, "people")
    assert "to analyse" not in flat(again.output)
    assert len(apps) == 2
    status = flat(run(cli, "status").output)
    assert "Faces: 8 found in 10 photos; 'people' groups them." in status


def test_sample_then_a_full_run_goes_on(cli: CliRunner, apps: list[object]) -> None:
    """--sample analyses a few, tells the rest, and serves no page."""
    sample = flat(run(cli, "people", "--sample", "3").output)
    assert "3 photos analysed" in sample
    assert "A full run would analyse 7 more photos" in sample
    assert apps == []
    rest = flat(run(cli, "people").output)
    assert "7 photos of 10 to analyse" in rest
    done = flat(run(cli, "people", "--sample", "2").output)
    assert "No photo left to analyse" in done


def test_path_limits_the_photos(
    cli: CliRunner, apps: list[object], locations: Locations
) -> None:
    """--path analyses the photos below one folder only."""
    host = locations.data_dir / "c" / "Family"
    result = run(cli, "people", "--path", str(host))
    assert result.exit_code == 0, result.output
    assert "5 photos analysed" in flat(result.output)
    nowhere = run(cli, "people", "--path", str(locations.data_dir / "c" / "None"))
    assert "No photo of the index below these folders" in flat(nowhere.output)
    assert len(apps) == 1


def test_forget_deletes_every_face_and_proves_it(
    cli: CliRunner, apps: list[object], locations: Locations
) -> None:
    """--forget leaves no face, read back from the index."""
    run(cli, "people")
    forgotten = flat(run(cli, "people", "--forget").output)
    assert "8 faces forgotten." in forgotten
    assert "Read back from the index: 0 faces left." in forgotten
    assert face_rows(locations) == 0
    assert "Faces:" not in flat(run(cli, "status").output)
    assert len(apps) == 1


def test_strict_settings_leave_every_face_out(
    cli: CliRunner, apps: list[object], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Faces too small are said and never grouped: no page."""
    monkeypatch.setenv("MEDIA_HYGIENE_PEOPLE__MIN_FACE", "100")
    output = flat(run(cli, "people").output)
    assert "Left out: 8 faces smaller than 100 pixels, 0 blurrier than 30." in output
    assert "no two of them look alike enough to be grouped" in output
    assert apps == []


def test_photos_of_folders_not_mounted_are_left_aside(
    cli: CliRunner, apps: list[object], locations: Locations
) -> None:
    """Photos of the index whose folder is gone are said absent, never undecodable."""
    family = locations.data_dir / "c" / "Family"
    for picture in family.iterdir():
        picture.unlink()
    family.rmdir()
    output = flat(run(cli, "people").output)
    assert "5 photos of the index are not in the mounted folders: left aside" in output
    assert "5 photos of 5 to analyse" in output
    assert "could not be decoded" not in output
    assert len(apps) == 1


def test_faces_of_photos_not_mounted_are_not_shown(
    cli: CliRunner, apps: list[object], locations: Locations
) -> None:
    """Faces of an earlier run stay in the index; the page shows those it can cut."""
    run(cli, "people")
    family = locations.data_dir / "c" / "Family"
    for picture in family.iterdir():
        picture.unlink()
    family.rmdir()
    output = flat(run(cli, "people").output)
    assert "5 photos of the index are not in the mounted folders" in output
    assert "4 faces in 5 photos: 2 groups of faces alike" in output
    assert face_rows(locations) == 8
    assert len(apps) == 2
