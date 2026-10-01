"""Where the review says its decisions file lies: host path, or its mount."""

from __future__ import annotations

from pathlib import Path

import pytest

from media_hygiene.paths.host_paths import HostPathMapper
from media_hygiene.review.place import DecisionsPlace, decisions_place

REPORTS = Path("/reports")
DESKTOP = HostPathMapper(Path("/data"), ((REPORTS, "C:\\Users\\Ann\\reports"),))
VOLUME = HostPathMapper(Path("/data"))


@pytest.mark.parametrize(
    ("mapper", "target", "place"),
    [
        (
            DESKTOP,
            REPORTS / "decisions.json",
            DecisionsPlace("decisions.json", "C:\\Users\\Ann\\reports\\decisions.json"),
        ),
        (
            VOLUME,
            REPORTS / "decisions.json",
            DecisionsPlace(
                "decisions.json", "decisions.json, in the folder mounted on /reports"
            ),
        ),
        (
            VOLUME,
            REPORTS / "2026/other.json",
            DecisionsPlace(
                "2026/other.json",
                "2026/other.json, in the folder mounted on /reports",
            ),
        ),
        (
            VOLUME,
            Path("/cache/d.json"),
            DecisionsPlace("/cache/d.json", "/cache/d.json"),
        ),
        (
            VOLUME,
            Path("/data/c/Photos/d.json"),
            DecisionsPlace("/data/c/Photos/d.json", "C:\\Photos\\d.json"),
        ),
    ],
)
def test_decisions_place(
    mapper: HostPathMapper, target: Path, place: DecisionsPlace
) -> None:
    """Desktop source, named volume, another name, an absolute path."""
    assert decisions_place(mapper, REPORTS, target) == place
