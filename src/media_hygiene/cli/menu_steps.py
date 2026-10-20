"""The lines of the `mh` menu: every action of the catalog, numbered across its spaces.

Every action is listed once, where it first comes in the cycle, so the user reads the
commands they will later type; one is proposed, the step `status` would print. A step
is marked done only when the tool folders prove it; one that takes words only the
user knows, or that is planned, is not selectable.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from media_hygiene.cli.command_help import command_help
from media_hygiene.cli.menu_catalog import catalog, with_others
from media_hygiene.cli.menu_needs import missing
from media_hygiene.cli.status_step import Slot, next_step
from media_hygiene.constants import RunKind
from media_hygiene.services.launcher_host import HOST_COMMANDS, windows_menu

if TYPE_CHECKING:
    from media_hygiene.cli.menu_catalog import Catalog
    from media_hygiene.cli.menu_entry import Area, Group, Step
    from media_hygiene.services.status import Status


@dataclass(frozen=True, slots=True)
class MenuStep:  # pylint: disable=too-many-instance-attributes  # one per thing drawn
    """One line of the menu: the action, as this state fills it."""

    area: Area
    group: Group
    step: Step
    command: str  # without `mh`; empty when the user must type it, or nothing to do
    number: int | None = None  # None: not selectable
    done: bool = False
    proposed: bool = False
    reason: str = ""  # why it cannot run yet (`menu_needs`), translated


@dataclass(frozen=True, slots=True)
class Menu:
    """Every line, and the one proposed (None when nothing is left)."""

    steps: tuple[MenuStep, ...]
    proposed: MenuStep | None


def full_catalog() -> Catalog:
    """The catalog, with the commands no action names yet under "Other commands".

    Returns:
        It.
    """
    names = (
        *((name, text) for name, _panel, text in command_help()),
        *((name, "") for name in HOST_COMMANDS),
    )
    return with_others(catalog(), names)


def build_menu(
    status: Status, purge_hint_days: int, *, windows: bool | None = None
) -> Menu:
    """List every action once, the proposed one marked, numbered from 1.

    Args:
        status: What the tool folders say.
        purge_hint_days: The age from which a quarantine is worth purging first.
        windows: False leaves out the Windows actions; None: unless the bash `mh`
            runs the menu.

    Returns:
        The menu, in the order of the spaces and of their groups.
    """
    proposal = next_step(status, purge_hint_days)
    windows = windows_menu() if windows is None else windows
    lines: list[MenuStep] = []
    number = 0
    for listed in _lines(full_catalog(), windows=windows):
        line = _filled(listed, status)
        if proposal is not None and line.step.slot is proposal.slot:
            line = replace(line, command=proposal.command, proposed=True)
        if line.command:
            number += 1
            line = replace(line, number=number)
        lines.append(line)
    proposed = next((line for line in lines if line.proposed), None)
    return Menu(tuple(lines), proposed)


def _lines(known: Catalog, *, windows: bool) -> list[MenuStep]:
    """Every action once, where it first comes, its command as the catalog writes it.

    Args:
        known: The catalog.
        windows: False leaves out the Windows actions.

    Returns:
        The lines, in the order of the spaces and of their groups.
    """
    seen: set[str] = set()
    lines = []
    for area in known.areas:
        for group in area.groups:
            for name in group.steps:
                step = known.step(name)
                if name in seen or (step.windows and not windows):
                    continue
                seen.add(name)
                lines.append(MenuStep(area, group, step, step.command))
    return lines


def _filled(line: MenuStep, status: Status) -> MenuStep:
    """Take a step's argument from the state, and say whether the state proves it done.

    Args:
        line: The step, its command as the catalog writes it.
        status: What the tool folders say.

    Returns:
        The step for this state; without a command when the state cannot fill it.
    """
    step = line.step
    reason = missing(step, status) or ""
    if step.fields or step.planned or reason:
        return replace(line, command="", reason=reason)
    match step.slot:
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
