"""`config tidy`: the entries of `config.toml` that point at nothing any more (0550).

Each one is judged against facts, never guessed: a folder against the disk (a folder on
a drive that is not mounted is unknown, not missing), the rules and clocks against the
index (`tidy_rules`). Hand-drawn places and spots set aside are never
proposed: they stay valid for photos to come.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Final

from media_hygiene.config.tidy_rules import (
    CLOCKS,
    RULES,
    StaleEntry,
    duplicate,
    stale_clocks,
    stale_rules,
)
from media_hygiene.i18n import _

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Mapping, Sequence

    from media_hygiene.config.tidy_rules import LibraryFacts

    type Exists = Callable[[str], bool | None]  # host folder → exists; None: unknown

PLACE_FOLDERS: Final = ("places", "folders")
FOLDER_ROLES: Final = ("preferred", "protected", "excluded", "backups")


@dataclass(frozen=True, slots=True)
class TidyFindings:
    """The stale entries, and the folders not judged (their drive is not mounted)."""

    stale: tuple[StaleEntry, ...]
    unknown: tuple[str, ...]


def find_stale(
    document: Mapping[str, Any], facts: LibraryFacts, exists: Exists
) -> TidyFindings:
    """List the entries of a parsed `config.toml` that point at nothing.

    Args:
        document: The file, as `tomllib` reads it.
        facts: What the index knows; empty: patterns and dates are not judged.
        exists: Tells whether a host folder exists, None when its drive is unmounted.

    Returns:
        The stale entries, in file order, and the folders not judged.
    """
    unknown: list[str] = []

    def folder(path: str) -> str | None:
        """Why a folder is stale, None when it is not (or not known).

        Args:
            path: The host folder.

        Returns:
            The reason, or None.
        """
        found = exists(path)
        if found is None:
            unknown.append(path)
        return None if found is not False else _("the folder does not exist")

    stale = [
        *_folder_lists(_table(document, "folders"), folder),
        *_place_folders(_array(document, PLACE_FOLDERS), folder),
        *stale_rules(_array(document, RULES), facts),
        *stale_clocks(_array(document, CLOCKS), facts),
    ]
    return TidyFindings(tuple(stale), tuple(dict.fromkeys(unknown)))


def _table(document: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = document.get(key)
    return value if isinstance(value, dict) else {}


def _array(document: Mapping[str, Any], where: tuple[str, str]) -> list[Any]:
    value = _table(document, where[0]).get(where[1])
    return value if isinstance(value, list) else []


def _folder_lists(
    folders: Mapping[str, Any], folder: Callable[[str], str | None]
) -> Iterator[StaleEntry]:
    for role in FOLDER_ROLES:
        values = folders.get(role)
        seen: dict[str, int] = {}
        for rank, path in enumerate(values if isinstance(values, list) else []):
            key = str(path).casefold()
            reason = duplicate(seen[key]) if key in seen else folder(str(path))
            seen.setdefault(key, rank)
            if reason:
                yield StaleEntry(f"folders.{role}", rank, str(path), reason)


def _place_folders(
    rows: Sequence[Any], folder: Callable[[str], str | None]
) -> Iterator[StaleEntry]:
    seen: dict[str, int] = {}
    for rank, row in enumerate(rows):
        path = str(row.get("folder", "")) if isinstance(row, dict) else ""
        key = path.casefold()
        reason = duplicate(seen[key]) if key in seen else folder(path)
        seen.setdefault(key, rank)
        if reason:
            yield StaleEntry(".".join(PLACE_FOLDERS), rank, path, reason)
