"""The files of the GeoNames snapshot: the towns, and small tables of names."""

from __future__ import annotations

import csv
import lzma
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

import numpy as np

from media_hygiene.constants import Locale

if TYPE_CHECKING:
    from pathlib import Path

    import numpy.typing as npt

TOWNS_FILE: Final = "towns.tsv.xz"
COUNTRIES_FILE: Final = "countries.tsv"
REGIONS_FILE: Final = "regions.tsv"
DISTRICTS_FILE: Final = "districts.tsv.xz"  # admin2: `Haut-Rhin` (0545)
_ENCODING: Final = "utf-8"
_TAB: Final = "\t"
# A row: its name, position, country, region, population (k), district (admin2).
_TOWN_FIELDS: Final = 7


@dataclass(frozen=True, slots=True)
class TownRows:
    """The towns as columns."""

    names: tuple[str, ...]
    latitudes: npt.NDArray[np.float64]
    longitudes: npt.NDArray[np.float64]
    countries: tuple[str, ...]  # ISO codes
    regions: tuple[str, ...]  # `BE.BRU`
    population_k: npt.NDArray[np.int_]
    districts: tuple[str, ...]  # `FR.44.68`, empty when GeoNames gives none


def read_towns(path: Path) -> TownRows:
    """Read the towns.

    Args:
        path: The compressed table of towns.

    Returns:
        Its columns.

    Raises:
        ValueError: A row has not the expected fields, or a number is no number.
    """
    text = lzma.decompress(path.read_bytes()).decode(_ENCODING)
    fields = [line.split(_TAB) for line in text.splitlines() if line]
    if any(len(row) != _TOWN_FIELDS for row in fields):
        message = f"{path.name}: a row has not {_TOWN_FIELDS} fields"
        raise ValueError(message)
    return TownRows(
        tuple(row[0] for row in fields),
        np.array([float(row[1]) for row in fields]),
        np.array([float(row[2]) for row in fields]),
        tuple(row[3] for row in fields),
        tuple(f"{row[3]}.{row[4]}" for row in fields),
        np.array([int(row[5]) for row in fields]),
        tuple(f"{row[3]}.{row[4]}.{row[6]}" if row[6] else "" for row in fields),
    )


def read_table(path: Path) -> list[list[str]]:
    """Read a small tab-separated file.

    Args:
        path: The file.

    Returns:
        Its rows.
    """
    with path.open(encoding=_ENCODING, newline="") as stream:
        reader = csv.reader(stream, delimiter=_TAB, quoting=csv.QUOTE_NONE)
        return [row for row in reader if row]


def read_names(folder: Path) -> tuple[dict[str, dict[Locale, str]], dict[str, str]]:
    """Read the names of the countries, and of the regions of both levels.

    Args:
        folder: Where the snapshot lies.

    Returns:
        Country names by code and language; region names by code (`BE.WAL`,
        `FR.44.68`).
    """
    countries = {
        row[0]: {Locale.EN: row[1], Locale.FR: row[2]}
        for row in read_table(folder / COUNTRIES_FILE)
    }
    regions = {row[0]: row[1] for row in read_table(folder / REGIONS_FILE)}
    text = lzma.decompress((folder / DISTRICTS_FILE).read_bytes()).decode(_ENCODING)
    for line in text.splitlines():
        code, name = line.split(_TAB)
        regions[code] = name
    return countries, regions
