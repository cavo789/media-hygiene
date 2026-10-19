r"""The journal of `mh phone` freeing a phone: `pending` before, `done` after (0248).

A run of kind `phone`, written ahead as `clean` writes: `phone-prove` records each
proven file `pending` before `mh` removes it from the phone, `phone-done` records it
`done` once the phone's folder, listed again, no longer holds it. Each entry keeps
the file's name on the phone, its size, its SHA-256 and its case; for the library and
the import, `keeper` names the PC file holding the same content. `undo` cannot put a
file back on a phone: it refuses such a run, and says where the copies are.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import PureWindowsPath
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

from media_hygiene.actions.journal import (
    JournalEntry,
    JournalWriter,
    journal_file,
    latest_states,
    read_journal,
)
from media_hygiene.actions.kinds import ActionKind, Phase, Status
from media_hygiene.actions.runs import RUN_ID_PATTERN, new_run_id, run_phase
from media_hygiene.errors import JournalError
from media_hygiene.i18n import _
from media_hygiene.services.phone_proof import Proven

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping
    from pathlib import Path

    from media_hygiene.services.phone_proof import Proof

_NANOSECONDS: Final = 1_000_000_000
_DCIM: Final = "DCIM"
KINDS: Final[Mapping[Proven, ActionKind]] = MappingProxyType(
    {
        Proven.LIBRARY: ActionKind.PHONE_LIBRARY,
        Proven.IMPORTED: ActionKind.PHONE_IMPORTED,
        Proven.SET_ASIDE: ActionKind.PHONE_SET_ASIDE,
    }
)


@dataclass(frozen=True, slots=True)
class PhoneRun:
    """A run freeing a phone: its journal, and the phone's name."""

    journal: Path
    phone: str

    @property
    def run_id(self) -> str:
        """Its identifier: the journal's name.

        Returns:
            It.
        """
        return self.journal.stem


def phone_run(journal_dir: Path, run_id: str | None, phone: str) -> PhoneRun:
    """Start a run freeing a phone, or go on with one (the next batch of files).

    Args:
        journal_dir: Journal mount point.
        run_id: The run to go on with; None starts a new one.
        phone: The phone's name, as Windows shows it.

    Returns:
        The run.

    Raises:
        JournalError: The run named is not a phone run of this journal.
    """
    journal_dir.mkdir(parents=True, exist_ok=True)
    if run_id is None:
        return PhoneRun(journal_file(journal_dir, new_run_id(journal_dir)), phone)
    journal = journal_file(journal_dir, run_id)
    named = RUN_ID_PATTERN.fullmatch(run_id) is not None and journal.is_file()
    if not named or run_phase(read_journal(journal)) is not Phase.PHONE:
        raise JournalError(_("Unknown run {run_id}.").format(run_id=run_id))
    return PhoneRun(journal, phone)


def record_pending(run: PhoneRun, proofs: Iterable[Proof]) -> int:
    """Write each proven file `pending`, on the disk before it leaves the phone.

    Args:
        run: The run.
        proofs: The proofs; the files kept on the phone are not written.

    Returns:
        How many were written.
    """
    proven = [proof for proof in proofs if proof.proven is not None]
    if not proven:
        return 0  # no journal for a run that deleted nothing
    entries = read_journal(run.journal) if run.journal.is_file() else []
    first = max((entry.seq for entry in entries), default=0) + 1
    with JournalWriter.open(run.journal) as journal:
        for seq, proof in enumerate(proven, first):
            journal.record(_pending(run, proof, seq))
    return len(proven)


def _pending(run: PhoneRun, proof: Proof, seq: int) -> JournalEntry:
    """The `pending` entry of a proven file.

    Args:
        run: The run (the phone's name).
        proof: The proof.
        seq: Its number in the journal.

    Returns:
        The entry; `keeper` names the PC copy (library, import).
    """
    file = proof.file
    proven = proof.proven or Proven.LIBRARY
    return JournalEntry(
        seq=seq,
        phase=Phase.PHONE,
        status=Status.PENDING,
        action=KINDS[proven],
        path=file.path.as_posix(),
        host_path=str(PureWindowsPath(run.phone, _DCIM, *file.path.parts)),
        size=file.size,
        mtime_ns=_nanoseconds(file.modified),
        sha256=proof.digest,
        keeper=proof.held if proven is not Proven.SET_ASIDE else None,
    )


def _nanoseconds(modified: str) -> int:
    """The phone's date of a file, in nanoseconds since 1970.

    Args:
        modified: `System.DateModified`, ISO 8601, UTC.

    Returns:
        It; 0 when the phone gave none.
    """
    try:
        return int(datetime.fromisoformat(modified).timestamp() * _NANOSECONDS)
    except ValueError:
        return 0


def record_done(run: PhoneRun, paths: Iterable[str]) -> tuple[str, ...]:
    """Write `done` the files gone from the phone, each written `pending` before.

    Args:
        run: The run.
        paths: The files no longer on the phone, below `DCIM`.

    Returns:
        The paths written `done`, in the order given; the others were not pending.
    """
    latest = latest_states(read_journal(run.journal), Phase.PHONE)
    pending = {
        entry.path: entry for entry in latest.values() if entry.status is Status.PENDING
    }
    done: list[str] = []
    with JournalWriter.open(run.journal) as journal:
        for path in paths:
            entry = pending.pop(path, None)
            if entry is not None:
                journal.record(entry.as_done())
                done.append(path)
    return tuple(done)
