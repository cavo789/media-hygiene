"""`[people]` read again only when one of its files changed.

Reading `[people]` parses `config.toml` and the file of every person, then turns each
face reference into a container path: 0.66 to 0.91 s for 90 people and 18,336 face
references (measured 2026-11-12 on a copy of the maintainer's config, in the local
image), paid by every photo opened large (its *who is on it* line, 0714) on the
server's loop, so the picture waited behind it. The settings are now kept with the
signature of each file they came from (inode, size, modification and change times):
an edit in place, an atomic save (a new inode), a copy keeping the modification time
(a new change time) or a `touch` changes it, and the next read parses the files again.
A file added, renamed or removed is seen through `config.toml`, which links it.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from media_hygiene.config.people_files import (
    ENCODING,
    FILE,
    IGNORED_FILE,
    PERSON,
    SECTION,
    linked_path,
)
from media_hygiene.people.config_file import read_people

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.config.people_settings import PeopleSettings

type Signature = tuple[tuple[str, tuple[int, int, int, int] | None], ...]


def file_signature(path: Path) -> tuple[int, int, int, int] | None:
    """What changes when a file is written, replaced, copied over or touched.

    Args:
        path: The file.

    Returns:
        Its inode, size, modification and change times; None when it is missing.
    """
    try:
        found = path.stat()
    except OSError:
        return None
    return (found.st_ino, found.st_size, found.st_mtime_ns, found.st_ctime_ns)


def linked_files(config_file: Path) -> tuple[Path, ...]:
    """The files `[people]` reads its lists from, as `config.toml` links them.

    Args:
        config_file: `config.toml`.

    Returns:
        Each person's file and the ignored faces' file; none when the section
        cannot be read (the read that follows says why).
    """
    try:
        section = tomllib.loads(config_file.read_text(ENCODING)).get(SECTION, {})
    except OSError, UnicodeDecodeError, tomllib.TOMLDecodeError:
        return ()
    if not isinstance(section, dict):
        return ()
    people = section.get(PERSON, [])
    written = [entry.get(FILE) for entry in people if isinstance(entry, dict)]
    written.append(section.get(IGNORED_FILE))
    found: list[Path] = []
    for relative in written:
        if isinstance(relative, str) and relative:
            try:
                found.append(linked_path(config_file.parent, relative))
            except ValueError, OSError:
                continue  # refused: the read that follows says why
    return tuple(found)


def signature_of(config_file: Path, linked: tuple[Path, ...]) -> Signature:
    """The signature of `config.toml` and of the files it links.

    Args:
        config_file: `config.toml`.
        linked: The files it links (`linked_files`).

    Returns:
        One entry per file, `config.toml` first.
    """
    return tuple((str(path), file_signature(path)) for path in (config_file, *linked))


@dataclass(frozen=True, slots=True)
class _Kept:
    """One read: the files linked, their signature, the settings."""

    linked: tuple[Path, ...]
    signature: Signature
    settings: PeopleSettings


@dataclass(slots=True)
class PeopleMemo:
    """The last `[people]` read of each `config.toml`, kept while no file changes."""

    _kept: dict[Path, _Kept] = field(default_factory=dict)

    def read(self, config_file: Path) -> PeopleSettings:
        """`[people]` as the files hold it now: parsed again only after a change.

        Args:
            config_file: `config.toml`.

        Returns:
            The section, as `read_people` returns it.

        Raises:
            ValueError: The file is not TOML, or a linked file is missing or invalid
                (`read_people`); nothing is kept then.
        """
        kept = self._kept.get(config_file)
        if (
            kept is not None
            and signature_of(config_file, kept.linked) == kept.signature
        ):
            return kept.settings
        linked = linked_files(config_file)
        signature = signature_of(config_file, linked)
        settings = read_people(
            config_file
        )  # after the signature: a later change is seen
        self._kept[config_file] = _Kept(linked, signature, settings)
        return settings
