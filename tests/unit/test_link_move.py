"""Where the atomic rename is refused, a move is a hard link then an unlink (0138)."""

from __future__ import annotations

import errno
import os
from typing import TYPE_CHECKING

import pytest

from media_hygiene.actions.no_overwrite import move_no_replace

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.actions.no_overwrite import Renamer


def files(tmp_path: Path) -> tuple[Path, Path]:
    """A photo, and the free name it is about to take."""
    source = tmp_path / "a" / "IMG_1.jpg"
    source.parent.mkdir()
    source.write_bytes(b"photo")
    return source, tmp_path / "b" / "IMG_1.jpg"


def refusing(code: int) -> Renamer:
    """An atomic rename that fails with `code`, as Docker Desktop's NTFS mounts do."""

    def rename(_source: Path, target: Path) -> None:
        raise OSError(code, os.strerror(code), str(target))

    return rename


def test_einval_moves_by_link_keeping_the_inode(tmp_path: Path) -> None:
    """Same inode at the target, the old name gone: nothing was copied."""
    source, target = files(tmp_path)
    inode = source.stat().st_ino
    move_no_replace(source, target, refusing(errno.EINVAL))
    assert target.stat().st_ino == inode
    assert not source.exists()


def test_an_existing_target_is_refused_by_the_link(tmp_path: Path) -> None:
    """EEXIST from link: FileExistsError, both files intact."""
    source, target = files(tmp_path)
    target.parent.mkdir()
    target.write_bytes(b"other")
    with pytest.raises(FileExistsError):
        move_no_replace(source, target, refusing(errno.EINVAL))
    assert (source.read_bytes(), target.read_bytes()) == (b"photo", b"other")


@pytest.mark.parametrize("code", [errno.EPERM, errno.ENOTSUP, errno.EXDEV])
def test_without_links_the_file_is_copied(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, code: int
) -> None:
    """A filesystem without hard links: the verified copy, a new inode."""
    source, target = files(tmp_path)
    inode = source.stat().st_ino

    def no_link(*_args: object) -> None:
        raise OSError(code, os.strerror(code))

    monkeypatch.setattr(os, "link", no_link)
    move_no_replace(source, target, refusing(errno.EINVAL))
    assert target.read_bytes() == b"photo"
    assert target.stat().st_ino != inode
    assert not source.exists()


def test_exdev_from_the_rename_never_tries_a_link(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Another disk: straight to the copy, a link could not cross it either."""
    source, target = files(tmp_path)
    tried: list[object] = []
    monkeypatch.setattr(os, "link", lambda *args: tried.append(args))
    move_no_replace(source, target, refusing(errno.EXDEV))
    assert not tried
    assert target.read_bytes() == b"photo"


def test_a_move_killed_between_link_and_unlink_is_finished(tmp_path: Path) -> None:
    """Both names hold one file: moving it again only drops the old name."""
    source, target = files(tmp_path)
    target.parent.mkdir()
    os.link(source, target)
    move_no_replace(source, target)
    assert target.read_bytes() == b"photo"
    assert not source.exists()
