"""`plan.json`: the source of truth of a `classify` run, versioned, one row per file.

The workbook is only its editing surface. Row ids come from the content (the SHA-256 the
audit computed), event ids from the engine: both survive a new run, so edits carry over.
"""

from __future__ import annotations

from collections import Counter
from typing import Final

from pydantic import BaseModel, ConfigDict

from media_hygiene.classify.layout import Values
from media_hygiene.classify.models import Band, DateSource, SortReason

PLAN_FORMAT: Final = 1


class _Frozen(BaseModel):
    """A frozen, strict pydantic model."""

    model_config = ConfigDict(frozen=True, extra="forbid")


class RowValues(_Frozen):
    """What the layouts know of a file: re-rendered when the user names its event."""

    year: int  # the year folder: an event keeps the year of its start
    month: int
    day: int
    category: str
    event: str  # the `{event}` value: the event's label or span
    event_start: str

    def as_values(self) -> Values:
        """The layout values.

        Returns:
            Them.
        """
        return Values(**self.model_dump())


class PlanRow(_Frozen):
    """One media file and where it is proposed to go."""

    id: str
    path: str  # host path of the file
    size: int
    mtime_ns: int
    sha256: str | None
    date: str | None  # ISO date and time, local
    date_source: DateSource | None
    event_id: str
    values: RowValues | None  # what the layout was rendered from; None: stays
    band: Band
    reason: SortReason
    score: int
    rule: str = ""  # the name of the rule that decided; empty: no rule
    root: str  # host folder the proposal is relative to
    folder: str | None  # relative to `root`, `/`-separated; None: stay where it is
    name: str  # the target name: the original one for now

    @property
    def category(self) -> str:
        """The proposed category.

        Returns:
            It, or an empty string.
        """
        return self.values.category if self.values else ""

    @property
    def why(self) -> str:
        """Why the file goes there: the rule's name, else the reason.

        Returns:
            It.
        """
        return self.rule or self.reason.value

    @property
    def parent(self) -> str:
        """The host folder of the file, written as the host writes it.

        Returns:
            It.
        """
        cut = max(self.path.rfind("\\"), self.path.rfind("/"))
        return self.path[:cut] if cut > 0 else self.path

    @property
    def in_place(self) -> bool:
        """Tell whether the file already sits in its proposed folder.

        Returns:
            True when it stays, or its folder is the proposed one.
        """
        if self.folder is None:
            return True
        target = f"{self.root}/{self.folder}".replace("\\", "/")
        return self.parent.replace("\\", "/") == target


class PlanEvent(_Frozen):
    """Files taken close together, named once."""

    id: str
    start: str
    end: str
    span: str  # the default name: `2016-07-01..07-15`
    label: str  # the meaningful folder the event came from, if any
    rows: tuple[str, ...]  # row ids, in date order


class ClassifyPlan(_Frozen):
    """Every proposal of one run, and the layouts that produced them."""

    version: int = PLAN_FORMAT
    plan_id: str
    layout: str  # the sure layout: re-rendered when the user names an event
    unsure_layout: str  # the "to check" layout: re-rendered when a category is renamed
    rows: tuple[PlanRow, ...]
    events: tuple[PlanEvent, ...]
    unused_rules: tuple[str, ...] = ()  # rules that decided no file of the plan

    def categories(self) -> dict[str, int]:
        """The proposed categories and their file counts, the largest first.

        Returns:
            Category → files.
        """
        counts = Counter(row.category for row in self.rows if row.category)
        return dict(counts.most_common())
