"""Move the layouts of the user's `config.toml` to the sort convention (0401).

`config.toml` is written whole on the first run, so a new default layout never reaches
it: the user's file keeps `{year}/{category}`, `To check`, `To sort`. `config
--convention` lists each layout that differs from this version's (old → new), and only
after the user says yes writes them, comments kept (tomlkit), in one atomic step, then
reads the file back. Nothing is ever rewritten silently.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

import tomlkit
from tomlkit.items import Table

from media_hygiene.config.classify_settings import ClassifySettings

if TYPE_CHECKING:
    from pathlib import Path

SECTION: Final = "classify"
LAYOUTS: Final = (
    "layout",
    "unsure_layout",
    "manual_layout",
    "undated_layout",
    "received_layout",
)
_ENCODING: Final = "utf-8"


@dataclass(frozen=True, slots=True)
class LayoutChange:
    """One layout of the file, and the convention's."""

    key: str
    old: str
    new: str


def convention() -> dict[str, str]:
    """The layouts of the convention: this version's defaults.

    Returns:
        Each layout by its key.
    """
    defaults = ClassifySettings()
    return {key: str(getattr(defaults, key)) for key in LAYOUTS}


def layout_changes(config_file: Path) -> tuple[LayoutChange, ...]:
    """The layouts the file sets otherwise than the convention.

    Args:
        config_file: `config.toml`; missing: no change (the defaults apply).

    Returns:
        One change per layout that differs, in the order of the section.

    Raises:
        ValueError: The file is not TOML.
    """
    if not config_file.is_file():
        return ()
    section = tomllib.loads(config_file.read_text(_ENCODING)).get(SECTION, {})
    wanted = convention()
    return tuple(
        LayoutChange(key, str(section[key]), wanted[key])
        for key in LAYOUTS
        if key in section and section[key] != wanted[key]
    )


def write_convention(config_file: Path) -> tuple[LayoutChange, ...]:
    """Write the convention's layouts into the file, then read them back.

    Args:
        config_file: `config.toml`.

    Returns:
        The changes, as the file read back holds them.

    Raises:
        ValueError: The file is not TOML, or does not hold the layouts read back.
        TypeError: `[classify]` is not a table.
        OSError: It cannot be written.
    """
    changes = layout_changes(config_file)
    if not changes:
        return ()
    document = tomlkit.parse(config_file.read_text(_ENCODING))
    table = document[SECTION]
    if not isinstance(table, Table):
        message = f"[{SECTION}] of {config_file} is not a table"
        raise TypeError(message)
    for change in changes:
        table[change.key] = change.new
    temporary = config_file.with_name(f".{config_file.name}.tmp")
    temporary.write_text(tomlkit.dumps(document), _ENCODING)
    temporary.replace(config_file)
    back = tomllib.loads(config_file.read_text(_ENCODING)).get(SECTION, {})
    if any(back.get(change.key) != change.new for change in changes):
        message = f"{config_file} does not hold the layouts just written"
        raise ValueError(message)
    return changes
