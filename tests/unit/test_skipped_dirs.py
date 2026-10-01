"""Folders skipped by name: the system ones, and those the user names (globs)."""

from __future__ import annotations

from pathlib import Path

import pytest

from media_hygiene.config.scan_settings import ScanSettings
from media_hygiene.scan.filters import ScanFilters

ROOT = Path("/data/d/Disk")


@pytest.mark.parametrize(
    "name",
    [
        "$RECYCLE.BIN",
        "System Volume Information",
        "@eaDir",
        "#recycle",
        "@Recycle",
        ".@__thumb",
        ".Trash",
        ".Trash-1000",
        ".Trashes",
        ".thumbnails",
    ],
)
def test_system_and_trash_folders_are_always_skipped(name: str) -> None:
    """Windows, Synology, QNAP, freedesktop and macOS trash or thumbnail folders."""
    assert ScanFilters().skips_dir(ROOT / name)


USER_NAMES = ScanFilters(excluded_names=("Thumbnails", "*.lrdata"))


@pytest.mark.parametrize("name", ["Thumbnails", "THUMBNAILS", "Catalog.lrdata"])
def test_user_names_are_globs_case_ignored(name: str) -> None:
    """`Thumbnails` matches in any case; `*.lrdata` is a glob."""
    assert USER_NAMES.skips_dir(ROOT / "2019" / name)


@pytest.mark.parametrize("name", ["Thumbnails 2", "My Thumbnails", "Photos"])
def test_user_names_match_the_whole_name(name: str) -> None:
    """A glob is not a substring search."""
    assert not USER_NAMES.skips_dir(ROOT / "2019" / name)


def test_names_are_split_trimmed_and_kept_as_written() -> None:
    """Comma-separated like --ext; empty values dropped; case kept for Czkawka."""
    scan = ScanSettings(excluded_names=("Thumbnails, .Trash-*", "", "Thumbnails"))
    assert scan.excluded_names == ("Thumbnails", ".Trash-*")


@pytest.mark.parametrize("value", ["D:\\backup", "Photos/Thumbnails"])
def test_a_path_is_refused_with_the_right_option(value: str) -> None:
    """A path names one folder: that is --exclude."""
    with pytest.raises(ValueError, match="is a path, not a folder name: use --exclude"):
        ScanSettings(excluded_names=(value,))
