"""What the user already dealt with: one rule for `import` and `phone` (0377).

Both commands ask the same question of a file found outside the library: does the user
already hold it, or did they set it aside on purpose? The reasons and their sources are
the same on both sides; only the key differs (a folder gives the content, a phone a name
and a size):

| Reason | Source |
|---|---|
| set aside by a choice (quarantined, purged since) | the journals (`remembered_of`) |
| deleted in the Explorer, confirmed | the journals (`mark-gone`, partial digest) |
| deleted in the Explorer, waiting for `review --gone` | the index (`gone_files`) |
| a run undone since | no reason: the journals forget it, the file came back |
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

from media_hygiene.actions.kinds import ActionKind
from media_hygiene.i18n import _
from media_hygiene.index.gone_rows import gone_records
from media_hygiene.plan.returned import Remembered, RememberedSet
from media_hygiene.services.returned import remembered_of

if TYPE_CHECKING:
    import sqlite3

    from media_hygiene.services.runtime import Runtime


@dataclass(frozen=True, slots=True)
class DealtReasons:
    """The contents dealt with: set aside or confirmed deleted, and still waiting."""

    aside: RememberedSet
    waiting: RememberedSet  # by partial digest only: deleted, `review --gone` to answer


def waiting_gone(runtime: Runtime, connection: sqlite3.Connection) -> RememberedSet:
    """The files deleted in the Explorer, waiting for `review --gone` (0224).

    Args:
        runtime: Settings, mount points and output (host paths).
        connection: The index.

    Returns:
        Their contents, by size and partial digest: a backup is never read whole
        (0274).
    """
    by_partial: dict[tuple[int, str], Remembered] = {}
    for record in gone_records(connection):
        at = datetime.fromisoformat(record.gone_at) if record.gone_at else None
        by_partial[record.size, record.partial_digest] = Remembered(
            "",
            at or datetime.now(UTC),
            ActionKind.MARK_GONE,
            runtime.mapper.to_host(Path(record.path)),
        )
    return RememberedSet(by_partial=by_partial)


def dealt_reasons(runtime: Runtime, connection: sqlite3.Connection) -> DealtReasons:
    """Every reason not to bring a content in again, from the journals and the index.

    Args:
        runtime: Settings, mount points and output.
        connection: The index, keeping what each journal said.

    Returns:
        The reasons, the same for `import` and `phone`.
    """
    return DealtReasons(
        aside=remembered_of(runtime, connection),
        waiting=waiting_gone(runtime, connection),
    )


def waiting_warning(at: datetime) -> str:
    """The words of a deletion still waiting for `review --gone`, on every page.

    Args:
        at: When the audit found it gone.

    Returns:
        The translated warning.
    """
    return _(
        "Deleted in the Explorer (found gone on {date}), not confirmed yet in mh "
        "review --gone: not proposed again."
    ).format(date=at.astimezone().strftime("%Y-%m-%d"))
