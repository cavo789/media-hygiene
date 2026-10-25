"""The photos of a person's folder join the user's folder of the same moment (0386).

The user sorted a trip into `2019/Montenegro/Budva`, `…/Cetinje`; a daughter's photos of
the same days sit in `2019/Photos Chloé`. Each such photo (and each loose one) taken
during a session where the user's named folders hold files joins that folder, the one
whose photo is nearest in time when there are several (`same-moment`, to check). A photo
of no such session joins the trip's folder: the deepest common parent of the user's
folders of the event (`Montenegro`), when it means something. The files of a folder the
user named never move. Off when no `same_moment` rule with a score is written.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.classify.models import SortReason
from media_hygiene.classify.rules.kinds import RuleMatch
from media_hygiene.classify.signals import NO_SIGNAL, Signal, with_neighbours

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence
    from datetime import datetime
    from pathlib import Path

    from media_hygiene.classify.folders import FolderRules
    from media_hygiene.classify.models import Dating, Event
    from media_hygiene.config.classify_settings import ClassifySettings

_JOINING: Final = frozenset({SortReason.NO_SIGNAL, SortReason.PERSON_FOLDER})


@dataclass(frozen=True, slots=True)
class Moments:
    """What the joins read: the dates, the folder names, the rules of the run."""

    datings: Mapping[Path, Dating]
    rules: FolderRules
    settings: ClassifySettings

    @property
    def on(self) -> bool:
        """Tell whether a `same_moment` rule with a score is written.

        Returns:
            True when the photos of the same moment may join a folder.
        """
        default = self.settings.scores.get(SortReason.SAME_MOMENT.value, 0)
        return any(
            (default if rule.score is None else rule.score) > 0
            for rule in self.settings.rules
            if rule.match is RuleMatch.SAME_MOMENT
        )


def joined_signals(
    signals: Mapping[Path, Signal], events: Sequence[Event], moments: Moments
) -> dict[Path, Signal]:
    """Let the loose files and those of a person's folder join the user's folders.

    Args:
        signals: The folder signal of every file.
        events: The events, with their sessions.
        moments: The dates, the folder names, the rules.

    Returns:
        The signals: event neighbours, then the photos of the same moment.
    """
    joined = with_neighbours(signals, events)
    if not moments.on:
        return joined
    for event in events:
        named = {
            path: signal.category
            for path in event.paths
            if (signal := signals.get(path, NO_SIGNAL)).reason
            is SortReason.EXISTING_FOLDER
        }
        if not named:
            continue
        trip = _trip_folder(named.values(), moments.rules)
        for session in event.sessions or (event.paths,):
            anchors = [
                (moments.datings[p].when, named[p]) for p in session if p in named
            ]
            for path in session:
                if joined.get(path, NO_SIGNAL).reason not in _JOINING:
                    continue
                folder = _nearest(anchors, moments.datings[path].when) or trip
                if folder:
                    joined[path] = Signal(SortReason.SAME_MOMENT, folder)
    return joined


def _nearest(anchors: Sequence[tuple[datetime, str]], when: datetime) -> str:
    """The folder of the user's photo nearest in time.

    Args:
        anchors: The dates and folders of the user's photos of the session.
        when: The date of the photo to place.

    Returns:
        The folder, or an empty string when the session has none.
    """
    if not anchors:
        return ""
    return min(anchors, key=lambda anchor: (abs(anchor[0] - when), anchor[1]))[1]


def _trip_folder(folders: Iterable[str], rules: FolderRules) -> str:
    """The deepest common parent of the user's folders of an event, if it means much.

    Args:
        folders: Their categories, `/`-separated.
        rules: Which names are generic.

    Returns:
        The parent (`Montenegro`), the folder itself when there is one; empty when
        they share nothing, or only a generic or a year folder.
    """
    split = [folder.split("/") for folder in dict.fromkeys(folders)]
    common: list[str] = []
    for parts in zip(*split, strict=False):
        if len(set(parts)) != 1:
            break
        common.append(parts[0])
    if not common or rules.label(common[-1]) is None or common[-1].isdigit():
        return ""
    return "/".join(common)
