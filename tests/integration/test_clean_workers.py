"""`[clean] workers`: how many files `clean` and `undo` handle at once (0161)."""

from __future__ import annotations

import threading
import time
from dataclasses import replace
from typing import TYPE_CHECKING

import pytest

from media_hygiene.actions import parallel
from media_hygiene.config.loader import load_settings
from media_hygiene.errors import ConfigError
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.audit import AuditService
from media_hygiene.services.clean import CleanService
from media_hygiene.services.undo import resolve_run_id, undo_run
from tests.support.demo import build_demo
from tests.support.runtime import make_runtime

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    from media_hygiene.actions.parallel import Runner
    from media_hygiene.paths.locations import Locations


def test_four_by_default_then_file_then_environment(
    locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """4 unless set; `config.toml` sets it, the environment overrides the file."""
    assert load_settings(locations).settings.clean.workers == parallel.WORKERS == 4
    locations.config_file.write_text("[clean]\nworkers = 2\n")
    assert load_settings(locations).settings.clean.workers == 2
    monkeypatch.setenv("MEDIA_HYGIENE_CLEAN__WORKERS", "1")
    assert load_settings(locations).settings.clean.workers == 1


@pytest.mark.parametrize("value", ["0", "-1", '"many"'])
def test_zero_or_less_is_refused(locations: Locations, value: str) -> None:
    """At least one file at a time: 0, a negative or a word names the key."""
    locations.config_file.write_text(f"[clean]\nworkers = {value}\n")
    with pytest.raises(ConfigError, match=r"'workers' in \[clean\]"):
        load_settings(locations)


class _Watch:
    """Wrap `run_all`: record each runner's workers and the most files at once."""

    def __init__(self) -> None:
        """Nothing seen yet."""
        self.workers: list[int] = []
        self.peak = 0
        self._running = 0
        self._lock = threading.Lock()

    def run_all[T](self, actions: Iterable[T], runner: Runner[T]) -> None:
        """Run the actions as `run_all` does, counting those under way."""
        self.workers.append(runner.workers)
        parallel.run_all(actions, replace(runner, work=self._counted(runner.work)))

    def _counted[T](self, work: Callable[[T], None]) -> Callable[[T], None]:
        """The same work, counted while it runs."""

        def counted(action: T) -> None:
            with self._lock:
                self._running += 1
                self.peak = max(self.peak, self._running)
            time.sleep(0.005)  # leave time to another worker, if there is one
            try:
                work(action)
            finally:
                with self._lock:
                    self._running -= 1

        return counted


def test_clean_and_undo_handle_one_file_at_a_time_when_set_to_one(
    locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`workers = 1`: clean then undo never handle two files at once."""
    build_demo(locations.data_dir)
    locations.config_file.write_text("[clean]\nworkers = 1\n")
    runtime = make_runtime(locations)
    cleaning, undoing = _Watch(), _Watch()
    monkeypatch.setattr("media_hygiene.actions.clean.run_all", cleaning.run_all)
    monkeypatch.setattr("media_hygiene.actions.undo.run_all", undoing.run_all)
    findings = AuditService(runtime, NullProgress()).run()
    service = CleanService(runtime, NullProgress())
    _run_id, outcome = service.execute(service.feasible(findings.plan))
    assert outcome.done > 1
    restored = undo_run(runtime, resolve_run_id(runtime, None), NullProgress())
    assert restored.done == outcome.done
    for watch in (cleaning, undoing):
        assert watch.workers
        assert set(watch.workers) == {1}
        assert watch.peak == 1


def test_clean_and_undo_follow_the_setting(
    locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`workers = 2`: clean and undo hand their runners two workers."""
    build_demo(locations.data_dir)
    locations.config_file.write_text("[clean]\nworkers = 2\n")
    runtime = make_runtime(locations)
    cleaning, undoing = _Watch(), _Watch()
    monkeypatch.setattr("media_hygiene.actions.clean.run_all", cleaning.run_all)
    monkeypatch.setattr("media_hygiene.actions.undo.run_all", undoing.run_all)
    findings = AuditService(runtime, NullProgress()).run()
    service = CleanService(runtime, NullProgress())
    service.execute(service.feasible(findings.plan))
    undo_run(runtime, resolve_run_id(runtime, None), NullProgress())
    for watch in (cleaning, undoing):
        assert 2 in watch.workers  # a single file or the orphans: 1, as before
        assert watch.peak <= 2
