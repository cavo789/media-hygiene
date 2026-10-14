"""`plan.json`: the source of truth of a `classify` run, versioned, one row per file.

The workbook is only its editing surface. Row ids come from the content (the SHA-256 the
audit computed), event ids from the engine: both survive a new run, so edits carry over.
"""

from __future__ import annotations

from collections import Counter
from typing import Final

from pydantic import BaseModel, ConfigDict

from media_hygiene.classify.carry_models import CarryRecord
from media_hygiene.classify.plan_deferred import DeferredEdits
from media_hygiene.classify.plan_rows import PlanEvent, PlanRow, RowValues

__all__ = ["PLAN_FORMAT", "ClassifyPlan", "PlanEvent", "PlanRow", "RowValues"]

PLAN_FORMAT: Final = 1


class ClassifyPlan(BaseModel):
    """Every proposal of one run, and the layouts that produced them."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    version: int = PLAN_FORMAT
    plan_id: str
    layout: str  # the sure layout: re-rendered when the user names an event
    unsure_layout: str  # the "to check" layout: re-rendered when a category is renamed
    rows: tuple[PlanRow, ...]
    events: tuple[PlanEvent, ...]
    unused_rules: tuple[str, ...] = ()  # rules that decided no file of the plan
    carried: CarryRecord | None = None  # the edits carried over from a workbook
    # `--year`, `--path`: the edits of the files left out, kept for a later run.
    deferred: DeferredEdits | None = None

    def categories(self) -> dict[str, int]:
        """The proposed categories and their file counts, the largest first.

        Returns:
            Category → files.
        """
        counts = Counter(row.category for row in self.rows if row.category)
        return dict(counts.most_common())
