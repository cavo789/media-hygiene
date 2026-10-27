"""Intruder files (0410): what is a companion, the tallies, what a pick takes."""

from __future__ import annotations

from pathlib import Path

import pytest

from media_hygiene.config.scan_settings import ScanSettings
from media_hygiene.scan.filters import ScanFilters
from media_hygiene.scan.intruders import (
    DEFAULT_COMPANIONS,
    Intruder,
    is_companion,
    outside,
    tally,
)
from media_hygiene.services.intruder_pick import IntruderPick

ROOT = Path("/data/c/Photos")
ZIP = Intruder(ROOT / "a.ZIP", 100, 0)
PDF = Intruder(ROOT / "Trip" / "b.pdf", 50, 0)
BARE = Intruder(ROOT / "README", 5, 0)


@pytest.mark.parametrize(
    ("name", "companion"),
    [
        ("Thumbs.db", True),
        ("IMG_1.jpg.json", True),
        (".DS_Store", True),
        ("a.XMP", True),
        ("GX010042.LRV", True),
        ("DJI_0001.srt", True),
        ("thumbs.db.zip", False),
        ("notes.docx", False),
    ],
)
def test_companions_by_name_or_extension(name: str, *, companion: bool) -> None:
    """A whole name, or an ending for an entry starting with a dot; case ignored."""
    assert is_companion(name, DEFAULT_COMPANIONS) is companion


def test_media_are_never_intruders_even_outside_ext() -> None:
    """`--ext jpg` leaves the png out of the audit; it is still no intruder."""
    filters = ScanFilters(extensions=frozenset({".jpg"}))
    assert not filters.is_intruder(ROOT / "a.png")
    assert filters.is_intruder(ROOT / "a.zip")
    assert not filters.is_intruder(ROOT / "desktop.ini")


def test_tallies_per_extension_and_folder() -> None:
    """Counts and bytes, the heaviest first; a file without extension is named."""
    assert tally((ZIP, PDF, BARE)).heaviest(2) == [(".zip", 1, 100), (".pdf", 1, 50)]
    per_folder = tally((ZIP, PDF, BARE), by_folder=True).heaviest(5)
    assert per_folder == [(str(ROOT), 2, 105), (str(ROOT / "Trip"), 1, 50)]
    assert BARE.extension == "(none)"


def test_outside_leaves_folders_out() -> None:
    """The files of a protected folder are never proposed."""
    assert outside((ZIP, PDF), (ROOT / "Trip",)) == (ZIP,)


def test_a_pick_by_extension_folder_or_both() -> None:
    """Both given: a file must match one of each; none given: nothing."""
    files = (ZIP, PDF, BARE)
    assert [f for f in files if IntruderPick(frozenset({".pdf"})).takes(f)] == [PDF]
    in_trip = IntruderPick(folders=(ROOT / "Trip",))
    assert [f for f in files if in_trip.takes(f)] == [PDF]
    both = IntruderPick(frozenset({".zip"}), (ROOT / "Trip",))
    assert not any(both.takes(f) for f in files)
    assert not any(IntruderPick().takes(f) for f in files)


def test_companions_setting_is_normalised() -> None:
    """Trimmed, lowercase, comma-separated values split, duplicates dropped."""
    scan = ScanSettings(companions=(" .LRV, Thumbs.db", ".lrv"))
    assert scan.companions == (".lrv", "thumbs.db")


def test_a_non_media_extension_is_refused() -> None:
    """media-hygiene only handles photos and videos (0409)."""
    with pytest.raises(ValueError, match="only handles photos and videos"):
        ScanSettings(extensions=("pdf",))
