"""The index forgets the files a walk proves gone, and nothing else."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

import pytest

from media_hygiene.constants import MediaKind
from media_hygiene.index.facts import FileFacts
from media_hygiene.index.pruning import WalkCoverage, forget_missing
from media_hygiene.index.repository import FactsRepository
from media_hygiene.scan import walker
from media_hygiene.scan.filters import ScanFilters
from media_hygiene.scan.models import MediaFile
from media_hygiene.scan.progress import NullProgress

ROOT = Path("/data/c/Photos")
KEPT = ROOT / "2019" / "kept.jpg"


def indexed(repository: FactsRepository, *paths: Path) -> None:
    """Give these paths a row in the index."""
    for path in paths:
        repository.put(MediaFile(path, 1, 1, MediaKind.IMAGE), FileFacts())


def coverage(
    unreadable: tuple[Path, ...] = (), filters: ScanFilters | None = None
) -> WalkCoverage:
    """A walk of ROOT that listed KEPT only."""
    listed = frozenset({str(KEPT)})
    return WalkCoverage((ROOT,), listed, unreadable, filters or ScanFilters())


def test_a_file_the_walk_did_not_list_is_forgotten() -> None:
    """Deleted, moved or renamed by hand: its old path loses its row."""
    with FactsRepository.open(None) as repository:
        indexed(repository, KEPT, ROOT / "2019" / "gone.jpg")
        assert forget_missing(repository, coverage()) == 1
        assert repository.paths_under(ROOT) == [str(KEPT)]


@pytest.mark.parametrize(
    ("path", "walk"),
    [
        (Path("/data/d/Old disk/a.jpg"), coverage()),
        (Path("/data/c/Photos2/a.jpg"), coverage()),
        (ROOT / "Locked" / "a.jpg", coverage(unreadable=(ROOT / "Locked",))),
        (ROOT / "2019" / "b.jpg", coverage(unreadable=(ROOT / "2019" / "b.jpg",))),
        (ROOT / "Backup" / "a.jpg", coverage(filters=ScanFilters((ROOT / "Backup",)))),
        (ROOT / "#recycle" / "a.jpg", coverage()),
        (
            ROOT / "2019" / "a.jpg",
            coverage(filters=ScanFilters(extensions=frozenset({".png"}))),
        ),
    ],
    ids=[
        "another-root",
        "same-prefix",
        "unreadable-folder",
        "unreadable-file",
        "excluded-folder",
        "system-folder",
        "out-of-ext",
    ],
)
def test_absence_proves_nothing_there(path: Path, walk: WalkCoverage) -> None:
    """Where the walk could not or would not look, rows are kept."""
    with FactsRepository.open(None) as repository:
        indexed(repository, KEPT, path)
        assert forget_missing(repository, walk) == 0


def test_only_complete_walks_are_dated() -> None:
    """A root walked without a read error gets its date; one with an error does not."""
    other = Path("/data/d/Old disk")
    with FactsRepository.open(None) as repository:
        forget_missing(repository, coverage())
        broken = WalkCoverage((other,), frozenset(), (other / "Locked",), ScanFilters())
        forget_missing(repository, broken)
        assert repository.walked_at(ROOT) is not None
        assert repository.walked_at(other) is None


def test_the_walk_lists_what_it_could_not_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An unreadable folder and a file whose stat fails are reported, not dropped."""
    for name in ("ok/a.jpg", "ok/b.jpg", "locked/c.jpg"):
        (tmp_path / name).parent.mkdir(exist_ok=True)
        (tmp_path / name).write_bytes(b"x")
    # A stat failure cannot be provoked on a real file when tests run as root.
    # pylint: disable-next=protected-access
    real_scandir, real_describe = os.scandir, walker._describe  # noqa: SLF001

    def scandir(folder: Path) -> object:
        if Path(folder).name == "locked":
            raise PermissionError(13, "Permission denied")
        return real_scandir(folder)

    def describe(entry: object, kind: MediaKind | None) -> object:
        if getattr(entry, "name", "") == "b.jpg":
            raise OSError(5, "Input/output error")
        return real_describe(entry, kind)  # type: ignore[arg-type]

    monkeypatch.setattr("media_hygiene.scan.walker.os.scandir", scandir)
    monkeypatch.setattr(walker, "_describe", describe)
    found = asyncio.run(walker.walk((tmp_path,), ScanFilters(), NullProgress()))
    assert [file.path.name for file in found.files] == ["a.jpg"]
    assert set(found.unreadable) == {tmp_path / "locked", tmp_path / "ok" / "b.jpg"}
