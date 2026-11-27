"""A settings file is read once while it stays the same, again after any change."""

from __future__ import annotations

import os
import pathlib
from typing import TYPE_CHECKING

import pytest

from media_hygiene.config.stamped_text import forget_texts, stamped_text

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def reads(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Every real read of a file, by name."""
    forget_texts()
    seen: list[str] = []
    original = pathlib.Path.read_text

    def counted(self: pathlib.Path, *args: str) -> str:
        seen.append(self.name)
        return original(self, *args)

    monkeypatch.setattr(pathlib.Path, "read_text", counted)
    return seen


def test_read_once_while_unchanged(tmp_path: Path, reads: list[str]) -> None:
    """Two reads of an untouched file: one from the disk."""
    path = tmp_path / "Ann.toml"
    path.write_text("faces = []\n", encoding="utf-8")
    assert stamped_text(path) == stamped_text(path) == "faces = []\n"
    assert reads == ["Ann.toml"]


def test_atomic_save_seen(tmp_path: Path, reads: list[str]) -> None:
    """A save through a draft renamed over it (new inode): read again."""
    path = tmp_path / "Ann.toml"
    path.write_text("a = 1\n", encoding="utf-8")
    stamped_text(path)
    draft = tmp_path / ".Ann.toml.tmp"
    draft.write_text("a = 2\n", encoding="utf-8")
    draft.replace(path)
    assert stamped_text(path) == "a = 2\n"
    assert len(reads) == 2


def test_in_place_edit_same_size_seen(tmp_path: Path, reads: list[str]) -> None:
    """An edit by hand, same size, same inode: its time tells it."""
    path = tmp_path / "Ann.toml"
    path.write_text("a = 1\n", encoding="utf-8")
    stamped_text(path)
    before = path.stat().st_mtime_ns
    path.write_text("a = 3\n", encoding="utf-8")
    os.utime(path, ns=(before + 1_000, before + 1_000))
    assert stamped_text(path) == "a = 3\n"
    assert len(reads) == 2


def test_copy_keeping_mtime_seen(tmp_path: Path, reads: list[str]) -> None:
    """A copy over it that keeps the old modification time: its change time tells."""
    path = tmp_path / "Ann.toml"
    path.write_text("a = 1\n", encoding="utf-8")
    stamped_text(path)
    before = path.stat()
    path.write_text("a = 4\n", encoding="utf-8")
    os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns))
    assert stamped_text(path) == "a = 4\n"
    assert len(reads) == 2


def test_touch_reads_again(tmp_path: Path, reads: list[str]) -> None:
    """`touch`: the time changes, the file is read again (harmless)."""
    path = tmp_path / "Ann.toml"
    path.write_text("a = 1\n", encoding="utf-8")
    stamped_text(path)
    later = path.stat().st_mtime_ns + 1_000
    os.utime(path, ns=(later, later))
    stamped_text(path)
    assert len(reads) == 2


def test_missing_file_raises(tmp_path: Path) -> None:
    """A missing file: the error of `stat`, as before."""
    with pytest.raises(FileNotFoundError):
        stamped_text(tmp_path / "gone.toml")
