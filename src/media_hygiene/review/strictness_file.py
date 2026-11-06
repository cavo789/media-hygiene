"""Thresholds read back from `config.toml`: what a page shows is what the disk holds."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from media_hygiene.i18n import _
from media_hygiene.places.toml_edit import loaded

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path


# Names said on the page, per direction: the count says the rest.
NAMES_SHOWN: Final = 12


def moved_names(
    first: Mapping[str, str], second: Mapping[str, str]
) -> dict[str, object]:
    """Who is in the first listing and not in the second.

    Args:
        first: File name by path.
        second: File name by path.

    Returns:
        Their `count`, and the first `names`.
    """
    found = sorted(path for path in first if path not in second)
    return {
        "count": len(found),
        "names": [first[path] for path in found[:NAMES_SHOWN]],
    }


def saved_values(
    config_file: Path, section: tuple[str, ...], expected: Mapping[str, object]
) -> dict[str, object]:
    """Read values from the file, and check it holds what was written.

    Args:
        config_file: `config.toml`.
        section: The tables down to the keys, as `("review", "unwanted")`.
        expected: The values just written, by key.

    Returns:
        The values, as read.

    Raises:
        ValueError: The file does not hold them.
    """
    found: object = loaded(config_file)
    for name in section:
        found = found.get(name) if isinstance(found, dict) else None
    table = found if isinstance(found, dict) else {}
    read = {key: table.get(key) for key in expected}
    if read != dict(expected):
        raise ValueError(_("config.toml does not hold the values written"))
    return read
