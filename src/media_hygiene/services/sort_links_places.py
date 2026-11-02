"""After a run that moved photos: the paths of the photos given a place or a word.

Places (0551) and the words typed by hand (0555) both list `{path, id}`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.i18n import ngettext
from media_hygiene.places.photo_moves import follow_place_photos
from media_hygiene.tags.hand_edit import follow_hand_tags

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path


def followed_places(config_file: Path, hosts: Mapping[str, str]) -> str:
    """Rewrite the paths of the photos given a place or a word that the run moved.

    Args:
        config_file: `config.toml`.
        hosts: New host path by old one.

    Returns:
        What changed, or nothing.
    """
    count = follow_place_photos(config_file, hosts)
    worded = follow_hand_tags(config_file, hosts)
    said = (
        ngettext(
            "{count} photo given a place", "{count} photos given a place", count
        ).format(count=count)
        if count
        else "",
        ngettext(
            "{count} photo given a word by hand",
            "{count} photos given a word by hand",
            worded,
        ).format(count=worded)
        if worded
        else "",
    )
    return ", ".join(filter(None, said))
