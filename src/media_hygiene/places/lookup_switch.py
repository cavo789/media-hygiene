"""`[places] reverse_lookup` shown and switched on the map page (0536).

Whether an `import` asks before naming its new photos' spots online (`ask`), always
names them (`always`: the rounded positions are sent to Nominatim) or never does
(`never`). Written with `toml_edit` (comments kept, atomic), then read back: the page
shows what the file holds.
"""

from __future__ import annotations

import tomllib
from typing import TYPE_CHECKING, Final, Literal

from pydantic import BaseModel, ConfigDict

from media_hygiene.places.toml_edit import (
    document_of,
    loaded,
    table_of,
    write_document,
)

if TYPE_CHECKING:
    from pathlib import Path

LOOKUP_PATH: Final = "/api/reverse-lookup"
_TABLE: Final = "places"
_KEY: Final = "reverse_lookup"
type Lookup = Literal["ask", "never", "always"]
_DEFAULT: Final[Lookup] = "ask"
_CHOICES: Final = frozenset({"ask", "never", "always"})


class LookupAsked(BaseModel):
    """`POST /api/reverse-lookup`: the choice."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    lookup: Lookup


def lookup_of(config_file: Path) -> str:
    """The choice the file holds, read from the disk.

    Args:
        config_file: `config.toml`; missing, unreadable or another value: `ask`.

    Returns:
        `ask`, `never` or `always`.
    """
    try:
        value = loaded(config_file).get(_TABLE, {}).get(_KEY, _DEFAULT)
    except OSError, tomllib.TOMLDecodeError, AttributeError:
        return _DEFAULT
    return value if value in _CHOICES else _DEFAULT


def save_lookup(config_file: Path, asked: LookupAsked) -> str:
    """Write the choice, then read it back.

    Args:
        config_file: `config.toml`.
        asked: What the page sent.

    Returns:
        The choice the file now holds.
    """
    document = document_of(config_file)
    table_of(document, _TABLE)[_KEY] = asked.lookup
    write_document(config_file, document)
    return lookup_of(config_file)
