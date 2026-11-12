"""Previous versions kept at each save of the user's files (0691)."""

from __future__ import annotations

import re
import shutil
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
import tomlkit

from media_hygiene import file_history
from media_hygiene.classify.event_files import read_not_events, write_ids
from media_hygiene.config.event_layer import event_files
from media_hygiene.config.photo_ref import write_refs
from media_hygiene.constants import CONFIG_FILE_NAME
from media_hygiene.file_history import (
    HISTORY_DIR,
    KEEP_VERSIONS,
    keep_previous,
    replace_text,
    restore_version,
    versions_of,
)
from media_hygiene.places.toml_edit import write_document
from media_hygiene.services.face_refs_audit import face_files
from media_hygiene.share.albums import Album, AlbumsFile, read_albums, write_albums

_SRC = Path(file_history.__file__).parent
# Every module that saves a file of /config or albums.json (0691): through the helper.
_WRITERS = (
    "people/config_file.py",
    "places/toml_edit.py",
    "places/config_file.py",
    "services/config_tidy.py",
    "services/config_convention.py",
    "services/config_upgrade.py",
    "config/photo_ref.py",
    "cli/home_favourites.py",
    "share/albums.py",
    "classify/remember_rule.py",  # its roll-back after a failed event write (0778)
)
_OWN_REPLACE = re.compile(r"\w+\.replace\((config_file|path|target|self\.path)\)")


@pytest.fixture
def config_dir(tmp_path: Path) -> Path:
    """A /config folder with its config.toml."""
    folder = tmp_path / "config"
    folder.mkdir()
    (folder / CONFIG_FILE_NAME).write_text("[scan]\n", "utf-8")
    return folder


@pytest.mark.parametrize("module", _WRITERS)
def test_every_writer_goes_through_the_helper(module: str) -> None:
    """The writers of /config and albums.json save with `replace_text`."""
    text = (_SRC / module).read_text("utf-8")
    assert "replace_text(" in text
    assert not _OWN_REPLACE.search(text)


def test_no_other_module_replaces_config_files() -> None:
    """No module but the writers listed saves over `config_file` itself."""
    found = {
        path.relative_to(_SRC).as_posix()
        for path in _SRC.rglob("*.py")
        if re.search(r"\.replace\(config_file\)", path.read_text("utf-8"))
    }
    assert found == set()


def _undo(path: Path) -> None:
    restore_version(path, versions_of(path)[0])


def test_config_toml_save_then_undo_is_byte_identical(config_dir: Path) -> None:
    """config.toml: a page's save, then the previous version put back."""
    config = config_dir / CONFIG_FILE_NAME
    before = config.read_bytes()
    write_document(config, tomlkit.parse("[scan]\nworkers = 2\n"))
    assert config.read_bytes() != before
    version = versions_of(config)[0]
    assert version.parent == config_dir / HISTORY_DIR
    _undo(config)
    assert config.read_bytes() == before


def test_person_file_save_then_undo(config_dir: Path) -> None:
    """people/<name>.toml: versions in /config/.history/people/, undone exactly."""
    path = config_dir / "people" / "ann.toml"
    path.parent.mkdir()
    write_refs(path, "Ann", {"faces": ["{ path = 'a.jpg' }"]})
    before = path.read_bytes()
    write_refs(path, "Ann", {"faces": []})
    assert versions_of(path)[0].parent == config_dir / HISTORY_DIR / "people"
    _undo(path)
    assert path.read_bytes() == before


def test_events_file_save_then_undo_and_readers_ignore_history(
    config_dir: Path,
) -> None:
    """events/: undone exactly; the readers never see `.history`."""
    write_ids(config_dir, "events/not-events.toml", ("folders", {"a", "b"}))
    path = config_dir / "events" / "not-events.toml"
    before = path.read_bytes()
    write_ids(config_dir, "events/not-events.toml", ("folders", set()))
    assert (config_dir / HISTORY_DIR / "events").is_dir()
    _undo(path)
    assert path.read_bytes() == before
    assert read_not_events(config_dir) == {"a", "b"}
    assert all(HISTORY_DIR not in str(each) for each in event_files(config_dir))


def test_albums_file_save_then_undo(tmp_path: Path) -> None:
    """albums.json (in /reports): versions beside it, undone exactly."""
    path = tmp_path / "albums.json"
    write_albums(path, AlbumsFile(albums=(Album(name="Sea"),)))
    before = path.read_bytes()
    write_albums(path, AlbumsFile())
    assert versions_of(path)[0].parent == tmp_path / HISTORY_DIR
    _undo(path)
    assert path.read_bytes() == before
    assert read_albums(path).albums[0].name == "Sea"


def test_unchanged_save_keeps_no_version(config_dir: Path) -> None:
    """A save that changes nothing writes no version."""
    config = config_dir / CONFIG_FILE_NAME
    replace_text(config, config.read_text("utf-8"))
    assert not versions_of(config)


def test_history_never_grows_past_its_bound(config_dir: Path) -> None:
    """At most KEEP_VERSIONS versions, the newest ones."""
    config = config_dir / CONFIG_FILE_NAME
    for rank in range(KEEP_VERSIONS + 5):
        replace_text(config, f"# {rank}\n")
    versions = versions_of(config)
    assert len(versions) == KEEP_VERSIONS
    assert versions[0].read_text("utf-8") == f"# {KEEP_VERSIONS + 3}\n"


def test_old_versions_are_trimmed_but_the_newest(config_dir: Path) -> None:
    """Versions older than KEEP_DAYS go at the next save, but the newest one."""
    config = config_dir / CONFIG_FILE_NAME
    old = datetime.now(tz=UTC) - timedelta(days=file_history.KEEP_DAYS + 1)
    stale = config_dir / HISTORY_DIR / f"config.toml.{old:%Y%m%dT%H%M%S%fZ}"
    stale.parent.mkdir()
    stale.write_text("# old\n", "utf-8")
    replace_text(config, "# new\n")
    assert not stale.exists()
    assert len(versions_of(config)) == 1


def test_restore_is_itself_undoable(config_dir: Path) -> None:
    """Putting a version back keeps the content it replaced."""
    config = config_dir / CONFIG_FILE_NAME
    replace_text(config, "# second\n")
    _undo(config)
    assert versions_of(config)[0].read_text("utf-8") == "# second\n"


def test_restore_refuses_a_foreign_file(config_dir: Path, tmp_path: Path) -> None:
    """Only a version of this very file can be put back."""
    foreign = tmp_path / "other"
    foreign.write_text("x", "utf-8")
    with pytest.raises(ValueError, match="not a version"):
        restore_version(config_dir / CONFIG_FILE_NAME, foreign)


def test_moved_config_folder_keeps_its_versions(
    config_dir: Path, tmp_path: Path
) -> None:
    """A /config folder moved or restored elsewhere keeps its history."""
    config = config_dir / CONFIG_FILE_NAME
    before = config.read_bytes()
    replace_text(config, "# changed\n")
    moved = tmp_path / "moved"
    shutil.move(config_dir, moved)
    _undo(moved / CONFIG_FILE_NAME)
    assert (moved / CONFIG_FILE_NAME).read_bytes() == before


def test_stray_names_in_history_are_not_versions(config_dir: Path) -> None:
    """A file without a stamp in `.history/` is never listed nor trimmed."""
    folder = config_dir / HISTORY_DIR
    folder.mkdir()
    stray = folder / "config.toml.notes"
    stray.write_text("x", "utf-8")
    assert keep_previous(config_dir / CONFIG_FILE_NAME) is not None
    assert stray.exists()
    assert len(versions_of(config_dir / CONFIG_FILE_NAME)) == 1


def test_first_save_has_no_previous(config_dir: Path) -> None:
    """A new file has nothing to keep."""
    assert keep_previous(config_dir / "missing.toml") is None
    assert [each.name for each in config_dir.iterdir()] == [CONFIG_FILE_NAME]


def test_people_readers_ignore_history(config_dir: Path) -> None:
    """The people's files listed by the audits never include their versions."""
    path = config_dir / "people" / "ann.toml"
    path.parent.mkdir()
    write_refs(path, "Ann", {"faces": []})
    write_refs(path, "Ann", {"faces": ["{ path = 'a.jpg' }"]})
    assert versions_of(path)
    assert face_files(config_dir) == [path]
