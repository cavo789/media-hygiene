"""At the end of an `audit`: the photos given a place or a word, renamed outside, found.

A folder renamed in Explorer leaves `path` stale in `places/<name>.toml`: the index,
just refreshed, holds every file with its size; among those of each listed id's size,
the digest decides (the index's, else read once from the disk: only files of a listed
size are read, never the collection). The `path` is rewritten, read back, and said in
one line (0551). A file that cannot be rewritten is said too; the audit stays done.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import TYPE_CHECKING, Final

from media_hygiene.classify.hand_placed import Candidate, digest_of
from media_hygiene.config.photo_ref import content_id, size_of
from media_hygiene.errors import MediaHygieneError
from media_hygiene.i18n import _, ngettext
from media_hygiene.index.repository import FactsRepository
from media_hygiene.places.photo_moves import ids_wanted, relocate_place_photos
from media_hygiene.tags.hand_edit import hand_ids, relocate_hand_tags

if TYPE_CHECKING:
    from collections.abc import Collection

    from media_hygiene.services.runtime import Runtime

_OF_SIZE: Final = "SELECT path, full_digest FROM files WHERE size = ?"


def relocate_after_audit(runtime: Runtime) -> None:
    """Rewrite the path of each photo given a place or a word, moved outside the tool.

    Args:
        runtime: Settings, mount points and output.
    """
    config_file = runtime.locations.config_file
    try:
        wanted = ids_wanted(config_file) | hand_ids(config_file)
        if not wanted:
            return
        with FactsRepository.open(runtime.index_file) as repository:
            found = located(repository.connection, wanted)
        hosts = {
            key: [runtime.mapper.to_host(Path(path)) for path in paths]
            for key, paths in found.items()
        }
        count = relocate_place_photos(config_file, hosts)
        worded = relocate_hand_tags(config_file, hosts)  # the words typed (0555)
    except (OSError, ValueError, sqlite3.Error, MediaHygieneError) as exc:
        runtime.output.info(
            _(
                "The photos given a place or a word were not followed ({reason})."
            ).format(reason=exc)
        )
        return
    if count:
        runtime.output.info(
            ngettext(
                "{count} photo given a place was renamed outside: its path is "
                "updated, read back from the disk.",
                "{count} photos given a place were renamed outside: their path is "
                "updated, read back from the disk.",
                count,
            ).format(count=count)
        )
    if worded:
        runtime.output.info(
            ngettext(
                "{count} photo given a word by hand was renamed outside: its path "
                "is updated, read back from the disk.",
                "{count} photos given a word by hand were renamed outside: their "
                "path is updated, read back from the disk.",
                worded,
            ).format(count=worded)
        )


def located(
    connection: sqlite3.Connection, wanted: Collection[str]
) -> dict[str, list[str]]:
    """The container paths of the index holding each id.

    Args:
        connection: The index.
        wanted: The ids.

    Returns:
        The paths of each id found.
    """
    found: dict[str, list[str]] = {}
    for size in sorted({size_of(key) for key in wanted}):
        for path, digest in connection.execute(_OF_SIZE, (size,)).fetchall():
            sha = digest_of(Candidate(Path(path), size, digest))
            if sha is not None and (key := content_id(sha, size)) in wanted:
                found.setdefault(key, []).append(str(path))
    return found
