"""What `shrink` says: the videos worth lightening, the gain expected, then the gain."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from rich.markup import escape

from media_hygiene.console.formatting import human_number, human_size
from media_hygiene.i18n import _, ngettext

if TYPE_CHECKING:
    from media_hygiene.services.runtime import Runtime
    from media_hygiene.services.shrink import ShrinkResult
    from media_hygiene.shrink.candidates import Candidate

_SHOWN: Final = 15  # the largest gains listed; the count says the rest
_MINUTE: Final = 60
_BY: Final = "\N{MULTIPLICATION SIGN}"  # between the width and the height


def show_candidates(runtime: Runtime, videos: tuple[Candidate, ...]) -> None:
    """List the videos worth lightening, the largest gain first, and the total.

    Args:
        runtime: Settings, mount points and output.
        videos: The candidates.
    """
    output = runtime.output
    before = sum(video.size for video in videos)
    after = sum(min(video.estimated, video.size) for video in videos)
    output.info(
        ngettext(
            "{count} video worth lightening: {before} today, about {after} after "
            "(estimated: only the encoding tells).",
            "{count} videos worth lightening: {before} today, about {after} after "
            "(estimated: only the encoding tells).",
            len(videos),
        ).format(
            count=human_number(len(videos)),
            before=human_size(before),
            after=human_size(after),
        )
    )
    for video in videos[:_SHOWN]:
        line = _("   {path} — {codec}, {pixels}, {minutes} min: {size} → ~{after}")
        output.info(
            line.format(
                path=escape(runtime.mapper.to_host(video.path)),
                codec=video.codec,
                pixels=f"{video.look.width}{_BY}{video.look.height}",
                minutes=max(1, round(video.duration / _MINUTE)),
                size=human_size(video.size),
                after=human_size(min(video.estimated, video.size)),
            )
        )
    if len(videos) > _SHOWN:
        rest = len(videos) - _SHOWN
        output.info(
            ngettext("   … and {count} more.", "   … and {count} more.", rest).format(
                count=human_number(rest)
            )
        )


def show_result(runtime: Runtime, result: ShrinkResult) -> None:
    """Say what was lightened and saved, what was not worth it, what failed.

    Args:
        runtime: Settings, mount points and output.
        result: The run.
    """
    output = runtime.output
    outcome, gains = result.outcome, result.gains
    output.success(
        ngettext(
            "{count} video lightened, {saved} saved; its original is in the "
            "quarantine.",
            "{count} videos lightened, {saved} saved; their originals are in the "
            "quarantine.",
            outcome.quarantined,
        ).format(count=human_number(outcome.quarantined), saved=human_size(gains.saved))
    )
    if gains.not_worth:
        output.info(
            ngettext(
                "{count} video not worth it (too little gain): left as it was, "
                "not tried again.",
                "{count} videos not worth it (too little gain): left as they were, "
                "not tried again.",
                gains.not_worth,
            ).format(count=human_number(gains.not_worth))
        )
    for incident in outcome.failed:
        output.warning(
            _("{path}: not lightened: {reason}").format(
                path=escape(runtime.mapper.to_host(incident.path)),
                reason=escape(incident.reason),
            )
        )
    for incident in outcome.skipped:
        output.warning(
            _("{path}: left where it was: {reason}").format(
                path=escape(runtime.mapper.to_host(incident.path)),
                reason=escape(incident.reason),
            )
        )
    if result.interrupted:
        output.warning(_("Stopped by Ctrl+C: type the command again for the rest."))
