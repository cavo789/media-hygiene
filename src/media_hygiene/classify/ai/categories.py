"""The categories a `subject` rule offers the model: a name, and the user's definition.

An entry `"At home = everyday life at home: games, meals"` is the category (and folder)
`At home`; its definition is sent to the mapping model only. The model chose the
categories by their names alone and a name holding "home" drew every indoor scene: a
definition tells it what the user means.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from collections.abc import Sequence

SEPARATOR: Final = " = "


@dataclass(frozen=True, slots=True)
class Offered:
    """One category offered to the model: its name, and what it holds."""

    name: str
    definition: str = ""

    @property
    def line(self) -> str:
        """The category as the prompt lists it.

        Returns:
            `Name: definition`, or the name alone.
        """
        return f"{self.name}: {self.definition}" if self.definition else self.name


def offered(entry: str) -> Offered:
    """Read one entry of `categories`.

    Args:
        entry: `Name` or `Name = definition`.

    Returns:
        The category.
    """
    name, _, definition = entry.partition(SEPARATOR)
    return Offered(name.strip(), definition.strip())


def names(entries: Sequence[str]) -> tuple[str, ...]:
    """The category names of a rule's entries, definitions left out.

    Args:
        entries: The rule's `categories`.

    Returns:
        The names, in order.
    """
    return tuple(offered(entry).name for entry in entries)
