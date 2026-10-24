"""`shrink --apply` and `shrink --try` in the terminal: the question, the run, the end.

`--try` (0307) serves the drafts' page; when it asks to lighten the videos chosen, the
same question as `--apply` comes here, then the same run, each draft reused.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import typer

from media_hygiene.cli.next_steps import carried, safety, suggest
from media_hygiene.console.progress import RichProgress
from media_hygiene.console.shrink_view import show_candidates, show_result
from media_hygiene.i18n import _, ngettext
from media_hygiene.review.shrink_app import LIGHTEN_CODE
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.interrupt import StopRequest
from media_hygiene.services.next_command import CHANGING, NextVerb
from media_hygiene.services.shrink import ShrinkJobs, ShrinkService
from media_hygiene.services.shrink_page import serve_try
from media_hygiene.services.shrink_tools import encoding_tools
from media_hygiene.services.shrink_try import chosen, ensure_cache, opened_try

if TYPE_CHECKING:
    from media_hygiene.services.runtime import Runtime
    from media_hygiene.shrink.candidates import Candidate


@dataclass(frozen=True, slots=True)
class Asked:
    """The command line: the videos listed, the level, whether to ask first."""

    videos: tuple[Candidate, ...]
    lighter: bool = False
    yes: bool = False


def lighten(runtime: Runtime, jobs: ShrinkJobs, *, yes: bool) -> None:
    """Ask, then lighten the videos and say how to undo it.

    Args:
        runtime: Settings, mount points and output.
        jobs: The videos, the tools and the drafts to reuse.
        yes: `--yes`, no question.

    Raises:
        typer.Exit: The user declined.
    """
    output = runtime.output
    if not yes and not typer.confirm(_("Lighten them?"), default=True):
        raise typer.Exit
    output.info(
        _(
            "🛟 Each video is re-encoded beside itself and checked (length, sound, "
            "date, place) before it replaces the original, which goes to the "
            "quarantine. Ctrl+C stops after the video being encoded."
        )
    )
    with RichProgress(output.console) as progress, StopRequest() as stop:
        result = ShrinkService(runtime, progress).execute(jobs, stop.requested)
    show_result(runtime, result)
    safety(
        runtime,
        _(
            "Changed your mind? 'media-hygiene undo {run_id}' removes the lighter "
            "videos and brings the originals back:"
        ).format(run_id=result.run_id),
        NextVerb(carried(runtime, f"undo {result.run_id}"), CHANGING),
    )
    if result.outcome.quarantined:  # an original aside, even one not replaced
        suggest(
            runtime,
            _(
                "once you have watched a few, 'purge' frees the space: the "
                "originals are still in the quarantine until then."
            ),
            NextVerb(carried(runtime, f"purge {result.run_id}"), CHANGING),
        )


def try_then_lighten(runtime: Runtime, asked: Asked) -> None:
    """Serve the drafts' page, then lighten what it chose, the drafts reused.

    Args:
        runtime: Settings, mount points and output.
        asked: The videos listed, the level, `--yes`.
    """
    output = runtime.output
    ensure_cache(runtime)
    tools = encoding_tools()
    videos = asked.videos[: runtime.settings.shrink.try_count]
    said = ngettext(
        "🔒 Nothing changes now: {count} draft, encoded in /cache only.",
        "🔒 Nothing changes now: {count} drafts, encoded one at a time in /cache only.",
        len(videos),
    )
    output.info(said.format(count=len(videos)))
    with opened_try(runtime, ShrinkJobs(videos, tools, lighter=asked.lighter)) as trial:
        if serve_try(runtime, trial) != LIGHTEN_CODE:
            output.info(_("Try stopped: its drafts are removed, nothing was changed."))
            return
        trial.bench.stop()  # the drafts left to encode: not now
        picked = chosen(trial)
        for path in picked.skipped:
            line = _("{path}: moved, renamed or changed since the page: skipped.")
            output.warning(line.format(path=runtime.mapper.to_host(Path(path))))
        if not picked.videos:
            output.info(_("No video left to lighten: nothing was changed."))
            return
        show_candidates(runtime, picked.videos)
        ready = ShrinkService(runtime, NullProgress()).ensure_ready()
        jobs = ShrinkJobs(picked.videos, ready, asked.lighter, picked.drafts)
        lighten(runtime, jobs, yes=asked.yes)
