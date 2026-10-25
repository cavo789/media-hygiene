"""From the files and what the index knows of them, one proposal per file.

Read-only. Dates, folders and events give the facts; `[[classify.rules]]` decide.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from functools import cache
from typing import TYPE_CHECKING

from media_hygiene.classify.bands import band_folders, layout_of, verdict
from media_hygiene.classify.convention import looked_at
from media_hygiene.classify.dating import datings_of, has_camera_trace
from media_hygiene.classify.event_folders import without_event_folders
from media_hygiene.classify.events import trusted_events
from media_hygiene.classify.folders import FolderRules
from media_hygiene.classify.guesses import keep_guess
from media_hygiene.classify.layout import Values, render
from media_hygiene.classify.models import Band, Proposal, SortReason, Verdict
from media_hygiene.classify.moments import Moments, joined_signals
from media_hygiene.classify.received import join_received, received_guesses
from media_hygiene.classify.rules.building import RuleFacts, Seen
from media_hygiene.classify.rules.order import decide, unused
from media_hygiene.classify.signals import folder_signal
from media_hygiene.classify.trips import find_whereabouts
from media_hygiene.classify.whereabouts import with_place
from media_hygiene.classify.years import below, in_years, year_folders
from media_hygiene.name_patterns import GENERIC_FOLDERS
from media_hygiene.paths.host_paths import is_within

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from pathlib import Path

    from media_hygiene.classify.layout import GeoValues
    from media_hygiene.classify.models import Dating, Event, MediaInput
    from media_hygiene.classify.signals import Signal
    from media_hygiene.config.classify_settings import ClassifySettings
    from media_hygiene.geo.gazetteer import Gazetteer


@dataclass(frozen=True, slots=True)
class Scope:  # pylint: disable=too-many-instance-attributes  # one field per option
    """Where the files go, which ones never move, which years are proposed."""

    target: Path | None = None  # None: each mounted folder, in place
    kept: tuple[Path, ...] = ()  # protected and `leave` folders
    years: tuple[int, int] | None = None
    generic: tuple[str, ...] = GENERIC_FOLDERS  # `[keep]`: DCIM, Camera…
    host: Callable[[Path], str] = str  # container → host path, for `path` rules
    seen: Seen = field(default_factory=Seen)  # the model's answers, the people
    towns: Gazetteer | None = None  # read only when a `trip` rule is on
    within: tuple[Path, ...] = ()  # `--path`: only the files below them get a proposal
    people: tuple[str, ...] = ()  # `[[people.person]]` names: their folders are theirs


@dataclass(frozen=True, slots=True)
class Classification:
    """Every proposal, the events they belong to, and the rules that decided nothing."""

    proposals: tuple[Proposal, ...]
    events: tuple[Event, ...]
    unused_rules: tuple[str, ...] = ()
    # `--year`: the years, and the files left out because only the disk dates them.
    years: tuple[tuple[int, int] | None, int] = (None, 0)


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
    ).with_people((*scope.people, *settings.person_folders))
    datings, received = received_guesses(
        files, datings_of(files, settings, rules), settings
    )
    signals = {file.path: folder_signal(file, rules) for file in files}
    events = trusted_events(
        {path: dating for path, dating in datings.items() if path not in received},
        {path: s.category for path, s in signals.items() if s.category},
        settings,
    )
    events = join_received(received, datings, (events, settings.merge_gap_hours))
    event_of = {path: event for event in events for path in event.paths}
    signals = without_event_folders(files, (signals, event_of), rules)
    where = find_whereabouts(files, (events, datings), (settings, scope.towns))
    signals = joined_signals(signals, events, Moments(datings, rules, settings))
    # Every `path` rule asks for the host path of every file: computed once each.
    facts = RuleFacts(datings, signals, event_of, cache(scope.host))
    facts = replace(facts, seen=scope.seen, where=where)
    signals = decide(files, settings, facts)
    moments = year_folders(files, datings, (signals, event_of, settings.event_year))
    proposals = [
        keep_guess(
            _propose(
                file,
                _Facts(
                    datings[file.path],
                    signals[file.path],
                    event_of.get(file.path),
                    moments[file.path],
                    where.values(file.path),
                ),
                (settings, scope),
            ),
            rules.guess(file.path.parent, file.root),
            settings.unsure,
        )
        for file in files
    ]
    kept, undated = in_years(below(proposals, scope.within), scope.years)
    return Classification(kept, events, unused(settings, kept), (scope.years, undated))


@dataclass(frozen=True, slots=True)
class _Facts:
    """What is known of one file."""

    dating: Dating
    signal: Signal
    event: Event | None
    moment: tuple[int, int]  # year and month folders; month 0: unknown
    geo: GeoValues


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
    if looked_at(file.path, scope.target or file.root, dating):  # nothing special
        return Proposal(
            file, dating, Verdict(Band.STAY, SortReason.NOTHING_SPECIAL, 100)
        )
    if signal.stay:
        return Proposal(
            file,
            dating,
            Verdict(Band.STAY, signal.reason, signal.score or 0, signal.rule),
        )
    judged = verdict(signal, dating, settings)
    year, month = facts.moment
    values = Values(
        year=year,
        month=month,
        day=dating.when.day,
        category=signal.category,
        event=(event.label or event.span) if event else f"{year:04d}-{month:02d}",
        event_start=event.start.date().isoformat() if event else "",
    )
    values = with_place(values, facts.geo)
    layout = layout_of(judged, settings, camera=has_camera_trace(file))
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
        root=root,
    )
