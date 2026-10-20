"""The spaces of the home page: what the cycle says of each, its badge, its progress.

"You are here" is the stage whose guide holds the next step; a stage is done, or has
something to do, only on the proof of the tool folders, as `mh menu` marks its steps.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from media_hygiene.cli.home_actions import home_groups, link
from media_hygiene.cli.home_stage_lines import extra_copies, stage_badge, stage_line
from media_hygiene.cli.menu_entry import Space
from media_hygiene.cli.status_step import to_import
from media_hygiene.review.home_views import HomeSpace

if TYPE_CHECKING:
    from media_hygiene.cli.menu_entry import Area
    from media_hygiene.cli.menu_steps import Menu
    from media_hygiene.services.status import Status


@dataclass(frozen=True, slots=True)
class CycleFacts:
    """What the spaces are drawn from."""

    status: Status
    menu: Menu
    newer: bool = False  # a newer version is published (0267)


def home_spaces(areas: tuple[Area, ...], facts: CycleFacts) -> tuple[HomeSpace, ...]:
    """Every space, in the sidebar's order.

    Args:
        areas: The spaces of the catalog.
        facts: The state, the menu, the version.

    Returns:
        The spaces for the page.
    """
    shown = {line.step.name for line in facts.menu.steps}
    lines = {line.step.name: line for line in facts.menu.steps}
    proposed = facts.menu.proposed
    here = next(
        (
            area.space
            for area in areas
            for group in area.groups
            if area.stage
            and group.numbered
            and proposed is not None
            and proposed.step.name in group.steps
        ),
        None,
    )
    spaces = []
    for area in areas:
        guided = [
            name
            for group in area.groups
            if group.numbered
            for name in group.steps
            if name in shown
        ]
        spaces.append(
            HomeSpace(
                id=area.space.value,
                title=area.title,
                long=area.long,
                pitch=area.pitch,
                icon=area.icon or "terminal",
                groups=home_groups(area, shown),
                stage=area.stage,
                planned=area.planned,
                guide=link(area.guide),
                guide_title=area.guide_title,
                line=stage_line(area.space, facts.status),
                badge=stage_badge(area.space, facts.status, newer=facts.newer),
                mark="here" if area.space is here else _mark(area, facts.status),
                done=sum(lines[name].done for name in guided),
                total=len(guided),
            )
        )
    return tuple(spaces)


def _mark(area: Area, status: Status) -> str:
    """A stage done, with something to do, or planned.

    Args:
        area: The space.
        status: What the tool folders say.

    Returns:
        `done`, `todo`, `planned` or empty.
    """
    if area.planned:
        return "planned"
    summary = status.analysis.summary
    extra = bool(extra_copies(status))
    done = {
        Space.IMPORT: status.imported is not None and not to_import(status),
        Space.CLEAN: summary is not None and not extra and not status.quarantine.runs,
        Space.SORT: status.sort.sorted,
        Space.FIND: bool(status.tagged and status.tagged[0]),
    }
    todo = {
        Space.IMPORT: to_import(status),
        Space.CLEAN: extra or bool(status.quarantine.runs),
        Space.SORT: status.sort.proposed is not None and not status.sort.sorted,
    }
    if done.get(area.space, False):
        return "done"
    return "todo" if todo.get(area.space, False) else ""
