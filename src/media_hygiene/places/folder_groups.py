r"""The folders of one town, one line of the map page's list (0383).

A collection sorted by year holds `2019\\Turin`, `2023\\Turin`: one line, one pin, one
save for all of them. The group is a view computed at each read from the town names
(`town_key` + country: `Turin` and `turin` meet, the two `Paris` do not);
`[[places.folders]]` keeps one entry per folder. A folder without a town (placed by
hand) or not found (⚠) stays alone: its name proves nothing, its warning stays seen.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from media_hygiene.geo.folding import town_key
from media_hygiene.places.toml_edit import DECIMALS

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from media_hygiene.places.folder_rows import FolderRow


@dataclass(frozen=True, slots=True)
class FolderGroup:
    """Two folders or more of one town."""

    ranks: tuple[int, ...]  # in the rows' order: the most photos first
    positions: int  # how many different positions its saved folders have
    latitude: float  # the pin: the saved folder with the most photos, else the town
    longitude: float


def _key(row: FolderRow) -> str:
    """The town a row joins, or "" for a row that stays alone.

    Args:
        row: A folder.

    Returns:
        The folded town name and its country.
    """
    if not row.town or not row.found:
        return ""
    return f"{town_key(row.town)}|{row.country}"


def folder_groups(rows: Sequence[FolderRow]) -> tuple[FolderGroup, ...]:
    """Gather the folders of each town.

    Args:
        rows: The list, the most photos first.

    Returns:
        The groups of two folders or more, in the order of their first row.
    """
    ranks: dict[str, list[int]] = {}
    for rank, row in enumerate(rows):
        key = _key(row)
        if key:
            ranks.setdefault(key, []).append(rank)
    groups: list[FolderGroup] = []
    for members in ranks.values():
        if len(members) < 2:  # noqa: PLR2004  # one folder is its own line
            continue
        saved = [rows[rank] for rank in members if rows[rank].saved]
        spots = {
            (round(row.latitude, DECIMALS), round(row.longitude, DECIMALS))
            for row in saved
        }
        pin = saved[0] if saved else rows[members[0]]
        groups.append(
            FolderGroup(tuple(members), len(spots), pin.latitude, pin.longitude)
        )
    return tuple(groups)


def groups_json(groups: Sequence[FolderGroup]) -> list[dict[str, object]]:
    """Write the groups for the page; a group's rank is the one `GET /api/group/` names.

    Args:
        groups: The groups.

    Returns:
        Each group's folders (their ranks in `folders`), positions and pin.
    """
    return [
        {
            "rank": rank,
            "folders": list(group.ranks),
            "positions": group.positions,
            "latitude": group.latitude,
            "longitude": group.longitude,
        }
        for rank, group in enumerate(groups)
    ]


def group_photos(rows: Sequence[FolderRow], group: FolderGroup) -> list[Path]:
    """The photos without a position of every folder of a group.

    Args:
        rows: The list.
        group: One of its groups.

    Returns:
        Their files, folder after folder.
    """
    return [path for rank in group.ranks for path in rows[rank].photos]
