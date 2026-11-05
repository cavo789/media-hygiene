"""`upkeep`: the steps of `[routine]` in order, one removed is skipped (0519)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any

import pytest

from media_hygiene.config.routine_settings import RoutineSettings, RoutineStep
from media_hygiene.services import upkeep

if TYPE_CHECKING:
    from collections.abc import Sequence


def _runtime(*steps: RoutineStep) -> Any:  # noqa: ANN401  # a stand-in
    """The settings and output `run_upkeep` reads."""
    output = SimpleNamespace(
        title=lambda _t: None, info=lambda _t: None, warning=lambda _t: None
    )
    settings = SimpleNamespace(
        routine=RoutineSettings(steps=steps),
        clean=SimpleNamespace(purge_hint_days=30),
    )
    return SimpleNamespace(settings=settings, output=output)


@pytest.fixture(autouse=True)
def _two_runs(monkeypatch: pytest.MonkeyPatch) -> None:
    """A quarantine with one old run and one recent."""
    now = datetime.now(UTC)
    runs = (
        SimpleNamespace(run_id="old", started=now - timedelta(days=40), files=3),
        SimpleNamespace(run_id="new", started=now, files=1),
    )
    status = SimpleNamespace(
        quarantine=SimpleNamespace(runs=runs),
        analysis=SimpleNamespace(summary=None),
    )
    monkeypatch.setattr(upkeep, "read_status", lambda _r: status)


def _ran(runtime: Any, code: int = 0) -> list[tuple[str, ...]]:  # noqa: ANN401
    """Run with a recording runner."""
    ran: list[tuple[str, ...]] = []

    def run(words: Sequence[str]) -> int:
        ran.append(tuple(words))
        return code

    upkeep.run_upkeep(runtime, run)
    return ran


def test_every_step_in_order_and_only_the_old_run_purged() -> None:
    """The default list; the recent quarantine stays."""
    assert _ran(_runtime(*RoutineSettings().steps)) == [
        ("audit",),
        ("clean",),
        ("purge", "old"),
        ("reports",),
    ]


def test_a_step_removed_is_skipped_and_the_written_order_ignored() -> None:
    """`purge` left out; the routine's order kept."""
    runtime = _runtime(RoutineStep.REPORTS, RoutineStep.AUDIT)
    assert _ran(runtime) == [("audit",), ("reports",)]


def test_an_empty_list_runs_nothing() -> None:
    """Nothing asked, nothing run."""
    assert not _ran(_runtime())


def test_a_failure_stops_the_chain() -> None:
    """What follows a failed step does not run."""
    assert _ran(_runtime(*RoutineSettings().steps), code=1) == [("audit",)]


def test_each_writing_step_names_its_count_and_its_page(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """0592: `clean` and `purge`, the count then the page; no step removed."""
    now = datetime.now(UTC)
    runs = (SimpleNamespace(run_id="old", started=now - timedelta(days=40), files=7),)
    status = SimpleNamespace(
        quarantine=SimpleNamespace(runs=runs),
        analysis=SimpleNamespace(summary=SimpleNamespace(duplicate_files=12)),
    )
    monkeypatch.setattr(upkeep, "read_status", lambda _r: status)
    said: list[str] = []
    runtime = _runtime(*RoutineSettings().steps)
    runtime.output.info = said.append
    upkeep.run_upkeep(runtime, lambda _words: 0)
    assert any("12" in line and "mh reports" in line for line in said)
    assert any("7" in line and "undo --pick" in line for line in said)
    assert len(said) == 2  # audit and reports change no file
