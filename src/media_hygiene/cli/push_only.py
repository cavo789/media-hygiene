"""`mh push`: the files set aside that exist nowhere else, said with its plan (0775).

`push` copies the photo folders, never the quarantine (option B of 0688: count, do not
copy). An exact copy set aside has its kept twin in the photos, so on the backup too;
a near duplicate, a burst shot, junk or an unreadable file set aside has no other copy
there. The plan says how many, read as the home page's card reads them (the same
cache), so that nobody takes the backup for a cover of the quarantine.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.console.formatting import human_number
from media_hygiene.i18n import ngettext
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.services.quarantines import mounted_quarantines
from media_hygiene.services.safety_cache import SlowAsk, slow_facts
from media_hygiene.services.status_parts import quarantine_state

if TYPE_CHECKING:
    from media_hygiene.services.runtime import Runtime


def say_only_copies(runtime: Runtime) -> int:
    """Say how many files set aside the backup does not hold, when there are any.

    Args:
        runtime: Settings, mount points and output.

    Returns:
        How many (0: nothing said; without a journal, nothing can be told).
    """
    if not runtime.persistent(MountKind.JOURNAL):
        return 0
    folders = mounted_quarantines(runtime).folders
    state = quarantine_state(folders, runtime.locations.journal_dir)
    runs = tuple(run.run_id for run in state.runs)
    if not runs:
        return 0
    facts = slow_facts(SlowAsk(runtime, runs, folders))
    # This push moves the NAS copies of files set aside into `.removed` (0781).
    only = facts.only + facts.nas
    if only:
        runtime.output.warning(
            ngettext(
                "{count} file set aside in the quarantine exists nowhere else, and "
                "the backup does not copy the quarantine: look at it before a purge.",
                "{count} files set aside in the quarantine exist nowhere else, and "
                "the backup does not copy the quarantine: look at them before a purge.",
                only,
            ).format(count=human_number(only))
        )
    return only
