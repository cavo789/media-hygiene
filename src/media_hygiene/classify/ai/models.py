"""The vocabulary of the `subject` rule: units to ask about, descriptions, subjects."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime
    from pathlib import Path


@dataclass(frozen=True, slots=True)
class Candidate:
    """A photo the model may see: large enough, decoded, dated."""

    path: Path
    when: datetime
    sharpness: float


@dataclass(frozen=True, slots=True)
class Unit:
    """An event (or a lone file) no stronger rule decided: one answer for its files.

    `members` take the answer; `candidates` are the photos the samples come from.
    """

    key: str
    members: tuple[Path, ...]
    candidates: tuple[Candidate, ...]


@dataclass(frozen=True, slots=True)
class Description:
    """What the model saw in one photo, independent of any taxonomy."""

    text: str
    tags: tuple[str, ...] = ()
    seconds: float = 0.0  # how long the model took: the next estimates

    @property
    def summary(self) -> str:
        """The text the mapping step reads.

        Returns:
            The description, then its tags.
        """
        if not self.tags:
            return self.text
        return f"{self.text} ({', '.join(self.tags)})"


@dataclass(frozen=True, slots=True)
class Subject:
    """The category a `subject` rule gives a file, and whether its samples agree.

    `agreed` only when at least two samples gave the same answer and none another:
    the confidence never comes from what the model says of itself.
    """

    category: str
    agreed: bool
