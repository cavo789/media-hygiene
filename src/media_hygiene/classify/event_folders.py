"""A file `sort` put in the "to sort" folder of its event is not given a meaning by it.

The "to sort" layout (`{year}/To sort/{event}`) names the folder after the event's label
when it has one: `2019/To sort/Seaside holidays`. Read on the next run as a folder the
user chose, that name would make the file sure and move it again. Below a band folder, a
name that equals the label of the file's own event is the tool's rendering, not a
meaning: the file is judged as on the first run, and its proposal is where it lies.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.classify.models import SortReason
from media_hygiene.classify.signals import NO_SIGNAL

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from pathlib import Path

    from media_hygiene.classify.folders import FolderRules
    from media_hygiene.classify.models import Event, MediaInput
    from media_hygiene.classify.signals import Signal


def without_event_folders(
    files: Sequence[MediaInput],
    facts: tuple[Mapping[Path, Signal], Mapping[Path, Event]],
    rules: FolderRules,
) -> dict[Path, Signal]:
    """Drop the meaning of the folders a layout named after the file's own event.

    Args:
        files: The files.
        facts: The folder signal and the event of each file.
        rules: Which names are band folders.

    Returns:
        The signals, those given by such a folder now none.
    """
    signals, event_of = facts
    kept = dict(signals)
    for file in files:
        signal, event = signals.get(file.path), event_of.get(file.path)
        if signal is None or event is None or not event.label:
            continue
        if _rendered(signal, event.label) and _below_band(file, rules):
            kept[file.path] = NO_SIGNAL
    return kept


def _rendered(signal: Signal, label: str) -> bool:
    """Tell whether a folder signal names the event's label, as a layout writes it.

    Args:
        signal: The folder signal of a file.
        label: The label of its event.

    Returns:
        True when its meaningful folder is the label.
    """
    return signal.reason is SortReason.EXISTING_FOLDER and signal.category == label


def _below_band(file: MediaInput, rules: FolderRules) -> bool:
    """Tell whether a file lies below one of the tool's band folders (`To sort`).

    Args:
        file: The file.
        rules: Which names are band folders.

    Returns:
        True when a folder between its root and itself is a band folder.
    """
    folder, root = file.path.parent, file.root
    parts = folder.relative_to(root).parts if folder.is_relative_to(root) else ()
    return any(name.casefold() in rules.bands for name in parts)
