"""Names confirmed before a photo moved still find its face (TODO 0146).

`config.toml` keeps each face as `<photo path>#<number>`. A photo that `sort` or
`undo` moved has its faces at a new path: an id whose path is no longer among the
faces of the index follows the moves the index recorded (`index.moves`), A → B → C,
to the path its faces have now. `sort` and `undo` rewrite the files themselves right
after moving (`follow_people`, 0382): the names no longer depend on the index.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from media_hygiene.people.config_file import read_people, save_people

if TYPE_CHECKING:
    from collections.abc import Container, Mapping
    from pathlib import Path

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


def follow_people(config_file: Path, moves: Mapping[str, str]) -> int:
    """Rewrite the face ids of the photos a run moved, in the people's files.

    Args:
        config_file: `config.toml`; missing: nothing to do.
        moves: New container path by old one, for this run only.

    Returns:
        The ids renamed, counted on the files read back.

    Raises:
        ValueError: The file is not TOML, or its `[people]` is invalid.
        OSError: A file cannot be written.
    """
    if not config_file.is_file():
        return 0
    before = read_people(config_file)
    after = follow_ids(before, moves, frozenset())
    if after == before:
        return 0
    save_people(config_file, after)
    back = read_people(config_file)
    targets = set(moves.values())
    keys = (
        *back.ignored,
        *(key for person in back.person for key in (*person.faces, *person.rejected)),
    )
    return sum(1 for key in keys if key.rpartition(_SEPARATOR)[0] in targets)
