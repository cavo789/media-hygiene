"""Rich progress bars: a bar for known totals, a running count otherwise."""

from __future__ import annotations

import io

import pytest
from rich.console import Console

from media_hygiene.console.progress import RichProgress
from media_hygiene.console.progress_columns import clock
from media_hygiene.constants import Locale
from media_hygiene.i18n import active, install
from media_hygiene.scan.progress import Step


def drawn(total: int | None, *, is_terminal: bool = True) -> str:
    """Run one step of one unit and return what was written to the console."""
    buffer = io.StringIO()
    progress = RichProgress(Console(file=buffer, force_terminal=is_terminal))
    progress.start(Step("Working", "What it does"), total)
    progress.advance()
    progress.stop()
    return buffer.getvalue()


@pytest.mark.parametrize("total", [3, None])
def test_steps_are_drawn(total: int | None) -> None:
    """Known and unknown totals both draw the step."""
    output = drawn(total)
    assert "Working" in output
    assert "What it does" in output
    assert "elapsed 0:00:00" in output
    assert ("left" in output) is (total is not None)


def test_nothing_is_drawn_for_empty_steps_or_without_terminal() -> None:
    """A step without work, or a console that is not a terminal, stays silent."""
    assert not drawn(0)
    assert not drawn(5, is_terminal=False)


def test_counts_keep_the_language_of_their_creation() -> None:
    """Counts use the separators of the language active when the bar was created."""
    install(Locale.FR)
    buffer = io.StringIO()
    progress = RichProgress(Console(file=buffer, force_terminal=True, width=120))
    progress.start(Step("Working"), 12345)
    for _step in range(1234):
        progress.advance()
    progress.stop()
    assert "1.234/12.345" in buffer.getvalue()


def test_a_weighted_step_counts_files_and_follows_bytes() -> None:
    """The count shows files; the bar follows the weight (a large file first)."""
    buffer = io.StringIO()
    progress = RichProgress(Console(file=buffer, force_terminal=True, width=120))
    progress.start(Step("Copying", total_weight=1000), 3)
    progress.advance(900)
    progress.stop()
    assert "1/3" in buffer.getvalue()


def test_durations_beyond_a_day_name_the_days_in_the_bar_language() -> None:
    """`1 jour 19:54:03` in French, never Python's English `1 day, 19:54:03`."""
    install(Locale.FR)
    assert clock(158_043, active()) == "1 jour 19:54:03"
    assert clock(2 * 86_400, active()) == "2 jours 0:00:00"
    assert clock(59, active()) == "0:00:59"
    assert clock(None, active()) == "…"


def test_the_file_at_hand_is_shown_under_the_bar() -> None:
    """`current` draws one line under the bar: what is being done right now."""
    buffer = io.StringIO()
    progress = RichProgress(Console(file=buffer, force_terminal=True, width=120))
    progress.start(Step("Cleaning", "What it does"), 2)
    progress.current("Moving a duplicate copy to the quarantine: C:\\Photos\\a.jpg")
    progress.advance()
    progress.stop()
    progress.current("ignored once the step is over")
    assert "quarantine: C:\\Photos\\a.jpg" in buffer.getvalue()
