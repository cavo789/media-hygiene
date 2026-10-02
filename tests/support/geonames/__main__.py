"""`python -m tests.support.geonames`: download GeoNames, refresh the snapshot.

The dumps are downloaded into the system's temporary folder; only
`src/media_hygiene/geo/data/` changes. GeoNames publishes them under CC BY 4.0: the
date of the dump is written into `ATTRIBUTION.txt`.
"""

from __future__ import annotations

import tempfile
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Final

from tests.support.geonames.snapshot import (
    CITIES_ZIP,
    COUNTRIES_TXT,
    REGIONS_TXT,
    build,
)

DUMPS: Final = "https://download.geonames.org/export/dump/"
DATA: Final = Path(__file__).resolve().parents[3] / "src/media_hygiene/geo/data"
ATTRIBUTION: Final = DATA / "ATTRIBUTION.txt"
_DATE_LINE: Final = "Snapshot of "


def main() -> None:
    """Download the three dumps and rebuild the snapshot."""
    with tempfile.TemporaryDirectory(prefix="geonames-") as folder:
        work = Path(folder)
        for name in (CITIES_ZIP, REGIONS_TXT, COUNTRIES_TXT):
            print(f"Downloading {DUMPS}{name}…")  # noqa: T201 - a developer tool
            urllib.request.urlretrieve(f"{DUMPS}{name}", work / name)  # noqa: S310
        count = build(work, DATA)
    today = datetime.now(UTC).date().isoformat()
    lines = ATTRIBUTION.read_text("utf-8").splitlines()
    dated = [
        f"{_DATE_LINE}{today}." if line.startswith(_DATE_LINE) else line
        for line in lines
    ]
    ATTRIBUTION.write_text("\n".join(dated) + "\n", "utf-8")
    print(f"{count} towns written to {DATA}.")  # noqa: T201 - a developer tool


if __name__ == "__main__":
    main()
