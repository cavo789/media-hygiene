"""The vocabulary of the journal: which command wrote an entry, what it did, how far."""

from __future__ import annotations

from enum import StrEnum
from typing import Final


class ActionKind(StrEnum):
    """What a run did to a file or a folder — recorded so `undo` can reverse it.

    Each kind needs its reversal in `actions/reversal.py`: `undo` refuses a kind it does
    not know rather than guess.
    """

    DELETE_DUPLICATE = "delete-duplicate"
    DELETE_EMPTY = "delete-empty"
    QUARANTINE = "quarantine"
    QUARANTINE_NEAR = "quarantine-near"
    QUARANTINE_DUPLICATE = "quarantine-duplicate"
    QUARANTINE_SIDECAR = "quarantine-sidecar"
    QUARANTINE_BURST = "quarantine-burst"
    # Written by `sort`: a file moved to `target`, a folder created, a folder left empty
    # and removed.
    MOVE = "move"
    CREATE_FOLDER = "create-folder"
    REMOVE_FOLDER = "remove-folder"


class Phase(StrEnum):
    """Which command wrote a journal entry."""

    CLEAN = "clean"
    SORT = "sort"
    UNDO = "undo"


class Status(StrEnum):
    """Write-ahead state of a journal entry: `pending` before acting, `done` after."""

    PENDING = "pending"
    DONE = "done"


# The phases that change files; `undo` reverses one of them.
ACTING_PHASES: Final = (Phase.CLEAN, Phase.SORT)
# Actions on folders: nothing is deleted nor freed by them.
FOLDER_ACTIONS: Final = frozenset({ActionKind.CREATE_FOLDER, ActionKind.REMOVE_FOLDER})
