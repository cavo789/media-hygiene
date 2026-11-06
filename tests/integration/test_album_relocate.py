"""0582: album link folders follow a changed `[album] root`, undone by `undo`."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from media_hygiene.constants import ALBUM_MARKER
from media_hygiene.places.toml_edit import document_of, table_of, write_document
from media_hygiene.search.album_move_desk import AlbumMoveDesk
from media_hygiene.search.album_root_desk import album_root_desk
from media_hygiene.search.folder_role_desk import RoleDesk
from tests.support.albums import ALBUMS, WEDDING_CATEGORY, saved_album
from tests.support.cli import run
from tests.support.runtime import make_runtime
from tests.support.sorting import PHOTOS

if TYPE_CHECKING:
    from pathlib import Path

    import pytest
    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations

_NEW: str = f"{PHOTOS}/Albums 2"
_NAME: str = "Crete 2023"


def _made(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> Path:
    """A saved album of two photos, its folder of links made in the old root.

    Args:
        cli: The runner.
        locations: The test mount points.
        monkeypatch: Sets `[album] root`.

    Returns:
        The folder of the photos.
    """
    photos = saved_album(cli, locations, monkeypatch, _NAME)
    assert run(cli, "album", _NAME, "--apply").exit_code == 0
    monkeypatch.setenv("MEDIA_HYGIENE_ALBUM__ROOT", "C:\\Photos\\Albums 2")
    return photos


def _move(locations: Locations) -> dict[str, object]:
    """Ask the page's desk to move the album folders of the old root.

    Args:
        locations: The test mount points.

    Returns:
        The answer's JSON.
    """
    desk = AlbumMoveDesk(make_runtime(locations))
    assert desk.movable("C:\\Photos\\Albums") == 1
    answer = desk.answer(json.dumps({"old": "C:\\Photos\\Albums"}).encode())
    shown: dict[str, object] = json.loads(answer.body)
    return shown


def test_the_folders_move_then_undo_puts_them_back(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The new folder holds the links, the old one is gone; undo reverses both."""
    photos = _made(cli, locations, monkeypatch)
    old = locations.data_dir / ALBUMS / _NAME
    said = str(_move(locations)["said"])
    assert "1 album made again in the new folder." in said
    new = locations.data_dir / _NEW / _NAME
    assert (new / "DSC_0000.jpg").samefile(photos / WEDDING_CATEGORY / "DSC_0000.jpg")
    assert (new / ALBUM_MARKER).is_file()
    assert not old.exists()
    run_id = said.rsplit("mh undo ", 1)[1].strip()
    undone = run(cli, "undo", "--yes", run_id)
    assert undone.exit_code == 0, undone.output
    assert (old / "IMG_9000.jpg").samefile(photos / "Divers" / "IMG_9000.jpg")
    assert (old / ALBUM_MARKER).is_file()
    assert not new.exists()


def test_a_file_the_tool_did_not_make_stays_said(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A file added by hand keeps the old folder and its marker."""
    _made(cli, locations, monkeypatch)
    old = locations.data_dir / ALBUMS / _NAME
    (old / "notes.txt").write_text("mine", encoding="utf-8")
    said = str(_move(locations)["said"])
    assert "was not made by media-hygiene: it stays" in said
    assert sorted(p.name for p in old.iterdir()) == [ALBUM_MARKER, "notes.txt"]


def test_a_folder_renamed_in_explorer_is_left_alone(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Renamed by hand: no album folder of that name in the old root, nothing moved."""
    _made(cli, locations, monkeypatch)
    old = locations.data_dir / ALBUMS / _NAME
    renamed = old.with_name("Crete (mine)")
    old.rename(renamed)
    desk = AlbumMoveDesk(make_runtime(locations))
    assert desk.movable("C:\\Photos\\Albums") == 0
    shown = json.loads(desk.answer(b'{"old": "C:\\\\Photos\\\\Albums"}').body)
    assert "0 albums made again" in shown["said"]
    assert (renamed / "DSC_0000.jpg").is_file()
    assert not (locations.data_dir / _NEW).exists()


def test_a_changed_root_offers_the_move_with_its_count(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Saving a new root on the page states how many folders the move would take."""
    _made(cli, locations, monkeypatch)
    monkeypatch.delenv("MEDIA_HYGIENE_ALBUM__ROOT")
    runtime = make_runtime(locations)
    roots = (locations.data_dir,)
    roles = RoleDesk(locations.config_file, runtime.mapper, roots)
    desk = album_root_desk(roles, runtime)
    table_of(document := document_of(locations.config_file), "album")["root"] = (
        "C:\\Photos\\Albums"
    )
    write_document(locations.config_file, document)
    answer = desk.answer(json.dumps({"root": "C:\\Photos\\Albums 2"}).encode())
    shown = json.loads(answer.body)
    assert shown["movable"] == 1
    assert shown["old"] == "C:\\Photos\\Albums"
    assert "1 album folder was made in C:\\Photos\\Albums" in shown["said"]
