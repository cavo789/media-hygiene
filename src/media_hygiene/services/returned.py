"""The audit recognises the files set aside by a choice that came back (0216).

The sizes remembered join the exact pipeline's candidates: a file of such a size is
hashed in full (the index keeps the digest) and compared with what was set aside.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from media_hygiene.actions.remembered import remembered_set
from media_hygiene.i18n import _
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.plan.returned import RememberedSet, ReturnedFile
from media_hygiene.scan.exact import ExactDuplicateFinder, full_pass, partial_pass
from media_hygiene.scan.progress import Step

if TYPE_CHECKING:
    import sqlite3
    from collections.abc import Sequence

    from media_hygiene.scan.deps import ScanDeps
    from media_hygiene.scan.models import MediaFile
    from media_hygiene.services.runtime import Runtime


@dataclass(frozen=True, slots=True)
class JournalFindings:
    """What the audit found the journal knows: the files back, the files gone."""

    returned: tuple[ReturnedFile, ...] = ()
    gone: int = 0  # files gone, waiting for `review --gone` (0224)


def remembered_of(runtime: Runtime, connection: sqlite3.Connection) -> RememberedSet:
    """What the journals remember, unless `[clean] returned = false`.

    Args:
        runtime: Settings, mount points and output.
        connection: The index, keeping what each journal said.

    Returns:
        The contents set aside by a choice; none without a journal mount (said once,
        when verbose).
    """
    if not runtime.settings.clean.returned:
        return RememberedSet()
    if not runtime.persistent(MountKind.JOURNAL):
        if runtime.output.verbose:
            runtime.output.info(
                _(
                    "No journal mount: the photos and videos you set aside before "
                    "are not recognised if they come back."
                )
            )
        return RememberedSet()
    return remembered_set(runtime.locations.journal_dir, connection)


def returned_finder(runtime: Runtime, deps: ScanDeps) -> ReturnedFinder | None:
    """The finder of the files back, when something is remembered.

    Args:
        runtime: Settings, mount points and output.
        deps: The audit's index, progress and I/O limit.

    Returns:
        The finder, or None.
    """
    remembered = remembered_of(runtime, deps.repository.connection)
    if not remembered:
        return None
    return ReturnedFinder(ExactDuplicateFinder(deps), remembered)


class ReturnedFinder:
    """Hashes the files of a size remembered, and tells which ones came back."""

    def __init__(self, exact: ExactDuplicateFinder, remembered: RememberedSet) -> None:
        """Compare through the exact pipeline's index and progress.

        Args:
            exact: The exact duplicate finder, whose digests the index keeps.
            remembered: What was set aside.
        """
        self._exact = exact
        self._remembered = remembered

    async def find(self, files: Sequence[MediaFile]) -> tuple[ReturnedFile, ...]:
        """Find the files whose content was set aside by a choice.

        Args:
            files: Healthy, non-empty media files.

        Returns:
            Each file back, with what was remembered of it: by SHA-256 first, else
            by partial digest (a file deleted in the Explorer, confirmed, 0224).
        """
        remembered = self._remembered
        step = Step(
            _("Recognising what you had set aside"),
            _(
                "Compares the files of the same size as a photo or video you had set "
                "aside: same SHA-256, it is back."
            ),
        )
        sizes = remembered.digest_sizes
        candidates = [file for file in files if file.size in sizes]
        digests = (
            await self._exact.digests(candidates, full_pass(step)) if candidates else {}
        )
        found = {
            file: ReturnedFile(file, said, digest)
            for file, digest in digests.items()
            if (said := remembered.by_digest.get((file.size, digest))) is not None
        }
        sizes = remembered.partial_sizes
        candidates = [f for f in files if f.size in sizes and f not in found]
        partials = (
            await self._exact.digests(candidates, partial_pass(step))
            if candidates
            else {}
        )
        for file, partial in partials.items():
            said = remembered.by_partial.get((file.size, partial))
            if said is not None:
                found[file] = ReturnedFile(file, said, partial=partial)
        return tuple(found.values())
