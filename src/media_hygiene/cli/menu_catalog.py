"""Every action of the tool, in the order of the cycle: `mh menu`, home page, palette.

Five stages (import, clean, sort, find, back up), then three tools (history, reports,
settings); one module per stage or group of tools. The badges are the guides': 🔒
photos untouched, ↩️ can be undone, ⚠️ for good. A command no entry names yet still
shows, under "Other commands" (`with_others`), and `tests/unit/test_menu_catalog.py`
fails until it has its entry.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from media_hygiene.cli.menu_catalog_clean import clean_area, clean_steps
from media_hygiene.cli.menu_catalog_clean_more import clean_more_steps
from media_hygiene.cli.menu_catalog_find import find_areas, find_steps
from media_hygiene.cli.menu_catalog_import import import_area, import_steps
from media_hygiene.cli.menu_catalog_settings import settings_steps
from media_hygiene.cli.menu_catalog_sort import sort_area, sort_steps
from media_hygiene.cli.menu_catalog_tools import tools_areas, tools_steps
from media_hygiene.cli.menu_entry import Area, Group, Risk, Space, Step
from media_hygiene.i18n import _

if TYPE_CHECKING:
    from collections.abc import Iterable


@dataclass(frozen=True, slots=True)
class Catalog:
    """The actions, and the spaces that show them."""

    steps: tuple[Step, ...]
    areas: tuple[Area, ...]

    def step(self, name: str) -> Step:
        """The action of a name.

        Args:
            name: Its name, e.g. `review-near`.

        Returns:
            It.

        Raises:
            KeyError: No action has that name.
        """
        found = next((step for step in self.steps if step.name == name), None)
        if found is None:
            raise KeyError(name)
        return found


def catalog() -> Catalog:
    """Every action and every space, in the language in use.

    Returns:
        The catalog, the spaces in the cycle's order, then the tools.
    """
    steps = (
        *import_steps(),
        *clean_steps(),
        *clean_more_steps(),
        *sort_steps(),
        *find_steps(),
        *tools_steps(),
        *settings_steps(),
    )
    areas = (import_area(), clean_area(), sort_area(), *find_areas(), *tools_areas())
    return Catalog(steps, areas)


def named(step: Step) -> tuple[str, str]:
    """The command and the review mode an action names.

    Args:
        step: The action.

    Returns:
        Its verb, and its first option (`--near`), or empty.
    """
    words = step.command.split()
    return words[0], words[1] if len(words) > 1 else ""


def with_others(known: Catalog, names: Iterable[tuple[str, str]]) -> Catalog:
    """Add the commands no action names yet, so that the menu never misses one.

    Args:
        known: The catalog.
        names: Each command and its `--help` short text.

    Returns:
        The catalog, with a last space "Other commands" when any is left.
    """
    verbs = {named(step)[0] for step in known.steps}
    left = {name: text for name, text in names if name not in verbs}
    if not left:
        return known
    title = _("Other commands")
    # Their risk is unknown: said as the highest until each one has its entry.
    steps = tuple(
        Step(name, Space.OTHER, text or name, "", name, Risk.FINAL)
        for name, text in left.items()
    )
    area = Area(Space.OTHER, title, title, "", "", (Group(title, tuple(left)),))
    return Catalog((*known.steps, *steps), (*known.areas, area))
