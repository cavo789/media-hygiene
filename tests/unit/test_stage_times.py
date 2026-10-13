"""Where an audit spends its time: the stopwatch and its line."""

from __future__ import annotations

import pytest

from media_hygiene.console.stage_times import short_duration, stages_line
from media_hygiene.scan.stopwatch import Stage, StageTime, Stopwatch

STOP = "stop"


def test_a_stage_run_twice_adds_up_and_stages_keep_their_order() -> None:
    """Times come back in the order stages run, whatever order they were timed in."""
    watch = Stopwatch()
    with watch.timing(Stage.SIMILAR):
        pass
    with watch.timing(Stage.LISTING):
        pass
    first = watch.times()[1].seconds
    with watch.timing(Stage.SIMILAR):
        pass
    times = watch.times()
    assert [item.stage for item in times] == [Stage.LISTING, Stage.SIMILAR]
    assert times[1].seconds >= first


def test_a_stage_that_raises_is_still_timed() -> None:
    """An interrupted stage keeps its time."""
    watch = Stopwatch()
    with pytest.raises(ValueError, match=STOP), watch.timing(Stage.COLOURS):
        raise ValueError(STOP)
    assert [item.stage for item in watch.times()] == [Stage.COLOURS]


def test_every_stage_has_a_label_on_the_line() -> None:
    """Every stage is named, with its duration, in one line."""
    line = stages_line([StageTime(stage, 1.25) for stage in Stage])
    assert line is not None
    assert line.startswith("Time per step: listing 1.2 s · cache upkeep")
    assert line.count("·") == len(Stage) - 1


def test_nothing_timed_prints_nothing() -> None:
    """No line without a timed stage."""
    assert stages_line([]) is None


def test_long_steps_read_as_minutes() -> None:
    """Tenths of a second below a minute, minutes beyond."""
    assert short_duration(0.04) == "0.0 s"
    assert short_duration(125) == "2 min 05 s"
