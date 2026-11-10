"""The journals and the user's choices in the archive of `backup` (0687).

`undo` reads `/journal/<run>.jsonl`: without it, the way back of a clean or a sort is
gone. The choices not applied yet live in `/reports` (`decisions.json`, a classify
plan's `sort-decisions.json`, the albums' list). All are small files: they go into
the archive under `journal/` and `reports/`, with their SHA-256 in the manifest.
`restore` puts back only the files that are missing, never over one that exists (a
journal on the disk is always as new as the archive's, or newer), and proves each by
reading it back.
"""

from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING, Final

from media_hygiene.actions.no_overwrite import move_no_replace
from media_hygiene.constants import JOURNAL_SUFFIX
from media_hygiene.paths.mount_kind import MountKind

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

    from media_hygiene.services.backup_archive import Manifest
    from media_hygiene.services.runtime import Runtime

JOURNAL_PREFIX: Final = "journal/"
REPORTS_PREFIX: Final = "reports/"
# The files of `/reports` holding the user's choices, at its top or one folder down.
CHOICES: Final = frozenset(
    {
        "decisions.json",
        "sort-decisions.json",
        "phone-decisions.json",
        "import-bursts.json",
        "albums.json",
    }
)
_DRAFT: Final = ".restore"


def extra_files(runtime: Runtime) -> Iterator[tuple[str, Path]]:
    """The journals and the choice files to archive, as (member, file).

    Args:
        runtime: Settings, mount points and output.

    Yields:
        Each member name and the file it is read from.
    """
    journal = runtime.locations.journal_dir
    if runtime.persistent(MountKind.JOURNAL) and journal.is_dir():
        for file in sorted(journal.glob(f"*{JOURNAL_SUFFIX}")):
            if file.is_file():
                yield JOURNAL_PREFIX + file.name, file
    reports = runtime.locations.reports_dir
    if runtime.persistent(MountKind.REPORTS) and reports.is_dir():
        found = (*reports.glob("*.json"), *reports.glob("*/*.json"))
        for file in sorted(found):
            if file.name in CHOICES and file.is_file():
                yield REPORTS_PREFIX + file.relative_to(reports).as_posix(), file


def is_extra(member: str) -> bool:
    """Tell whether a member of the archive is a journal or a choice file.

    Args:
        member: Its name.

    Returns:
        True below `journal/` or `reports/`.
    """
    return member.startswith((JOURNAL_PREFIX, REPORTS_PREFIX))


def put_back_missing(
    runtime: Runtime, extracted: Path, manifest: Manifest
) -> tuple[str, ...]:
    """Put back the journals and choice files that are missing, read back.

    Args:
        runtime: Settings, mount points and output.
        extracted: The folder the archive was extracted to, checked.
        manifest: Its manifest.

    Returns:
        The members written; a file already there is left untouched.
    """
    roots = {
        JOURNAL_PREFIX: (runtime.locations.journal_dir, MountKind.JOURNAL),
        REPORTS_PREFIX: (runtime.locations.reports_dir, MountKind.REPORTS),
    }
    written: list[str] = []
    for member, expected in sorted(manifest.members.items()):
        prefix = next((p for p in roots if member.startswith(p)), None)
        if prefix is None or not runtime.persistent(roots[prefix][1]):
            continue
        target = roots[prefix][0] / member.removeprefix(prefix)
        if target.exists():
            continue
        draft = target.with_name(f".{target.name}{_DRAFT}")
        target.parent.mkdir(parents=True, exist_ok=True)
        draft.write_bytes((extracted / member).read_bytes())
        try:
            move_no_replace(draft, target)
        except FileExistsError:  # written meanwhile: the newer one stays
            draft.unlink(missing_ok=True)
            continue
        if hashlib.sha256(target.read_bytes()).hexdigest() == expected:
            written.append(member)
    return tuple(written)
