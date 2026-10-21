"""What the home page shows, as `GET /api/state` sends it: built by `cli/home_state.py`.

The page only draws it: the spaces of the cycle and the tools, every action of the
catalog with its state (available, done, proposed, its reason, its command), the next
step, the tiles, the findings, the folders and the version. The next step and the
availability are never computed again in the page.
"""

from __future__ import annotations

from typing import Final

from media_hygiene.review.home_parts import (
    Frozen,
    HomeFindings,
    HomeFolder,
    HomeLink,
    HomeQuarantine,
    HomeReport,
    HomeTile,
    HomeUndo,
    HomeUpdate,
)

# A step's button ends the home server with `STEP_EXIT_BASE + n`, `n` its number in
# `mh menu`: `mh` then runs that step with the mounts it needs. The whole range stays
# below 125 (Docker's own codes, then 128 + n for a signal: Ctrl+C is 130), so an
# interrupted run is never read as a step (0287, tests in `test_launcher_home.py`).
STEP_EXIT_BASE: Final = 20
# A step with fields: `mh` runs the words of the one-shot file instead (`home_fields`).
# Also the highest code `mh` reads as a step: no step is numbered 99 (`test_menu.py`).
FIELDS_STEP: Final = 99
# A code from here on is a signal's (128 + n): `mh` ends its loop, never runs a step.
SIGNAL_EXIT_BASE: Final = 128
REPORTS_PREFIX: Final = "/reports/"


class HomeField(Frozen):
    """A word an action takes from a form."""

    name: str
    label: str
    example: str
    kind: str  # text, number, folder


class HomeAction(Frozen):  # one field per thing the page draws
    """One action of the catalog, as this state fills it."""

    name: str
    space: str
    title: str
    text: str
    command: str  # the full command, `mh` included; an example for fields
    risk: str  # safe, undo, final
    kind: str  # console, page, host
    icon: str
    keywords: str
    number: int | None = None  # its step in `mh menu`; None: not runnable now
    available: bool = True
    reason: str = ""  # why not, translated
    done: bool = False
    proposed: bool = False
    optional: bool = False
    ai: bool = False
    windows: bool = False
    planned: bool = False
    fields: tuple[HomeField, ...] = ()
    doc: HomeLink | None = None


class HomeGroup(Frozen):
    """Actions shown together: a numbered guide, "go further", a panel."""

    title: str
    actions: tuple[str, ...]
    numbered: bool = False
    extra: str = ""  # folders, update, ai, about


class HomeSpace(Frozen):  # one field per thing the page draws
    """A stage of the cycle or a tool, with its place in the sidebar."""

    id: str
    title: str
    long: str
    pitch: str
    icon: str
    groups: tuple[HomeGroup, ...]
    stage: int = 0
    planned: bool = False
    guide: HomeLink | None = None
    guide_title: str = ""
    line: str = ""  # what the cycle says of it
    badge: str = ""  # the sidebar's count
    mark: str = ""  # here, done, todo, planned
    done: int = 0  # steps of its guides done
    total: int = 0


class HomeNext(Frozen):
    """The step proposed first, as `status` ends with it."""

    name: str
    number: int
    command: str
    why: str  # translated, e.g. "start with an audit: it changes nothing."
    where: str  # e.g. "Clean the duplicates · step 3 of 8"


class HomeState(Frozen):  # one field per part of the page
    """Everything the home page shows."""

    version: str
    lines: tuple[str, ...]  # what `status` says, one line per part
    spaces: tuple[HomeSpace, ...]
    actions: tuple[HomeAction, ...]
    docs: HomeLink  # the documentation's home
    docs_index: str | None = None  # the served docs' index, for the palette (0270)
    given: tuple[str, ...] = ()  # the folders `mh --photos` added, one line each
    proposed: HomeNext | None = None
    tiles: tuple[HomeTile, ...] = ()
    findings: HomeFindings | None = None
    folders: tuple[HomeFolder, ...] = ()
    quarantine: tuple[HomeQuarantine, ...] = ()
    undo: HomeUndo | None = None
    reports: tuple[HomeReport, ...] = ()
    index: str | None = None  # `/reports/index.html`, when it exists
    previews: tuple[str, ...] = ()  # thumbnails of the last audit's report
    update: HomeUpdate | None = None  # a newer version, from Docker Hub (0267)
    windows: bool = True  # the Windows actions are offered
    ai: bool = False  # a local model is set

    def command_of(self, number: int) -> str | None:
        """The command of a runnable step.

        Args:
            number: Its number in `mh menu`.

        Returns:
            Its command, or None when no step has that number.
        """
        return next(
            (action.command for action in self.actions if action.number == number),
            None,
        )

    def action(self, name: str) -> HomeAction | None:
        """The action of a name.

        Args:
            name: Its name, e.g. `album`.

        Returns:
            It, or None.
        """
        return next((action for action in self.actions if action.name == name), None)
