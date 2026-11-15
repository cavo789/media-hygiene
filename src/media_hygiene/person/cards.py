"""The photos of `/person`'s grid as `pick_grid.js.j2` reads them.

Each photo's address carries its version on the disk now: one `stat` per photo,
the grid's side by side (`disk_tags`; 1.4 s for 201 photos before, three `stat`s
each one after the other on the Windows mount, 2026-11-15).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.person.routes import FACE_PREFIX, JPEG, PREVIEW_PREFIX, THUMB_PREFIX
from media_hygiene.review.disk_tags import disk_tags
from media_hygiene.review.versioned import tagged

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from media_hygiene.paths.host_paths import HostPathMapper

type Shown = tuple[int, Path]  # a face's number, its photo


def grid_cards(
    mapper: HostPathMapper, shown: Sequence[Shown], chosen: frozenset[str]
) -> list[dict[str, object]]:
    """The grid's photos, in order.

    Args:
        mapper: Host ↔ container.
        shown: Each photo by the number of its face.
        chosen: The host paths set aside.

    Returns:
        One card per photo.
    """
    tags = disk_tags(path for _key, path in shown)
    return [_card(mapper, item, (chosen, tags[item[1]])) for item in shown]


def _card(
    mapper: HostPathMapper, item: Shown, seen: tuple[frozenset[str], str]
) -> dict[str, object]:
    """One photo of the grid.

    Args:
        mapper: Host ↔ container.
        item: The face's number and its photo.
        seen: The host paths set aside, and the photo's tag on the disk now.

    Returns:
        What `pick_grid.js.j2` reads of a file.
    """
    (key, path), (chosen, tag) = item, seen
    host = mapper.to_host(path)
    return {
        "key": key,
        "name": path.name,
        "thumb": tagged(f"{THUMB_PREFIX}{key}{JPEG}", tag),
        "preview": tagged(f"{PREVIEW_PREFIX}{key}{JPEG}", tag),
        "original": tagged(f"{PREVIEW_PREFIX}{key}{JPEG}", tag),
        "where": host,
        "path": host,  # 👤: `/person` again, from this photo
        "face": f"{FACE_PREFIX}{key}{JPEG}",  # the face that matched (0714)
        "chosen": host in chosen,
    }
