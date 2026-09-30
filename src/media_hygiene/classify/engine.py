"""From the files and what the index knows of them, one proposal per file.

Read-only: nothing here touches a file. Dates, folders and events decide; the rules of
`[classify.rules]` come on top (0035).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from media_hygiene.classify.bands import band_folders, layout_of, verdict
from media_hygiene.classify.dates import clock_not_set, zone_of
from media_hygiene.classify.dating import DatingContext, dating_of, has_camera_trace
from media_hygiene.classify.events import EventRules, find_events
from media_hygiene.classify.folders import FolderRules
from media_hygiene.classify.layout import Values, render
from media_hygiene.classify.models import (
    Band,
    DateSource,
    Proposal,
    SortReason,
    Verdict,
)
from media_hygiene.classify.signals import folder_signal, with_neighbours
from media_hygiene.classify.years import year_folders
from media_hygiene.constants import GENERIC_FOLDERS
from media_hygiene.paths.host_paths import is_within
from media_hygiene.plan.name_rules import compile_patterns

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from media_hygiene.classify.models import Dating, Event, MediaInput
    from media_hygiene.classify.signals import Signal
    from media_hygiene.config.classify_settings import ClassifySettings


@dataclass(frozen=True, slots=True)
class Scope:
    """Where the files go, which ones never move, which years are proposed."""

    target: Path | None = None  # None: each mounted folder, in place
    kept: tuple[Path, ...] = ()  # protected and `leave` folders
    years: tuple[int, int] | None = None
    generic: tuple[str, ...] = GENERIC_FOLDERS  # `[keep]`: DCIM, Camera…


@dataclass(frozen=True, slots=True)
class Classification:
    """Every proposal, and the events they belong to."""

    proposals: tuple[Proposal, ...]
    events: tuple[Event, ...]


def classify(
    files: Sequence[MediaInput], settings: ClassifySettings, scope: Scope
) -> Classification:
    """Propose a place for every file.

    Args:
        files: The media files and their facts.
        settings: `[classify]`.
        scope: Target, folders never moved, years.

    Returns:
        The proposals (only the years in scope) and the events.
    """
    rules = FolderRules.build(
        (*scope.generic, *settings.generic_folders), band_folders(settings)
    )
    context = DatingContext(
        rules,
        compile_patterns(settings.name_dates),
        zone_of(settings.timezone),
        clock_not_set(files, rules),
    )
    datings = {file.path: dating_of(file, context) for file in files}
    signals = {file.path: folder_signal(file, rules) for file in files}
    labels = {path: s.category for path, s in signals.items() if s.category}
    trusted = [
        (path, dating.when)
        for path, dating in datings.items()
        if dating.source is not DateSource.MTIME
    ]
    event_rules = EventRules.of(
        settings.session_gap_hours, settings.merge_gap_hours, settings.min_event_size
    )
    events = find_events(trusted, event_rules, labels)
    signals = with_neighbours(signals, events)
    event_of = {path: event for event in events for path in event.paths}
    years = year_folders(files, datings, (signals, event_of, settings.event_year))
    proposals = [
        _propose(
            file,
            _Facts(
                datings[file.path],
                signals[file.path],
                event_of.get(file.path),
                years[file.path],
            ),
            (settings, scope),
        )
        for file in files
    ]
    return Classification(
        tuple(p for p in proposals if _in_years(p, scope.years)), events
    )


@dataclass(frozen=True, slots=True)
class _Facts:
    """What is known of one file."""

    dating: Dating
    signal: Signal
    event: Event | None
    year: int


def _propose(
    file: MediaInput, facts: _Facts, config: tuple[ClassifySettings, Scope]
) -> Proposal:
    """Build the proposal of one file.

    Args:
        file: The file.
        facts: Its date, signal and event.
        config: `[classify]` and the scope.

    Returns:
        Its proposal.
    """
    settings, scope = config
    dating, signal, event = facts.dating, facts.signal, facts.event
    if any(is_within(file.path, folder) for folder in scope.kept):
        return Proposal(file, dating, Verdict(Band.STAY, SortReason.LEFT_AS_IS, 100))
    judged = verdict(signal, dating, settings)
    when = dating.when
    values = Values(
        year=facts.year,
        month=when.month,
        day=when.day,
        category=signal.category,
        event=(event.label or event.span)
        if event
        else f"{when.year:04d}-{when.month:02d}",
        event_start=event.start.date().isoformat() if event else "",
    )
    layout = layout_of(judged.band, settings, camera=has_camera_trace(file))
    folder = render(layout, values)
    root = scope.target or file.root
    return Proposal(
        file,
        dating,
        judged,
        values=values,
        event_id=event.event_id if event else "",
        folder=folder,
        target=root / folder if folder is not None else None,
    )


def _in_years(proposal: Proposal, years: tuple[int, int] | None) -> bool:
    """Tell whether a proposal falls in the years asked for.

    Args:
        proposal: A proposal.
        years: First and last year, or None for all.

    Returns:
        True when in scope.
    """
    if years is None or proposal.dating is None:
        return years is None
    return years[0] <= proposal.dating.when.year <= years[1]
