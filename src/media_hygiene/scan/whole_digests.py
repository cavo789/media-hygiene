"""Give every photo and video its SHA-256 at the audit, once (0634).

Tag and a place given by hand keep an id of each file's content, and refuse above 200
files without one, saying "run an audit first": the audit must give it, whatever the
file's size. Pictures get it from their decoding; videos, pictures too large to read
at once and pictures indexed by an older version get it here. Stored as it goes, so a
stopped audit keeps what it read. The files of a backup folder never come here (0274).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from media_hygiene.constants import MediaKind
from media_hygiene.i18n import _
from media_hygiene.scan.exact import full_pass
from media_hygiene.scan.progress import Step

if TYPE_CHECKING:
    from collections.abc import Sequence

    from media_hygiene.scan.exact import ExactDuplicateFinder
    from media_hygiene.scan.models import MediaFile

_KINDS: Final = frozenset({MediaKind.IMAGE, MediaKind.RAW, MediaKind.VIDEO})


async def fill_whole_digests(
    exact: ExactDuplicateFinder, files: Sequence[MediaFile]
) -> None:
    """Read in full the healthy photos and videos the index has no SHA-256 for.

    Args:
        exact: The exact pipeline, whose index keeps the digests.
        files: The library's healthy files.
    """
    step = Step(
        _("Identifying the remaining files (full SHA-256), once"),
        _(
            "Each file read here is kept in the cache: tagging or placing it later "
            "is immediate. You can stop at any time: what is read is kept."
        ),
    )
    await exact.digests([f for f in files if f.kind in _KINDS], full_pass(step))
