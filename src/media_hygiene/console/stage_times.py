"""One line saying where an audit spent its time (`--verbosity verbose`)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from media_hygiene.console.formatting import human_duration, human_number
from media_hygiene.i18n import _
from media_hygiene.scan.stopwatch import Stage

if TYPE_CHECKING:
    from collections.abc import Sequence

    from media_hygiene.scan.stopwatch import StageTime

_SEPARATOR: Final = " · "
# Below a minute, tenths of a second tell a quick stage from an instant one.
_SHORT_SECONDS: Final = 60


def stage_label(stage: Stage) -> str:
    """Name a stage the way the user knows it.

    Args:
        stage: The stage.

    Returns:
        Its translated, lower-case label.
    """
    labels = {
        Stage.LISTING: _("listing"),
        Stage.INDEX: _("cache upkeep"),
        Stage.INTEGRITY: _("checks"),
        Stage.DIGESTS: _("fingerprints"),
        Stage.SIMILAR: _("near duplicates"),
        Stage.COLOURS: _("colours"),
        Stage.STREAMS: _("same streams"),
    }
    return labels[stage]


def short_duration(seconds: float) -> str:
    """Render a step's duration: `0.4 s`, `21.3 s`, then `3 min 05 s`.

    Args:
        seconds: The duration.

    Returns:
        The rounded duration.
    """
    if seconds < _SHORT_SECONDS:
        return _("{seconds} s").format(seconds=human_number(seconds, 1))
    return human_duration(seconds)


def stages_line(stages: Sequence[StageTime]) -> str | None:
    """Say how long each stage took, on one line.

    Args:
        stages: The stages timed, in the order they ran.

    Returns:
        `Time per step: listing 1.2 s · checks 3.4 s · …`, or None when nothing
        was timed.
    """
    if not stages:
        return None
    steps = _SEPARATOR.join(
        f"{stage_label(item.stage)} {short_duration(item.seconds)}" for item in stages
    )
    return _("Time per step: {steps}").format(steps=steps)
