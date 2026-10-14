"""The index commits as it goes: a killed run keeps what it already stored (0143)."""

from __future__ import annotations

import signal
import sqlite3
import subprocess
import sys
from contextlib import closing
from pathlib import Path
from typing import Final

import pytest

from media_hygiene.__main__ import stop_like_ctrl_c
from media_hygiene.constants import MediaKind
from media_hygiene.index.facts import FileFacts
from media_hygiene.index.repository import FactsRepository
from media_hygiene.scan.models import MediaFile

_COUNT: Final = "SELECT COUNT(*) FROM files"
_KILLED: Final = """
import os, signal, sys
from pathlib import Path
from media_hygiene.constants import MediaKind
from media_hygiene.index import repository
from media_hygiene.index.facts import FileFacts
from media_hygiene.scan.models import MediaFile
repository._COMMIT_EVERY_SECONDS = 0.0
index = repository.FactsRepository.open(Path(sys.argv[1]))
for number in range(3):
    file = MediaFile(Path(f"/data/c/{number}.jpg"), 1, 1, MediaKind.IMAGE)
    index.put(file, FileFacts(full_digest="d"))
os.kill(os.getpid(), signal.SIGKILL)
"""


def photo(number: int) -> MediaFile:
    """A photo of the index."""
    return MediaFile(Path(f"/data/c/{number}.jpg"), 1, 1, MediaKind.IMAGE)


def rows(index_file: Path) -> int:
    """The rows another connection sees: those committed."""
    with closing(sqlite3.connect(index_file)) as reader:
        found: int = reader.execute(_COUNT).fetchone()[0]
    return found


def test_rows_are_committed_every_few_seconds(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Before the interval, nothing is visible elsewhere; after it, everything."""
    clock = iter((0.0, 1.0, 10.0, 10.0))
    monkeypatch.setattr("time.monotonic", lambda: next(clock))
    index_file = tmp_path / "index.sqlite"
    with FactsRepository.open(index_file) as index:
        index.put(photo(1), FileFacts(full_digest="a"))
        assert rows(index_file) == 0
        index.put(photo(2), FileFacts(full_digest="b"))
        assert rows(index_file) == 2


def test_a_killed_run_keeps_what_it_committed(tmp_path: Path) -> None:
    """SIGKILL after the puts: the rows are in the file."""
    index_file = tmp_path / "index.sqlite"
    killed = subprocess.run(  # noqa: S603 - the test's own interpreter and script
        [sys.executable, "-c", _KILLED, str(index_file)], check=False
    )
    assert killed.returncode == -signal.SIGKILL
    assert rows(index_file) == 3


def test_docker_stop_ends_like_ctrl_c() -> None:
    """SIGTERM raises KeyboardInterrupt, which every command already handles."""
    with pytest.raises(KeyboardInterrupt):
        stop_like_ctrl_c(signal.SIGTERM, None)
