"""Where a setting comes from: default, config.toml, environment, command line."""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping

    from media_hygiene.config.layers import Layer


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
