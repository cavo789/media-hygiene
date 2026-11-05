"""Files of `{path, id}` lines linked from `config.toml`: the shared save and rewrite.

Places (`/config/places/`, 0551) and the words typed by hand (`/config/tags/`, 0555)
keep each entry short in `config.toml` (its name and `file`), its photos in a file of
their own. The save writes every file atomically, then edits `config.toml` with
`tomlkit` (comments kept), then removes the files no longer linked. A rewrite of the
paths (the tool's moves, an `audit`) saves only when a path changed, and counts what
reads back.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

import tomlkit
from tomlkit.items import AoT, Table

from media_hygiene.config.people_files import linked_path
from media_hygiene.config.photo_ref import ref_line, write_refs
from media_hygiene.places.toml_edit import document_of, table_of, write_document

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from pathlib import Path
    from typing import Self

    from media_hygiene.config.photo_ref import PhotoRef

FILE = "file"
PHOTOS = "photos"
SUFFIX = ".toml"


class Linked(Protocol):
    """An entry whose photos live in a linked file."""

    @property
    def photos(self) -> tuple[PhotoRef, ...]:
        """Its photos."""
        ...

    def model_copy(self, *, update: dict[str, object]) -> Self:
        """A copy, some fields changed.

        Args:
            update: The fields changed.
        """
        ...


@dataclass(frozen=True, slots=True)
class LinkPlace:
    """Where the entries live: `[[<section>.<key>]]`, by `label`, files in `folder`."""

    section: str
    key: str
    label: str
    folder: str


@dataclass(frozen=True, slots=True)
class LinkedFile:
    """One entry to save: its name, its file, its photos, its file's first line."""

    name: str
    file: str
    photos: Sequence[PhotoRef]
    header: str


def free_file(written: str, base: str, taken: set[str]) -> str:
    """An entry's file: the one written, else `<base>.toml`, or `<base> (2).toml`.

    Args:
        written: The file written in `config.toml`; empty: none yet.
        base: The folder and the safe name, without the suffix.
        taken: The files already given (case folded), completed here.

    Returns:
        The file, relative to the folder of `config.toml`.
    """
    if written:
        taken.add(written.casefold())
        return written
    candidate, rank = f"{base}{SUFFIX}", 2
    while candidate.casefold() in taken:
        candidate, rank = f"{base} ({rank}){SUFFIX}", rank + 1
    taken.add(candidate.casefold())
    return candidate


def save_linked(
    config_file: Path, place: LinkPlace, entries: Sequence[LinkedFile]
) -> None:
    """Write each entry's file, link them from `config.toml`, drop the unlinked.

    Args:
        config_file: `config.toml`, created when missing.
        place: Where the entries live.
        entries: The entries with photos, in order.
    """
    config_dir = config_file.parent
    for entry in entries:
        lines = {PHOTOS: [ref_line(photo) for photo in entry.photos]}
        write_refs(linked_path(config_dir, entry.file), entry.header, lines)
    document = document_of(config_file)
    before = _write_links(document, place, entries)
    write_document(config_file, document)
    linked = {entry.file.casefold() for entry in entries}
    for file in (file for file in before if file.casefold() not in linked):
        path = linked_path(config_dir, file)
        if (
            path.parent == linked_path(config_dir, place.folder)
            and path.suffix == SUFFIX
        ):
            path.unlink(missing_ok=True)


def _write_links(
    document: tomlkit.TOMLDocument, place: LinkPlace, entries: Sequence[LinkedFile]
) -> set[str]:
    """Replace the entries of `config.toml`, keeping the tables (and comments).

    Args:
        document: `config.toml`.
        place: Where the entries live.
        entries: The entries with photos.

    Returns:
        The files linked before.
    """
    section = document.get(place.section)
    rows = section.get(place.key) if isinstance(section, Table) else None
    tables = list(rows.body) if isinstance(rows, AoT) else []
    before = {str(t[FILE]) for t in tables if FILE in t}
    by_name = {str(t.get(place.label, "")).casefold(): t for t in tables}
    if isinstance(section, Table) and place.key in section:
        del section[place.key]
    if not entries:
        return before
    fresh = tomlkit.aot()
    for entry in entries:
        table = by_name.get(entry.name.casefold(), tomlkit.table())
        table[place.label] = entry.name
        table[FILE] = entry.file
        if PHOTOS in table:
            del table[PHOTOS]  # moved to the file
        fresh.append(table)
    table_of(document, place.section)[place.key] = fresh
    return before


def rewritten[E: Linked](
    before: tuple[E, ...], rewrite: Callable[[list[PhotoRef]], list[PhotoRef]]
) -> tuple[E, ...] | None:
    """The entries, each photo's path rewritten; None when nothing changed.

    Args:
        before: The entries read.
        rewrite: The new references, in order, from the old ones.

    Returns:
        The entries to save, or None.
    """
    after = tuple(
        entry.model_copy(update={"photos": tuple(rewrite(list(entry.photos)))})
        for entry in before
    )
    return None if after == before else after
