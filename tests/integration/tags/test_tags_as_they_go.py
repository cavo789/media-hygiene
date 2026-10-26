"""`tags`: the model's words reach the search as each photo is described (0353)."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from typing import TYPE_CHECKING

import pytest

from media_hygiene.index.read_only import connect_read_only
from media_hygiene.services.tags import TagStep
from tests.support.cli import run
from tests.support.fake_ollama import describe, images, map_answer

if TYPE_CHECKING:
    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations
    from tests.support.fake_ollama import FakeOllama

_MODEL_ROWS = (
    "SELECT path, source, value FROM tags WHERE source IN ('caption', 'vision')"
    " ORDER BY path, source, value"
)


def _model_rows(locations: Locations) -> list[tuple[str, str, str]]:
    """Every word of the model in the index, sorted."""
    index = locations.cache_dir / "index.sqlite"
    with closing(sqlite3.connect(index)) as connection:
        return [tuple(row) for row in connection.execute(_MODEL_ROWS)]


def test_a_search_open_during_the_run_reads_the_words_as_they_come(
    cli: CliRunner, fake: FakeOllama, locations: Locations
) -> None:
    """Read while `tags` writes, never locked: the words grow from the first answers."""
    index = locations.cache_dir / "index.sqlite"
    seen: list[int] = []

    def answer(body: dict[str, object]) -> dict[str, object]:
        if not images(body):
            return map_answer(body)
        with closing(connect_read_only(index)) as reader:  # a search page reading
            seen.append(
                reader.execute(
                    "SELECT COUNT(*) FROM tags WHERE source = 'vision'"
                ).fetchone()[0]
            )
        return describe(body)

    fake.answer = answer
    result = run(cli, "tags")
    assert result.exit_code == 0, result.output
    assert "locked" not in result.output
    assert seen == sorted(seen)
    assert seen[-1] > 0  # words of earlier answers, before the end of the run


def test_a_run_killed_before_its_end_keeps_the_words_described(
    cli: CliRunner, locations: Locations
) -> None:
    """The end of the run never comes: every photo described has its words."""
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(TagStep, "derive", lambda _self, _work: 0)
        first = run(cli, "tags")
    assert first.exit_code == 0, first.output
    killed = _model_rows(locations)
    assert killed
    assert run(cli, "tags").exit_code == 0  # the end of the run: nothing new to write
    assert _model_rows(locations) == killed


def test_the_words_are_those_of_the_end_of_run_derive(
    cli: CliRunner, locations: Locations
) -> None:
    """Equivalence: as they go, then from the cache alone, the same rows."""
    assert run(cli, "tags").exit_code == 0
    as_they_go = _model_rows(locations)
    index = locations.cache_dir / "index.sqlite"
    with closing(sqlite3.connect(index)) as connection:
        connection.execute("DELETE FROM tags WHERE source IN ('caption', 'vision')")
        connection.commit()
    assert run(cli, "tags").exit_code == 0  # answers cached: the old derive alone
    assert _model_rows(locations) == as_they_go
