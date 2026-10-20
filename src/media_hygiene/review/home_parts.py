"""The parts of the home page's state around the actions: tiles, findings, folders.

Built by `cli/home_*.py`, sent by `GET /api/state`; the page only draws them.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class Frozen(BaseModel):
    """A part of the state: frozen, no field left unknown."""

    model_config = ConfigDict(frozen=True, extra="forbid")


class Pill(StrEnum):
    """The mark of a tile: what it asks of the user."""

    NONE = ""
    OK = "ok"
    TODO = "todo"
    CHECK = "check"
    PLANNED = "planned"


class HomeLink(Frozen):
    """A chapter of the documentation, in the page's language and in English."""

    url: str
    url_en: str


class HomeTile(Frozen):
    """A "where you are" tile: it leads to its space."""

    label: str
    value: str
    sub: str
    space: str
    pill: Pill = Pill.NONE


class HomeFinding(Frozen):
    """What the last audit found, and the action it calls for."""

    icon: str
    title: str
    sub: str
    action: str | None = None  # the action's name
    ok: bool = False


class HomeFindings(Frozen):
    """The findings of the last audit or clean, its time and size."""

    title: str
    note: str
    rows: tuple[HomeFinding, ...]


class HomeFolder(Frozen):
    """A folder `mh` knows: photos, a backup, the quarantine."""

    path: str
    role: str
    note: str
    ok: bool = True


class HomeQuarantine(Frozen):
    """The quarantine of one run."""

    run_id: str
    files: str
    size: str
    since: str


class HomeUndo(Frozen):
    """The newest run still undoable."""

    run_id: str
    text: str
    command: str  # `mh undo <run>`
    number: int | None = None  # its step in `mh menu`


class HomeUpdate(Frozen):
    """A newer version published (0267): the banner, its notes and its step."""

    version: str  # e.g. "0.5.0"
    notes: str  # the release notes
    number: int | None  # the step `mh update` in `mh menu`
    command: str  # `mh update`


class HomeReport(Frozen):
    """A report the page links to, served under `/reports/`."""

    label: str  # e.g. "Last audit", translated
    when: str
    url: str
