"""The year folder of each file: one event or one meaningful folder, one year."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.classify.models import SortReason

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from pathlib import Path

    from media_hygiene.classify.models import Dating, Event, MediaInput
    from media_hygiene.classify.signals import Signal


def year_folders(
    files: Sequence[MediaInput],
    datings: Mapping[Path, Dating],
    grouping: tuple[Mapping[Path, Signal], Mapping[Path, Event], str],
) -> dict[Path, int]:
    """The year folder of each file.

    With `event_year = "start"`, an event takes the year of its start (a New Year's Eve
    party stays whole), and so does a meaningful folder, from its oldest file.

    Args:
        files: Every file.
        datings: Their dates.
        grouping: Their signals, their events, and `[classify] event_year`.

    Returns:
        The year of each file.
    """
    signals, event_of, mode = grouping
    years = {file.path: datings[file.path].when.year for file in files}
    if mode != "start":
        return years
    oldest: dict[Path, int] = {}
    for file in files:
        if signals[file.path].reason is SortReason.EXISTING_FOLDER:
            folder = file.path.parent
            oldest[folder] = min(oldest.get(folder, years[file.path]), years[file.path])
    for file in files:
        event = event_of.get(file.path)
        if event is not None:
            years[file.path] = event.start.year
        elif file.path.parent in oldest:
            years[file.path] = oldest[file.path.parent]
    return years
