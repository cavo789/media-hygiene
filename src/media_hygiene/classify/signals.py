"""What the folders say about each file: its category and why, before any rule.

A meaningful folder is kept as is (`existing-folder`); a person or device folder at the
top (`Léa/2018/…`) or a folder holding a person's name (`2019/Photos Chloé`) gives its
name (`person-folder`); the loose files of an event whose
other files sit in one meaningful folder join it (`event-neighbour`). A file whose own
folders say nothing reads those of the copies `clean` removed (0208), as if it lay
there: when they give one meaning; when they give several, none is used.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from media_hygiene.classify.former import FormerHint
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
    hint: FormerHint | None = None  # read from the folders of removed copies (0208)


NO_SIGNAL = Signal(SortReason.NO_SIGNAL)


def folder_signal(file: MediaInput, rules: FolderRules) -> Signal:
    """What the folders of one file say, else those of the copies `clean` removed.

    Args:
        file: The file.
        rules: Which names are generic.

    Returns:
        Its category from a meaningful folder, or no signal (with the folders of
        removed copies that disagreed, if any).
    """
    own = _own_signal(file, rules)
    if own.category or not file.former:
        return own
    found: dict[str, tuple[Signal, list[Path]]] = {}
    for copy in file.former:
        lying = replace(file, path=copy.path, root=copy.root, former=())
        signal = _own_signal(lying, rules)
        if signal.category:
            found.setdefault(signal.category.casefold(), (signal, []))[1].append(
                copy.path.parent
            )
    folders = tuple(dict.fromkeys(f for _s, paths in found.values() for f in paths))
    if not found:
        return own
    if len(found) > 1:
        return replace(own, hint=FormerHint(folders, agreed=False))
    signal = next(iter(found.values()))[0]
    return replace(signal, hint=FormerHint(folders))


def _own_signal(file: MediaInput, rules: FolderRules) -> Signal:
    """What the folders of one file say, from its own path only.

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
    if rules.of_person(labels):
        return Signal(SortReason.PERSON_FOLDER, "/".join(labels))
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
