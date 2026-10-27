"""`import` names the folder of the copies after the source (0378)."""

from __future__ import annotations

from pathlib import Path
from typing import Final

import pytest

from media_hygiene.services.import_source import destinations, source_name

_DATA: Final = Path("/data")
_LIBRARY: Final = _DATA / "c" / "Photos"


@pytest.mark.parametrize(
    ("folder", "name"),
    [
        (_DATA / "unc" / "NAS" / "Photos", "NAS"),
        (_DATA / "e" / "DCIM", "E"),
        (_DATA / "e", "E"),
        (Path("/elsewhere/Old"), "Old"),
    ],
)
def test_a_source_is_named_after_where_it_is(folder: Path, name: str) -> None:
    """A share: NAS; a disk: its letter; outside /data: the folder's name."""
    assert source_name(_DATA, folder) == name


def test_each_source_gets_its_own_folder() -> None:
    """A NAS and an SD card: `From NAS`, `From E`."""
    nas, card = _DATA / "unc" / "NAS" / "Photos", _DATA / "e" / "DCIM"
    assert destinations(_LIBRARY, _DATA, (nas, card)) == {
        nas: _LIBRARY / "From NAS",
        card: _LIBRARY / "From E",
    }


def test_two_sources_of_one_name_keep_their_folder_name() -> None:
    """Two folders of drive E: never mixed in one folder."""
    one, two = _DATA / "e" / "DCIM", _DATA / "e" / "Old"
    assert destinations(_LIBRARY, _DATA, (one, two)) == {
        one: _LIBRARY / "From E" / "DCIM",
        two: _LIBRARY / "From E" / "Old",
    }
