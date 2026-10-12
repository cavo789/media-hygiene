"""`tags`: cheap words, describe, inherit, resume, --no-describe, --sample, refusals."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from typing import TYPE_CHECKING

from tests.support.cli import run
from tests.support.tagging import BURST, write_tags_config

if TYPE_CHECKING:
    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations
    from tests.support.fake_ollama import FakeOllama

# 15 event shots, one burst of three (one asked), one copy (none asked).
ASKED = 16
PHOTOS = 15 + BURST + 1


def tags_of(locations: Locations, ending: str) -> dict[str, list[str]]:
    """The tags of the file whose path ends so, by source."""
    found: dict[str, list[str]] = {}
    index = locations.cache_dir / "index.sqlite"
    with closing(sqlite3.connect(index)) as connection:
        rows = connection.execute(
            "SELECT source, value FROM tags WHERE path LIKE ? ORDER BY rowid",
            (f"%{ending}",),
        )
        for source, value in rows:
            found.setdefault(source, []).append(value)
    return found


def test_describe_once_per_burst_and_copy_then_from_the_cache(
    cli: CliRunner, fake: FakeOllama, locations: Locations
) -> None:
    """The burst and the copy inherit; the next runs ask nothing new."""
    first = run(cli, "tags")
    assert first.exit_code == 0, first.output
    assert fake.described() == ASKED
    assert f"{ASKED} photos described" in first.output
    assert f"{PHOTOS} photos have the words of the vision model; 0 left" in (
        first.output.replace("\n", " ")
    )
    burst = tags_of(locations, "Durbuy - ours/IMG_0.jpg")
    assert burst["vision"] == ["snow"]
    assert burst["caption"] == ["Snow on a mountain."]
    assert burst["folder"] == ["Durbuy", "ours"]
    assert burst["date"] == ["2022", "December", "winter", "Christmas"]
    assert tags_of(locations, "Copies/IMG_beach_0.jpg")["vision"] == ["beach", "sea"]
    asked = len(fake.calls)
    again = run(cli, "tags")
    assert again.exit_code == 0, again.output
    assert len(fake.calls) == asked
    assert run(cli, "tags", "--no-describe").exit_code == 0
    assert len(fake.calls) == asked
    inventory = run(cli, "inventory", "--format", "csv")
    assert inventory.exit_code == 0, inventory.output
    written = next(locations.reports_dir.rglob("inventory.csv")).read_text("utf-8")
    assert "Durbuy; ours; 2022; December; winter; Christmas; snow" in written


def test_no_describe_asks_nothing(cli: CliRunner, fake: FakeOllama) -> None:
    """The cheap words only; nobody tagged by the model yet."""
    result = run(cli, "tags", "--no-describe")
    assert result.exit_code == 0, result.output
    assert fake.calls == []
    assert f"{PHOTOS} files: " in result.output
    assert f"{ASKED} photos to describe" in result.output


def test_without_a_model_the_cheap_words_and_a_tip(
    cli: CliRunner, fake: FakeOllama, locations: Locations
) -> None:
    """The tool tags without a model, and says how to add one."""
    write_tags_config(locations.config_dir, fake.url, ai="")
    result = run(cli, "tags")
    assert result.exit_code == 0, result.output
    assert fake.calls == []
    assert "Set [classify.ai] model" in result.output
    assert tags_of(locations, "IMG_beach_0.jpg")["date"][0] == "2021"


def test_a_long_run_asks_first_and_yes_describes(
    cli: CliRunner, fake: FakeOllama, locations: Locations
) -> None:
    """Above confirm_above, no terminal means no; --yes describes."""
    write_tags_config(
        locations.config_dir, fake.url, 'model = "vision"\nconfirm_above = 2'
    )
    refused = run(cli, "tags")
    assert refused.exit_code == 0, refused.output
    assert fake.described() == 0
    assert "--sample 50" in refused.output
    assert run(cli, "tags", "--yes").exit_code == 0
    assert fake.described() == ASKED


def test_a_sample_is_timed_and_kept(cli: CliRunner, fake: FakeOllama) -> None:
    """Two photos, their words, the estimate; the full run skips them."""
    result = run(cli, "tags", "--sample", "2")
    assert result.exit_code == 0, result.output
    assert fake.described() == 2
    assert "A full run would describe 14 more photos" in result.output
    assert run(cli, "tags").exit_code == 0
    assert fake.described() == ASKED


def test_path_limits_the_run(
    cli: CliRunner, fake: FakeOllama, locations: Locations
) -> None:
    """Only the burst folder: one photo asked, three tagged."""
    folder = locations.data_dir / "c" / "Photos" / "2022"
    result = run(cli, "tags", "--path", str(folder))
    assert result.exit_code == 0, result.output
    assert fake.described() == 1
    assert f"{BURST} files: " in result.output
    empty = run(cli, "tags", "--path", str(locations.data_dir / "nowhere"))
    assert empty.exit_code == 0
    assert "No photo nor video of the index" in empty.output


def test_a_model_without_vision_is_refused(cli: CliRunner, fake: FakeOllama) -> None:
    """The cheap words are written; nothing is sent; the message names the model."""
    fake.capabilities = ("completion",)
    result = run(cli, "tags")
    assert result.exit_code == 1
    assert "The model vision cannot see images" in result.output
    assert fake.described() == 0


def test_without_an_index_tags_says_to_audit_first(
    cli: CliRunner, locations: Locations
) -> None:
    """No index file: a clear error, nothing created."""
    (locations.cache_dir / "index.sqlite").unlink()
    result = run(cli, "tags")
    assert result.exit_code == 1
    assert "Run 'audit' first" in result.output
    assert not (locations.cache_dir / "index.sqlite").exists()
