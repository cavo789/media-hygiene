"""The tree of `browse`: photos and videos counted up to the mounted folders."""

from __future__ import annotations

from pathlib import Path

from media_hygiene.search.folder_tree import FolderCount, folder_counts


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
