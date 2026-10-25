"""0358: a server of the whole session reads its settings again when they change.

One test per event that changes a settings file (`.claude/rules/workflow.md`): an atomic
save (another inode), an edit in place, a copy keeping the old mtime, a removal, a file
that no longer loads; a people file added, renamed, removed.
"""

from __future__ import annotations

import os
import shutil
from typing import TYPE_CHECKING

from media_hygiene.config.people_files import FOLDER
from media_hygiene.services.fresh_runtime import FreshRuntime, settings_mark
from tests.support.runtime import make_locations, make_runtime

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.paths.locations import Locations


def _port(text: str) -> str:
    """A `config.toml` choosing the page's port."""
    return f"[review]\nport = {text}\n"


def _fresh(tmp_path: Path) -> tuple[FreshRuntime, Locations]:
    """A fresh runtime on a `config.toml` choosing port 8101."""
    locations = make_locations(tmp_path)
    locations.config_dir.mkdir(parents=True, exist_ok=True)
    locations.config_file.write_text(_port("8101"), "utf-8")
    fresh = FreshRuntime(make_runtime(locations), every=0)
    return fresh, locations


def test_nothing_changed_gives_the_same_runtime(tmp_path: Path) -> None:
    """No file changed: the very same object, nothing loaded again."""
    fresh, _locations = _fresh(tmp_path)
    assert fresh.runtime() is fresh.runtime()


def test_an_atomic_save_is_seen(tmp_path: Path) -> None:
    """A new file renamed over the old one (another inode): its settings."""
    fresh, locations = _fresh(tmp_path)
    before = fresh.runtime()
    written = locations.config_dir / "config.toml.tmp"
    written.write_text(_port("8102"), "utf-8")
    written.replace(locations.config_file)
    after = fresh.runtime()
    assert after is not before
    assert after.settings.review.port == 8102


def test_an_edit_in_place_is_seen(tmp_path: Path) -> None:
    """The same file written again."""
    fresh, locations = _fresh(tmp_path)
    with locations.config_file.open("w", encoding="utf-8") as config:
        config.write(_port("8103"))
    assert fresh.runtime().settings.review.port == 8103


def test_a_copy_keeping_the_old_mtime_is_seen(tmp_path: Path) -> None:
    """Another content, the same size and modification time: the content counts."""
    fresh, locations = _fresh(tmp_path)
    stat = locations.config_file.stat()
    other = tmp_path / "other.toml"
    other.write_text(_port("8104"), "utf-8")
    shutil.copyfile(other, locations.config_file)
    os.utime(locations.config_file, ns=(stat.st_atime_ns, stat.st_mtime_ns))
    assert fresh.runtime().settings.review.port == 8104


def test_a_removed_file_gives_the_defaults(tmp_path: Path) -> None:
    """No `config.toml` any more: the defaults, as a command started then."""
    fresh, locations = _fresh(tmp_path)
    default = make_runtime(make_locations(tmp_path / "none")).settings.review.port
    locations.config_file.unlink()
    assert fresh.runtime().settings.review.port == default


def test_a_file_that_no_longer_loads_keeps_the_last_good_settings(
    tmp_path: Path,
) -> None:
    """A typo while editing: the last good settings stay, said once."""
    fresh, locations = _fresh(tmp_path)
    good = fresh.runtime()
    locations.config_file.write_text(_port("not a number"), "utf-8")
    assert fresh.runtime() is good
    assert fresh.runtime() is good  # the same broken file: nothing tried again
    locations.config_file.write_text(_port("8105"), "utf-8")
    assert fresh.runtime().settings.review.port == 8105


def test_a_people_file_added_renamed_or_removed_changes_the_mark(
    tmp_path: Path,
) -> None:
    """The files of the people (0300) are read by the settings too."""
    _fresh_runtime, locations = _fresh(tmp_path)
    people = locations.config_dir / FOLDER
    people.mkdir()
    marks = [settings_mark(locations)]
    (people / "Mamie.toml").write_text('faces = ["/a#0"]\n', "utf-8")
    marks.append(settings_mark(locations))
    (people / "Mamie.toml").rename(people / "Mamie Jeanne.toml")
    marks.append(settings_mark(locations))
    (people / "Mamie Jeanne.toml").unlink()
    marks.append(settings_mark(locations))
    assert len(set(marks[:3])) == 3
    assert marks[3] == marks[0]


def test_the_files_are_read_at_most_once_a_second(tmp_path: Path) -> None:
    """A page asks a dozen times when it opens: one read of the files per second."""
    locations = make_locations(tmp_path)
    locations.config_dir.mkdir(parents=True, exist_ok=True)
    locations.config_file.write_text(_port("8101"), "utf-8")
    fresh = FreshRuntime(make_runtime(locations))
    locations.config_file.write_text(_port("8106"), "utf-8")
    assert fresh.runtime().settings.review.port == 8101  # within the second
