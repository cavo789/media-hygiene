"""Give every checked file its partial digest, once: it proves a moved file is the same.

A file moved or renamed outside media-hygiene is recognised by its size, its time and
its partial digest (`index.rematch`, TODO 0147). Pictures checked since 0148 get it
from their decoding; videos, files indexed by an older version and pictures too large
to read at once get it here: 128 KiB read once per file version, then kept.
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from media_hygiene.constants import Sizes
from media_hygiene.i18n import _
from media_hygiene.scan.bounded import bounded_map
from media_hygiene.scan.hashing import partial_digest
from media_hygiene.scan.progress import Step

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from pathlib import Path

    from media_hygiene.index.facts import FileFacts
    from media_hygiene.scan.deps import ScanDeps
    from media_hygiene.scan.models import MediaFile

_LOGGER = logging.getLogger(__name__)


async def fill_partials(
    files: Sequence[MediaFile], known: Mapping[Path, FileFacts], deps: ScanDeps
) -> dict[Path, FileFacts]:
    """Read the partial digest of each checked file that lacks one, and keep it.

    Args:
        files: Every media file found.
        known: The facts of the files checked.
        deps: Index, progress sink.

    Returns:
        The updated facts of the files digested, by path.
    """
    missing = [
        file
        for file in files
        if file.size and (facts := known.get(file.path)) and not facts.partial_digest
    ]
    if not missing:
        return {}

    async def one(file: MediaFile) -> tuple[Path, FileFacts | None]:
        """Digest one file in a thread, and store it at once (TODO 0143).

        Args:
            file: The file.

        Returns:
            Its path, and its updated facts (None when it cannot be read).
        """
        try:
            digest = await asyncio.to_thread(partial_digest, file.path)
        except OSError as exc:
            _LOGGER.warning("Cannot read %s: %s", file.path, exc.strerror)
            return file.path, None
        finally:
            deps.progress.advance()
        facts = known[file.path].with_partial(digest)
        deps.repository.put(file, facts)
        return file.path, facts

    deps.progress.start(_step(), len(missing))
    done = await bounded_map(missing, one, Sizes.IO_CONCURRENCY)
    deps.progress.stop()
    return {path: facts for path, facts in done if facts is not None}


def _step() -> Step:
    """The progress step of the one-time partial digests.

    Returns:
        Its translated title and explanation.
    """
    return Step(
        _("Reading 128 KB of each file already in the cache, once"),
        _(
            "A short fingerprint of each file: a file moved or renamed later in "
            "Explorer is recognised without being read again."
        ),
    )
