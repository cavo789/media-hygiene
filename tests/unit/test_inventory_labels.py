"""The inventory's derived labels and cells: thresholds, offsets, text, formulas."""

from __future__ import annotations

from datetime import UTC
from pathlib import Path

import pytest
from openpyxl import Workbook

from media_hygiene.config.inventory_settings import InventorySettings
from media_hygiene.constants import MediaKind
from media_hygiene.index.facts import FileFacts
from media_hygiene.index.listing import IndexedFile
from media_hygiene.paths.host_paths import HostPathMapper
from media_hygiene.report.inventory_columns import Column
from media_hygiene.report.inventory_entries import (
    Entry,
    Flag,
    InventoryContext,
    entry_of,
)
from media_hygiene.report.inventory_labels import (
    flags_label,
    flash_label,
    format_of,
    integrity_label,
    kind_label,
    time_zone,
)
from media_hygiene.report.inventory_workbook import _cell, _text
from media_hygiene.scan.metadata import MediaMetadata
from media_hygiene.scan.models import VisualFacts

CONTEXT = InventoryContext(HostPathMapper(Path("/data")), {}, InventorySettings(), UTC)


def entry(
    name: str = "a.jpg", facts: FileFacts | None = None, kind: MediaKind | None = None
) -> Entry:
    """An entry for a file of the index."""
    file = IndexedFile(Path("/data/c") / name, 1, 0, facts or FileFacts())
    found = entry_of(file, CONTEXT)
    assert found is not None
    return found if kind is None else Entry(file, kind, CONTEXT)


def look(width: int, sharpness: float) -> FileFacts:
    """Facts of a decoded image, square."""
    return FileFacts(visual=VisualFacts(0, 0, width, width, sharpness))


def test_quality_follows_the_thresholds() -> None:
    """Below `blurry_below` blurry, below `small_below` small, else fine."""
    assert entry(facts=look(4000, 500.0)).quality() == ()
    assert entry(facts=look(400, 5.0)).quality() == (Flag.BLURRY, Flag.SMALL)
    assert entry().quality() is None
    assert flags_label(()) == "ok"
    assert flags_label((Flag.BLURRY, Flag.SMALL)) == "blurry, small"
    assert flags_label(None) is None


@pytest.mark.parametrize(
    ("measures", "flags"),
    [
        ((120.0, 0.0, 0.0), ()),
        ((20.0, 0.0, 0.0), (Flag.DARK,)),
        ((240.0, 0.0, 0.0), (Flag.BRIGHT,)),
        ((120.0, 0.5, 0.5), (Flag.DARK, Flag.BRIGHT)),
    ],
)
def test_exposure_follows_the_thresholds(
    measures: tuple[float, float, float], flags: tuple[Flag, ...]
) -> None:
    """Mean brightness and clipped shares give dark, bright, or both."""
    brightness, dark, bright = measures
    metadata = MediaMetadata(
        brightness=brightness, dark_share=dark, bright_share=bright
    )
    assert entry(facts=FileFacts(metadata=metadata)).exposure() == flags


def test_no_exposure_without_measures() -> None:
    """A file never measured has no exposure label."""
    assert entry(facts=FileFacts(metadata=MediaMetadata())).exposure() is None


def test_the_offset_comes_from_exif_or_the_local_video_date() -> None:
    """An EXIF offset, else the offset of Apple's local date; nothing otherwise."""
    with_offset = FileFacts(metadata=MediaMetadata(offset="+02:00"))
    local = FileFacts(metadata=MediaMetadata(created_local="2021-06-05T12:00:00+0100"))
    broken = FileFacts(metadata=MediaMetadata(created_local="yesterday"))
    assert time_zone(entry(facts=with_offset)) == "+02:00"
    assert time_zone(entry("v.mp4", local)) == "+01:00"
    assert time_zone(entry("v.mp4", broken)) is None
    assert time_zone(entry()) is None
    assert time_zone(entry(facts=FileFacts(metadata=MediaMetadata()))) is None


def test_small_labels() -> None:
    """Flash bit 0, kinds, formats from the extension, integrity states."""
    assert (flash_label(None), flash_label(16), flash_label(25)) == (None, "no", "yes")
    assert kind_label(MediaKind.RAW) == "RAW"
    assert kind_label(MediaKind.OTHER) == "other"
    assert format_of(entry("v.mp4")) == "MP4"
    assert integrity_label(entry()) == "not checked"
    assert integrity_label(entry(facts=FileFacts().with_integrity(None, ""))) == (
        "healthy"
    )


def test_other_files_are_not_listed() -> None:
    """A PDF asked for with `--ext` is not a media file of the inventory."""
    file = IndexedFile(Path("/data/c/doc.pdf"), 1, 0, FileFacts())
    assert entry_of(file, CONTEXT) is None


def test_csv_text_follows_the_list_separator() -> None:
    """French Excel reads `1,5` with `;`; English Excel reads `1.5` with `,`."""
    assert _text(1.5, ";") == "1,5"
    assert _text(1.5, ",") == "1.5"
    assert _text(None, ";") == ""
    assert _text(7, ";") == "7"


def test_csv_text_that_starts_like_a_formula_keeps_an_apostrophe() -> None:
    """Decided in TODO 0055: Excel shows `'-2019 trip.jpg`, never `#NAME?`.

    A number stays a number: a negative longitude has no apostrophe.
    """
    for name in ("=1.jpg", "+1.jpg", "-2019 trip.jpg", "@home.jpg"):
        assert _text(name, ",") == f"'{name}"
    assert _text("IMG_0001.jpg", ",") == "IMG_0001.jpg"
    assert _text(-3.5, ",") == "-3.5"
    assert _text(-3.5, ";") == "-3,5"


def test_a_name_starting_with_equals_stays_text() -> None:
    """`=1.jpg` is a file name, never a formula Excel would refuse."""
    sheet = Workbook(write_only=True).create_sheet()
    named = _cell(sheet, Column("Name", lambda e: e.file.path.name), entry("=1.jpg"))
    assert (named.value, named.data_type) == ("=1.jpg", "s")
