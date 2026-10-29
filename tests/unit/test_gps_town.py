"""0458: the large view's facts name the town of a GPS position, offline."""

from __future__ import annotations

from media_hygiene.search.exif_facts import exif_lines
from media_hygiene.search.gps_town import town_text


def test_a_known_point_of_the_snapshot_names_its_town_and_country() -> None:
    """Durbuy's coordinates read as Durbuy, Belgium."""
    assert town_text(50.3524, 5.4568) == "Durbuy, Belgium"


def test_a_photo_with_gps_shows_the_town_one_without_nothing_more() -> None:
    """The town follows the coordinates; without a position, no place line."""
    with_gps = exif_lines({"latitude": 50.85, "longitude": 4.35}, "")
    assert "GPS: 50.85000, 4.35000 (Brussels, Belgium)" in with_gps
    assert not [line for line in exif_lines({}, "") if "GPS" in line]
