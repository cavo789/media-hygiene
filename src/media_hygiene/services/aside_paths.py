"""The files set aside, wherever a page set them aside: a soft delete (0518).

A file set aside (`chosen` by search, browse or the albums; a shot left out in the
burst review) no longer counts anywhere until *Apply now* moves it: albums, the TV,
the slideshow and every action on a picking leave it out. Read from the decisions
file at each call, so a stale page cannot bypass it.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.errors import MediaHygieneError
from media_hygiene.report.decisions import read_decisions
from media_hygiene.review.place import DEFAULT_DECISIONS
from media_hygiene.search.aside_filter import AsideFilter
from media_hygiene.share.album_pickers import KeyPicker

if TYPE_CHECKING:
    from collections.abc import Callable

    from media_hygiene.review.session import ReviewSession
    from media_hygiene.search.aside_filter import Kept
    from media_hygiene.services.runtime import Runtime
    from media_hygiene.share.album_api import AlbumAsked


def set_aside(runtime: Runtime) -> frozenset[str]:
    """The host paths set aside in the reports folder's decisions file.

    Args:
        runtime: Settings, mount points and output.

    Returns:
        The files chosen on the pages and the burst shots left out; none when the
        file is missing or unreadable.
    """
    target = runtime.locations.reports_dir / DEFAULT_DECISIONS
    if not target.is_file():
        return frozenset()
    try:
        decisions = read_decisions(target)
    except MediaHygieneError:
        return frozenset()
    shots = (path for burst in decisions.bursts for path in burst.discarded)
    return frozenset((*shots, *(entry.path for entry in decisions.chosen)))


def review_picker(
    runtime: Runtime, session: ReviewSession
) -> Callable[[AlbumAsked], Kept]:
    """What the burst review's albums take: its shots, those set aside left out.

    Args:
        runtime: Settings, mount points and output.
        session: The review, whose choices may not be in the reports folder.

    Returns:
        The picker; what is set aside is read again at each request.
    """

    def aside() -> frozenset[str]:
        """Every host path set aside, now.

        Returns:
            Them.
        """
        shots = (
            path for burst in session.decisions().bursts for path in burst.discarded
        )
        return set_aside(runtime) | frozenset(shots)

    return KeyPicker(session.preview_source, AsideFilter(aside, runtime.mapper)).files
