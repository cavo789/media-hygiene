"""0625, 0626: an album's folder from its page; `_Albums`, its read-me, the move."""

from __future__ import annotations

import asyncio
import json
import sqlite3
from typing import TYPE_CHECKING

from media_hygiene.actions.album_readme import readme_text
from media_hygiene.constants import ALBUM_MARKER, ALBUM_README_NAMES, Locale
from media_hygiene.i18n import _, using
from media_hygiene.review.http import Request, Response
from media_hygiene.search.album_make_desk import AlbumMakeDesk
from media_hygiene.search.album_move_desk import AlbumMoveDesk
from media_hygiene.search.album_root_desk import album_root_desk
from media_hygiene.search.folder_role_desk import RoleDesk
from media_hygiene.services.album_pages import album_edit_page, album_page
from media_hygiene.services.albums import album_store
from media_hygiene.share.album_folder_door import AlbumFolderDoor
from media_hygiene.share.album_store import AlbumChange
from tests.support.albums import ALBUMS, SAVED_ALBUM, saved_album
from tests.support.cli import run
from tests.support.runtime import make_runtime
from tests.support.sorting import PHOTOS

if TYPE_CHECKING:
    from pathlib import Path

    import pytest
    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations

_NAME = SAVED_ALBUM
_README = ALBUM_README_NAMES[0]
_OTHER = "C:\\Photos\\Other"
_NEW = f"{PHOTOS}/Other"


def _saved(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> Path:
    """A saved album of two photos, no folder made.

    Args:
        cli: The runner.
        locations: The test mount points.
        monkeypatch: Its `[album] root`.

    Returns:
        The folder of the photos.
    """
    return saved_album(cli, locations, monkeypatch)


def _make(locations: Locations, **asked: object) -> tuple[int, dict[str, object]]:
    """Ask the desk of the album's page.

    Args:
        locations: The test mount points.
        **asked: What the page posts, the album apart.

    Returns:
        The status and the JSON.
    """
    desk = AlbumMakeDesk(make_runtime(locations))
    answer = desk.answer(json.dumps({"album": _NAME, **asked}).encode())
    return answer.status, json.loads(answer.body)


def test_shown_first_then_made_read_back_and_undone(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The dry run touches nothing and states the count; the run says its undo line."""
    _saved(cli, locations, monkeypatch)
    folder = locations.data_dir / ALBUMS / _NAME
    status, shown = _make(locations)
    assert status == 200
    assert shown["links"] == 2
    assert "2" in str(shown["button"])
    assert not folder.exists()
    status, done = _make(locations, apply=True, links=2, remove=0)
    assert status == 200
    assert done["done"] is True
    said = " ".join(done["said"])  # type: ignore[arg-type]
    assert "2 photos and videos" in said
    assert (folder / "DSC_0000.jpg").is_file()
    run_id = said.rsplit("mh undo ", 1)[1].strip()
    assert run(cli, "undo", "--yes", run_id).exit_code == 0
    assert not folder.exists()


def test_counts_changed_since_nothing_is_made(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A run asked with counts that are no longer true shows the album again."""
    _saved(cli, locations, monkeypatch)
    _status, shown = _make(locations, apply=True, links=9, remove=0)
    assert "done" not in shown
    assert not (locations.data_dir / ALBUMS / _NAME).exists()


def test_a_missing_journal_is_one_sentence(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """What `album --apply` refuses comes back as a sentence, never a traceback."""
    _saved(cli, locations, monkeypatch)
    monkeypatch.setattr(
        "media_hygiene.search.album_make_desk.AlbumService.ensure_ready",
        lambda _self: (_ for _ in ()).throw(OSError("no journal")),
    )
    status, answer = _make(locations)
    assert status == 409
    assert answer["error"] == "no journal"


def test_it_asks_for_the_folder_only_when_unknown(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Neither `[album] root` nor a target: the page asks."""
    _saved(cli, locations, monkeypatch)
    monkeypatch.delenv("MEDIA_HYGIENE_ALBUM__ROOT")
    monkeypatch.delenv("MEDIA_HYGIENE_CLASSIFY__TARGET", raising=False)
    locations.config_file.write_text("", "utf-8")
    assert _make(locations)[1] == {"ask_folder": True}


def test_a_phone_is_refused_by_the_door() -> None:
    """A phone's request, marked by its door, is refused, the desk not called."""

    def never(_body: bytes) -> Response:
        raise AssertionError

    door = AlbumFolderDoor({}, {"/w": never}, "x-phone")
    asked = Request("POST", "/w", {"x-phone": "1"}, b"{}")
    answered = asyncio.run(door.answer(asked))
    assert answered is not None
    assert answered.status == 403


def test_the_setting_is_on_the_albums_page_hidden_from_a_link() -> None:
    """The line is on the PC's page; a 24 h link has neither it nor the button."""
    assert 'id="albumRoot"' in album_page().decode()
    assert 'id="albumRoot"' not in album_page(link=True).decode()
    assert 'id="folderMake"' in album_edit_page().decode()


def test_the_read_me_sits_at_the_root_alone_and_undo_keeps_it_for_others(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """One read-me at the root, none in the album; undo only with the last album."""
    photos = _saved(cli, locations, monkeypatch)
    root = locations.data_dir / ALBUMS
    first = _make(locations, apply=True, links=2, remove=0)[1]
    assert (root / _README).is_file()
    assert not (root / _NAME / _README).exists()
    text = (root / _README).read_text("utf-8")
    assert "never touched" in text
    other = photos / "Divers" / "IMG_9000.jpg"
    album_store(make_runtime(locations)).add(AlbumChange("Other", (other,)))
    assert run(cli, "album", "Other", "--apply").exit_code == 0
    said = " ".join(first["said"])  # type: ignore[arg-type]
    undone = run(cli, "undo", "--yes", said.rsplit("mh undo ", 1)[1].strip())
    assert undone.exit_code == 0, undone.output
    assert not (root / _NAME).exists()
    assert (root / _README).is_file()  # another album remains


def test_a_read_me_in_the_other_language_is_kept_alone(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Changing language leaves one read-me, the one already there."""
    _saved(cli, locations, monkeypatch)
    root = locations.data_dir / ALBUMS
    root.mkdir(parents=True, exist_ok=True)
    (root / ALBUM_README_NAMES[1]).write_text("fr", "utf-8")
    _make(locations, apply=True, links=2, remove=0)
    names = {p.name for p in root.iterdir()} & set(ALBUM_README_NAMES)
    assert names == {ALBUM_README_NAMES[1]}


def test_the_move_carries_the_read_me_then_undo_puts_it_back(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A read-me does not stop the old folder being emptied; undo restores all."""
    _saved(cli, locations, monkeypatch)
    root = locations.data_dir / ALBUMS
    _make(locations, apply=True, links=2, remove=0)
    monkeypatch.setenv("MEDIA_HYGIENE_ALBUM__ROOT", _OTHER)
    desk = AlbumMoveDesk(make_runtime(locations))
    answer = desk.answer(json.dumps({"old": "C:\\Photos\\Albums"}).encode())
    said = str(json.loads(answer.body)["said"])
    assert not root.exists()
    new = locations.data_dir / _NEW
    assert (new / _README).is_file()
    assert (
        run(cli, "undo", "--yes", said.rsplit("mh undo ", 1)[1].strip()).exit_code == 0
    )
    assert (root / _README).is_file()
    assert (root / _NAME / ALBUM_MARKER).is_file()


def test_a_users_file_at_the_old_root_stays_said(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A file of the user at the root keeps the folder, its read-me, and is reported."""
    _saved(cli, locations, monkeypatch)
    root = locations.data_dir / ALBUMS
    _make(locations, apply=True, links=2, remove=0)
    (root / "mine.txt").write_text("mine", "utf-8")
    monkeypatch.setenv("MEDIA_HYGIENE_ALBUM__ROOT", _OTHER)
    desk = AlbumMoveDesk(make_runtime(locations))
    answer = desk.answer(json.dumps({"old": "C:\\Photos\\Albums"}).encode())
    assert "mine.txt" in str(json.loads(answer.body)["said"])
    assert (root / "mine.txt").is_file()
    assert (root / _README).is_file()


def test_the_former_default_folder_is_offered_the_move(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A default moving from `Albums` to `_Albums`: the move is offered, counted."""
    _saved(cli, locations, monkeypatch)
    _make(locations, apply=True, links=2, remove=0)  # made in <Photos>/Albums
    monkeypatch.setenv("MEDIA_HYGIENE_ALBUM__ROOT", "")
    locations.config_file.write_text("[classify]\ntarget = 'C:\\Photos'\n", "utf-8")
    runtime = make_runtime(locations)
    roles = RoleDesk(locations.config_file, runtime.mapper, (locations.data_dir,))
    state = json.loads(album_root_desk(roles, runtime).state().body)
    assert state["used"] == "C:\\Photos\\_Albums"
    assert state["old"] == "C:\\Photos\\Albums"
    assert state["movable"] == 1


def test_the_read_me_is_listed_by_no_scan(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """After a folder is made, an audit lists neither the read-me nor the album."""
    _saved(cli, locations, monkeypatch)
    _make(locations, apply=True, links=2, remove=0)
    audited = run(cli, "audit")
    assert audited.exit_code == 0, audited.output
    runtime = make_runtime(locations)
    connection = sqlite3.connect(runtime.locations.index_file)
    rows = connection.execute("SELECT path FROM files").fetchall()
    connection.close()
    assert rows
    assert not [row for row in rows if "READ-ME" in row[0] or ALBUMS in row[0]]


def test_the_read_me_follows_the_language() -> None:
    """Its name in French is one of those recognised, its text translated."""
    with using(Locale.FR):
        assert _("READ-ME - managed by Media Hygiene.txt") == ALBUM_README_NAMES[1]
        assert "jamais touché" in readme_text()
