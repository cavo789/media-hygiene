"""`import --phone --since`: the phone's new files before the period stay there (0476).

The period is decided in the container, where `phone-plan` already reads the listing
before any copy: one set of rules for the phone and the tests (the day in the name, else
the modified time), and the last import's day read from the journal folder.
"""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

from media_hygiene.services.import_since import (
    first_day,
    kept,
    last_import,
    today_local,
)
from media_hygiene.services.phone_plan import PhoneCase

if TYPE_CHECKING:
    from collections.abc import Iterable

    from media_hygiene.services.phone_plan import Verdict
    from media_hygiene.services.runtime import Runtime


def held_back(
    runtime: Runtime, verdicts: Iterable[Verdict], since: str | None
) -> tuple[Verdict, ...]:
    """Turn the new files before the period into `older`: listed, never copied.

    A file the library, the journals or the destination know keeps its case: freeing
    the phone (`--free`) still needs it.

    Args:
        runtime: Settings, mount points and output (the journal folder).
        verdicts: The cases decided.
        since: `--since` as typed; None: since the last import.

    Returns:
        The verdicts, the new files out of the period now `older`.
    """
    last = last_import(runtime.locations.journal_dir)
    first = first_day(since, today_local(), last)
    return tuple(
        replace(verdict, case=PhoneCase.OLDER)
        if verdict.case is PhoneCase.NEW
        and not kept(verdict.file.path.name, verdict.file.modified, first)
        else verdict
        for verdict in verdicts
    )
