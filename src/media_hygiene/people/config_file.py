"""Write the names of `[people]` into `config.toml`, keeping the user's comments.

`tomlkit` edits the document in place: the other keys of `[people]` and their comments
stay; a person already written keeps its table (and its comments), a new one follows
the others. The file is replaced atomically, and checked to be valid TOML and valid
settings first: a crash leaves the old file or the new one, never half.
"""

from __future__ import annotations

import tomllib
from typing import TYPE_CHECKING, Final

import tomlkit
from tomlkit.items import AoT, Table, Whitespace

from media_hygiene.config.people_settings import PeopleSettings, Person

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
    return PeopleSettings.model_validate(loaded.get(SECTION, {}))


def save_people(config_file: Path, wanted: PeopleSettings) -> None:
    """Write the names and the ignored faces, leaving every other setting as it is.

    Args:
        config_file: `config.toml`, created when missing.
        wanted: The section; only `person` and `ignored` are written.

    Raises:
        ValueError: The file is not TOML, or the result would not load.
        OSError: The file cannot be written.
    """
    text = config_file.read_text(_ENCODING) if config_file.is_file() else ""
    document = tomlkit.parse(text)
    section = _section(document)
    if wanted.ignored:
        section[IGNORED] = _array(wanted.ignored)
    elif IGNORED in section:
        del section[IGNORED]
    _write_people(section, wanted.person)
    result = tomlkit.dumps(document)
    PeopleSettings.model_validate(tomllib.loads(result).get(SECTION, {}))
    temporary = config_file.with_name(f".{config_file.name}.tmp")
    temporary.write_text(result, _ENCODING)
    temporary.replace(config_file)


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


def _write_people(section: Table, people: tuple[Person, ...]) -> None:
    """Replace the people of the section, keeping the tables of those still there.

    Args:
        section: `[people]`.
        people: Every person, in order.
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
    for person in people:
        table = tables.get(person.name.strip().casefold(), tomlkit.table())
        _fill(table, person)
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


def _fill(table: Table, person: Person) -> None:
    """Write one person into its table.

    Args:
        table: The table, empty or as written.
        person: The person.
    """
    table["name"] = person.name
    table["faces"] = _array(person.faces)
    if person.rejected:
        table["rejected"] = _array(person.rejected)
    elif "rejected" in table:
        del table["rejected"]


def _array(values: tuple[str, ...]) -> object:
    """A list of face ids, one per line.

    Args:
        values: The ids.

    Returns:
        The TOML array.
    """
    array = tomlkit.array()
    array.extend(values)
    return array.multiline(multiline=True)
