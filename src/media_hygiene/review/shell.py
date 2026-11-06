"""The home page's frame around every page (0491): sidebar, top bar, the meerkat.

The sidebar lists the spaces of the catalog (`cli/menu_catalog_*`) as the home page
does: the home page, the five stages, share, the tools; the page's own space is
highlighted (apricot: you are here). Each entry opens that space of the home page:
a plain link when the home server serves the page (`/albums`, 0356); from a page
`mh` opened from the home page, the click ends this page as *Back to the home page*
does and the home page comes back on that space (`shell.js.j2`); from a page typed
in the console, there is no home page to go back to: no entry is drawn (0585), the
top bar says how to reach it. A tile page (`page_frame.html.j2`) gets the sidebar
folded to its icons, so its grid keeps its columns (estimated: a 64 px rail loses
none at 1366 and 1920 px, the full 248 px sidebar one of 5 and of 8).
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib.metadata import version
from typing import Final

from media_hygiene.cli.menu_catalog import catalog
from media_hygiene.cli.menu_entry import Space
from media_hygiene.constants import APP_NAME

# The home page's own entry: not a space of the catalog.
HOME_SPACE: Final = "home"
_HOME_ICON: Final = "home"


@dataclass(frozen=True, slots=True)
class ShellLink:
    """An entry of the sidebar: a space of the home page."""

    space: str  # its id, the home page's `#…`
    title: str
    icon: str  # a symbol of `home_icons.svg.j2`
    current: bool = False  # the page's own space


@dataclass(frozen=True, slots=True)
class Shell:
    """What the frame around a page shows."""

    home: ShellLink
    stages: tuple[ShellLink, ...]
    share: tuple[ShellLink, ...]
    tools: tuple[ShellLink, ...]
    version: str
    compact: bool = False  # a tile page: the sidebar folded to its icons
    drawer: bool = False  # the phone layout at every width: top bar and ☰ (0497)


@dataclass(frozen=True, slots=True)
class ShellAsk:
    """The frame a page asks for."""

    space: Space | None  # its space, highlighted; None: none
    compact: bool = False
    drawer: bool = False  # the sidebar off-canvas, opened by ☰ (the phone's page)


def page_shell(ask: ShellAsk, home_title: str) -> Shell:
    """The frame of a page, in the language in use.

    Args:
        ask: The page's space, and whether it shows tiles.
        home_title: The home page's entry, translated.

    Returns:
        Its sidebar's entries.
    """
    areas = [area for area in catalog().areas if area.space is not Space.OTHER]

    def links(*, stage: bool, share: bool = False) -> tuple[ShellLink, ...]:
        """The entries of a group of the sidebar.

        Args:
            stage: The stages of the cycle; else share or the tools.
            share: Among the others, share alone; else the tools.

        Returns:
            Them, in the catalog's order.
        """
        return tuple(
            ShellLink(area.space.value, area.title, area.icon, area.space is ask.space)
            for area in areas
            if bool(area.stage) is stage
            and (stage or (area.space is Space.SHARE) is share)
        )

    return Shell(
        home=ShellLink(HOME_SPACE, home_title, _HOME_ICON),
        stages=links(stage=True),
        share=links(stage=False, share=True),
        tools=links(stage=False),
        version=version(APP_NAME),
        compact=ask.compact,
        drawer=ask.drawer,
    )
