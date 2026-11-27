"""The people whose linked file is gone (0849): loaded empty, warned, unlinked by tidy.

A `[[people.person]]` whose `file = "people/<name>.toml"` is missing (deleted, or
renamed in Explorer) no longer stops the settings from loading: the person loads with
the faces written inline only (`people_files`), one warning line names the file and
the person, and `config tidy` lists the link, ticked, to remove its `file` line. Once
the file is back, the warning goes: it is judged from the disk at each load.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.config.origin import Origin
from media_hygiene.config.people_files import FILE, PERSON, SECTION, linked_path
from media_hygiene.config.tidy_rules import StaleEntry
from media_hygiene.i18n import _

if TYPE_CHECKING:
    from collections.abc import Iterator, Mapping
    from pathlib import Path

    from media_hygiene.config.loader import LoadedSettings

PEOPLE_LINKS: Final = f"{SECTION}.{PERSON}"  # the section `config tidy` unlinks in


@dataclass(frozen=True, slots=True)
class MissingLink:
    """A person whose linked file is not on the disk."""

    rank: int  # their rank in `[[people.person]]`, from 0
    name: str
    file: str


def missing_links(
    document: Mapping[str, object], config_dir: Path
) -> tuple[MissingLink, ...]:
    """The people of a parsed `config.toml` whose linked file is missing.

    Args:
        document: The file's tables (the raw file, or its settings layer).
        config_dir: The folder of `config.toml`.

    Returns:
        One entry per missing file, in file order.
    """
    section = document.get(SECTION)
    rows = section.get(PERSON) if isinstance(section, dict) else None
    return tuple(_missing(rows if isinstance(rows, list) else [], config_dir))


def _missing(rows: list[object], config_dir: Path) -> Iterator[MissingLink]:
    for rank, row in enumerate(rows):
        file = row.get(FILE) if isinstance(row, dict) else None
        if not (isinstance(row, dict) and isinstance(file, str) and file):
            continue
        try:
            gone = not linked_path(config_dir, file).is_file()
        except ValueError:  # outside the folder: the settings refuse it
            continue
        if gone:
            yield MissingLink(rank, str(row.get("name", "")), file)


def missing_warning(links: tuple[MissingLink, ...]) -> str:
    """The one line the console and the pages show, empty when nothing is missing.

    Args:
        links: The missing files.

    Returns:
        The translated line.
    """
    if not links:
        return ""
    named = ", ".join(f"{link.file} ({link.name})" for link in links)
    return _(
        "A linked people file is missing, its faces are not loaded: {files}. "
        "Restore it, or run config tidy --apply to unlink it."
    ).format(files=named)


def settings_warning(loaded: LoadedSettings, config_dir: Path) -> str:
    """The warning of the settings just loaded, judged from `config.toml`'s layer.

    Args:
        loaded: The settings and their layers.
        config_dir: The folder of `config.toml`.

    Returns:
        The line, empty when every linked file is there.
    """
    file_layer = loaded.layers.get(Origin.FILE, {})
    return missing_warning(missing_links(file_layer, config_dir))


def stale_links(links: tuple[MissingLink, ...]) -> Iterator[StaleEntry]:
    """The missing files as `config tidy` entries, ticked by default.

    Args:
        links: The missing files.

    Yields:
        One entry each: `--apply` removes the person's `file` line.
    """
    for link in links:
        label = f"{link.name}: {link.file}"
        yield StaleEntry(PEOPLE_LINKS, link.rank, label, _("the file is gone"))
