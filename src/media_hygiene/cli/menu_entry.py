"""The records of the action catalog: an action, its fields, its doc, its space.

`mh menu`, the home page and its palette read the same catalog (`menu_catalog.py`):
five stages of a cycle (import, clean, sort, find, back up), the share area outside
it, then three tools.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, Final

from media_hygiene.cli.menu_words import command_words
from media_hygiene.constants import DOC_PAGES, Locale
from media_hygiene.i18n import active_locale

if TYPE_CHECKING:
    from collections.abc import Mapping

    from media_hygiene.cli.status_step import Slot

_QUOTE: Final = '"'


class Risk(StrEnum):
    """What a step may do to the photos, as the guides badge it."""

    SAFE = "🔒"
    UNDO = "↩️"
    FINAL = "⚠️"


class Space(StrEnum):
    """The five stages of the cycle, share, then the tools, in the menu's order."""

    IMPORT = "import"
    CLEAN = "clean"
    SORT = "sort"
    FIND = "find"
    BACKUP = "backup"
    SHARE = "share"  # outside the cycle: a goal, not a stage
    HISTORY = "history"
    REPORTS = "reports"
    SETTINGS = "settings"
    OTHER = "other"  # the commands no entry names yet: filled at run time


class Kind(StrEnum):
    """Where an action runs."""

    CONSOLE = "console"  # in the terminal
    PAGE = "page"  # in its own page, in the browser
    HOST = "host"  # by `mh` itself, on the host (`services/launcher_host.py`)


class FieldKind(StrEnum):
    """What a field of an action holds."""

    TEXT = "text"
    NUMBER = "number"
    FOLDER = "folder"  # a folder as the Explorer shows it
    ALBUM = "album"  # an album saved, picked from their list, never typed
    CHOICE = "choice"  # one of its `choices`, buttons on the page (0785)


@dataclass(frozen=True, slots=True)
class Doc:
    """A chapter of the documentation: its page, and its anchor in each language."""

    page: str  # e.g. `commands/audit/`, the same in both languages
    en: str = ""  # `#…`, empty for the top of the page
    fr: str = ""

    def url(self, locale: Locale | None = None) -> str:
        """The chapter on the documentation site.

        Args:
            locale: Its language; None: the language in use.

        Returns:
            Its full address.
        """
        french = (locale or active_locale()) is Locale.FR
        prefix = f"{Locale.FR.value}/" if french else ""
        return f"{DOC_PAGES}/{prefix}{self.page}{self.fr if french else self.en}"


@dataclass(frozen=True, slots=True)
class Field:
    """A word an action takes from the user: an album's name, a folder."""

    name: str  # its `{name}` in the command
    label: str  # translated
    example: str
    pattern: str = r"[^\"\x00-\x1f]+"  # the whole value: no quote, no control character
    kind: FieldKind = FieldKind.TEXT
    choices: tuple[tuple[str, str], ...] = ()  # CHOICE: (value, translated label)
    option: str = ""  # an option added when its value is not `example`, e.g. `--since`


@dataclass(frozen=True, slots=True)
class Step:  # pylint: disable=too-many-instance-attributes  # one per catalog column
    """An action of the catalog: what the user gets, its command, what it risks."""

    name: str  # unique, e.g. `review-near`
    space: Space  # its home
    title: str  # what the user gets, translated
    text: str  # how, translated
    command: str  # without `mh`; a `{field}` word for each field
    risk: Risk
    kind: Kind = Kind.CONSOLE
    icon: str = ""  # a name the page maps to its drawing
    keywords: str = ""  # the palette's everyday words, translated
    doc: Doc | None = None
    slot: Slot | None = None  # the step `next_step` may propose
    fields: tuple[Field, ...] = ()
    optional: bool = False
    ai: bool = False  # may ask the local model of `[classify.ai]` 🤖
    windows: bool = False  # Windows PowerShell only: not in the bash `mh`
    planned: bool = False  # shown, not runnable yet
    confirm: tuple[str, str] | None = None  # its own confirmation: title, text (0311)
    web: bool = True  # False: `mh menu` only, the home page already shows it (0504)
    inline: bool = False  # the home server runs it and shows its output (0505)

    @property
    def verb(self) -> str:
        """The command's first word.

        Returns:
            It, e.g. `review` for `review --near`.
        """
        return self.command.split(maxsplit=1)[0]

    def words(self, values: Mapping[str, str]) -> tuple[str, ...]:
        """The command's words, each `{field}` replaced by its value, kept whole.

        Args:
            values: The value of each field, by name.

        Returns:
            The words, `Noël 2025` one of them; an option field's after them.
        """
        return command_words(self, values)

    @property
    def asks(self) -> tuple[Field, ...]:
        """The fields only the user can type: those with choices have a default.

        Returns:
            Them; empty when `mh menu` can run the step as it is.
        """
        return tuple(field for field in self.fields if not field.option)

    @property
    def typed(self) -> str:
        """The command to type, its fields filled with their examples.

        Returns:
            It, a value with a space between double quotes; empty without fields.
        """
        if not self.asks:
            return ""
        values = {field.name: field.example for field in self.fields}
        return " ".join(
            f"{_QUOTE}{word}{_QUOTE}" if " " in word or "\\" in word else word
            for word in self.words(values)
        )


@dataclass(frozen=True, slots=True)
class Group:
    """Actions shown together in a space: a numbered guide or "go further"."""

    title: str  # translated
    steps: tuple[str, ...]  # their names, in order
    numbered: bool = False  # a guide, numbered on the page
    extra: str = ""  # a panel the page adds: `folders`, `update`, `ai`, `albums`…
    doc: Doc | None = None  # the chapter beside its title (the albums, 0730)


@dataclass(frozen=True, slots=True)
class Area:  # pylint: disable=too-many-instance-attributes  # one per catalog column
    """A space: a stage of the cycle or a tool, its pitch and its groups."""

    space: Space
    title: str  # short, the sidebar's
    long: str  # the page's title
    pitch: str
    icon: str
    groups: tuple[Group, ...]
    guide: Doc | None = None
    guide_title: str = ""
    stage: int = 0  # its place in the cycle, from 1; 0: a tool
    planned: bool = False
