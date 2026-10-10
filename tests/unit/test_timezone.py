"""The user's time zone: checked, installed for the run, its absence noticed."""

from __future__ import annotations

import os
import time
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest
from pydantic import ValidationError

from media_hygiene.actions.journal import JournalEntry
from media_hygiene.actions.kinds import ActionKind, Phase, Status
from media_hygiene.actions.runs import list_run_ids
from media_hygiene.config.settings import GeneralSettings
from media_hygiene.config.zone import apply_timezone, timezone_unknown

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path


@pytest.fixture
def process_zone() -> Iterator[None]:
    """Give the process zone back after the test, whatever it set."""
    saved = os.environ.get("TZ")
    yield
    if saved is None:
        os.environ.pop("TZ", None)
    else:
        os.environ["TZ"] = saved
    time.tzset()


@pytest.mark.usefixtures("process_zone")
def test_the_configured_zone_becomes_local_time() -> None:
    """Folder names and run identifiers follow the zone written in config.toml."""
    apply_timezone("America/Montreal")
    winter = datetime(2026, 1, 15, 12, tzinfo=UTC).astimezone()
    assert winter.hour == 7
    assert not timezone_unknown()


def test_an_unknown_zone_is_refused() -> None:
    """A typo is caught when the settings load, not silently taken as UTC."""
    assert GeneralSettings(timezone="Europe/Brussels").timezone == "Europe/Brussels"
    with pytest.raises(ValidationError, match="Europe/Brussels"):
        GeneralSettings(timezone="Europe/Bruxelles")


def test_runs_are_ordered_by_when_they_started(tmp_path: Path) -> None:
    """A name earlier in local time (a zone set west of UTC) is still the newest."""
    for run_id, hour in (("20261010-140000", 14), ("20261010-100000", 15)):
        entry = JournalEntry(
            seq=1,
            phase=Phase.CLEAN,
            status=Status.DONE,
            action=ActionKind.DELETE_DUPLICATE,
            path="/data/c/a.jpg",
            host_path="C:\\a.jpg",
            size=1,
            mtime_ns=1,
            at=datetime(2026, 10, 10, hour, tzinfo=UTC),
        )
        (tmp_path / f"{run_id}.jsonl").write_text(entry.model_dump_json() + "\n")
    assert list_run_ids(tmp_path) == ["20261010-100000", "20261010-140000"]
