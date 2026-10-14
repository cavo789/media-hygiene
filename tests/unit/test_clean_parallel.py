"""A clean acts on a few files at a time, the screen updated from one thread (0149)."""

from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import TYPE_CHECKING, Final

import pytest

from media_hygiene.actions.parallel import Runner, run_all
from media_hygiene.constants import MediaKind
from media_hygiene.scan.models import MediaFile

if TYPE_CHECKING:
    from media_hygiene.actions.clean_step import Planned

_FILES: Final = 30
_WORKERS: Final = 3


def planned(index: int) -> Planned:
    """One action doing nothing but wait a little."""
    file = MediaFile(Path(f"/data/x/{index}.jpg"), index, 1, MediaKind.IMAGE)
    return file, "{path}", lambda: time.sleep(0.002)


def test_a_few_at_a_time_shown_from_the_calling_thread() -> None:
    """Never more than the workers at once; each action shown once, by the caller."""
    lock = threading.Lock()
    running = peak = 0
    shown: list[int] = []
    caller = threading.get_ident()

    def work(action: Planned) -> None:
        nonlocal running, peak
        with lock:
            running += 1
            peak = max(peak, running)
        action[2]()
        with lock:
            running -= 1

    def show(action: Planned) -> None:
        assert threading.get_ident() == caller
        shown.append(action[0].size)

    run_all([planned(i) for i in range(_FILES)], Runner(work, show, _WORKERS))
    assert sorted(shown) == list(range(_FILES))
    assert peak <= _WORKERS


def test_a_stop_starts_no_new_file() -> None:
    """Ctrl+C while files run: the run stops, the rest never starts."""
    started: list[int] = []

    def work(action: Planned) -> None:
        started.append(action[0].size)
        action[2]()

    def show(_action: Planned) -> None:
        raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        run_all([planned(i) for i in range(_FILES)], Runner(work, show, _WORKERS))
    assert len(started) < _FILES
