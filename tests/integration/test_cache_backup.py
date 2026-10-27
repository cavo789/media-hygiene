"""`backup` / `restore` (0352): the index and the settings, kept and put back safely.

A restore never loses what is there without proof and a way back: the archive is
checked whole before anything is overwritten, and the current state is backed up first.
"""

from __future__ import annotations

import json
import sqlite3
import zipfile
from typing import TYPE_CHECKING, Final

import pytest

from media_hygiene.errors import MountError
from media_hygiene.index.schema import SCHEMA_VERSION, prepare
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.services.backup_archive import MANIFEST, BackupError
from media_hygiene.services.cache_backup import KEPT, archives, make_backup
from media_hygiene.services.cache_restore import RestoreRequest, restore_backup
from tests.support.cli import point_mounts, run
from tests.support.runtime import make_locations, make_runtime

if TYPE_CHECKING:
    from pathlib import Path

    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations
    from media_hygiene.services.runtime import Runtime

_TAGS: Final = (
    ("/data/c/a.jpg", "beach"),
    ("/data/c/a.jpg", "sea"),
    ("/data/c/b.jpg", "cat"),
)
_SETTINGS: Final = "[general]\nlocale = 'fr'\n"


def _index(runtime: Runtime, tags: tuple[tuple[str, str], ...] = _TAGS) -> None:
    """Write an index holding files and tags.

    Args:
        runtime: The runtime whose index is written.
        tags: The (path, word) rows of `tags`.
    """
    runtime.locations.index_file.unlink(missing_ok=True)
    connection = sqlite3.connect(runtime.locations.index_file)
    prepare(connection)
    for path, word in tags:
        connection.execute(
            "INSERT OR IGNORE INTO files (path, size, mtime_ns) VALUES (?, 1, 1)",
            (path,),
        )
        connection.execute(
            "INSERT INTO tags (path, size, mtime_ns, source, value)"
            " VALUES (?, 1, 1, 'ai', ?)",
            (path, word),
        )
    connection.commit()
    connection.close()


def _rows(runtime: Runtime) -> list[tuple[object, ...]]:
    """Every row of `files` and `tags`, sorted.

    Args:
        runtime: The runtime whose index is read.

    Returns:
        Them.
    """
    connection = sqlite3.connect(runtime.locations.index_file)
    try:
        return sorted(connection.execute("SELECT * FROM tags")) + sorted(
            connection.execute("SELECT * FROM files")
        )
    finally:
        connection.close()


@pytest.fixture
def runtime(tmp_path: Path) -> Runtime:
    """A runtime with every mount, an index and a `config.toml`.

    Args:
        tmp_path: Pytest temporary directory.

    Returns:
        It.
    """
    made = make_runtime(make_locations(tmp_path))
    _index(made)
    made.locations.config_file.write_text(_SETTINGS, encoding="utf-8")
    return made


def test_round_trip_keeps_every_row(runtime: Runtime) -> None:
    """The cache lost (the volume removed), the restore gives every row back."""
    before = _rows(runtime)
    backup = make_backup(runtime)
    assert backup.manifest.counts["files"] == 2
    assert backup.manifest.counts["tags"] == 3
    assert backup.size == backup.path.stat().st_size
    runtime.locations.index_file.unlink()
    restored = restore_backup(runtime, RestoreRequest())
    assert restored.before is None
    assert restored.archive == backup.path
    assert _rows(runtime) == before


def test_restore_backs_up_the_current_index_first(runtime: Runtime) -> None:
    """The index replaced is archived before: restoring that archive undoes it."""
    old = make_backup(runtime)
    _index(runtime, (("/data/c/new.jpg", "dog"),))
    newer = _rows(runtime)
    restored = restore_backup(runtime, RestoreRequest(old.path.name))
    assert restored.before is not None
    assert _rows(runtime) != newer
    restore_backup(runtime, RestoreRequest(restored.before.path.name))
    assert _rows(runtime) == newer


def test_a_damaged_archive_is_refused_and_nothing_changes(runtime: Runtime) -> None:
    """A member differing from its digest: refused before the index is touched."""
    backup = make_backup(runtime)
    with zipfile.ZipFile(backup.path) as archive:
        members = {name: archive.read(name) for name in archive.namelist()}
    members["config/config.toml"] = b"altered"
    with zipfile.ZipFile(backup.path, "w") as archive:
        for name, data in members.items():
            archive.writestr(name, data)
    _index(runtime, (("/data/c/kept.jpg", "kept"),))
    kept = _rows(runtime)
    with pytest.raises(BackupError, match="damaged"):
        restore_backup(runtime, RestoreRequest())
    assert _rows(runtime) == kept
    assert len(archives(runtime.locations.backups_dir)) == 1  # no backup of the refusal


def test_not_a_zip_is_refused(runtime: Runtime) -> None:
    """A file that is not a zip at all."""
    (runtime.locations.backups_dir / "mh-backup-x.zip").write_bytes(b"nonsense")
    with pytest.raises(BackupError, match="cannot be read"):
        restore_backup(runtime, RestoreRequest())


def test_a_member_outside_the_folder_is_refused(runtime: Runtime) -> None:
    """A manifest naming `config/../../x` is never extracted."""
    backup = make_backup(runtime)
    with zipfile.ZipFile(backup.path) as archive:
        members = {name: archive.read(name) for name in archive.namelist()}
    manifest = json.loads(members[MANIFEST])
    manifest["members"]["config/../../evil"] = "0"
    members[MANIFEST] = json.dumps(manifest).encode()
    with zipfile.ZipFile(backup.path, "w") as archive:
        for name, data in members.items():
            archive.writestr(name, data)
    with pytest.raises(BackupError, match="not an mh backup"):
        restore_backup(runtime, RestoreRequest())


def test_a_newer_schema_is_refused(runtime: Runtime) -> None:
    """An index made by a newer image: mh update first; the index stays."""
    connection = sqlite3.connect(runtime.locations.index_file)
    connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION + 1}")
    connection.commit()
    connection.close()
    make_backup(runtime)
    _index(runtime, (("/data/c/kept.jpg", "kept"),))
    kept = _rows(runtime)
    with pytest.raises(BackupError, match="mh update"):
        restore_backup(runtime, RestoreRequest())
    assert _rows(runtime) == kept


def test_the_three_most_recent_are_kept(runtime: Runtime) -> None:
    """The fourth backup removes the oldest; never the one being restored."""
    made = [make_backup(runtime) for _ in range(KEPT + 1)]
    assert made[-1].removed == (made[0].path,)
    assert archives(runtime.locations.backups_dir) == [m.path for m in made[1:]]
    oldest = made[1].path
    restored = restore_backup(runtime, RestoreRequest(oldest.name))
    assert oldest.is_file()
    assert restored.before is not None
    assert restored.before.removed == ()  # the oldest left is the one restored


def test_settings_restored_only_when_asked(runtime: Runtime) -> None:
    """`--config` writes `config.toml` back; without it, the settings stay."""
    make_backup(runtime)
    config = runtime.locations.config_file
    config.write_text("edited", encoding="utf-8")
    restore_backup(runtime, RestoreRequest())
    assert config.read_text(encoding="utf-8") == "edited"
    restored = restore_backup(
        runtime,
        RestoreRequest(archives(runtime.locations.backups_dir)[0].name, config=True),
    )
    assert restored.config == ("config.toml",)
    assert config.read_text(encoding="utf-8") == _SETTINGS


def test_no_archive_no_index_no_mount(tmp_path: Path) -> None:
    """Nothing to restore, nothing to back up, `/backups` not mounted: refused."""
    runtime = make_runtime(make_locations(tmp_path))
    with pytest.raises(BackupError, match="no backup"):
        restore_backup(runtime, RestoreRequest())
    with pytest.raises(BackupError, match="no backup named"):
        restore_backup(runtime, RestoreRequest("mh-backup-missing.zip"))
    with pytest.raises(MountError, match="no index"):
        make_backup(runtime)
    unmounted = make_runtime(make_locations(tmp_path / "other", MountKind.BACKUPS))
    with pytest.raises(MountError, match="not mounted"):
        make_backup(unmounted)


def test_a_moved_file_is_read_again_by_the_next_audit(runtime: Runtime) -> None:
    """Rows are keyed by path: a file moved since the backup is a path gone.

    The restored index still names the old path; the next audit prunes it and reads
    the new one (`index/pruning`): nothing restored points at a wrong file.
    """
    make_backup(runtime)
    restore_backup(runtime, RestoreRequest())
    assert ("/data/c/a.jpg", 1, 1, "ai", "beach", "", "") in _rows(runtime)


def test_the_commands_say_what_was_read_back(
    locations: Locations, monkeypatch: pytest.MonkeyPatch, cli: CliRunner
) -> None:
    """`backup` shows the archive and its rows; `restore` the undo line."""
    point_mounts(locations, monkeypatch)
    _index(make_runtime(locations))
    saved = run(cli, "backup")
    assert saved.exit_code == 0, saved.output
    assert "tags: 3" in saved.output
    restored = run(cli, "restore")
    assert restored.exit_code == 0, restored.output
    assert "mh restore mh-backup-" in " ".join(restored.output.split())
