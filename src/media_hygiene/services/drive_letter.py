r"""A run whose drive came back under another letter (0186): found, not refused.

A USB drive set aside as `E:` and plugged back as `F:`: the journal says
`/quarantine/e/<run>/…` and `/data/e/…`, the files sit in `/quarantine/f/<run>` and the
photos under `/data/f`. A run identifier is unique, so the run's folder found in exactly
one other drive's quarantine tells the new letter; found in two (a copy made by hand),
`undo` and `purge` refuse, naming both. A file comes back only when its folder exists
under the new letter: never onto another drive's path by guess.
"""

from __future__ import annotations

import contextlib
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from media_hygiene.actions.outcome import Incident
from media_hygiene.errors import MountError
from media_hygiene.i18n import _
from media_hygiene.paths.quarantines import drive_name
from media_hygiene.services.letter_refusals import refused as refusals

if TYPE_CHECKING:
    from collections.abc import Iterable

    from media_hygiene.actions.journal import JournalEntry
    from media_hygiene.paths.quarantines import Quarantines


@dataclass(frozen=True, slots=True)
class LetterChange:
    """A drive of a run, then and now, with the mount points of both letters."""

    old: str  # `e`
    new: str  # `f`
    quarantine: Path  # `/quarantine`
    data: Path  # `/data`

    def move(self, value: str | None) -> str | None:
        """Write a journal path under the new letter.

        Args:
            value: A path of the journal, or None.

        Returns:
            The same path under `f` when it was under `e`, unchanged otherwise.
        """
        return _swapped(value, (self.quarantine, self.data), (self.old, self.new))

    def back(self, value: str | None) -> str | None:
        """Write a path of the new letter as the journal and the index first had it.

        Args:
            value: A path under the new letter, or None.

        Returns:
            The same path under `e` when it was under `f`, unchanged otherwise.
        """
        return _swapped(value, (self.quarantine, self.data), (self.new, self.old))


def moved_to(quarantines: Quarantines, run_id: str, drive: str) -> str | None:
    """Look for a run's folder in the other drives' quarantines.

    Args:
        quarantines: The quarantines mounted.
        run_id: The run.
        drive: The drive the journal names, not mounted now, e.g. `E:`.

    Returns:
        The letter of the one other drive holding that drive's files of the run (`f`:
        `/quarantine/f/<run>/e`), else None; a drive holding only its own is no match.

    Raises:
        MountError: Two drives hold the run's folder.
    """
    old = drive[0].lower()
    found = [  # the run mirrors /data inside its folder: `<run>/e/…` for E:'s files
        name
        for name, folder in quarantines.by_drive
        if (folder / run_id / old).is_dir()
    ]
    if len(found) > 1:
        raise MountError(
            _(
                "The run {run_id} set files aside on {drive}, and a folder of that run "
                "is in the quarantines of {both}: nothing was changed."
            ).format(run_id=run_id, drive=drive, both=", ".join(found)),
            _("Keep one of them: the other is a copy."),
        )
    return found[0][0].lower() if found else None


def relocate(
    entries: list[JournalEntry], changes: Iterable[LetterChange]
) -> tuple[list[JournalEntry], tuple[Incident, ...]]:
    """Write a run's journal under the new letters, for its undo.

    Args:
        entries: The run's journal.
        changes: The drives that changed letter.

    Returns:
        The entries to undo, and one refusal per file whose folder is missing under
        the new letter (all the lines of that file left out).
    """
    moved = list(entries)
    for change in changes:
        moved = [_moved(entry, change) for entry in moved]
    refused = refusals(moved, entries)  # a folder the run removed comes back first
    reason = _("its folder is not on the drive under its new letter")
    return (
        [entry for entry in moved if entry.seq not in refused],
        tuple(Incident(path, reason) for path in refused.values()),
    )


def tidy(change: LetterChange, run_id: str) -> None:
    """Remove the run's folders left empty in the quarantine of the new letter.

    Inside, the run still mirrors the old letter (`<run>/e/Photos`), which the undo's
    own clean-up, matching folder names, stops at. `rmdir` never deletes content.

    Args:
        change: The change of letter.
        run_id: The run undone.
    """
    root = change.quarantine / change.new / run_id
    folders = [path for path in root.rglob("*") if path.is_dir()]
    for folder in (*sorted(folders, key=lambda path: -len(path.parts)), root):
        with contextlib.suppress(OSError):  # not empty, or already gone
            folder.rmdir()


def found_line(change: LetterChange, run_id: str) -> str:
    """Say where the run was found.

    Args:
        change: The change of letter.
        run_id: The run.

    Returns:
        The translated line.
    """
    return _("Run {run_id} found in the quarantine of {new}, not of {old}.").format(
        run_id=run_id, new=drive_name(change.new), old=drive_name(change.old)
    )


def _moved(entry: JournalEntry, change: LetterChange) -> JournalEntry:
    """One journal line under the new letter.

    Args:
        entry: The line.
        change: The change of letter.

    Returns:
        A copy, its paths moved.
    """
    return entry.model_copy(
        update={
            name: change.move(getattr(entry, name))
            for name in ("path", "quarantine", "keeper", "target")
        }
    )


def _swapped(
    value: str | None, roots: tuple[Path, Path], letters: tuple[str, str]
) -> str | None:
    """Write a path under one letter as the same path under another.

    Args:
        value: A path, or None.
        roots: The mount points that hold one folder per letter.
        letters: From, then to.

    Returns:
        The path moved when it was under the first letter, unchanged otherwise.
    """
    if value is None:
        return None
    path = Path(value)
    source, destination = letters
    for root in roots:
        if path.is_relative_to(root / source):
            return str(root / destination / path.relative_to(root / source))
    return value
