"""The advice a command closes with: one next step, then the tips that matter most.

Users stop reading after two tips: the tips of a command are collected while it runs,
then ranked by kind (safety, then next step, setup and discovery) and cut to a budget at
its end. Safety lines are never cut; setup tips are merged into one line.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Final


class TipKind(IntEnum):
    """What a tip is about, from the most to the least important."""

    SAFETY = 0  # how to undo what was just done: never cut
    NEXT = 1  # a command worth running after this one
    SETUP = 2  # an option to add once (cache, /reports, TZ): merged into one line
    DISCOVERY = 3  # a feature worth knowing (second opinion, --prefer, near…)
    DETAIL = 4  # more about what is on screen (where every report is listed)


TIP_BUDGET: Final = 2  # tips shown after the next step, safety lines apart


@dataclass(frozen=True, slots=True)
class Advice:
    """One tip, and the command it suggests when there is one to paste."""

    kind: TipKind
    text: str
    command: str | None = None


@dataclass(slots=True)
class AdviceBoard:
    """The advice collected while a command runs, printed once at its end."""

    tips: list[Advice] = field(default_factory=list[Advice])
    settings: list[str] = field(default_factory=list[str])
    step: Advice | None = None

    def add(self, advice: Advice) -> None:
        """Collect a tip, once: the same text twice is said once.

        Args:
            advice: The tip.
        """
        if advice not in self.tips:
            self.tips.append(advice)

    def add_setting(self, fragment: str) -> None:
        """Collect an option worth setting once, merged later with the others.

        Args:
            fragment: E.g. `-v media-hygiene-cache:/cache (faster audits)`.
        """
        if fragment not in self.settings:
            self.settings.append(fragment)

    def drain(self) -> tuple[Advice | None, tuple[Advice, ...], tuple[str, ...]]:
        """Hand over everything collected and start again empty.

        Returns:
            The next step, the tips and the setting fragments.
        """
        drained = self.step, tuple(self.tips), tuple(self.settings)
        self.step = None
        self.tips.clear()
        self.settings.clear()
        return drained


@dataclass(frozen=True, slots=True)
class Selection:
    """What to print: the lines never cut, the best tips, how many were left out."""

    safety: tuple[Advice, ...]
    shown: tuple[Advice, ...]
    hidden: int


def select(
    tips: tuple[Advice, ...], setup: Advice | None, *, verbose: bool
) -> Selection:
    """Rank the tips by kind (stable), keep the safety lines and the best few.

    Args:
        tips: The tips collected, in the order they were given.
        setup: The setting fragments merged into one tip, if any.
        verbose: Keep every tip (`--verbosity verbose`).

    Returns:
        The selection.
    """
    safety = tuple(tip for tip in tips if tip.kind is TipKind.SAFETY)
    others = [tip for tip in tips if tip.kind is not TipKind.SAFETY]
    if setup is not None:
        others.append(setup)
    ranked = tuple(sorted(others, key=lambda tip: tip.kind))
    if verbose:
        return Selection(safety, ranked, 0)
    return Selection(safety, ranked[:TIP_BUDGET], max(len(ranked) - TIP_BUDGET, 0))
