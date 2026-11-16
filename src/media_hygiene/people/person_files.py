"""Write the face lists of `[people]` into their files under `/config/people/` (0300).

One file per person, named after them (`people/Frédérique.toml`), and one for the
ignored faces (`people/ignored.toml`). A file whose text would not change is not
written again: a change rewrites the person it touches only. Each file is replaced
atomically; the files of the people gone are removed once `config.toml` no longer
links them. The name is made safe for Windows, and two names that differ by case only
never share a file.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.config.face_refs import face_line, face_mapper
from media_hygiene.config.people_files import (
    FACES,
    FOLDER,
    REJECTED,
    linked_path,
)
from media_hygiene.config.photo_ref import write_refs
from media_hygiene.i18n import _
from media_hygiene.people.face_ids import known_ids
from media_hygiene.people.unchanged_file import person_header, unchanged
from media_hygiene.review.disk_tags import side_by_side
from media_hygiene.review.slow_log import Laps

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from media_hygiene.config.people_settings import PeopleSettings, Person

SUFFIX: Final = ".toml"
IGNORED_NAME: Final = "ignored"
IGNORED_PATH: Final = f"{FOLDER}/{IGNORED_NAME}{SUFFIX}"
_FORBIDDEN: Final = re.compile(r'[<>:"/\\|?*\x00-\x1f]')  # refused by Windows
_RESERVED: Final = frozenset(
    {"CON", "PRN", "AUX", "NUL"}
    | {f"{device}{n}" for device in ("COM", "LPT") for n in range(1, 10)}
)


@dataclass(frozen=True, slots=True)
class Links:
    """The files `config.toml` links: one per person, in order, and the ignored."""

    people: tuple[str, ...]
    ignored: str = ""  # empty: no face ignored


def safe_name(name: str) -> str:
    """A file name for a person, as close to their name as Windows allows.

    Args:
        name: The name.

    Returns:
        It, the forbidden characters replaced; never a device name nor `ignored`.
    """
    cleaned = _FORBIDDEN.sub("_", name.strip()).rstrip(". ")
    stem = cleaned.split(".", 1)[0]
    if not cleaned or stem.upper() in _RESERVED or stem.casefold() == IGNORED_NAME:
        cleaned = f"_{cleaned}"
    return cleaned


def file_names(people: tuple[Person, ...]) -> tuple[str, ...]:
    """The file of each person: the one written, else one after their name.

    Args:
        people: Every person, in order.

    Returns:
        Their files, relative to the folder of `config.toml`, each once whatever
        its case (Windows does not tell `Manon` from `manon`).
    """
    taken = {person.file.casefold() for person in people if person.file}
    taken.add(IGNORED_PATH)
    names: list[str] = []
    for person in people:
        if person.file:
            names.append(person.file)
            continue
        base = f"{FOLDER}/{safe_name(person.name)}"
        candidate, rank = f"{base}{SUFFIX}", 2
        while candidate.casefold() in taken:
            candidate, rank = f"{base} ({rank}){SUFFIX}", rank + 1
        taken.add(candidate.casefold())
        names.append(candidate)
    return tuple(names)


def write_files(
    config_dir: Path, wanted: PeopleSettings, moves: Mapping[str, str] | None = None
) -> Links:
    """Write the lists of every person, and the ignored faces, into their files.

    Args:
        config_dir: The folder of `config.toml`.
        wanted: `[people]` to write.
        moves: New container path by old one, when a run just moved photos: their
            ids follow them.

    Returns:
        The files to link from `config.toml`.

    Raises:
        ValueError: A file written by hand leads out of the folder.
        OSError: A file cannot be written.
    """
    files, mapper = file_names(wanted.person), face_mapper()
    laps = Laps("people files")
    changed = [
        (person, file)
        for person, file in zip(wanted.person, files, strict=True)
        if moves or not unchanged(config_dir, file, person)
    ]
    every = (
        *wanted.ignored,
        *(k for p, _f in changed for k in (*p.faces, *p.rejected)),
    )
    laps.lap(f"{len(changed)} of {len(files)} changed")
    ids = known_ids(config_dir, every, moves)
    laps.lap(f"ids of {len(every)} faces")

    def lines(keys: tuple[str, ...]) -> list[str]:
        """The faces as written.

        Args:
            keys: `<container path>#<n>`.

        Returns:
            Their lines.
        """
        return [face_line(key, ids, mapper) for key in keys]

    side_by_side(  # a cross may rule a face out of 13 people: 13 files at once
        _write_one,
        [
            (
                linked_path(config_dir, f),
                person_header(p.name),
                lines(p.faces),
                lines(p.rejected),
            )
            for p, f in changed
        ],
    )
    laps.lap("written")
    if not wanted.ignored:
        laps.said()
        return Links(files)
    header = _("The faces ignored on the people page; config.toml links this file.")
    _write(
        linked_path(config_dir, IGNORED_PATH), header, {FACES: lines(wanted.ignored)}
    )
    laps.lap(f"{len(wanted.ignored)} ignored")
    laps.said()
    return Links(files, IGNORED_PATH)


def _write_one(job: tuple[Path, str, list[str], list[str]]) -> None:
    """Write one person's file: its path, header, faces and faces ruled out."""
    path, header, faces, rejected = job
    _write(path, header, {FACES: faces, REJECTED: rejected})


def _write(path: Path, header: str, lists: Mapping[str, list[str]]) -> None:
    """Replace a file with its lists, atomically; left as it is when unchanged.

    The text is built here, not by `tomlkit`: these files hold no comment of the
    user's to keep, and building 40 000 ids with `tomlkit` takes seconds (measured,
    TODO 0300). Each face is `{path, id, face}` once its id is known (0570).

    Args:
        path: The file.
        header: The comment on its first line.
        lists: Its arrays' lines, by key; an empty one is left out, but `faces`.
    """
    write_refs(path, header, {k: v for k, v in lists.items() if v or k == FACES})
