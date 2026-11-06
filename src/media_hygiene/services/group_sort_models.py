"""What sorting a group from a page answers (0397, 0406): the run, the files left."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path


@dataclass(frozen=True, slots=True)
class GroupMove:
    """A group to sort: each file's folder, the category, the root if one is imposed."""

    folders: Mapping[Path, str]  # container path → its folder below its root
    category: str
    root: Path | None = None  # the target chosen (0596); None: each row's own root


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
    unknown: int = 0  # files the index does not know: run an audit (0452)
    fixed: int = 0  # files the plan leaves as they are
    already: int = 0  # files an earlier run of the plan moved already
    links: tuple[str, ...] = ()  # the user's files naming photos, rewritten (0406)


@dataclass(frozen=True, slots=True)
class Matched:
    """The files of a group, sorted out against the plan."""

    rows: dict[str, str]  # row id → its folder: to move now
    already: int
    fixed: int
    strangers: tuple[Path, ...]  # container paths the plan has no row for

    @property
    def unknown(self) -> int:
        """Count the files the plan does not know.

        Returns:
            Them.
        """
        return len(self.strangers)
