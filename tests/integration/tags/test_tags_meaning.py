"""`tags --meaning`, then `search` by what the photos show: the colour model.

The real model is never downloaded here (a measure does that, never CI): the files
are faked, and the model is `tests.support.meaning`: a picture's vector is its colour.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from typing import TYPE_CHECKING

import pytest

from media_hygiene.cli import meaning_flow
from media_hygiene.meaning.clip import MODEL
from media_hygiene.meaning.files import clip_known
from media_hygiene.services import search_meaning
from tests.support.cli import run
from tests.support.meaning import ColourImages, ColourWords
from tests.support.tagging import BURST

if TYPE_CHECKING:
    from pathlib import Path

    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations

# 15 event shots, a burst of three, one copy: every photo of the tree.
PHOTOS = 15 + BURST + 1


@pytest.fixture
def model(monkeypatch: pytest.MonkeyPatch) -> list[Path]:
    """The colour model in place of CLIP; its files "downloaded" when asked.

    Returns:
        The cache folders the download was asked for.
    """
    downloads: list[Path] = []

    def downloaded(cache: Path) -> object:
        downloads.append(cache)
        known = clip_known(cache)
        known.vision.parent.mkdir(parents=True, exist_ok=True)
        for path in (known.vision, known.text, known.tokenizer, known.dense):
            path.write_bytes(b"model")
        return known

    monkeypatch.setattr(meaning_flow, "clip_files", downloaded)
    monkeypatch.setattr(meaning_flow, "ClipImages", ColourImages)
    monkeypatch.setattr(search_meaning, "ClipWords", ColourWords)
    return downloads


def _vectors(locations: Locations) -> int:
    """How many vectors the index holds."""
    with closing(sqlite3.connect(locations.cache_dir / "index.sqlite")) as connection:
        query = "SELECT COUNT(*) FROM meanings WHERE model = ?"
        return int(connection.execute(query, (MODEL,)).fetchone()[0])


def test_tags_looks_once_then_search_finds_by_meaning(
    cli: CliRunner, locations: Locations, model: list[Path]
) -> None:
    """The download said first, every photo once, the copy free; then "sea"."""
    first = run(cli, "tags", "--no-describe", "--meaning")
    assert first.exit_code == 0, first.output
    assert "894 MB" in first.output
    assert f"{PHOTOS} photos to look at" in first.output
    assert f"{PHOTOS} photos can now be found by what they show" in first.output
    assert model == [locations.cache_dir]
    assert _vectors(locations) == PHOTOS
    again = run(cli, "tags", "--no-describe", "--meaning")
    assert "every photo is looked at already" in again.output
    assert model == [locations.cache_dir]
    found = run(cli, "search", "--limit", "5", "sea")
    assert found.exit_code == 0, found.output
    assert f"{PHOTOS} photos can be found by what they show" in found.output
    table = found.output.split("can be found by what they show")[-1]
    assert table.count("IMG_beach_") == 5


def test_without_meaning_tags_looks_at_nothing(
    cli: CliRunner, locations: Locations, model: list[Path]
) -> None:
    """Opt-in: by default no model runs, and search stays on its words."""
    assert run(cli, "tags", "--no-describe").exit_code == 0
    assert _vectors(locations) == 0
    assert model == []
    found = run(cli, "search", "sea")
    assert "by what they show" not in found.output
    assert "Nothing found." in found.output


@pytest.mark.usefixtures("model")
def test_the_setting_turns_it_on_and_search_says_a_missing_model(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`[tags] meaning = true`; the model deleted since: the words alone, said."""
    monkeypatch.setenv("MEDIA_HYGIENE_TAGS__MEANING", "true")
    assert run(cli, "tags", "--no-describe").exit_code == 0
    assert _vectors(locations) == PHOTOS
    clip_known(locations.cache_dir).text.unlink()
    found = run(cli, "search", "sea")
    assert found.exit_code == 0, found.output
    assert "the words alone answer" in found.output
    assert "tags --meaning" in found.output
