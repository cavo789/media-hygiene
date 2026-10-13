"""`xmp` and the names of the people: opt-in, said before writing, never by default."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from media_hygiene.config.tags_settings import XMP_SOURCES
from media_hygiene.tags.models import TagSource
from media_hygiene.tags.xmp_doc import items, parse
from media_hygiene.tags.xmp_merge import PERSON_IN_IMAGE
from tests.support.cli import run

if TYPE_CHECKING:
    from pathlib import Path

    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations

_WARNING = "The names of the people go into the sidecars"


@pytest.fixture
def named(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> CliRunner:
    """The tree tagged; Léa is on every photo (the faces are not computed here)."""
    assert run(cli, "tags", "--no-describe").exit_code == 0

    def on_every_photo(connection: object, settings: object) -> dict[Path, tuple[str]]:
        del connection, settings
        photos = locations.data_dir.rglob("*.jpg")
        return dict.fromkeys(photos, ("Léa",))

    monkeypatch.setattr("media_hygiene.services.xmp_plan.people_words", on_every_photo)
    return cli


def _names(locations: Locations) -> set[str]:
    """Every name written into a sidecar."""
    return {
        name
        for sidecar in locations.data_dir.rglob("*.xmp")
        for name in items(parse(sidecar.read_bytes()).find(PERSON_IN_IMAGE))
    }


def _choose(locations: Locations, sources: str) -> None:
    """Set `[tags] xmp_sources` (the config ends in `[tags]`)."""
    config = locations.config_dir / "config.toml"
    config.write_text(config.read_text("utf-8") + f"xmp_sources = {sources}\n", "utf-8")


def test_without_the_person_source_no_name_is_written(
    named: CliRunner, locations: Locations
) -> None:
    """Sources without `person` (as by default): no `PersonInImage`, no warning."""
    _choose(locations, '["folder"]')
    result = run(named, "xmp", "--apply")
    assert result.exit_code == 0, result.output
    assert _WARNING not in " ".join(result.output.split())
    assert list(locations.data_dir.rglob("*.xmp"))
    assert _names(locations) == set()


def test_the_person_source_writes_the_names(
    named: CliRunner, locations: Locations
) -> None:
    """`person` chosen: one warning line, then the names in every sidecar."""
    _choose(locations, '["folder", "person"]')
    result = run(named, "xmp", "--apply")
    assert result.exit_code == 0, result.output
    assert _WARNING in " ".join(result.output.split())
    assert _names(locations) == {"Léa"}


def test_the_default_sources_hold_no_person() -> None:
    """Writing names next to the photos is opt-in."""
    assert TagSource.PERSON not in XMP_SOURCES
