"""The landmarks of the snapshot (0472): monuments, castles, churches, museums….

GeoNames has no dump of landmarks alone: they are read from `allCountries.zip` (about
420 MB, downloaded into the temporary folder), features of class S (spots, buildings)
and L (areas) whose code a visitor would name a photo after. Positions rounded to 4
decimals (about 11 m); sorted by position, which compresses best.
"""

from __future__ import annotations

import io
import lzma
import zipfile
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from pathlib import Path

ALL_ZIP: Final = "allCountries.zip"
ALL_TXT: Final = "allCountries.txt"
LANDMARKS_FILE: Final = "landmarks.tsv.xz"
# Feature codes (https://www.geonames.org/export/codes.html) worth a photo's caption;
# bridges, radio towers, parks and cemeteries are left out: too many trivial ones.
CODES: Final = frozenset({
    "AMTH", "AMUS", "ANS", "ARCH", "CH", "CSTL", "CVNT", "FT", "GDN", "HSTS", "LTHSE",
    "MNMT", "MSQE", "MSTY", "MUS", "OBPT", "OPRA", "PAL", "PGDA", "PYR", "PYRS", "RUIN",
    "SHRN", "SQR", "STDM", "TMPL", "THTR", "ZOO",
})  # fmt: skip
_CLASSES: Final = frozenset({"S", "L"})
_ENCODING: Final = "utf-8"
_TAB: Final = "\t"
_NAME, _LATITUDE, _LONGITUDE, _CLASS, _CODE = 1, 4, 5, 6, 7


def build_landmarks(archive: Path, target: Path) -> int:
    """Write `landmarks.tsv.xz` from the full dump.

    Args:
        archive: `allCountries.zip`.
        target: The data folder of `media_hygiene.geo`.

    Returns:
        The number of landmarks written.
    """
    rows: set[tuple[float, float, str]] = set()
    with (
        zipfile.ZipFile(archive) as opened,
        opened.open(ALL_TXT) as raw,
        io.TextIOWrapper(raw, _ENCODING) as stream,
    ):
        for line in stream:
            row = line.split(_TAB)
            if row[_CLASS] in _CLASSES and row[_CODE] in CODES and row[_NAME]:
                latitude = round(float(row[_LATITUDE]), 4)
                longitude = round(float(row[_LONGITUDE]), 4)
                rows.add((latitude, longitude, row[_NAME]))
    text = "".join(f"{name}\t{lat:.4f}\t{lon:.4f}\n" for lat, lon, name in sorted(rows))
    compressed = lzma.compress(text.encode(_ENCODING), preset=9 | lzma.PRESET_EXTREME)
    (target / LANDMARKS_FILE).write_bytes(compressed)
    return len(rows)
