"""`is_within` and `root_of` compare paths as text (0703): same answers as by parts."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, cast

import pytest

from media_hygiene.paths.host_paths import is_within
from media_hygiene.services.classify_inputs import root_of

if TYPE_CHECKING:
    from media_hygiene.services.runtime import Runtime

PATHS = (
    "/data/c/Photos/IMG.jpg",
    "/data/C/photos/img.JPG",
    "/data/c",
    "/data/cc/x.jpg",
    "/data",
    "/elsewhere/data/c/x.jpg",
    "/data/c/Straße/x.jpg",
    "/data/c/STRASSE/x.jpg",
    "relative/x.jpg",
    "/",
)
FOLDERS = ("/data/c", "/data/C/Photos", "/data", "/", "/data/c/straße", "relative", ".")


def _by_parts(path: Path, folder: Path) -> bool:
    """The former `is_within`: part by part, ignoring case.

    Args:
        path: Candidate path.
        folder: Folder.

    Returns:
        True when inside.
    """
    folder_parts = [part.casefold() for part in folder.parts]
    path_parts = [part.casefold() for part in path.parts]
    return path_parts[: len(folder_parts)] == folder_parts


@pytest.mark.parametrize("folder", FOLDERS)
@pytest.mark.parametrize("path", PATHS)
def test_is_within_answers_as_by_parts(path: str, folder: str) -> None:
    """Every pair of paths: the text comparison agrees with the parts."""
    assert is_within(Path(path), Path(folder)) == _by_parts(Path(path), Path(folder))


def _former_root(path: Path, roots: tuple[Path, ...], data_dir: Path) -> Path:
    """The former `root_of`, by `relative_to`.

    Args:
        path: A file.
        roots: Mounted folders.
        data_dir: The data mount point.

    Returns:
        Its root.
    """
    root = next((r for r in roots if _by_parts(path, r)), data_dir)
    if root == data_dir and path.is_relative_to(data_dir):
        return data_dir / path.relative_to(data_dir).parts[0]
    return root


@pytest.mark.parametrize(
    "roots", [(Path("/data"),), (Path("/data/c/Photos"), Path("/data/d"))]
)
@pytest.mark.parametrize("path", [p for p in PATHS if p not in {"/data", "/"}])
def test_root_of_answers_as_before(path: str, roots: tuple[Path, ...]) -> None:
    """Each file: the same root as `relative_to` gave."""
    data_dir = Path("/data")
    runtime = cast(
        "Runtime", SimpleNamespace(locations=SimpleNamespace(data_dir=data_dir))
    )
    expected = _former_root(Path(path), roots, data_dir)
    assert root_of(Path(path), roots, runtime) == expected
