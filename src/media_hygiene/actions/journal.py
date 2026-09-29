"""Write-ahead journal: a JSON line before an action (`pending`), one after (`done`)."""

from __future__ import annotations

import os
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Self

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from media_hygiene.actions.kinds import ActionKind, Phase, Status
from media_hygiene.constants import JOURNAL_SUFFIX
from media_hygiene.errors import JournalError
from media_hygiene.i18n import _

if TYPE_CHECKING:
    from pathlib import Path
    from typing import TextIO


class JournalEntry(BaseModel):
    """One action on one file, as recorded in the journal."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    seq: int
    phase: Phase
    status: Status
    action: ActionKind
    path: str
    host_path: str
    size: int
    mtime_ns: int
    sha256: str | None = None
    keeper: str | None = None
    quarantine: str | None = None
    # Where a `move` put the file (absent from journals written before 0.3).
    target: str | None = None
    at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def as_done(self) -> JournalEntry:
        """Return the `done` twin of a `pending` entry.

        Returns:
            A copy with status `done` and a fresh timestamp.
        """
        return self.model_copy(update={"status": Status.DONE, "at": datetime.now(UTC)})


def journal_file(journal_dir: Path, run_id: str) -> Path:
    """Return the journal path of a run.

    Args:
        journal_dir: Journal mount point.
        run_id: Identifier of the run.

    Returns:
        `<journal_dir>/<run_id>.jsonl`.
    """
    return journal_dir / f"{run_id}{JOURNAL_SUFFIX}"


class JournalWriter:
    """Appends entries and forces them to disk before the action they announce."""

    def __init__(self, stream: TextIO) -> None:
        """Wrap an append-mode text stream.

        Args:
            stream: Journal file opened for appending.
        """
        self._stream = stream

    @classmethod
    def open(cls, file: Path) -> Self:
        """Open (or create) a journal for appending.

        Args:
            file: Journal path.

        Returns:
            The writer.
        """
        return cls(file.open("a", encoding="utf-8"))

    def __enter__(self) -> Self:
        """Use the writer as a context manager.

        Returns:
            The writer itself.
        """
        return self

    def __exit__(self, *exc_info: object) -> None:
        """Close the journal.

        Args:
            *exc_info: Exception details from the `with` statement (unused).
        """
        self._stream.close()

    def record(self, entry: JournalEntry) -> None:
        """Append one entry and flush it to the disk.

        Args:
            entry: Entry to persist.
        """
        self._stream.write(entry.model_dump_json() + "\n")
        self._stream.flush()
        os.fsync(self._stream.fileno())


def read_journal(file: Path) -> list[JournalEntry]:
    """Read every entry of a journal.

    Args:
        file: Journal path.

    Returns:
        The entries, in write order.

    Raises:
        JournalError: The journal is missing or a line is corrupt.
    """
    if not file.is_file():
        raise JournalError(_("No journal found at {path}.").format(path=file))
    entries: list[JournalEntry] = []
    for number, line in enumerate(file.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            entries.append(JournalEntry.model_validate_json(line))
        except ValidationError as exc:
            raise _corrupt(file, number, exc) from exc
    return entries


def _corrupt(file: Path, number: int, exc: ValidationError) -> JournalError:
    """Explain why a journal line cannot be read.

    Args:
        file: The journal.
        number: The line number.
        exc: What the validation said.

    Returns:
        The error; an action this version does not know gets a tip of its own.
    """
    if any(error["loc"] == ("action",) for error in exc.errors()):
        message = _(
            "Line {number} of {path} holds an action this version does not know: "
            "nothing was changed."
        )
        tip = _("A newer version wrote this journal: update media-hygiene to undo it.")
        return JournalError(message.format(number=number, path=file), tip)
    message = _("Line {number} of {path} is corrupt.")
    return JournalError(message.format(number=number, path=file))


def latest_states(entries: list[JournalEntry], phase: Phase) -> dict[int, JournalEntry]:
    """Keep, for each action of a phase, its last recorded state.

    Args:
        entries: Journal entries, in write order.
        phase: `clean` or `undo`.

    Returns:
        The latest entry of each sequence number.
    """
    return {entry.seq: entry for entry in entries if entry.phase is phase}


def done_states(entries: list[JournalEntry], phase: Phase) -> list[JournalEntry]:
    """List the actions of a phase that completed (their latest state is `done`).

    A run resumed after an interruption skips these.

    Args:
        entries: Journal entries, in write order.
        phase: `clean`, `sort` or `undo`.

    Returns:
        Their latest entries, in sequence order.
    """
    latest = latest_states(entries, phase)
    return [latest[seq] for seq in sorted(latest) if latest[seq].status is Status.DONE]
