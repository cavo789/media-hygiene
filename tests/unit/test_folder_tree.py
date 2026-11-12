"""The tree of `browse`: photos and videos counted up to the mounted folders."""

from __future__ import annotations

import random
from pathlib import Path

from media_hygiene.constants import MediaKind
from media_hygiene.scan.filters import media_kind
from media_hygiene.search.folder_tree import PHOTOS, FolderCount, folder_counts


def test_counts_climb_to_the_mounted_folder_and_skip_the_others() -> None:
    """A video, a RAW and another file count in every folder above them."""
    rows = [
        ("/data/c/Photos/2019/Noël/IMG_1.jpg", 10),
        ("/data/c/Photos/2019/Noël/clip.mp4", 100),
        ("/data/c/Photos/2019/DSC_2.nef", 5),
        ("/data/c/Photos/notes.pdf", 1),
        ("/data/d/Old/IMG_9.jpg", 7),  # not mounted now
    ]
    counts = folder_counts(rows, (Path("/data/c/Photos"), Path("/data/e/Empty")))
    assert counts["/data/c/Photos/2019/Noël"] == FolderCount(1, 1, 110, 2)
    assert counts["/data/c/Photos/2019"] == FolderCount(2, 1, 115, 1)
    assert counts["/data/c/Photos"] == FolderCount(2, 1, 116, 1)
    assert counts["/data/e/Empty"] == FolderCount()
    assert not any(folder.startswith("/data/d") for folder in counts)
    assert "/data/c" not in counts


def _by_path(
    rows: list[tuple[str, int]], roots: tuple[Path, ...]
) -> dict[str, FolderCount]:
    """The counts as 0704 made them before: a `Path` per file and per parent.

    Args:
        rows: The path and size of every file.
        roots: The mounted folders.

    Returns:
        Each folder and what it holds.
    """
    counts = {str(root): FolderCount() for root in roots}
    for path, size in rows:
        file = Path(path)
        top = next((root for root in roots if file.is_relative_to(root)), None)
        if top is None or file == top:
            continue
        kind = media_kind(file)
        folder = file.parent
        counts.setdefault(str(folder), FolderCount()).files += 1
        for above in (folder, *folder.parents):
            count = counts.setdefault(str(above), FolderCount())
            count.size += size
            count.photos += kind in PHOTOS
            count.videos += kind is MediaKind.VIDEO
            if above == top:
                break
    return counts


def test_text_counts_equal_the_path_counts() -> None:
    """0704: the same tree as the `Path` version, on odd names and nested mounts."""
    rng = random.Random(704)  # noqa: S311 - test data
    names = ("IMG.JPG", "a.heic", ".jpg", "..mp4", "noext", "x.", "v.MOV", "r.dng")
    folders: tuple[str, ...] = (
        "/data/c/P",
        "/data/c/P/2019",
        "/data/c/P/2019/a b",
        "/data/c/Px",
    )
    folders += ("/data/c/P/2019/a b/é", "/data/d", "/data/c")
    rows = [
        (f"{rng.choice(folders)}/{rng.choice(names)}", rng.randrange(1000))
        for _ in range(500)
    ]
    rows.append(("/data/c/P", 3))  # a file named as a mounted folder
    for roots in (
        (Path("/data/c/P"),),
        (Path("/data/c/P/2019"), Path("/data/c/P")),
        (Path("/data/c/P"), Path("/data/c/P/2019"), Path("/data/e")),
    ):
        assert folder_counts(rows, roots) == _by_path(rows, roots)
