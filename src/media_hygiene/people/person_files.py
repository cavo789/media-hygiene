"""Write the face lists of `[people]` into their files under `/config/people/` (0300).

One file per person, named after them (`people/Frédérique.toml`), and one for the
ignored faces (`people/ignored.toml`). A file whose text would not change is not
written again: a change rewrites the person it touches only. Each file is replaced
atomically; the files of the people gone are removed once `config.toml` no longer
links them. The name is made safe for Windows, and two names that differ by case only
never share a file.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.config.people_files import (
    ENCODING,
    FACES,
    FOLDER,
    REJECTED,
    linked_path,
)
from media_hygiene.i18n import _

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping
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


def write_files(config_dir: Path, wanted: PeopleSettings) -> Links:
    """Write the lists of every person, and the ignored faces, into their files.

    Args:
        config_dir: The folder of `config.toml`.
        wanted: `[people]` to write.

    Returns:
        The files to link from `config.toml`.

    Raises:
        ValueError: A file written by hand leads out of the folder.
        OSError: A file cannot be written.
    """
    files = file_names(wanted.person)
    for person, file in zip(wanted.person, files, strict=True):
        header = _(
            "The faces of {name}, saved by the people page; "
            "config.toml links this file."
        )
        lists = {FACES: person.faces, REJECTED: person.rejected}
        _write(linked_path(config_dir, file), header.format(name=person.name), lists)
    if not wanted.ignored:
        return Links(files)
    header = _("The faces ignored on the people page; config.toml links this file.")
    _write(linked_path(config_dir, IGNORED_PATH), header, {FACES: wanted.ignored})
    return Links(files, IGNORED_PATH)


def _write(path: Path, header: str, lists: Mapping[str, tuple[str, ...]]) -> None:
    """Replace a file with its lists, atomically; left as it is when unchanged.

    The text is built here, not by `tomlkit`: these files hold no comment of the
    user's to keep, and building 40 000 ids with `tomlkit` takes seconds (measured,
    TODO 0300).

    Args:
        path: The file.
        header: The comment on its first line.
        lists: Its arrays, by key; an empty one is left out, but `faces`.
    """
    lines = [f"# {' '.join(header.split())}"]
    for key, values in lists.items():
        if values or key == FACES:
            lines.append(f"{key} = [")
            lines.extend(f"    {_quoted(value)}," for value in values)
            lines.append("]")
    text = "\n".join(lines) + "\n"
    if path.is_file() and path.read_text(ENCODING) == text:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(text, ENCODING)
    temporary.replace(path)


def _quoted(value: str) -> str:
    """A TOML basic string: JSON's escapes are TOML's, DEL escaped as TOML wants.

    Args:
        value: The text.

    Returns:
        It, quoted.
    """
    return json.dumps(value, ensure_ascii=False).replace("\x7f", "\\u007f")


def remove_unlinked(config_dir: Path, before: Iterable[str], links: Links) -> None:
    """Remove the files `config.toml` linked before and no longer does.

    Only files of the people folder are removed: a file linked by hand elsewhere
    stays.

    Args:
        config_dir: The folder of `config.toml`.
        before: The files it linked before the change.
        links: Those it links now.
    """
    kept = {file.casefold() for file in (*links.people, links.ignored) if file}
    folder = linked_path(config_dir, FOLDER)
    for file in before:
        if file.casefold() in kept:
            continue
        try:
            path = linked_path(config_dir, file)
        except ValueError:
            continue  # never ours to remove
        if path.parent == folder and path.suffix == SUFFIX:
            path.unlink(missing_ok=True)
