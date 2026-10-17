"""What `review --near` and `review --pairs` do alike with their choices, by rank."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from media_hygiene.errors import DecisionsError

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, MutableMapping, Sequence

    from pydantic import BaseModel

    from media_hygiene.review.place import DecisionsPlace


class _Placed(Protocol):
    """What a review is about, as far as its decisions file goes."""

    @property
    def place(self) -> DecisionsPlace:
        """The decisions file."""


class RankedSession[A]:
    """A review whose choices are kept by rank: the groups or pairs of an audit.

    Subclasses set `_source`, `_states` (one per rank) and `_actions` (the choices).
    """

    _source: _Placed
    _states: Sequence[BaseModel]
    _actions: dict[int, A]

    @property
    def place(self) -> DecisionsPlace:
        """The decisions file, for `clean --decisions` and on the host.

        Returns:
            Its names.
        """
        return self._source.place

    @property
    def decided(self) -> tuple[int, int]:
        """How far the review went.

        Returns:
            The ranks decided, and every rank.
        """
        return len(self._actions), len(self._states)

    def counts(self) -> dict[str, int]:
        """How far the review went, as the page reads it after each choice.

        Returns:
            `decided` and `total`.
        """
        decided, total = self.decided
        return {"decided": decided, "total": total}


def record[A](
    actions: MutableMapping[int, A],
    choices: Mapping[int, A | None],
    problem: Callable[[int, A | None], str | None],
) -> None:
    """Check every choice first, then record them all: none or all.

    Args:
        actions: The decisions so far, by rank; updated.
        choices: The new ones (None: back to undecided).
        problem: Why a choice cannot be made, or None.

    Raises:
        DecisionsError: A choice that cannot be made; nothing is recorded.
    """
    for rank, action in choices.items():
        reason = problem(rank, action)
        if reason is not None:
            raise DecisionsError(reason)
    for rank, action in choices.items():
        if action is None:
            actions.pop(rank, None)
        else:
            actions[rank] = action


def with_actions[M: BaseModel](
    states: Sequence[M], actions: Mapping[int, object]
) -> tuple[M, ...]:
    """Give each state its decision, empty when undecided.

    Args:
        states: The states, undecided, by rank.
        actions: The decisions, by rank.

    Returns:
        The states, each with its `action`.
    """
    return tuple(
        state.model_copy(update={"action": actions.get(rank, "")})
        for rank, state in enumerate(states)
    )
