r"""Whether the PC holds what a phone file holds: the proof before freeing it (0248).

The phone gives a name, a size and a date: enough to propose, never to delete. `mh`
copies each file ticked in the page into an empty staging folder first; its SHA-256
is then compared, in this order, with:

1. a file of the library still there now (the index's digest while its size and
   date are unchanged, else computed now);
2. the import's own copy (`mh phone` copied it, now or before): the phone's size and
   the same SHA-256 — a second, independent read of the phone, so a truncated copy
   never frees its original;
3. a content the journals remember as set aside on purpose (full SHA-256, else the
   partial digest when only that one was kept): proven, with a warning — still in a
   quarantine, or purged and then nowhere else.

Otherwise the file stays on the phone, with its reason.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, Final

from media_hygiene.i18n import _
from media_hygiene.scan.hashing import full_digest
from media_hygiene.services.phone_holdings import (
    imported_copy,
    in_library,
    remembered_content,
)
from media_hygiene.services.phone_plan import PhoneCase

if TYPE_CHECKING:
    from datetime import datetime
    from pathlib import Path

    from media_hygiene.services.phone_holdings import Holdings
    from media_hygiene.services.phone_plan import PhoneFile

_DAY: Final = "%Y-%m-%d"


class Proven(StrEnum):
    """Where the PC holds the content of a phone file: the case of its deletion."""

    LIBRARY = "library"  # case 1: a file of the library
    IMPORTED = "imported"  # case 2: the copy `mh phone` made
    SET_ASIDE = "set-aside"  # case 3: set aside on purpose before (with a warning)


@dataclass(frozen=True, slots=True)
class Ticked:
    """A file ticked in the page: its case in the plan, and the plan's reason."""

    case: PhoneCase
    file: PhoneFile
    reason: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Proof:
    """The proof of one file: its SHA-256, where the PC holds it, or why not."""

    file: PhoneFile
    digest: str = ""  # empty: the staged copy could not be read whole
    proven: Proven | None = None  # None: kept on the phone
    held: str = ""  # the PC copy (host path), or the run that set it aside
    note: str = ""  # the warning of a set-aside, or why it stays on the phone


def prove(ticked: Ticked, staged: Path, holdings: Holdings) -> Proof:
    """Prove that the PC holds the content of one phone file.

    Args:
        ticked: The file, as the plan described it.
        staged: Its copy, just made from the phone into the staging folder.
        holdings: What the PC holds.

    Returns:
        The proof; `proven` is None when the file must stay on the phone.
    """
    file = ticked.file
    try:
        whole = staged.stat().st_size == file.size
        digest = full_digest(staged) if whole else ""
    except OSError:
        digest = ""
    if not digest:
        note = _("The copy from the phone is missing or incomplete: kept on the phone.")
        return Proof(file, note=note)
    rows = holdings.library.get(file.size, ())
    if (held := in_library(rows, file.size, digest)) is not None:
        return Proof(file, digest, Proven.LIBRARY, holdings.mapper.to_host(held))
    if (copy := _imported(ticked, digest, holdings.destination)) is not None:
        return Proof(file, digest, Proven.IMPORTED, holdings.mapper.to_host(copy))
    said = remembered_content(staged, (file.size, digest), holdings.remembered)
    if said is not None:
        quarantined = said.run_id in holdings.quarantined
        note = aside_warning(said.run_id, said.at, quarantined=quarantined)
        return Proof(file, digest, Proven.SET_ASIDE, said.run_id, note)
    return Proof(file, digest, note=_kept_reason(ticked))


def _imported(ticked: Ticked, digest: str, destination: Path | None) -> Path | None:
    """Find the import's copy a `destination` case names, of the same content.

    Args:
        ticked: The file and the plan's reason (the copy's relative path).
        digest: The SHA-256 of the staged copy.
        destination: The import's folder, in the container.

    Returns:
        The copy, or None.
    """
    if ticked.case is not PhoneCase.DESTINATION or destination is None:
        return None
    relative = ticked.reason[0] if ticked.reason else ""
    return imported_copy(destination, relative, (ticked.file.size, digest))


def aside_warning(run_id: str, at: datetime, *, quarantined: bool) -> str:
    """The warning of a file set aside before: recoverable, or lost for good.

    Args:
        run_id: The run that set it aside.
        at: When.
        quarantined: That run's quarantine is still there.

    Returns:
        The translated warning.
    """
    day = at.astimezone().strftime(_DAY)
    if quarantined:
        return _(
            "Set aside on {date}, still recoverable with mh undo {run} until mh purge."
        ).format(date=day, run=run_id)
    return _(
        "Set aside on {date} and purged since: it is nowhere else. Deleted from the "
        "phone, it is lost for good."
    ).format(date=day)


def _kept_reason(ticked: Ticked) -> str:
    """Why a file stays on the phone: the plan's file does not hold its content.

    Args:
        ticked: The file and the plan's reason.

    Returns:
        The translated reason.
    """
    if ticked.case in {PhoneCase.LIBRARY, PhoneCase.DESTINATION} and ticked.reason:
        return _("Not the same content as {path}: kept on the phone.").format(
            path=ticked.reason[0]
        )
    return _("Its content is nowhere on the PC: kept on the phone.")
