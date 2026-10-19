"""The places a save renames or deletes (old name to new name, or None)."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

    from media_hygiene.config.classify_places import PersonalPlace
    from media_hygiene.places.config_file import PlaceEdit


def renamed(
    old: Sequence[PersonalPlace], edits: Sequence[PlaceEdit]
) -> dict[str, str | None]:
    """The places a save renames (old name → new) or deletes (→ None).

    Args:
        old: The places as read back before the save.
        edits: Every place kept, with its key (its rank in `old`), and the new ones.

    Returns:
        The names that change.
    """
    kept = {edit.key: edit.place.name for edit in edits if edit.key is not None}
    return {
        place.name: kept.get(key)
        for key, place in enumerate(old)
        if kept.get(key) != place.name
    }
