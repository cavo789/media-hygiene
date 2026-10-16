r"""Every quarantine of this run, and the refusal when a run's drive is not mounted.

The journal records where each file was set aside (`/quarantine/e/<run>/…` for a file
of `E:` with a quarantine of its own). When that drive's quarantine is not mounted now
(the drive unplugged, `mh` written again without its folders), Docker may still have
left an empty `e` folder in `/quarantine`: `undo` would find nothing there and `purge`
would erase the other drives only. Both refuse instead, naming the drive to plug in.
"""

from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING

from media_hygiene.actions.journal import journal_file, read_journal
from media_hygiene.actions.kinds import Status
from media_hygiene.actions.quarantine import QUARANTINED
from media_hygiene.actions.runs import RUN_ID_PATTERN
from media_hygiene.actions.undo import actions_to_undo
from media_hygiene.errors import MountError
from media_hygiene.i18n import _, ngettext
from media_hygiene.paths.quarantines import Quarantines

if TYPE_CHECKING:
    from collections.abc import Sequence

    from media_hygiene.services.runtime import Runtime


def mounted_quarantines(runtime: Runtime) -> Quarantines:
    """The quarantines of this run: `/quarantine` and the per-drive mounts.

    Args:
        runtime: Settings, mount points and output.

    Returns:
        Them.
    """
    default = runtime.locations.quarantine_dir
    return Quarantines.mounted(default, runtime.mounts.mount_points)


def refuse_unplugged(runtime: Runtime, run_ids: Sequence[str]) -> None:
    """Refuse when a run set files aside in a drive's quarantine not mounted now.

    A run without a journal here is not checked: nothing tells where its files went;
    nor is a name that is no run identifier (`purge e`).

    Args:
        runtime: Settings, mount points and output.
        run_ids: The runs about to be undone or purged.

    Raises:
        MountError: The first run with files in an unmounted quarantine.
    """
    quarantines = mounted_quarantines(runtime)
    for run_id in run_ids:
        missing = _unplugged(runtime, quarantines, run_id)
        if not missing:
            continue
        drive, count = missing.most_common(1)[0]
        letter = drive[0].lower()
        raise MountError(
            ngettext(
                "The run {run_id} set {count} file aside in the quarantine of "
                "{drive}, which is not mounted (/quarantine/{letter}): nothing was "
                "changed.",
                "The run {run_id} set {count} files aside in the quarantine of "
                "{drive}, which is not mounted (/quarantine/{letter}): nothing was "
                "changed.",
                count,
            ).format(run_id=run_id, count=count, drive=drive, letter=letter),
            _(
                "Plug {drive} in and keep one of its photo folders in mh ('mh "
                "folders add'), or mount its quarantine yourself: -v "
                '"{drive}\\media-hygiene\\quarantine:/quarantine/{letter}".'
            ).format(drive=drive, letter=letter),
        )


def held_back(runtime: Runtime, run_ids: Sequence[str]) -> dict[str, str]:
    """Find the runs with files in the quarantine of a drive not mounted now.

    Args:
        runtime: Settings, mount points and output.
        run_ids: The runs about to be purged.

    Returns:
        The drive to plug in, by run; the other runs are not listed.
    """
    quarantines = mounted_quarantines(runtime)
    missing = {run: _unplugged(runtime, quarantines, run) for run in run_ids}
    return {
        run: drives.most_common(1)[0][0] for run, drives in missing.items() if drives
    }


def _unplugged(runtime: Runtime, quarantines: Quarantines, run_id: str) -> Counter[str]:
    """Count a run's files waiting in the quarantine of a drive not mounted now.

    Args:
        runtime: Settings, mount points and output.
        quarantines: The quarantines mounted.
        run_id: The run.

    Returns:
        How many files per drive to plug in; empty when none.
    """
    path = journal_file(runtime.locations.journal_dir, run_id)
    if RUN_ID_PATTERN.fullmatch(run_id) is None or not path.is_file():
        return Counter()
    drives = (  # a `pending` move may never have happened: it holds nothing back
        quarantines.unplugged(entry.quarantine)
        for entry in actions_to_undo(read_journal(path))
        if entry.action in QUARANTINED
        and entry.status is Status.DONE
        and entry.quarantine
    )
    return Counter(drive for drive in drives if drive is not None)
