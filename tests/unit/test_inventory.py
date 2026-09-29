"""The inventory of an audit: counted from facts already collected, shown briefly."""

from __future__ import annotations

from pathlib import Path
from types import MappingProxyType

from media_hygiene.console.formatting import human_share
from media_hygiene.console.inventory_view import inventory_table
from media_hygiene.constants import Locale, MediaKind
from media_hygiene.i18n import install
from media_hygiene.scan.broken import IntegrityFindings
from media_hygiene.scan.inventory import Inventory, take_inventory
from media_hygiene.scan.metadata import MediaMetadata
from media_hygiene.scan.models import MediaFile, VisualFacts


def file(name: str, kind: MediaKind) -> MediaFile:
    """A media file of the audit."""
    return MediaFile(Path("/data/c") / name, 10, 1, kind)


def test_counts_come_from_the_facts_of_the_audit() -> None:
    """Dated photos, dated and located videos, formats, total length; RAW left out."""
    photos = [file(f"{index}.jpg", MediaKind.IMAGE) for index in range(3)]
    videos = [file(f"{index}.mov", MediaKind.VIDEO) for index in range(2)]
    raw = file("raw.cr2", MediaKind.RAW)
    visuals = {photos[0].path: VisualFacts(1, 2, 4, 3, 1.0, "2021:07:04 10:15:00")}
    metadata = {
        photos[0].path: MediaMetadata(file_format="JPEG", latitude=1.0, longitude=2.0),
        photos[1].path: MediaMetadata(file_format="JPEG"),
        photos[2].path: MediaMetadata(file_format="HEIF"),
        videos[0].path: MediaMetadata(created="2021-07-04T08:00:00Z", duration=12.5),
        videos[1].path: MediaMetadata(duration=2.5, latitude=3.0, longitude=4.0),
    }
    findings = IntegrityFindings(
        (), MappingProxyType(visuals), MappingProxyType(metadata)
    )
    inventory = take_inventory([*photos, *videos, raw], findings)
    assert inventory == Inventory(
        images=3,
        videos=2,
        dated_images=1,
        dated_videos=1,
        located=2,
        formats={"JPEG": 2, "HEIF": 1},
        video_seconds=15.0,
    )


def test_shares_read_naturally_in_both_languages() -> None:
    """`59 of 60 (98%)` in English, `59 sur 60 (98 %)` in French."""
    assert human_share(59, 60) == "59 of 60 (98%)"
    install(Locale.FR)
    assert human_share(1234, 2000) == "1.234 sur 2.000 (62 %)"


def test_no_table_without_photos_or_videos() -> None:
    """An audit of PDF files (`--ext pdf`) shows no inventory."""
    assert inventory_table(Inventory()) is None
    assert inventory_table(Inventory(images=1, formats={"PNG": 1})) is not None
