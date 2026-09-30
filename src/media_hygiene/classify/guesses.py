"""A file `sort` put in the "to check" folder of its guess stays there, still to check.

Its folder is the previous guess, not a meaning: without a sure rule, a new run would
only guess again, and `sort` would move it back and forth. A sure rule still moves it;
confirming or renaming its category in the workbook moves it too.
"""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

from media_hygiene.classify.models import Band, SortReason, Verdict

if TYPE_CHECKING:
    from media_hygiene.classify.models import Proposal


def keep_guess(proposal: Proposal, guess: str | None, score: int) -> Proposal:
    """Leave a file in the "to check" folder it was sorted into, unless a rule is sure.

    Args:
        proposal: What the rules propose for the file.
        guess: The category of the "to check" folder it lies in, or None.
        score: The score of a "to check" proposal (`[classify] unsure`).

    Returns:
        The proposal, or the file left in place, "to check", its category the guess.
    """
    if guess is None or proposal.band in {Band.SURE, Band.STAY}:
        return proposal
    file = proposal.file
    values = replace(proposal.values, category=guess) if proposal.values else None
    return replace(
        proposal,
        verdict=Verdict(Band.UNSURE, SortReason.PREVIOUS_GUESS, score),
        values=values,
        folder=file.path.parent.relative_to(file.root).as_posix(),
        target=file.path.parent,
    )
