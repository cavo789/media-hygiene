"""Nominatim's answers, recorded (synthetic places): the areas, their outlines, ids."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Final

import pytest

from media_hygiene.geo.areas import MAX_POINTS
from media_hygiene.geo.osm_results import read_results

RECORDED: Final = Path(__file__).resolve().parents[1] / "fixtures" / "nominatim"


def recorded() -> object:
    """The recorded answer of a search: a village, a park, a node, a broken one."""
    return json.loads((RECORDED / "search.json").read_text(encoding="utf-8"))


def test_only_outlines_are_listed() -> None:
    """The node and the result without a position are left out."""
    found = read_results(recorded())
    assert [area.osm for area in found.areas] == ["R9000001", "W9000002"]
    assert found.too_large == 0


def test_a_polygon_keeps_its_hole_as_latitude_longitude() -> None:
    """GeoJSON's [longitude, latitude] turned round; the closing point dropped."""
    village = read_results(recorded()).areas[0]
    assert village.name == "Fictiville"
    assert village.kind == "village"
    assert village.label.startswith("Fictiville, Imaginary Municipality")
    assert (village.latitude, village.longitude) == (50.315, 5.12)
    outer, hole = village.area[0]
    assert outer[0] == (50.3, 5.1)
    assert len(outer) == len(hole) == 4


def test_a_multipolygon_keeps_its_parts_and_names_itself() -> None:
    """Without a name, the first part of the full name."""
    park = read_results(recorded()).areas[1]
    assert len(park.area) == 2
    assert park.name == "Twin Ponds Park"
    assert park.kind == "leisure"


def test_a_too_detailed_outline_is_counted_not_listed() -> None:
    """A country: a `trip` rule names it better."""
    ring = [[index / 1000, 50 + (index % 2) / 1000] for index in range(MAX_POINTS + 1)]
    row = {
        "osm_type": "relation",
        "osm_id": 1,
        "lat": "50",
        "lon": "0.5",
        "display_name": "Utopia",
        "geojson": {"type": "Polygon", "coordinates": [ring]},
    }
    found = read_results([row])
    assert not found.areas
    assert found.too_large == 1


def test_an_answer_that_is_not_a_list_is_refused() -> None:
    """An error page in JSON, say."""
    with pytest.raises(TypeError, match="list"):
        read_results({"error": "nope"})
