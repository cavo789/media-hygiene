"""The year and month of each file, and the proposals a `--year` or `--path` run keeps.

One event or one meaningful folder, one year and one month.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.classify.models import DateSource, SortReason
from media_hygiene.paths.host_paths import is_within

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from pathlib import Path

    from media_hygiene.classify.models import Dating, Event, MediaInput, Proposal
    from media_hygiene.classify.signals import Signal


def year_folders(
    files: Sequence[MediaInput],
    datings: Mapping[Path, Dating],
    grouping: tuple[Mapping[Path, Signal], Mapping[Path, Event], str],
) -> dict[Path, tuple[int, int]]:
    """The year and month folders of each file, both from the same date (0400).

    With `event_year = "start"`, an event takes the year and month of its start (a New
    Year's Eve party stays whole, in December), and so does a meaningful folder, from
    its oldest file. The month is 0 when only the year is known (a folder `1985`).

    Args:
        files: Every file.
        datings: Their dates.
        grouping: Their signals, their events, and `[classify] event_year`.

    Returns:
        The year and month of each file.
    """
    signals, event_of, mode = grouping
    moments = {
        file.path: (datings[file.path].when.year, datings[file.path].month)
        for file in files
    }
    if mode != "start":
        return moments
    oldest: dict[Path, Dating] = {}
    for file in files:
        if signals[file.path].reason is SortReason.EXISTING_FOLDER:
            folder, dating = file.path.parent, datings[file.path]
            if folder not in oldest or dating.when < oldest[folder].when:
                oldest[folder] = dating
    for file in files:
        event = event_of.get(file.path)
        if event is not None:
            moments[file.path] = (event.start.year, event.start.month)
        elif (first := oldest.get(file.path.parent)) is not None:
            moments[file.path] = (first.when.year, first.month)
    return moments


def in_years(
    proposals: Sequence[Proposal], years: tuple[int, int] | None
) -> tuple[tuple[Proposal, ...], int]:
    """The proposals of the years asked for.

    A file dated only by the disk (its modification date: a copy, a download) goes to
    the undated folder whatever its year: a `--year` run leaves it to a run without
    `--year` instead of counting it.

    Args:
        proposals: Every proposal.
        years: First and last year, or None for all.

    Returns:
        The proposals kept, and how many files dated by the disk were left out.
    """
    if years is None:
        return tuple(proposals), 0
    first, last = years
    dated = [p for p in proposals if p.dating and first <= p.dating.when.year <= last]
    kept = tuple(
        p for p in dated if p.dating and p.dating.source is not DateSource.MTIME
    )
    return kept, len(dated) - len(kept)


def below(proposals: Sequence[Proposal], folders: tuple[Path, ...]) -> list[Proposal]:
    """The proposals of the files below the `--path` folders.

    Args:
        proposals: Every proposal.
        folders: The folders; empty: every file.

    Returns:
        Those in scope.
    """
    if not folders:
        return list(proposals)
    return [p for p in proposals if any(is_within(p.file.path, f) for f in folders)]
