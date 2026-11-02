"""A move emptying a `[[places.folders]]` folder rewrites `config.toml` (0549)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.places.config_folders import read_folders
from media_hygiene.services.sort_links_folders import emptied_settings
from tests.support.runtime import make_locations, make_runtime

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.services.runtime import Runtime

_CONFIG = (
    "# my notes\n[[places.folders]]\nfolder = 'C:\\Photos\\Figeac'\n"
    "latitude = 44.609\nlongitude = 2.032\n"
)


def _setup(tmp_path: Path) -> tuple[Runtime, Path]:
    """A config placing the Figeac folder, the folder created.

    Args:
        tmp_path: Temporary directory.

    Returns:
        The runtime and the folder.
    """
    locations = make_locations(tmp_path)
    locations.config_file.write_text(_CONFIG, encoding="utf-8")
    runtime = make_runtime(locations)
    old = runtime.mapper.to_container("C:\\Photos\\Figeac")
    old.mkdir(parents=True)
    return runtime, old


def _move(runtime: Runtime, pairs: list[tuple[Path, Path]]) -> tuple[str, ...]:
    """Move the files, then follow the settings.

    Args:
        runtime: The runtime.
        pairs: Old and new path.

    Returns:
        The lines said.
    """
    for old, new in pairs:
        new.parent.mkdir(parents=True, exist_ok=True)
        old.replace(new)
    return emptied_settings(runtime, {str(old): str(new) for old, new in pairs})


def _folders(runtime: Runtime) -> list[str]:
    """The placed folders, read back.

    Args:
        runtime: The runtime.

    Returns:
        Their host paths.
    """
    return [spot.folder for spot in read_folders(runtime.locations.config_file)]


def test_one_new_folder_takes_the_place(tmp_path: Path) -> None:
    """All photos to one folder: the place follows, and back on undo."""
    runtime, old = _setup(tmp_path)
    (old / "a.jpg").write_bytes(b"a")
    target = runtime.mapper.to_container("C:\\Photos\\2017\\2017-07\\Dordogne")
    said = _move(runtime, [(old / "a.jpg", target / "a.jpg")])
    assert _folders(runtime) == ["C:\\Photos\\2017\\2017-07\\Dordogne"]
    assert "# my notes" in runtime.locations.config_file.read_text(encoding="utf-8")
    assert any("moved to" in line for line in said)
    _move(runtime, [(target / "a.jpg", old / "a.jpg")])  # undo
    assert _folders(runtime) == ["C:\\Photos\\Figeac"]


def test_several_folders_remove_then_undo_restores(tmp_path: Path) -> None:
    """Photos to several folders: removed, comments kept; undo restores."""
    runtime, old = _setup(tmp_path)
    (old / "a.jpg").write_bytes(b"a")
    (old / "b.jpg").write_bytes(b"b")
    first = runtime.mapper.to_container("C:\\Photos\\One")
    second = runtime.mapper.to_container("C:\\Photos\\Two")
    pairs = [(old / "a.jpg", first / "a.jpg"), (old / "b.jpg", second / "b.jpg")]
    said = _move(runtime, pairs)
    assert not _folders(runtime)
    assert any("removed from config.toml" in line for line in said)
    assert "# my notes" in runtime.locations.config_file.read_text(encoding="utf-8")
    _move(runtime, [(new, old) for old, new in pairs])  # undo
    assert _folders(runtime) == ["C:\\Photos\\Figeac"]


def test_kept_while_the_folder_holds_files(tmp_path: Path) -> None:
    """A folder still holding a photo keeps its place."""
    runtime, old = _setup(tmp_path)
    (old / "a.jpg").write_bytes(b"a")
    (old / "b.jpg").write_bytes(b"b")
    target = runtime.mapper.to_container("C:\\Photos\\One")
    assert not _move(runtime, [(old / "a.jpg", target / "a.jpg")])
    assert _folders(runtime) == ["C:\\Photos\\Figeac"]
