"""Turn the GeoNames dumps into the small snapshot `media_hygiene.geo` reads offline.

Towns of more than 1,000 inhabitants (`cities1000`), without sections of towns and
abandoned, destroyed or historical places; positions rounded to 3 decimals (about
110 m); sorted by country, region and population, which compresses best. Country names
in English and French come from CLDR (Babel), once, here: never at runtime.
"""

from __future__ import annotations

import io
import lzma
import zipfile
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from babel import Locale

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

CITIES_ZIP: Final = "cities1000.zip"
CITIES_TXT: Final = "cities1000.txt"
REGIONS_TXT: Final = "admin1CodesASCII.txt"
COUNTRIES_TXT: Final = "countryInfo.txt"
SKIPPED_CODES: Final = frozenset({"PPLX", "PPLH", "PPLQ", "PPLW", "PPLCH"})
_ENCODING: Final = "utf-8"
_TAB: Final = "\t"
_COMMENT: Final = "#"
# Columns of the GeoNames `geoname` table.
_NAME, _LATITUDE, _LONGITUDE, _CODE, _COUNTRY, _REGION, _POPULATION = (
    1,
    4,
    5,
    7,
    8,
    10,
    14,
)
_COUNTRY_NAME: Final = 4  # column of countryInfo.txt
_THOUSAND: Final = 1000


@dataclass(frozen=True, slots=True, order=True)
class _Town:
    """One row of the snapshot, ordered as written."""

    country: str
    region: str
    minus_population: int
    name: str
    latitude: float
    longitude: float

    def line(self) -> str:
        """The row as written.

        Returns:
            Name, position, country, region, population in thousands.
        """
        thousands = -self.minus_population // _THOUSAND
        fields = (
            self.name,
            f"{self.latitude:.3f}",
            f"{self.longitude:.3f}",
            self.country,
            self.region,
            str(thousands),
        )
        return _TAB.join(fields) + "\n"


def build(dumps: Path, target: Path) -> int:
    """Write `towns.tsv.xz`, `regions.tsv` and `countries.tsv`.

    Args:
        dumps: The folder holding the three GeoNames files.
        target: The data folder of `media_hygiene.geo`.

    Returns:
        The number of towns written.
    """
    towns = sorted(_towns(dumps / CITIES_ZIP))
    text = "".join(town.line() for town in towns).encode(_ENCODING)
    compressed = lzma.compress(text, preset=9 | lzma.PRESET_EXTREME)
    (target / "towns.tsv.xz").write_bytes(compressed)
    used_regions = {f"{town.country}.{town.region}" for town in towns}
    regions = [row for row in _rows(dumps / REGIONS_TXT) if row[0] in used_regions]
    _write(target / "regions.tsv", sorted((row[0], row[1]) for row in regions))
    names = {row[0]: row[_COUNTRY_NAME] for row in _rows(dumps / COUNTRIES_TXT)}
    english, french = Locale("en").territories, Locale("fr").territories
    countries = sorted(
        (code, english.get(code, names.get(code, code)), french.get(code, code))
        for code in {town.country for town in towns}
    )
    _write(target / "countries.tsv", countries)
    return len(towns)


def _towns(archive: Path) -> list[_Town]:
    """Read the populated places of the dump.

    Args:
        archive: `cities1000.zip`.

    Returns:
        The towns kept.
    """
    with (
        zipfile.ZipFile(archive) as opened,
        opened.open(CITIES_TXT) as raw,
        io.TextIOWrapper(raw, _ENCODING) as stream,
    ):
        rows = [line.rstrip("\n").split(_TAB) for line in stream]
    return [
        _Town(
            row[_COUNTRY],
            row[_REGION],
            -int(row[_POPULATION] or 0),
            row[_NAME],
            float(row[_LATITUDE]),
            float(row[_LONGITUDE]),
        )
        for row in rows
        if row[_CODE] not in SKIPPED_CODES
    ]


def _rows(path: Path) -> list[list[str]]:
    """Read a tab-separated GeoNames file, without its comments.

    Args:
        path: The file.

    Returns:
        Its rows.
    """
    lines = path.read_text(_ENCODING).splitlines()
    return [
        line.split(_TAB) for line in lines if line and not line.startswith(_COMMENT)
    ]


def _write(path: Path, rows: Sequence[tuple[str, ...]]) -> None:
    """Write a small tab-separated file.

    Args:
        path: The file.
        rows: Its rows.
    """
    path.write_text("".join(_TAB.join(row) + "\n" for row in rows), _ENCODING)
