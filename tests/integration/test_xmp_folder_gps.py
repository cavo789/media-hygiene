"""`xmp` and `[tags] xmp_folder_gps`: a photo without GPS gets its folder town's place.

TODO 0230. A folder `Saint-Jean de Luz` (spaces, 0229) is GeoNames' Saint-Jean-de-Luz;
its two unlocated photos get its centre, the located one keeps its own; a folder with
no town name gets nothing; `undo` takes every sidecar back.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

import pytest
from typer.testing import CliRunner

from media_hygiene.tags.xmp_doc import parse
from media_hygiene.tags.xmp_gps import LATITUDE, LONGITUDE
from media_hygiene.tags.xmp_places import CITY, COUNTRY, simple_value
from tests.support.cli import point_mounts, run
from tests.support.scenes import Shot, write_shot

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.paths.locations import Locations

_LUZ_BEACH: Final = (43.3895, -1.6630)  # by the bay, in the town


@pytest.fixture(name="photos")
def photos_fixture(locations: Locations, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Two unlocated photos and a located one in `Saint-Jean de Luz`, one elsewhere."""
    point_mounts(locations, monkeypatch)
    folder = locations.data_dir / "c" / "Photos" / "2019" / "Saint-Jean de Luz"
    for seed in (11, 12):
        write_shot(
            folder / f"IMG_{seed}.jpg",
            Shot(seed, taken_at="2019:08:0{seed % 10} 10:00:00"),
        )
    write_shot(folder / "IMG_13.jpg", Shot(13), _LUZ_BEACH)
    write_shot(
        locations.data_dir / "c" / "Photos" / "Vacances" / "IMG_14.jpg", Shot(14)
    )
    return folder


def _said(runner: CliRunner, *args: str) -> str:
    """Run a command that must succeed; its output on one line."""
    result = run(runner, *args)
    assert result.exit_code == 0, result.output
    return " ".join(result.output.split())


def _turn_on(locations: Locations) -> None:
    """`[tags] xmp_folder_gps = true`."""
    config = locations.config_dir / "config.toml"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text("[tags]\nxmp_folder_gps = true\n", "utf-8")


def test_the_unlocated_photos_get_their_folder_towns_position(
    photos: Path, locations: Locations
) -> None:
    """Said in the dry run; written with --apply; the located one untouched; undone."""
    _turn_on(locations)
    runner = CliRunner()
    assert run(runner, "audit").exit_code == 0
    shown = _said(runner, "xmp")
    assert (
        "2 photos without GPS get the position of their folder's town "
        "(its centre, approximate): Saint-Jean-de-Luz 2." in shown
    )
    written = _said(runner, "xmp", "--apply")
    assert "2 sidecars written and read back" in written
    for seed in (11, 12):
        doc = parse((photos / f"IMG_{seed}.jpg.xmp").read_bytes())
        assert simple_value(doc, LATITUDE).startswith("43,23.")
        assert simple_value(doc, LATITUDE).endswith("N")
        assert simple_value(doc, LONGITUDE).startswith("1,39.")
        assert simple_value(doc, LONGITUDE).endswith("W")
        assert simple_value(doc, CITY) == "Saint-Jean-de-Luz"
        assert simple_value(doc, COUNTRY) == "France"
    assert not (photos / "IMG_13.jpg.xmp").exists()
    assert not list((locations.data_dir / "c" / "Photos" / "Vacances").glob("*.xmp"))
    run_id = written.split("undo ")[1].split()[0].strip("'")
    assert run(runner, "undo", run_id, "--yes").exit_code == 0
    assert not list(locations.data_dir.rglob("*.xmp"))


def test_turned_off_again_the_positions_are_taken_back(
    photos: Path, locations: Locations
) -> None:
    """Ours, and the town and country that came with them, leave the sidecars."""
    _turn_on(locations)
    runner = CliRunner()
    assert run(runner, "audit").exit_code == 0
    assert "2 sidecars written" in _said(runner, "xmp", "--apply")
    (locations.config_dir / "config.toml").write_text("", "utf-8")
    assert "2 sidecars written" in _said(runner, "xmp", "--apply")
    for seed in (11, 12):
        doc = parse((photos / f"IMG_{seed}.jpg.xmp").read_bytes())
        assert (simple_value(doc, LATITUDE), simple_value(doc, CITY)) == ("", "")
    assert "Nothing to write." in _said(runner, "xmp", "--apply")


def test_without_the_setting_no_position_is_written(photos: Path) -> None:
    """Off by default: nothing said, nothing to write."""
    runner = CliRunner()
    assert run(runner, "audit").exit_code == 0
    shown = _said(runner, "xmp")
    assert "position of their folder" not in shown
    assert "0 sidecars to write" in shown
    assert not list(photos.glob("*.xmp"))
