"""The steps of the `mh` menu: the three guides in order, each with its full command.

Every step is listed, so the user reads the commands they will later type; one is
proposed, the step `status` would print. A step is marked done only when the tool
folders prove it, and one that needs what the tool cannot fill is not selectable.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import StrEnum
from typing import TYPE_CHECKING

from media_hygiene.cli.menu_catalog import clean_steps, find_steps, sort_steps
from media_hygiene.cli.status_step import Slot, next_step
from media_hygiene.constants import RunKind

if TYPE_CHECKING:
    from media_hygiene.cli.menu_catalog import Step
    from media_hygiene.services.status import Status


class Section(StrEnum):
    """The three guides, in the order the documentation gives them."""

    CLEAN = "clean"
    SORT = "sort"
    FIND = "find"


@dataclass(frozen=True, slots=True)
class MenuStep:
    """One line of the menu: the step of the guide, as this state fills it."""

    section: Section
    step: Step
    command: str  # without `mh`; empty when the user must type it
    number: int | None = None  # None: not selectable
    done: bool = False
    proposed: bool = False


@dataclass(frozen=True, slots=True)
class Menu:
    """Every step, and the one proposed (None when nothing is left)."""

    steps: tuple[MenuStep, ...]
    proposed: MenuStep | None


def build_menu(status: Status, purge_hint_days: int) -> Menu:
    """List the steps of the three guides, the proposed one marked.

    Args:
        status: What the tool folders say.
        purge_hint_days: The age from which a quarantine is worth purging first.

    Returns:
        The menu, its selectable steps numbered from 1.
    """
    proposal = next_step(status, purge_hint_days)
    sections = (
        (Section.CLEAN, clean_steps()),
        (Section.SORT, sort_steps()),
        (Section.FIND, find_steps()),
    )
    lines: list[MenuStep] = []
    number = 0
    for section, catalog in sections:
        for step in catalog:
            line = _filled(MenuStep(section, step, step.command), status)
            if proposal is not None and step.slot is proposal.slot:
                line = replace(line, command=proposal.command, proposed=True)
            if line.command:
                number += 1
                line = replace(line, number=number)
            lines.append(line)
    proposed = next((line for line in lines if line.proposed), None)
    return Menu(tuple(lines), proposed)


def _filled(line: MenuStep, status: Status) -> MenuStep:
    """Take a step's argument from the state, and say whether the state proves it done.

    Args:
        line: The step, its command as the catalog writes it.
        status: What the tool folders say.

    Returns:
        The step for this state; without a command when the state cannot fill it.
    """
    match line.step.slot:
        case Slot.PURGE:
            runs = status.quarantine.runs
            command = f"purge {runs[0].run_id}" if runs else ""
            return replace(line, command=command)
        case Slot.UNDO:
            undoable = status.undoable
            command = f"undo {undoable[0].run_id}" if undoable else ""
            return replace(line, command=command)
        case _:
            return replace(line, done=_done(line.step.slot, status))


def _done(slot: Slot | None, status: Status) -> bool:
    """Tell whether the tool folders prove a step done; unknown is not done.

    Args:
        slot: The step.
        status: What the tool folders say.

    Returns:
        True only on proof: an audit seen, no copy left, a sort applied, tags, faces.
    """
    summary = status.analysis.summary
    proofs = {
        Slot.AUDIT: status.analysis.seen,
        Slot.CLEAN: summary is not None
        and (summary.kind is RunKind.CLEAN or not summary.duplicate_files),
        Slot.CLASSIFY: status.sort.proposed is not None,
        Slot.SORT: status.sort.sorted,
        Slot.TAGS: bool(status.tagged and status.tagged[0]),
        Slot.PEOPLE: status.faces is not None,
    }
    return slot is not None and proofs.get(slot, False)


def choice_lines(menu: Menu) -> tuple[str, ...]:
    """The lines `mh` reads on stdout: `number<TAB>command`, `0` for Enter.

    Args:
        menu: The menu.

    Returns:
        The proposed step as number 0 first, when there is one, then every
        selectable step.
    """
    enter = () if menu.proposed is None else (f"0\t{menu.proposed.command}",)
    return (
        *enter,
        *(f"{line.number}\t{line.command}" for line in menu.steps if line.number),
    )
