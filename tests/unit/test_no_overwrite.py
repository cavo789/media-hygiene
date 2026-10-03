"""Moves and copies that never replace a file: races, fallbacks, failed copies."""

from __future__ import annotations

import errno
import os
from typing import TYPE_CHECKING

import pytest

from media_hygiene.actions import no_overwrite
from media_hygiene.actions.no_overwrite import (
    copy_exclusive,
    create_empty,
    move_no_replace,
    rename_no_replace,
)

if TYPE_CHECKING:
    from pathlib import Path

MTIME = 1_600_000_000_000_000_000


def files(tmp_path: Path) -> tuple[Path, Path]:
    """A photo, and the free name it is about to take."""
    source = tmp_path / "a" / "IMG_1.jpg"
    source.parent.mkdir()
    source.write_bytes(b"photo")
    os.utime(source, ns=(MTIME, MTIME))
    return source, tmp_path / "b" / "IMG_1.jpg"


def refusing(code: int) -> no_overwrite.Renamer:
    """An atomic rename that fails with `code`, as an old kernel or a FUSE mount."""

    def rename(_source: Path, target: Path) -> None:
        raise OSError(code, os.strerror(code), str(target))

    return rename


def test_the_atomic_rename_refuses_an_existing_target(tmp_path: Path) -> None:
    """Same disk: renamed; a second time onto the same name: EEXIST, both kept."""
    source, target = files(tmp_path)
    move_no_replace(source, target)
    assert target.read_bytes() == b"photo"
    assert not source.exists()
    source.write_bytes(b"other")
    with pytest.raises(FileExistsError):
        rename_no_replace(source, target)
    assert (source.read_bytes(), target.read_bytes()) == (b"other", b"photo")


def test_a_file_appearing_before_the_rename_is_never_replaced(tmp_path: Path) -> None:
    """The race: a file lands on the target between the check and the rename."""
    source, target = files(tmp_path)

    def racing(first: Path, second: Path) -> None:
        second.write_bytes(b"arrived meanwhile")
        rename_no_replace(first, second)

    with pytest.raises(FileExistsError):
        move_no_replace(source, target, racing)
    assert source.read_bytes() == b"photo"
    assert target.read_bytes() == b"arrived meanwhile"


@pytest.mark.parametrize("code", [errno.ENOSYS, errno.EINVAL, errno.EXDEV])
def test_without_the_atomic_rename_the_file_is_copied_and_proven(
    tmp_path: Path, code: int
) -> None:
    """Unsupported here, or another disk: an exclusive copy, then the source goes."""
    source, target = files(tmp_path)
    move_no_replace(source, target, refusing(code))
    assert target.read_bytes() == b"photo"
    assert target.stat().st_mtime_ns == MTIME
    assert not source.exists()


def test_the_copy_never_replaces_a_file_appearing_meanwhile(tmp_path: Path) -> None:
    """The fallback copy opens its target exclusively: the newcomer stays whole."""
    source, target = files(tmp_path)

    def racing(_first: Path, second: Path) -> None:
        second.write_bytes(b"arrived meanwhile")
        raise OSError(errno.EXDEV, os.strerror(errno.EXDEV), str(second))

    with pytest.raises(FileExistsError):
        move_no_replace(source, target, racing)
    assert source.read_bytes() == b"photo"
    assert target.read_bytes() == b"arrived meanwhile"


def test_a_copy_that_differs_is_removed_and_the_source_kept(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The digests disagree: only the copy made here goes, the original stays."""
    source, target = files(tmp_path)
    digests = iter(("one", "two"))
    monkeypatch.setattr(no_overwrite, "full_digest", lambda _path: next(digests))
    with pytest.raises(OSError, match="differs"):
        move_no_replace(source, target, refusing(errno.EXDEV))
    assert source.read_bytes() == b"photo"
    assert not target.exists()


def test_a_failed_copy_leaves_nothing_behind(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A disk error in the middle: the partial copy is removed, the source kept."""
    source, target = files(tmp_path)
    target.parent.mkdir()

    def broken(*_streams: object) -> None:
        raise OSError(errno.EIO, os.strerror(errno.EIO))

    monkeypatch.setattr("shutil.copyfileobj", broken)
    with pytest.raises(OSError, match=os.strerror(errno.EIO)):
        copy_exclusive(source, target)
    assert source.read_bytes() == b"photo"
    assert not target.exists()


def test_other_rename_errors_are_raised(tmp_path: Path) -> None:
    """A missing source is no reason to copy: the error comes back as is."""
    with pytest.raises(FileNotFoundError):
        move_no_replace(tmp_path / "gone.jpg", tmp_path / "t" / "gone.jpg")


def test_a_c_library_without_renameat2_means_copying(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No `renameat2` (old glibc, musl): ENOSYS, hence the verified copy."""
    monkeypatch.setattr(no_overwrite, "_libc_renameat2", lambda: None)
    source, target = files(tmp_path)
    with pytest.raises(OSError, match=os.strerror(errno.ENOSYS)):
        rename_no_replace(source, target)
    move_no_replace(source, target)
    assert target.read_bytes() == b"photo"


def test_an_empty_file_is_never_created_over_another(tmp_path: Path) -> None:
    """`undo` of an empty file deleted: refused when a file took its name."""
    path = tmp_path / "empty.jpg"
    create_empty(path)
    assert path.stat().st_size == 0
    path.write_bytes(b"new")
    with pytest.raises(FileExistsError):
        create_empty(path)
    assert path.read_bytes() == b"new"
