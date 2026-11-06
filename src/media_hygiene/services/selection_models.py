"""What the search page shows before *Move to an event…* (0403): the source folders."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from media_hygiene.classify.layout import safe_name

if TYPE_CHECKING:
    from collections.abc import Mapping
    from datetime import datetime
    from pathlib import Path

    from media_hygiene.classify.folders import FolderRules


@dataclass(frozen=True, slots=True)
class Picked:
    """The photos picked on the page: their container paths, and the index's dates."""

    paths: Mapping[int, Path]  # by key
    # When each was taken, read from the index: a photo the plan lacks keeps its month.
    days: Mapping[Path, datetime] = field(default_factory=dict)


class SourceFolder(BaseModel):
    """One source folder of the photos picked: ticked or not, and why."""

    model_config = ConfigDict(frozen=True)

    folder: str  # host path
    files: int
    keys: tuple[int, ...]
    ticked: bool
    named: str = ""  # its meaning, when the user named it after another event


class MoveView(BaseModel):
    """Where the photos picked would go: the name, the destination, the sources."""

    model_config = ConfigDict(frozen=True)

    proposed: str  # the name of the user's folder holding most of them; empty: none
    name: str  # the name kept, folder-safe
    month: str  # `YYYY/YYYY-MM` of the earliest photo: its event folders are offered
    target: str  # the destination, as Windows writes it; empty without a name
    sources: tuple[SourceFolder, ...]


class MonthGroup(BaseModel):
    """The photos picked that go to one month (0623)."""

    model_config = ConfigDict(frozen=True)

    target: str  # the destination, as Windows writes it
    keys: tuple[int, ...]


class MonthView(BaseModel):
    """What *Move to their month* would do with the photos picked (0623)."""

    model_config = ConfigDict(frozen=True)

    months: tuple[MonthGroup, ...]
    there: tuple[int, ...]  # already in their month: not moved
    undated: tuple[int, ...]  # no date, none guessed: not moved
    moves: int


def event_path(name: str) -> str:
    r"""The event's folder below the month: one name, or sub-folders (`France\Morzine`).

    Args:
        name: As typed, `\` or `/` between the folders.

    Returns:
        `France/Morzine`, each folder made safe, the empty ones dropped.
    """
    parts = (safe_name(part) for part in name.replace("\\", "/").split("/"))
    return "/".join(part for part in parts if part)


def sole_label(names: Mapping[str, str], rules: FolderRules) -> str:
    """The meaning of the only source folder's name: every picked photo comes from it.

    Even one naming a person or of several days (`Anniversaire Chloé`): the user moves
    that folder. A person's own folder (`Chloé`, one word) names no event.

    Args:
        names: The name of each source folder.
        rules: Tell a generic name (`Juin 2012`, `DCIM`) and a person's.

    Returns:
        Its label; empty for several folders, a generic name or a person's folder.
    """
    label = rules.label(next(iter(names.values()))) if len(names) == 1 else None
    if not label or (" " not in label and rules.of_person((label,))):
        return ""
    return label
