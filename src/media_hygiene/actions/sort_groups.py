"""The names of a group, decided before its files move, while other groups move.

`sort` moves a few groups at a time (0163). Each group's names are chosen in the
calling thread, in the plan's order, before any of its files moves: a name given to a
group still under way is taken for the next ones, even though no file holds it yet, so
two groups never race for one name. Once a group ended, its files hold their names on
the disk, and the names are handed back.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from operator import attrgetter
from typing import TYPE_CHECKING

from media_hygiene.actions.sort_names import SourceSidecars, free_names

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from media_hygiene.actions.journal import JournalEntry
    from media_hygiene.actions.sort_plan import MoveGroup


@dataclass(frozen=True, slots=True)
class ReadyGroup:
    """A group with its sidecars and the name each file takes in its folder."""

    group: MoveGroup
    sidecars: tuple[Path, ...]
    targets: Mapping[str, str]  # name of a file or sidecar → its name in the folder

    @property
    def names(self) -> list[str]:
        """The names of the group's files (not its sidecars), the leading one first.

        Returns:
            The names.
        """
        return [move.source.name for move in self.group.moves]


class NameBook:
    """The names given to the groups under way, by target folder (calling thread)."""

    def __init__(self) -> None:
        """Start with no name given."""
        self._given: dict[Path, set[str]] = {}
        self._sidecars = SourceSidecars()

    def ready(self, group: MoveGroup) -> ReadyGroup:
        """Find a group's sidecars and give each file a free name, kept for it.

        Args:
            group: Files that travel together.

        Returns:
            The group and its names.
        """
        sidecars = tuple(self._sidecars.take(group))
        names = [move.source.name for move in group.moves]
        given = self._given.setdefault(group.folder, set())
        targets = free_names(
            group.folder, names + [path.name for path in sidecars], given
        )
        given.update(name.casefold() for name in targets.values())
        return ReadyGroup(group, sidecars, targets)

    def release(self, ready: ReadyGroup) -> None:
        """Hand back the names of a group that ended: its files hold them now.

        Args:
            ready: The group.
        """
        given = self._given.get(ready.group.folder, set())
        given.difference_update(name.casefold() for name in ready.targets.values())
        if not given:
            self._given.pop(ready.group.folder, None)


class Ledger:
    """What the workers of a sort record: the moves done, the files left (locked)."""

    def __init__(self) -> None:
        """Start empty."""
        self._lock = threading.Lock()
        self._moved: list[JournalEntry] = []

    def add[T](self, items: list[T], item: T) -> None:
        """Add a file left to a list of the run's tally.

        Args:
            items: The list (skipped or failed).
            item: What to add.
        """
        with self._lock:
            items.append(item)

    def moved(self, entry: JournalEntry) -> None:
        """Remember a move done.

        Args:
            entry: Its journal entry.
        """
        with self._lock:
            self._moved.append(entry)

    def entries(self) -> tuple[JournalEntry, ...]:
        """The moves done, in the order they were journaled, whatever ended first.

        Returns:
            Their entries, by sequence number.
        """
        with self._lock:
            return tuple(sorted(self._moved, key=attrgetter("seq")))
