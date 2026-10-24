"""The choices of the page of `shrink --try`, kept in `shrink-decisions.json` (0307).

Only a draft ready can be chosen; each choice rewrites the file in one atomic step,
and the page is answered with what the disk holds then.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

from media_hygiene.shrink.draft_bench import DraftState
from media_hygiene.shrink.try_choices import (
    TryChoice,
    TryChoices,
    read_choices,
    save_choices,
)

if TYPE_CHECKING:
    from media_hygiene.services.shrink_try import Trial
    from media_hygiene.shrink.draft_bench import Draft


class ChoiceAsked(BaseModel):
    """`POST /api/shrink/choose`: drafts added to the choices, or taken out."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    drafts: tuple[int, ...] = Field(min_length=1)
    chosen: bool


def ready_draft(trial: Trial, number: int) -> Draft | None:
    """Find a draft ready to be shown or chosen.

    Args:
        trial: The try.
        number: Its number in the try.

    Returns:
        It, or None.
    """
    drafts = trial.bench.drafts()
    found = drafts[number - 1] if 0 < number <= len(drafts) else None
    return found if found is not None and found.state is DraftState.READY else None


def record_choice(trial: Trial, asked: ChoiceAsked) -> None:
    """Add the drafts asked to the file, or take them out, then save it.

    Args:
        trial: The try.
        asked: The drafts, and whether they are chosen.

    Raises:
        OSError: The file could not be written.
    """
    known = read_choices(trial.choices)
    if known is None or known.run != trial.run:
        known = TryChoices(run=trial.run)
    kept = [choice for choice in known.chosen if choice.draft not in asked.drafts]
    if asked.chosen:
        for number in asked.drafts:
            draft = ready_draft(trial, number)
            if draft is None:
                continue
            video = draft.video
            kept.append(
                TryChoice(
                    path=str(video.path),
                    size=video.size,
                    mtime_ns=video.mtime_ns,
                    draft=draft.number,
                )
            )
    kept.sort(key=lambda choice: choice.draft)
    save_choices(trial.choices, known.model_copy(update={"chosen": tuple(kept)}))


def chosen_count(trial: Trial) -> int:
    """Count the videos the file holds, read from the disk.

    Args:
        trial: The try.

    Returns:
        Their number; 0 without a file of this try.
    """
    choices = read_choices(trial.choices)
    return len(choices.chosen) if choices and choices.run == trial.run else 0
