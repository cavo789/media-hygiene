"""What the home page shows, as `GET /api/state` sends it: built by `cli/home_state.py`.

The page only displays it: where you are (the lines of `status`), the next step, every
step of the three guides as `mh menu` numbers them, the reports and a few previews.
"""

from __future__ import annotations

from typing import Final

from pydantic import BaseModel, ConfigDict

# A step's button ends the home server with `STEP_EXIT_BASE + n`, `n` its number in
# `mh menu`: `mh` then runs that step with the mounts it needs.
STEP_EXIT_BASE: Final = 100
REPORTS_PREFIX: Final = "/reports/"


class _Frozen(BaseModel):
    """A part of the state: frozen, no field left unknown."""

    model_config = ConfigDict(frozen=True, extra="forbid")


class HomeStep(_Frozen):
    """One step of a guide, as `mh menu` lists it."""

    number: int | None  # None: nothing to do yet, or to type yourself
    command: str  # the full command, `mh` included
    text: str
    badges: tuple[str, ...]  # 🔒 ↩️ ⚠️, 🤖, "optional"
    done: bool = False
    proposed: bool = False
    typed: bool = False  # a step the menu cannot fill: the command is to type


class HomeSection(_Frozen):
    """One guide, its steps in order."""

    title: str
    steps: tuple[HomeStep, ...]


class HomeNext(_Frozen):
    """The step proposed first, as `status` ends with it."""

    number: int
    command: str
    why: str  # translated, e.g. "start with an audit: it changes nothing."


class HomeReport(_Frozen):
    """A report the page links to, served under `/reports/`."""

    label: str  # e.g. "Last audit", translated
    when: str
    url: str


class HomeState(_Frozen):
    """Everything the home page shows."""

    lines: tuple[str, ...]  # what `status` says, one line per part
    given: tuple[str, ...] = ()  # the folders `mh --photos` added, one line each
    sections: tuple[HomeSection, ...]
    proposed: HomeNext | None = None
    undo: str | None = None  # the undo line of the newest run, when one is undoable
    reports: tuple[HomeReport, ...] = ()
    index: str | None = None  # `/reports/index.html`, when it exists
    previews: tuple[str, ...] = ()  # thumbnails of the last audit's report

    def command_of(self, number: int) -> str | None:
        """The command of a selectable step.

        Args:
            number: Its number in `mh menu`.

        Returns:
            Its command, or None when no step has that number.
        """
        return next(
            (
                step.command
                for section in self.sections
                for step in section.steps
                if step.number == number
            ),
            None,
        )
