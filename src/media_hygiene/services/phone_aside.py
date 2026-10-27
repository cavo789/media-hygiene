"""The phone's files the user dealt with before, by name and size (0219, 0377).

The reasons are `dealt_with`'s, the same as `import`'s; only the key is the phone's:
the name (case ignored) and the size of where the content lay. Between several of the
same key, the latest is named: the same answer on every run. A set-aside by a choice
wins over a deletion still waiting for `review --gone`.
"""

from __future__ import annotations

from itertools import chain
from pathlib import PureWindowsPath
from typing import TYPE_CHECKING

from media_hygiene.actions.purge import runs_in
from media_hygiene.actions.purged import purge_dates
from media_hygiene.services.dealt_with import dealt_reasons
from media_hygiene.services.phone_plan import AsideState, SetAside
from media_hygiene.services.quarantines import mounted_quarantines

if TYPE_CHECKING:
    import sqlite3

    from media_hygiene.plan.returned import Remembered, RememberedSet
    from media_hygiene.services.phone_plan import NameKey
    from media_hygiene.services.runtime import Runtime


def _latest(
    remembered: RememberedSet, wanted: frozenset[NameKey]
) -> dict[NameKey, Remembered]:
    """Find the latest content remembered of each name and size wanted.

    Args:
        remembered: Contents, by SHA-256 or partial digest.
        wanted: The names and sizes of the phone.

    Returns:
        The latest of each.
    """
    found: dict[NameKey, Remembered] = {}
    pairs = chain(remembered.by_digest.items(), remembered.by_partial.items())
    for (size, _digest), said in pairs:
        key = (PureWindowsPath(said.host_path).name.casefold(), size)
        if key not in wanted:
            continue
        last = found.get(key)
        if last is None or (said.at, said.run_id) > (last.at, last.run_id):
            found[key] = said
    return found


def set_aside_of(
    runtime: Runtime, connection: sqlite3.Connection, wanted: frozenset[NameKey]
) -> dict[NameKey, SetAside]:
    """Find the files dealt with before named like the phone's, of the same size.

    Args:
        runtime: Settings, mount points and the journal.
        connection: The index, keeping what each journal said and the files gone.
        wanted: The names and sizes of the phone.

    Returns:
        The latest set-aside of each, with its run's quarantine state and, once
        purged, when (0256); else the deletion waiting for `review --gone` (0377).
    """
    reasons = dealt_reasons(runtime, connection)
    found = _latest(reasons.aside, wanted)
    held = frozenset(runs_in(mounted_quarantines(runtime).folders))
    purged = purge_dates(
        runtime.locations.journal_dir,
        {said.run_id for said in found.values()} - held,
    )
    aside = {
        key: SetAside(
            said.run_id,
            said.at,
            said.action.value,
            AsideState.QUARANTINE if said.run_id in held else AsideState.PURGED,
            said.host_path,
            purged.get(said.run_id),
        )
        for key, said in found.items()
    }
    waiting = _latest(reasons.waiting, wanted - aside.keys())
    aside |= {
        key: SetAside(
            "", said.at, said.action.value, AsideState.WAITING, said.host_path
        )
        for key, said in waiting.items()
    }
    return aside
