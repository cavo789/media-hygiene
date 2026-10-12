"""`status`: one state per test, read from the tool folders alone."""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from typing import TYPE_CHECKING

from media_hygiene.cli.status_next import advise_status
from media_hygiene.cli.status_view import status_lines
from media_hygiene.constants import CLASSIFY_PLAN_FILE_NAME
from media_hygiene.index.walks import last_walk
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.services.status import read_status
from tests.support.runtime import make_locations, make_runtime, output_of

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.services.runtime import Runtime

_OLD_RUN = "20200101-120000"


def _shown(runtime: Runtime) -> str:
    """Print the lines and the advice of `status`, as the command does.

    Args:
        runtime: The runtime.

    Returns:
        Everything printed.
    """
    status = read_status(runtime)
    for line in status_lines(status):
        runtime.output.info(line)
    advise_status(runtime, status)
    runtime.output.finish()
    return output_of(runtime)


def _decisions(runtime: Runtime, document: dict[str, object]) -> None:
    """Write `decisions.json` in the reports folder.

    Args:
        runtime: The runtime.
        document: Its content, beyond the version and the roots.
    """
    path = runtime.locations.reports_dir / "decisions.json"
    path.write_text(json.dumps({"version": 1, "roots": [], **document}), "utf-8")


def test_nothing_yet_suggests_an_audit(tmp_path: Path) -> None:
    """Empty tool folders: no audit, empty quarantine, the audit comes next."""
    shown = _shown(make_runtime(make_locations(tmp_path)))
    assert "No audit yet." in shown
    assert "Quarantine: empty." in shown
    assert "start with an audit" in shown
    assert "Not looked at" not in shown


def test_missing_mounts_are_said_never_fatal(tmp_path: Path) -> None:
    """Journal and quarantine not mounted: said in one line."""
    locations = make_locations(tmp_path, MountKind.JOURNAL, MountKind.QUARANTINE)
    shown = _shown(make_runtime(locations))
    assert "Not looked at (not mounted): /journal, /quarantine." in shown


def test_an_old_quarantine_suggests_purging_that_run(tmp_path: Path) -> None:
    """A quarantine older than purge_hint_days: purge that run, said with its age."""
    runtime = make_runtime(make_locations(tmp_path))
    folder = runtime.locations.quarantine_dir / _OLD_RUN / "c"
    folder.mkdir(parents=True)
    (folder / "IMG_1.jpg").write_bytes(b"x" * 10)
    shown = _shown(runtime)
    assert "Quarantine: 1 files, 10 B, 1 run, set aside 2020-01-01" in shown
    assert f"the quarantine of {_OLD_RUN} is more than 30 days old" in shown
    assert f"purge {_OLD_RUN}" in shown


def test_bursts_left_to_see_come_before_the_quarantine(tmp_path: Path) -> None:
    """Series still `todo`: review, its page port published."""
    runtime = make_runtime(make_locations(tmp_path))
    _decisions(runtime, {"bursts": [{"status": "todo", "kept": ["a.jpg", "b.jpg"]}]})
    shown = _shown(runtime)
    assert "Burst review: 1 series still to see." in shown
    assert "finish the burst review" in shown
    assert "-p 127.0.0.1:8088:8088" in shown


def test_decisions_not_applied_suggest_clean_decisions(tmp_path: Path) -> None:
    """Shots set aside and near groups decided: clean --tier near --decisions."""
    runtime = make_runtime(make_locations(tmp_path))
    near = {"kept": "a.jpg", "copies": ["b.jpg"], "action": "planned"}
    bursts = [{"kept": ["c.jpg"], "discarded": ["d.jpg"]}]
    _decisions(runtime, {"bursts": bursts, "near": [near]})
    shown = _shown(runtime)
    assert "1 shots set aside, 1 near duplicate groups" in shown
    assert "clean --tier near --decisions" in shown


def test_an_unreadable_decisions_file_is_said(tmp_path: Path) -> None:
    """A broken decisions.json: one line, no step built on it."""
    runtime = make_runtime(make_locations(tmp_path))
    (runtime.locations.reports_dir / "decisions.json").write_text("{", "utf-8")
    assert "decisions.json cannot be read" in _shown(runtime)


def test_a_proposal_not_sorted_suggests_sort(tmp_path: Path) -> None:
    """A plan.json and no sort run since: sort comes next."""
    runtime = make_runtime(make_locations(tmp_path))
    folder = runtime.locations.reports_dir / "20261010-120000-classify"
    folder.mkdir()
    (folder / CLASSIFY_PLAN_FILE_NAME).write_text("{}", "utf-8")
    shown = _shown(runtime)
    assert "Last classify proposal:" in shown
    assert "not sorted yet." in shown
    assert "'sort' applies the edited workbook" in shown


def test_the_cache_alone_tells_the_date_of_the_last_audit(tmp_path: Path) -> None:
    """No report, an index with a walk: the date, read without changing the file."""
    runtime = make_runtime(make_locations(tmp_path, MountKind.REPORTS))
    index = runtime.index_file
    assert index is not None
    with closing(sqlite3.connect(index)) as connection:
        connection.execute("CREATE TABLE roots (path TEXT, walked_at TEXT)")
        connection.execute(
            "INSERT INTO roots VALUES ('/data', '2026-10-01T10:00:00+00:00')"
        )
        connection.commit()
    shown = _shown(runtime)
    assert "Last audit: 2026-10-01" in shown
    assert "mount /reports to see its figures" in shown
    assert "start with an audit" not in shown


def test_an_index_without_walks_or_unreadable_tells_nothing(tmp_path: Path) -> None:
    """No roots table, not a database, no file: no date."""
    index = tmp_path / "index.sqlite"
    assert last_walk(index) is None
    assert last_walk(None) is None
    index.write_bytes(b"not a database")
    assert last_walk(index) is None
