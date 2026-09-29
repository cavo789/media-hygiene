"""The vocabulary of the journal: which command wrote an entry, what it did, how far."""

from __future__ import annotations

from enum import StrEnum


class ActionKind(StrEnum):
    """What `clean` did to a file — recorded in the journal so `undo` can reverse it."""

    DELETE_DUPLICATE = "delete-duplicate"
    DELETE_EMPTY = "delete-empty"
    QUARANTINE = "quarantine"
    QUARANTINE_NEAR = "quarantine-near"
    QUARANTINE_DUPLICATE = "quarantine-duplicate"
    QUARANTINE_SIDECAR = "quarantine-sidecar"
    QUARANTINE_BURST = "quarantine-burst"


class Phase(StrEnum):
    """Which command wrote a journal entry."""

    CLEAN = "clean"
    UNDO = "undo"


class Status(StrEnum):
    """Write-ahead state of a journal entry: `pending` before acting, `done` after."""

    PENDING = "pending"
    DONE = "done"
