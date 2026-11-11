"""0678: the synthetic library has the real schema; the budget catches a route grown."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from typing import TYPE_CHECKING

from media_hygiene.index.schema import SCHEMA_VERSION
from tests.measure.pages.budget import problems
from tests.measure.pages.library import Library, build

if TYPE_CHECKING:
    from pathlib import Path

_TABLE = """
| Route | Files | Cold ms | Warm ms | Budget ms |
|---|---:|---:|---:|---:|
| folders | 1,000 | 300.0 | 200.0 | 400 |
| albums | 1,000 | 1.0 | 0.2 | 100 |
"""


def _result(folders: float, albums: float) -> dict[str, object]:
    """A bench's document of two routes."""
    return {
        "files": 1000,
        "routes": {"folders": {"warm_ms": folders}, "albums": {"warm_ms": albums}},
    }


def test_the_library_has_rows_tags_faces_and_placeholders(tmp_path: Path) -> None:
    """Every file listed, tagged, its placeholder on disk; faces for some."""
    index = tmp_path / "index.sqlite"
    build(Library(index, tmp_path / "c", 200))
    with closing(sqlite3.connect(index)) as connection:
        assert connection.execute("PRAGMA user_version").fetchone() == (SCHEMA_VERSION,)
        files = connection.execute("SELECT COUNT(*) FROM files").fetchone()[0]
        tagged = connection.execute("SELECT COUNT(DISTINCT path) FROM tags").fetchone()
        faces = connection.execute("SELECT COUNT(*) FROM faces").fetchone()[0]
    assert (files, tagged[0]) == (200, 200)
    assert faces > 0
    assert len([path for path in (tmp_path / "c").rglob("*") if path.is_file()]) == 200


def test_a_route_grown_by_more_than_30_percent_fails(tmp_path: Path) -> None:
    """+30 % fails, +20 % passes; a route under 5 ms is not compared on growth."""
    table = tmp_path / "budget.md"
    table.write_text(_TABLE, encoding="utf-8")
    assert not problems(table, [_result(240.0, 0.9)])
    said = problems(table, [_result(270.0, 0.2)])
    assert len(said) == 1
    assert said[0].startswith("folders @ 1000")


def test_a_route_past_its_budget_fails(tmp_path: Path) -> None:
    """Over the budget column, whatever the growth."""
    table = tmp_path / "budget.md"
    table.write_text(_TABLE, encoding="utf-8")
    assert problems(table, [_result(200.0, 101.0)]) == [
        "albums @ 1000: 101.0 ms > budget 100.0 ms"
    ]
