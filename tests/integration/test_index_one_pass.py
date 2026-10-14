"""A warm audit reads the index in one pass, and leaves an up-to-date schema alone."""

from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING

from media_hygiene.index import repository as repository_module
from media_hygiene.index.schema import SCHEMA_VERSION
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.audit import AuditService
from media_hygiene.services.classify import ClassifyService
from tests.support.demo import build_demo
from tests.support.runtime import make_runtime

if TYPE_CHECKING:
    from pathlib import Path

    import pytest

    from media_hygiene.paths.locations import Locations

_TABLES = "SELECT name FROM sqlite_master WHERE type = 'table'"
_ONE_FILE = "FROM files WHERE path = '"  # values are shown bound


def traced_audit(
    locations: Locations, monkeypatch: pytest.MonkeyPatch, *, classify: bool = False
) -> list[str]:
    """Run an audit (or `classify`), recording every SQL statement the index runs."""
    statements: list[str] = []
    real = sqlite3.connect

    def connect(target: str) -> sqlite3.Connection:
        connection = real(target)
        connection.set_trace_callback(statements.append)
        return connection

    monkeypatch.setattr(sqlite3, "connect", connect)
    service = ClassifyService if classify else AuditService
    service(make_runtime(locations), NullProgress()).run()
    monkeypatch.undo()
    return statements


def test_a_warm_audit_reads_no_row_one_by_one(
    locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Every file is answered from the rows read at once below each folder."""
    build_demo(locations.data_dir)
    cold = traced_audit(locations, monkeypatch)
    assert not [statement for statement in cold if _ONE_FILE in statement]
    warm = traced_audit(locations, monkeypatch)
    assert not [statement for statement in warm if _ONE_FILE in statement]
    assert sum(
        "FROM files WHERE path >= '" in s and "partial_digest" in s for s in warm
    )
    assert not [statement for statement in warm if "CREATE TABLE" in statement]


def test_a_warm_classify_reads_no_row_one_by_one(
    locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`classify` reads the index at once too (TODO 0157)."""
    build_demo(locations.data_dir)
    traced_audit(locations, monkeypatch)
    warm = traced_audit(locations, monkeypatch, classify=True)
    assert not [statement for statement in warm if _ONE_FILE in statement]


def test_an_index_of_the_previous_version_still_upgrades(tmp_path: Path) -> None:
    """Skipping the up-to-date check never skips an upgrade."""
    index_file = tmp_path / "index.sqlite"
    with repository_module.FactsRepository.open(index_file) as index:
        index.connection.execute("DROP TABLE measures")
        index.connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION - 1}")
    with repository_module.FactsRepository.open(index_file) as index:
        tables = {row[0] for row in index.connection.execute(_TABLES)}
        version = index.connection.execute("PRAGMA user_version").fetchone()
    assert "measures" in tables
    assert version == (SCHEMA_VERSION,)
