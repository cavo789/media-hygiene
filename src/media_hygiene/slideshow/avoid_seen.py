"""Where a person is in a show (0825): the keys of their photos, named or guessed."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Seen:
    """Where a person is in a show: the keys with a face named theirs, those guessed."""

    sure: frozenset[int] = frozenset()
    guessed: frozenset[int] = frozenset()

    @property
    def keys(self) -> frozenset[int]:
        """Every key of theirs, sure or guessed."""
        return self.sure | self.guessed
