"""The people avoided in every show (0834): `[slideshow] avoid` of `config.toml`.

Ticked on the PC's remote (or its *On this PC* screen), they are written there with
tomlkit (comments kept, atomic) and read back from the disk: what the remote says is
remembered is what the file holds. Every show starts with them set out; the phone
ticks for its show only and never writes. A name no longer in `[[people.person]]`
(renamed, removed) stays in the file, ignored.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.people.folding import folded
from media_hygiene.places.toml_edit import (
    document_of,
    loaded,
    table_of,
    write_document,
)

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence
    from pathlib import Path

TABLE: Final = "slideshow"
KEY: Final = "avoid"


def remembered(config_file: Path | None) -> tuple[str, ...]:
    """The names `[slideshow] avoid` holds on the disk.

    Args:
        config_file: `config.toml`; None, missing or unreadable: none.

    Returns:
        The names, in the file's order.
    """
    if config_file is None:
        return ()
    try:
        table: object = loaded(config_file).get(TABLE, {})
    except OSError, tomllib.TOMLDecodeError, ValueError:
        return ()
    names = table.get(KEY, []) if isinstance(table, dict) else []
    return tuple(name for name in names if isinstance(name, str))


def known_of(names: Iterable[str], people: Sequence[str]) -> list[str]:
    """The people named among `names`, as `[[people.person]]` writes them.

    Args:
        names: The names remembered.
        people: The names of `[[people.person]]`.

    Returns:
        Those known, in the order of `people`.
    """
    wanted = {folded(name) for name in names}
    return [name for name in people if folded(name) in wanted]


@dataclass(frozen=True, slots=True)
class Remembering:
    """Who the remote offered, and who it ticked, to write into the file."""

    offered: tuple[str, ...]
    ticked: tuple[str, ...]


def remember(config_file: Path, asked: Remembering) -> tuple[str, ...]:
    """Write the ticks of the names offered, keep every other name, read back.

    Args:
        config_file: `config.toml`.
        asked: The names offered by the remote and those ticked among them.

    Returns:
        The names the file now holds.
    """
    offered = {folded(name) for name in asked.offered}
    kept = [name for name in remembered(config_file) if folded(name) not in offered]
    document = document_of(config_file)
    table_of(document, TABLE)[KEY] = [*kept, *asked.ticked]
    write_document(config_file, document)
    return remembered(config_file)
