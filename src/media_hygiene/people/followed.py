"""Names confirmed before a photo moved still find its face (TODO 0146).

`config.toml` keeps each face as `<photo path>#<number>`. A photo that `sort` or
`undo` moved has its faces at a new path: an id whose path is no longer among the
faces of the index follows the moves the index recorded (`index.moves`), A → B → C,
to the path its faces have now. The file itself is rewritten the next time the
`people` page saves a name.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from collections.abc import Container, Mapping

    from media_hygiene.config.people_settings import PeopleSettings

_SEPARATOR: Final = "#"


def follow_ids(
    settings: PeopleSettings, moves: Mapping[str, str], present: Container[str]
) -> PeopleSettings:
    """The names with each face id pointing where its photo is now.

    Args:
        settings: `[people]` as written.
        moves: New path by old path, as the index recorded them.
        present: The paths of the photos the index has faces for.

    Returns:
        The same settings, the ids of moved photos updated; unchanged without moves.
    """
    if not moves:
        return settings

    def ids(keys: tuple[str, ...]) -> tuple[str, ...]:
        """Follow each id, once each.

        Args:
            keys: Face ids.

        Returns:
            Them, followed, without duplicates.
        """
        return tuple(dict.fromkeys(_followed(key, moves, present) for key in keys))

    people = tuple(
        person.model_copy(
            update={"faces": ids(person.faces), "rejected": ids(person.rejected)}
        )
        for person in settings.person
    )
    return settings.model_copy(
        update={"person": people, "ignored": ids(settings.ignored)}
    )


def _followed(key: str, moves: Mapping[str, str], present: Container[str]) -> str:
    """One face id, its path followed through the moves while it has no face.

    Args:
        key: `<path>#<number>`.
        moves: New path by old path.
        present: The paths that have faces.

    Returns:
        The id where the photo is now, or the id unchanged.
    """
    path, separator, number = key.rpartition(_SEPARATOR)
    if not separator:
        return key
    seen = {path}
    while path not in present and (path := moves.get(path, path)) not in seen:
        seen.add(path)
    return f"{path}{separator}{number}"
