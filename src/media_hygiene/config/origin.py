"""Where a setting comes from: default, config.toml, environment, command line."""

from __future__ import annotations

from collections.abc import Mapping
from enum import StrEnum
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from collections.abc import Sequence

    from media_hygiene.config.layers import Layer

_SECTION_AND_KEY: Final = 2  # an item of an array of tables sits below `section.key`


class Origin(StrEnum):
    """Where an effective setting comes from (shown by the `config` command)."""

    DEFAULT = "default"
    FILE = "file"
    ENV = "env"
    CLI = "cli"


def origin_in(layers: Mapping[Origin, Layer], section: str, key: str) -> Origin:
    """Tell which layer provides a setting, the highest precedence first.

    Args:
        layers: The raw layers of the run, by origin.
        section: TOML table, e.g. `general`.
        key: Key in the table, e.g. `locale`.

    Returns:
        One of the `Origin` values.
    """
    for origin in (Origin.CLI, Origin.ENV, Origin.FILE):
        if key in layers.get(origin, {}).get(section, {}):
            return origin
    return Origin.DEFAULT


def item_name(layers: Mapping[Origin, Layer], path: Sequence[str | int]) -> str | None:
    """Read the `name` the user gave the item of an array of tables, as written.

    The raw layer is read, not the settings: the item may be the one refused.

    Args:
        layers: The raw layers of the run, by origin.
        path: A pydantic location inside the item, e.g.
            `("classify", "rules", 1, "match")`.

    Returns:
        E.g. `Birthday`; `None` outside an item, or for a missing, empty or
        non-text name.
    """
    last = max((at for at, part in enumerate(path) if isinstance(part, int)), default=0)
    if last < _SECTION_AND_KEY:
        return None
    node: object = layers.get(origin_in(layers, str(path[0]), str(path[1])), {})
    for part in path[: last + 1]:
        node = _child(node, part)
    name = node.get("name") if isinstance(node, Mapping) else None
    return name if isinstance(name, str) and name.strip() else None


def _child(node: object, part: str | int) -> object:
    """Step one level down a raw TOML value, or nowhere.

    Args:
        node: A table, an array or a plain value.
        part: A key of a table or an index of an array.

    Returns:
        The value below, or `None` when there is none.
    """
    if isinstance(part, str):
        return node.get(part) if isinstance(node, Mapping) else None
    if isinstance(node, list) and 0 <= part < len(node):
        return node[part]
    return None
