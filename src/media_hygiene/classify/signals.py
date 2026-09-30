"""What the folders say about each file: its category and why, before any rule.

A meaningful folder is kept as is (`existing-folder`); a person or device folder at the
top (`Léa/2018/…`) gives its name (`person-folder`); the loose files of an event whose
other files sit in one meaningful folder join it (`event-neighbour`).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from media_hygiene.classify.models import SortReason

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping
    from pathlib import Path

    from media_hygiene.classify.folders import FolderRules
    from media_hygiene.classify.models import Event, MediaInput


@dataclass(frozen=True, slots=True)
class Signal:
    """A category, the reason and the rule it was given by; no category: no signal.

    `score` None takes the score of the reason; `stay` leaves the file where it is.
    """

    reason: SortReason
    category: str = ""
    rule: str = ""
    score: int | None = None
    stay: bool = False


NO_SIGNAL = Signal(SortReason.NO_SIGNAL)


def folder_signal(file: MediaInput, rules: FolderRules) -> Signal:
    """What the folders of one file say.

    Args:
        file: The file.
        rules: Which names are generic.

    Returns:
        Its category from a meaningful folder, or no signal.
    """
    labels = rules.meaning(file.path.parent, file.root)
    if not labels:
        return NO_SIGNAL
    relative = file.path.parent.relative_to(file.root).parts
    if (
        len(relative) > 1
        and labels[0] == relative[0]
        and rules.label(relative[1]) is None
    ):
        return Signal(SortReason.PERSON_FOLDER, labels[0])
    return Signal(SortReason.EXISTING_FOLDER, "/".join(labels))


def with_neighbours(
    signals: Mapping[Path, Signal], events: Iterable[Event]
) -> dict[Path, Signal]:
    """Let the loose files of an event join the one meaningful folder it has.

    Args:
        signals: The folder signal of every file.
        events: The events.

    Returns:
        The signals, the loose files of such events now `event-neighbour`.
    """
    joined = dict(signals)
    for event in events:
        found = {
            signal.category
            for path in event.paths
            if (signal := signals.get(path))
            and signal.reason is SortReason.EXISTING_FOLDER
        }
        if len(found) != 1:
            continue
        (category,) = found
        for path in event.paths:
            if joined.get(path, NO_SIGNAL).reason is SortReason.NO_SIGNAL:
                joined[path] = Signal(SortReason.EVENT_NEIGHBOUR, category)
    return joined
