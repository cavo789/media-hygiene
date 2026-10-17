"""What `clean` says of the folders it leaves empty: before it asks, once it is over."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.actions.sort_folders import Fate
from media_hygiene.console.formatting import human_number
from media_hygiene.console.tables import outcome_table
from media_hygiene.i18n import ngettext

if TYPE_CHECKING:
    from media_hygiene.actions.outcome import Outcome
    from media_hygiene.actions.sort_folders import FolderReport
    from media_hygiene.console.output import Output


def tell_emptied(output: Output, predicted: FolderReport) -> None:
    """Say how many folders the clean will leave empty and remove.

    Args:
        output: Where to print.
        predicted: The prediction of the walk, before anything moves.
    """
    if predicted.removed:
        message = ngettext(
            "{count} folder will be left empty and removed; 'undo' recreates it.",
            "{count} folders will be left empty and removed; 'undo' recreates them.",
            predicted.removed,
        )
        output.info(message.format(count=human_number(predicted.removed)))
    junk = sum(verdict.fate is Fate.HOLDS_JUNK for verdict in predicted.kept)
    if junk:
        message = ngettext(
            "{count} folder will hold only system files (Thumbs.db...): it stays, "
            "no quarantine is mounted to put them in.",
            "{count} folders will hold only system files (Thumbs.db...): they stay, "
            "no quarantine is mounted to put them in.",
            junk,
        )
        output.info(message.format(count=human_number(junk)))


def show_clean_outcome(output: Output, outcome: Outcome, title: str) -> None:
    """Show the counts of a clean, then how many folders it left empty and removed.

    Args:
        output: Where to print.
        outcome: What the clean did.
        title: The title of the table, naming the run.
    """
    output.show(outcome_table(outcome, title))
    if not outcome.folders_removed:
        return
    message = ngettext(
        "{count} folder left empty was removed.",
        "{count} folders left empty were removed.",
        outcome.folders_removed,
    )
    output.info(message.format(count=human_number(outcome.folders_removed)))
