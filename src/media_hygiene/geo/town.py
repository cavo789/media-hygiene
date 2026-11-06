"""A town of the GeoNames snapshot."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from media_hygiene.geo.distance import Point


@dataclass(frozen=True, slots=True)
class Town:
    """A town, its region and its country, named in the language in use."""

    name: str
    point: Point
    country: str
    region: str
    population_k: int  # thousands of inhabitants
    district: str = ""  # admin2 of GeoNames: stored and searched, never a folder (0545)
    code: str = ""  # the country's ISO code
