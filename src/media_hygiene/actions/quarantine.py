"""The actions undone by moving a file back from the quarantine."""

from __future__ import annotations

from typing import Final

from media_hygiene.actions.kinds import ActionKind

# Actions undone by moving the file back from the quarantine.
QUARANTINED: Final = frozenset(
    {ActionKind.QUARANTINE, ActionKind.QUARANTINE_NEAR}
    | {ActionKind.QUARANTINE_DUPLICATE, ActionKind.QUARANTINE_SIDECAR}
    | {ActionKind.QUARANTINE_BURST, ActionKind.QUARANTINE_JUNK},
)
