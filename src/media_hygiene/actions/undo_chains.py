"""Which actions of an undo may run at once, and which must wait for others (0161).

An undo reverses the actions newest first. Most of them touch paths no other action
of the run touches: those run a few at a time. What depends on order stays in it:

- a folder action (a folder a `sort` created is removed once its files are out, a
  folder it removed comes back before them) and an orphan sidecar of a `clean` run
  alone, after everything newer and before everything older;
- actions sharing a path one of them changes (a file moved by `sort`, then its name
  taken by another) form a chain, run by one worker in the reversed order.

A path only read (the kept copy a deleted copy is rebuilt from) links nothing: copies
of one file come back at once.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from media_hygiene.actions.kinds import FOLDER_ACTIONS, ActionKind

if TYPE_CHECKING:
    from collections.abc import Sequence

    from media_hygiene.actions.journal import JournalEntry
    from media_hygiene.actions.reversal import Reversal

# One action to reverse, and how.
type Undoing = tuple[JournalEntry, Reversal]
# Actions reversed one after the other, by one worker.
type Chain = tuple[Undoing, ...]

# Reversed alone, in order: folders, and the sidecars a clean set aside last.
_IN_SERIES: Final = FOLDER_ACTIONS | {ActionKind.QUARANTINE_SIDECAR}


def stages(newest_first: Sequence[Undoing]) -> list[tuple[Chain, ...]]:
    """Cut the actions into stages run one after the other.

    Args:
        newest_first: The actions to reverse, newest first.

    Returns:
        The stages, in order: the chains of a stage may run at once.
    """
    result: list[tuple[Chain, ...]] = []
    batch: list[Undoing] = []
    for undoing in newest_first:
        if undoing[0].action not in _IN_SERIES:
            batch.append(undoing)
            continue
        if batch:
            result.append(chains(batch))
            batch = []
        result.append(((undoing,),))
    if batch:
        result.append(chains(batch))
    return result


def chains(actions: Sequence[Undoing]) -> tuple[Chain, ...]:
    """Group the actions that share a path one of them changes, keeping their order.

    Args:
        actions: Actions free of folder actions, newest first.

    Returns:
        The chains, by their first action; each chain in the order given.
    """
    root = list(range(len(actions)))
    users: dict[str, list[int]] = {}
    changed: set[str] = set()
    for index, (entry, _reversal) in enumerate(actions):
        for path in _changed_paths(entry):
            users.setdefault(path, []).append(index)
            changed.add(path)
        if entry.keeper:  # only read
            users.setdefault(entry.keeper, []).append(index)
    for path in changed:
        first, *others = users[path]
        for other in others:
            root[_find(root, other)] = _find(root, first)
    grouped: dict[int, list[Undoing]] = {}
    for index, undoing in enumerate(actions):
        grouped.setdefault(_find(root, index), []).append(undoing)
    return tuple(tuple(chain) for chain in grouped.values())


def _changed_paths(entry: JournalEntry) -> set[str]:
    """The paths reversing an action creates, moves or removes.

    Args:
        entry: The action.

    Returns:
        Its path, and where a move or the quarantine put it.
    """
    return {path for path in (entry.path, entry.target, entry.quarantine) if path}


def _find(root: list[int], index: int) -> int:
    """The first action of the chain an action belongs to (union-find).

    Args:
        root: The link of each action to another of its chain.
        index: The action.

    Returns:
        The representative of its chain.
    """
    while root[index] != index:
        root[index] = root[root[index]]
        index = root[index]
    return index
