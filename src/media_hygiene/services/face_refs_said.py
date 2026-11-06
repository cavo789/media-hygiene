"""The audit's lines about the named faces it followed (0570)."""

from __future__ import annotations

import tomllib
from typing import TYPE_CHECKING, Final

from media_hygiene.config.face_refs import split_key
from media_hygiene.config.people_files import ENCODING, FACES, REJECTED
from media_hygiene.i18n import ngettext

if TYPE_CHECKING:
    import sqlite3
    from collections.abc import Sequence
    from pathlib import Path

    from media_hygiene.services.face_refs_audit import FaceTally
    from media_hygiene.services.runtime import Runtime

# Named photos to read whole before the first audit after 0570 says so: about 50 photos
# of 5 MB on a USB disk read in a few seconds (estimated); more is a wait worth a line.
READ_ONCE_SAID: Final = 50
_DIGEST: Final = "SELECT full_digest FROM files WHERE path = ?"


def unread_named(files: Sequence[Path], connection: sqlite3.Connection) -> int:
    """Count the photos of old-form faces (before 0570) the index has no digest of.

    Args:
        files: The people's files.
        connection: The index.

    Returns:
        How many distinct photos the audit will read whole once.
    """
    paths: set[str] = set()
    for file in files:
        loaded = tomllib.loads(file.read_text(ENCODING))
        for key in (FACES, REJECTED):
            value = loaded.get(key, [])
            for entry in value if isinstance(value, list) else []:
                parts = None if isinstance(entry, dict) else split_key(str(entry))
                if parts is not None:
                    paths.add(parts[0])
    rows = (connection.execute(_DIGEST, (path,)).fetchone() for path in paths)
    return sum(1 for row in rows if not (row and row[0]))


def say_reading(runtime: Runtime, count: int) -> None:
    """Say, before it starts, that many named photos are read once (0570).

    Args:
        runtime: Settings, mount points and output.
        count: From `unread_named`; nothing said up to `READ_ONCE_SAID`.
    """
    if count <= READ_ONCE_SAID:
        return
    runtime.output.info(
        ngettext(
            "{count} named photo read once, to follow its faces from now on…",
            "{count} named photos read once, to follow their faces from now on…",
            count,
        ).format(count=count)
    )


def say_faces(runtime: Runtime, tally: FaceTally) -> None:
    """One line per kind of change, none when nothing changed.

    Args:
        runtime: Settings, mount points and output.
        tally: What the audit changed, read back.
    """
    output = runtime.output
    if tally.moved:
        output.info(
            ngettext(
                "{count} named face is on a photo renamed outside: its path is "
                "updated, read back from the disk.",
                "{count} named faces are on photos renamed outside: their path is "
                "updated, read back from the disk.",
                tally.moved,
            ).format(count=tally.moved)
        )
    if tally.dropped:
        output.info(
            ngettext(
                "{count} named face was on a photo edited since: another photo, "
                "its name is forgotten.",
                "{count} named faces were on photos edited since: other photos, "
                "their names are forgotten.",
                tally.dropped,
            ).format(count=tally.dropped)
        )
