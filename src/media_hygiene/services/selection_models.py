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


def event_path(name: str) -> str:
    r"""The event's folder below the month: one name, or sub-folders (`France\Morzine`).

    Args:
        name: As typed, `\` or `/` between the folders.

    Returns:
        `France/Morzine`, each folder made safe, the empty ones dropped.
    """
    parts = (safe_name(part) for part in name.replace("\\", "/").split("/"))
    return "/".join(part for part in parts if part)
