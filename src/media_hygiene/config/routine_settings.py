"""`[routine]` — the regular chores one click runs, in order, each on or off (0519).

`audit` (incremental), `copies` (the exact copies to the quarantine, `clean`'s own
question, `mh undo` puts them back), `purge` (the quarantine runs older than `[clean]
purge_hint_days`, `purge`'s own question for each), `reports` (the list refreshed).
An empty list: nothing runs.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, field_validator


class RoutineStep(StrEnum):
    """A step of the upkeep, in the order they run."""

    AUDIT = "audit"
    COPIES = "copies"
    PURGE = "purge"
    REPORTS = "reports"


class RoutineSettings(BaseModel):
    """`[routine]` — the steps of `upkeep`."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    steps: tuple[RoutineStep, ...] = (
        RoutineStep.AUDIT,
        RoutineStep.COPIES,
        RoutineStep.REPORTS,
    )  # purge is opt-in: it runs on its own (review 2026-11-05)

    @field_validator("steps")
    @classmethod
    def _in_order(cls, steps: tuple[RoutineStep, ...]) -> tuple[RoutineStep, ...]:
        """Run each step once, in the routine's order.

        Args:
            steps: The steps as written.

        Returns:
            Them in order.
        """
        return tuple(step for step in RoutineStep if step in steps)
