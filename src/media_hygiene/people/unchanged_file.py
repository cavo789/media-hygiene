"""Whether a person's file already says what a save would write (2026-11-15).

A save of `[people]` wrote every person's file again, unchanged ones included: each
of their faces formatted, then compared with the file (0.35 s for 12 000 faces here,
about four times that on the maintainer's PC). A person whose file holds the same
faces, the same faces ruled out and the same header is now left as it is, its file
untouched: one naming formats one person. A face whose content id became known
since (an `audit`) is written with it by that audit (`face_refs_audit`), or by the
next save of that person.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.config.people_files import linked_path
from media_hygiene.config.people_parsed import FACES, REJECTED, parsed_file
from media_hygiene.config.stamped_text import stamped_text
from media_hygiene.i18n import _

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.config.people_settings import Person


def person_header(name: str) -> str:
    """The comment on the first line of a person's file.

    Args:
        name: The person.

    Returns:
        The comment, without its `#`.
    """
    header = _(
        "The faces of {name}, saved by the people page; config.toml links this file."
    )
    return header.format(name=name)


def unchanged(config_dir: Path, file: str, person: Person) -> bool:
    """Whether the person's file holds their lists and header already.

    Args:
        config_dir: The folder of `config.toml`.
        file: The file, as `config.toml` links it.
        person: The person as the save would write them.

    Returns:
        True when writing the file would change nothing a reader sees.
    """
    try:
        path = linked_path(config_dir, file)
        held = parsed_file(path).lists
        first = stamped_text(path).split("\n", 1)[0]
    except OSError, ValueError:
        return False
    if first != f"# {' '.join(person_header(person.name).split())}":
        return False
    return held.get(FACES) == person.faces and held.get(REJECTED) == person.rejected
