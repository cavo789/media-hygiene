"""What the console says of a describing run, for `classify` and `tags` alike."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.console.formatting import human_number
from media_hygiene.i18n import _, ngettext

if TYPE_CHECKING:
    from media_hygiene.classify.ai.describe import DescribeOutcome
    from media_hygiene.console.output import Output


def show_describe_counts(output: Output, outcome: DescribeOutcome) -> None:
    """Say how many photos the model described, and how many it could not.

    Args:
        output: Where to print.
        outcome: How describing went.
    """
    videos = outcome.videos
    photos = outcome.described - videos
    if videos:
        output.success(
            _("{photos} and {videos} described; kept in the cache.").format(
                photos=ngettext("{count} photo", "{count} photos", photos).format(
                    count=human_number(photos)
                ),
                videos=ngettext("{count} video", "{count} videos", videos).format(
                    count=human_number(videos)
                ),
            )
        )
    elif photos:
        output.success(
            ngettext(
                "{count} photo described; kept in the cache.",
                "{count} photos described; kept in the cache.",
                photos,
            ).format(count=human_number(photos))
        )
    if outcome.unreadable:
        output.warning(
            ngettext(
                "{count} photo could not be described: unreadable, or no answer.",
                "{count} photos could not be described: unreadable, or no answer.",
                outcome.unreadable,
            ).format(count=human_number(outcome.unreadable))
        )
