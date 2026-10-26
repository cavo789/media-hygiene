"""What the search page shows before *Move to an event…* (0403): the source folders."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


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
    target: str  # the destination, as Windows writes it; empty without a name
    sources: tuple[SourceFolder, ...]
