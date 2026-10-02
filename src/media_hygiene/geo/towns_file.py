"""The files of the GeoNames snapshot: the towns, and small tables of names."""

from __future__ import annotations

import csv
import lzma
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

import numpy as np

if TYPE_CHECKING:
    from pathlib import Path

    import numpy.typing as npt

_ENCODING: Final = "utf-8"
_TAB: Final = "\t"
_TOWN_FIELDS: Final = 6  # name, latitude, longitude, country, region, population (k)


@dataclass(frozen=True, slots=True)
class TownRows:
    """The towns as columns."""

    names: tuple[str, ...]
    latitudes: npt.NDArray[np.float64]
    longitudes: npt.NDArray[np.float64]
    countries: tuple[str, ...]  # ISO codes
    regions: tuple[str, ...]  # `BE.BRU`
    population_k: npt.NDArray[np.int_]


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
