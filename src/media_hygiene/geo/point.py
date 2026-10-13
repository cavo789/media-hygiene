"""A position on the Earth, without numpy: the settings read it at every start."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Point:
    """A position in decimal degrees: south and west are negative."""

    latitude: float
    longitude: float
