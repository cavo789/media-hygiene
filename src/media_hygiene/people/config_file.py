"""Write the names of `[people]` into `config.toml`, keeping the user's comments.

`tomlkit` edits the document in place: the other keys of `[people]` and their comments
stay; a person already written keeps its table (and its comments), a new one follows
the others. Each table holds the name and the file of the person's faces
(`person_files`, TODO 0300): those files are written first, then `config.toml` is
replaced atomically, checked to be valid TOML and valid settings first, then the files
no person links any more are removed. A crash leaves the old file or the new one,
never half, and never a face lost; lists still inline move to the files on the first
save.
"""

from __future__ import annotations

import tomllib
from typing import TYPE_CHECKING, Final

import tomlkit
from tomlkit.items import AoT, Table, Whitespace

from media_hygiene.config.people_files import (
    FACES,
    FILE,
    IGNORED_FILE,
    REJECTED,
    linked_section,
)
from media_hygiene.config.people_settings import PeopleSettings, Person
from media_hygiene.people.person_files import Links, remove_unlinked, write_files

if TYPE_CHECKING:
    from pathlib import Path

    from tomlkit.toml_document import TOMLDocument

SECTION: Final = "people"
PEOPLE: Final = "person"
IGNORED: Final = "ignored"
_ENCODING: Final = "utf-8"


def read_people(config_file: Path) -> PeopleSettings:
    """The `[people]` section as written in the file.

    Args:
        config_file: `config.toml`; missing: no name.

    Returns:
        The section (defaults where the file says nothing).

    Raises:
        ValueError: The file is not TOML or the section is invalid.
    """
    if not config_file.is_file():
        return PeopleSettings()
    loaded = tomllib.loads(config_file.read_text(_ENCODING))
    section = linked_section(loaded.get(SECTION, {}), config_file.parent)
    return PeopleSettings.model_validate(section)


def save_people(config_file: Path, wanted: PeopleSettings) -> None:
    """Write the names and the ignored faces, leaving every other setting as it is.

    Args:
        config_file: `config.toml`, created when missing.
        wanted: The section; only `person` and `ignored` are written.

    Raises:
        ValueError: The file is not TOML, or the result would not load.
        OSError: A file cannot be written.
    """
    text = config_file.read_text(_ENCODING) if config_file.is_file() else ""
    document = tomlkit.parse(text)
    section = _section(document)
    before = _links(tomllib.loads(text).get(SECTION, {}))
    links = write_files(config_file.parent, wanted)
    if IGNORED in section:
        del section[IGNORED]
    if links.ignored:
        section[IGNORED_FILE] = links.ignored
    elif IGNORED_FILE in section:
        del section[IGNORED_FILE]
    _write_people(section, wanted.person, links)
    result = tomlkit.dumps(document)
    written = tomllib.loads(result).get(SECTION, {})
    PeopleSettings.model_validate(linked_section(written, config_file.parent))
    temporary = config_file.with_name(f".{config_file.name}.tmp")
    temporary.write_text(result, _ENCODING)
    temporary.replace(config_file)
    remove_unlinked(config_file.parent, before, links)


def _links(section: dict[str, object]) -> tuple[str, ...]:
    """The files a `[people]` table links, as written.

    Args:
        section: The raw table.

    Returns:
        The file of each person, and of the ignored faces.
    """
    people = section.get(PEOPLE)
    tables = people if isinstance(people, list) else []
    files = [table.get(FILE) for table in tables if isinstance(table, dict)]
    files.append(section.get(IGNORED_FILE))
    return tuple(file for file in files if isinstance(file, str) and file)


def _section(document: TOMLDocument) -> Table:
    """The `[people]` table of the document, added at its end when missing.

    Args:
        document: The parsed file.

    Returns:
        The table.

    Raises:
        TypeError: `people` is not a table.
    """
    section = document.get(SECTION)
    if section is None:
        section = tomlkit.table()
        document[SECTION] = section
    if not isinstance(section, Table):
        message = f"[{SECTION}] is not a table"
        raise TypeError(message)
    return section


def _write_people(section: Table, people: tuple[Person, ...], links: Links) -> None:
    """Replace the people of the section, keeping the tables of those still there.

    Args:
        section: `[people]`.
        people: Every person, in order.
        links: The file of each person.
    """
    written = section.get(PEOPLE)
    tables = (
        {_key(table): table for table in written.body}
        if isinstance(written, AoT)
        else {}
    )
    if PEOPLE in section:
        del section[PEOPLE]
    if not people:
        return
    rows = tomlkit.aot()
    for person, file in zip(people, links.people, strict=True):
        table = tables.get(person.name.strip().casefold(), tomlkit.table())
        _fill(table, person.name, file)
        _trim(table)
        rows.append(table)
    rows.body[-1].add(tomlkit.nl())  # a blank line before what follows
    section[PEOPLE] = rows


def _trim(table: Table) -> None:
    """Drop the blank lines ending a table: the array of tables separates them.

    Args:
        table: A person's table.
    """
    body = table.value.body
    while body and body[-1][0] is None and isinstance(body[-1][1], Whitespace):
        body.pop()


def _key(table: Table) -> str:
    """How a person's table is found again: its name, any case.

    Args:
        table: A `[[people.person]]` table.

    Returns:
        The folded name.
    """
    return str(table.get("name", "")).strip().casefold()


def _fill(table: Table, name: str, file: str) -> None:
    """Write one person into its table: the name, and the file of the faces.

    Args:
        table: The table, empty or as written.
        name: The person.
        file: Their file, relative to the folder of `config.toml`.
    """
    table["name"] = name
    table[FILE] = file
    for key in (FACES, REJECTED):  # moved to the file
        if key in table:
            del table[key]
