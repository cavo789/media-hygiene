"""The byte check of `purge --to` (0306): a copy differing in any way is refused."""

from __future__ import annotations

import shutil
from typing import TYPE_CHECKING

import pytest

from media_hygiene.actions.archive_copy import (
    ArchiveError,
    ArchiveJob,
    archive_run,
    missing_space,
    same_bytes,
)

if TYPE_CHECKING:
    from pathlib import Path


def _quarantine(tmp_path: Path) -> ArchiveJob:
    folder = tmp_path / "q" / "20261027-101010"
    (folder / "sub").mkdir(parents=True)
    (folder / "a.jpg").write_bytes(b"a" * 3000)
    (folder / "sub" / "b.jpg").write_bytes(b"b" * 10)
    return ArchiveJob("20261027-101010", (("C", folder),), tmp_path / "nas")


def test_an_identical_copy_passes(tmp_path: Path) -> None:
    """Every file copied, sizes read back from the target."""
    job = _quarantine(tmp_path)
    done = archive_run(job)
    assert (done.files, done.size) == (2, 3010)
    assert (job.target / job.run / "C" / "sub" / "b.jpg").read_bytes() == b"b" * 10


def test_same_bytes_refuses_a_missing_file_another_size_or_content(
    tmp_path: Path,
) -> None:
    """Missing, shorter, longer or same size but other bytes: all differ."""
    source = tmp_path / "s"
    source.write_bytes(b"abcd")
    copy = tmp_path / "c"
    assert not same_bytes(source, copy)
    for other in (b"abc", b"abcde", b"abce"):
        copy.write_bytes(other)
        assert not same_bytes(source, copy)
    copy.write_bytes(b"abcd")
    assert same_bytes(source, copy)


def test_a_corrupt_copy_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The copy lands with one byte changed: refused, the file named."""
    job = _quarantine(tmp_path)

    def flipped(source: Path, copy: Path) -> None:
        data = bytearray(source.read_bytes())
        data[0] ^= 1
        copy.write_bytes(bytes(data))

    monkeypatch.setattr(shutil, "copy2", flipped)
    with pytest.raises(ArchiveError, match=r"a\.jpg"):
        archive_run(job)


def test_a_file_changed_during_the_copy_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The source is rewritten after its copy: its copy is no proof."""
    job = _quarantine(tmp_path)
    real = shutil.copy2

    def then_changed(source: Path, copy: Path) -> None:
        real(source, copy)
        source.write_bytes(b"new content")

    monkeypatch.setattr(shutil, "copy2", then_changed)
    with pytest.raises(ArchiveError):
        archive_run(job)


def test_missing_space_counts_from_the_nearest_existing_folder(
    tmp_path: Path,
) -> None:
    """A target not created yet is measured on its parent's disk."""
    assert missing_space(tmp_path / "not" / "yet", 1) == 0
    assert missing_space(tmp_path, 1 << 62) > 0
