"""The runs of the journal as rows, for the terminal and the home page alike (0350).

`mh history` prints them as a table, the home page's *History and undo* space shows
the same cells: one function builds them, so both say the same thing.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.actions.kinds import Phase
from media_hygiene.console.formatting import human_number, human_size
from media_hygiene.i18n import _

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from media_hygiene.actions.runs import RunSummary

# Runs `undo <run>` cannot reverse: `push` has its own undo, the others none.
_NO_UNDO: Final = frozenset({Phase.UNDO, Phase.PHONE, Phase.PUSH})


@dataclass(frozen=True, slots=True)
class HistoryRow:
    """One run: its name, its command, its figures, the line that undoes it."""

    run_id: str
    command: str
    cells: tuple[str, ...]  # the figures, in the order of `HistoryTable.figures`
    undo: str  # the command to copy; empty when `undo` cannot reverse it
    source: str = ""  # "from the quarantine": known only from its journal's copy (0721)


@dataclass(frozen=True, slots=True)
class HistoryTable:
    """The runs, newest first, and the notes that apply to them."""

    figures: tuple[str, ...]  # the headers after *Run* and *Command*
    rows: tuple[HistoryRow, ...]
    notes: tuple[str, ...]


def undo_line(run: RunSummary) -> str:
    """The command that puts a run back.

    Args:
        run: The run.

    Returns:
        It; empty when `undo` cannot reverse this run.
    """
    return "" if run.kind in _NO_UNDO else f"mh undo {run.run_id}"


def history_table(
    summaries: Sequence[RunSummary], copied: frozenset[str] = frozenset()
) -> HistoryTable:
    """Build the rows: the optional columns only when some run has something in them.

    Args:
        summaries: The runs, newest first.
        copied: The runs known only from the copy of their journal in a quarantine.

    Returns:
        The columns, the rows and the 🛟 / 📱 / 🧾 notes.
    """
    optional: list[tuple[str, Callable[[RunSummary], int]]] = [
        (_("Of which unwanted"), lambda run: run.unwanted),
        (_("Of which back again"), lambda run: run.returned),
        (_("Deleted in the Explorer"), lambda run: run.marked),
        (_("Moved"), lambda run: run.moved),
        (_("Linked"), lambda run: run.linked),
        (_("Sidecars"), lambda run: run.kept.written),
        (_("Folders removed"), lambda run: run.folders_removed),
        (_("Copied"), lambda run: run.kept.copied),  # bytes: import, mh push
    ]
    shown = [(h, count) for h, count in optional if any(map(count, summaries))]
    sizes = {_("Copied")}
    figures = (_("Deleted"), _("Freed"), _("Quarantined"))
    rows = tuple(
        HistoryRow(
            run.run_id,
            run.kind.value,
            (
                human_number(run.deleted),
                human_size(run.freed),
                human_number(run.quarantined),
                *(
                    (human_size if header in sizes else human_number)(count(run))
                    for header, count in shown
                ),
                human_number(run.restored),
            ),
            undo_line(run),
            _("from the quarantine") if run.run_id in copied else "",
        )
        for run in summaries
    )
    return HistoryTable(
        (*figures, *(header for header, _count in shown), _("Restored")),
        rows,
        _notes(summaries, copied),
    )


def _notes(summaries: Sequence[RunSummary], copied: frozenset[str]) -> tuple[str, ...]:
    """The 🛟 backup, 📱 phone and 🧾 copy notes, when a run of that kind is listed.

    Args:
        summaries: The runs.
        copied: The runs known only from the copy of their journal in a quarantine.

    Returns:
        The notes that apply.
    """
    notes: list[str] = []
    if copied:
        notes.append(
            _(
                "🧾 A run marked 'from the quarantine' has no journal in the journal "
                "folder: the copy beside its quarantine says what it did, and "
                "mh undo <run> takes that copy back first."
            )
        )
    if any(run.kind is Phase.PUSH for run in summaries):
        notes.append(
            _(
                "🛟 A backup run changed its backup folder only, never your photos: "
                "mh push --undo <run> puts back what it renamed or set aside there."
            )
        )
    if any(run.kind is Phase.PHONE for run in summaries):
        notes.append(
            _(
                "📱 A phone run deleted files from a phone: undo cannot put them "
                "back on it. Each one was first proven on the PC by its content."
            )
        )
    return tuple(notes)
