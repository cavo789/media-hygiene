"""A tiny GeoNames dump, turned into a snapshot the way the real one is made.

Real, public towns (their GeoNames positions); the personal places of the tests are
fictitious points.
"""

from __future__ import annotations

import zipfile
from typing import TYPE_CHECKING, Final

from tests.support.geonames.snapshot import (
    CITIES_TXT,
    CITIES_ZIP,
    COUNTRIES_TXT,
    REGIONS_TXT,
    build,
)

if TYPE_CHECKING:
    from pathlib import Path

# name, latitude, longitude, feature code, country, region, population
TOWNS: Final = (
    ("Brussels", 50.85045, 4.34878, "PPLC", "BE", "BRU", 1019022),
    ("Bruges", 51.20892, 3.22424, "PPLA2", "BE", "VLG", 117073),
    ("Turin", 45.07049, 7.68682, "PPLA", "IT", "12", 847287),
    ("Moncalieri", 44.99960, 7.68240, "PPLA3", "IT", "12", 57552),
    ("Pino Torinese", 45.04060, 7.77700, "PPLA3", "IT", "12", 8458),
    ("Milan", 45.46427, 9.18951, "PPLA", "IT", "09", 1371498),
    ("Sydney", -33.86785, 151.20732, "PPLA", "AU", "02", 4627345),
    ("The Rocks", -33.85923, 151.20807, "PPL", "AU", "02", 1500),
    ("Turin 04 Old district", 45.07100, 7.68500, "PPLX", "IT", "12", 50000),
)
REGIONS: Final = (
    ("BE.BRU", "Brussels Capital"),
    ("BE.VLG", "Flanders"),
    ("IT.12", "Piedmont"),
    ("IT.09", "Lombardy"),
    ("AU.02", "New South Wales"),
)
COUNTRIES: Final = (("BE", "Belgium"), ("IT", "Italy"), ("AU", "Australia"))


def write_towns(folder: Path) -> Path:
    """Write the dump and build its snapshot.

    Args:
        folder: A scratch folder.

    Returns:
        The snapshot's folder, for `Gazetteer.load`.
    """
    dumps, data = folder / "dumps", folder / "data"
    dumps.mkdir()
    data.mkdir()
    rows = [
        "\t".join(
            (
                *(str(number), name, name, "", str(lat), str(lon), "P", code, country),
                *("", region, "", "", "", str(people), "", "0", "Zone", "2026-01-01"),
            )
        )
        for number, (name, lat, lon, code, country, region, people) in enumerate(TOWNS)
    ]
    with zipfile.ZipFile(dumps / CITIES_ZIP, "w") as archive:
        archive.writestr(CITIES_TXT, "\n".join(rows) + "\n")
    (dumps / REGIONS_TXT).write_text(
        "".join(f"{code}\t{name}\t{name}\t0\n" for code, name in REGIONS), "utf-8"
    )
    (dumps / COUNTRIES_TXT).write_text(
        "#ISO\tISO3\tnumber\tfips\tCountry\n"
        + "".join(f"{code}\t\t\t\t{name}\n" for code, name in COUNTRIES),
        "utf-8",
    )
    build(dumps, data)
    return data
