"""Copies kept by messaging apps: the folders they lie in, the day their names give."""

from __future__ import annotations

from pathlib import Path

import pytest

from media_hygiene.plan.messaging_copies import in_messaging_folder, same_day

DATA = Path("/data/c")


@pytest.mark.parametrize(
    ("folder", "messaging"),
    [
        ("Android/Media/WhatsApp Images/Sent", True),
        ("Telegram Desktop", True),
        ("Email", True),
        ("Outlook Attachments", True),
        ("Pièces jointes", True),
        ("2019/Vacances", False),
        ("Signal", True),
        ("Signalisation", False),  # whole words only
    ],
)
def test_messaging_folders(folder: str, *, messaging: bool) -> None:
    """Any folder of the path counts, whole names, any case."""
    assert in_messaging_folder(DATA / folder / "a.jpg") is messaging


@pytest.mark.parametrize(
    ("taken_at", "name", "same"),
    [
        ("2019:07:12 23:59:00", "IMG-20190712-WA0003.jpg", True),
        ("2019-07-12T08:00:00+0200", "VID-20190712-WA0001.mp4", True),
        ("2019:07:12 10:00:00", "IMG-20190713-WA0003.jpg", False),
        ("2019:07:12 10:00:00", "IMG-WA0003.jpg", False),
        (None, "IMG-20190712-WA0003.jpg", False),
        ("garbage", "IMG-20190712-WA0003.jpg", False),
    ],
)
def test_same_day(taken_at: str | None, name: str, *, same: bool) -> None:
    """The day of the kept version (EXIF or ISO) against the day of the name."""
    assert same_day(taken_at, DATA / "WhatsApp" / name) is same
