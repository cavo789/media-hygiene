"""What sorting a group from a page answers (0397, 0406): the run, the files left."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypedDict


class Counted(TypedDict):
    """The files of a group the run does not move, by why."""

    unknown: int
    fixed: int
    already: int


@dataclass(frozen=True, slots=True)
class GroupSorted:  # pylint: disable=too-many-instance-attributes  # the page's JSON
    """What the run did, read back; the files it could not take, counted."""

    run_id: str  # empty: nothing to move, no run
    moved: int
    verified: int  # moves checked at their new place after the run
    intact: bool
    unknown: int = 0  # files the classify run does not know: run classify again
    fixed: int = 0  # files the plan leaves as they are
    already: int = 0  # files an earlier run of the plan moved already
    links: tuple[str, ...] = ()  # the user's files naming photos, rewritten (0406)


@dataclass(frozen=True, slots=True)
class Matched:
    """The files of a group, sorted out against the plan."""

    rows: dict[str, str]  # row id → its folder: to move now
    already: int
    fixed: int
    unknown: int
