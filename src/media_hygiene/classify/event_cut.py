"""The dates of a run and its events: one cut, for `classify` and its preview (0646)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from media_hygiene.classify.dating import datings_of
from media_hygiene.classify.events import trusted_events
from media_hygiene.classify.received import join_received, received_guesses
from media_hygiene.classify.signals import folder_signal

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from pathlib import Path

    from media_hygiene.classify.folders import FolderRules
    from media_hygiene.classify.models import Dating, Event, MediaInput
    from media_hygiene.classify.signals import Signal
    from media_hygiene.config.classify_settings import ClassifySettings


@dataclass(frozen=True, slots=True)
class DatedFiles:
    """What the grouping values do not change: the dates and what folders say."""

    datings: Mapping[Path, Dating]
    received: frozenset[Path]
    signals: Mapping[Path, Signal]


def dated_files(
    files: Sequence[MediaInput], settings: ClassifySettings, rules: FolderRules
) -> DatedFiles:
    """Date the files and read their folders.

    Args:
        files: Every file.
        settings: `[classify]`.
        rules: What folder names say.

    Returns:
        The dates, the pictures received by a messaging app, the folder signals.
    """
    datings, received = received_guesses(
        files, datings_of(files, settings, rules), settings
    )
    signals = {file.path: folder_signal(file, rules) for file in files}
    return DatedFiles(datings, received, signals)


def events_of(dated: DatedFiles, settings: ClassifySettings) -> tuple[Event, ...]:
    """Cut the dated files into events.

    Args:
        dated: The dates and the folder signals.
        settings: `[classify]`: the gaps and the minimum size.

    Returns:
        The events, the received pictures joined.
    """
    received, datings = dated.received, dated.datings
    events = trusted_events(
        {path: dating for path, dating in datings.items() if path not in received},
        {path: s.category for path, s in dated.signals.items() if s.category},
        settings,
    )
    return join_received(received, datings, (events, settings.merge_gap_hours))
