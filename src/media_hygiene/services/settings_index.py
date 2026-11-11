"""The settings index (0670): each row's value read from the disk, then the rest.

The values come from `config.toml` as the file holds it, the default when a key is
missing. *In config.toml only*: every key of the settings model no row names (a table
whose items are tables, `[[classify.rules]]`, counts as one key).
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from pydantic import BaseModel

from media_hygiene.config.settings import Settings
from media_hygiene.i18n import _
from media_hygiene.places.toml_edit import loaded

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.services.settings_rows import SettingRow

_SHOWN_ITEMS: Final = 5  # a list longer than this is counted, not written out
_DEFAULTS: Final = Settings()


@dataclass(frozen=True, slots=True)
class ShownValue:
    """One key and its value, as text."""

    key: str
    value: str
    default: bool  # the file does not hold it


@dataclass(frozen=True, slots=True)
class Listed:
    """A row of the page and its values."""

    row: SettingRow
    values: tuple[ShownValue, ...]


def leaf_keys(model: type[BaseModel] = Settings, prefix: str = "") -> tuple[str, ...]:
    """Every key of the settings, dotted, in the model's order.

    Args:
        model: The table.
        prefix: Its dotted name, empty for the file.

    Returns:
        The keys.
    """
    found: list[str] = []
    for name, field in model.model_fields.items():
        kind = field.annotation
        if isinstance(kind, type) and issubclass(kind, BaseModel):
            found.extend(leaf_keys(kind, f"{prefix}{name}."))
        else:
            found.append(f"{prefix}{name}")
    return tuple(found)


def config_only(rows: tuple[SettingRow, ...]) -> tuple[str, ...]:
    """The keys no page changes.

    Args:
        rows: The settings the pages change.

    Returns:
        Them, in the model's order.
    """
    named = {key for row in rows for key in row.keys}
    return tuple(key for key in leaf_keys() if key not in named)


def _text(value: object) -> str:
    """A value as one line of text."""
    if isinstance(value, bool):
        return _("yes") if value else _("no")
    if isinstance(value, dict):
        value = tuple(value)
    if isinstance(value, (list, tuple)):
        if not value:
            return _("none")
        if len(value) > _SHOWN_ITEMS or not all(
            isinstance(one, (str, int, float)) for one in value
        ):
            return _("{n} items").format(n=len(value))
        return ", ".join(str(one) for one in value)
    if isinstance(value, BaseModel):
        return _text(value.model_dump())
    return str(getattr(value, "value", value)) or _("none")


def _default(key: str) -> object:
    """The value the settings load without the key."""
    node: object = _DEFAULTS
    for part in key.split("."):
        node = getattr(node, part, None)
    return node


def shown_values(config_file: Path, row: SettingRow) -> tuple[ShownValue, ...]:
    """A row's keys, as the file holds them.

    Args:
        config_file: `config.toml`; missing or unreadable: the defaults.
        row: The setting.

    Returns:
        Each key with its value.
    """
    try:
        held: object = loaded(config_file)
    except OSError, tomllib.TOMLDecodeError, ValueError:
        held = {}
    shown: list[ShownValue] = []
    for key in row.keys:
        node = held
        for part in key.split("."):
            node = node.get(part) if isinstance(node, dict) else None
        missing = node is None
        value = _default(key) if missing else node
        shown.append(ShownValue(key, _text(value), default=missing))
    return tuple(shown)
