"""The tiles of *Where you are* as the user arranged them: `[home] tiles` (0516).

The list gives the order, a `-` before an id hides its tile: `["copies", "-faces"]`.
A tile the list does not name (added by a later version) comes last, shown: an old list
never hides it. An id no tile has is ignored; an empty list is the default arrangement.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from media_hygiene.cli.home_favourites import read_home_list, save_home_list

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from media_hygiene.review.home_parts import HomeTile

KEY: Final = "tiles"
HIDDEN: Final = "-"


def read_tiles(config_file: Path) -> tuple[str, ...]:
    """The arrangement written in the file.

    Args:
        config_file: `config.toml`.

    Returns:
        Its words.
    """
    return read_home_list(config_file, KEY)


def save_tiles(config_file: Path, words: Sequence[str]) -> tuple[str, ...]:
    """Write the arrangement, then read it back from the disk.

    Args:
        config_file: `config.toml`.
        words: The ids in their order, `-` before those hidden; none: the default.

    Returns:
        What the file now holds.
    """
    return save_home_list(config_file, KEY, words)


def arranged(
    tiles: Sequence[HomeTile], words: Sequence[str]
) -> tuple[tuple[HomeTile, ...], tuple[HomeTile, ...]]:
    """Apply the arrangement to the tiles of today.

    Args:
        tiles: The tiles, in the default order.
        words: What the file holds.

    Returns:
        The tiles shown, in their order; the tiles hidden.
    """
    by_id = {tile.id: tile for tile in tiles}
    shown: list[HomeTile] = []
    hidden: list[HomeTile] = []
    for word in words:
        tile = by_id.pop(word.removeprefix(HIDDEN), None)
        if tile is not None:
            (hidden if word.startswith(HIDDEN) else shown).append(tile)
    return (*shown, *by_id.values()), tuple(hidden)
