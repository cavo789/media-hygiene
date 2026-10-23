"""`media-hygiene shrink`: list the heavy videos worth lightening, then lighten them.

The list comes from the index alone (the last audit described every video): nothing
is decoded, nothing changes. `--apply` re-encodes them one at a time, journaled
(`actions.shrink`): each original goes to its drive's quarantine, `undo` brings it
back. Refused without a persistent journal and quarantine, on read-only photo folders,
or with an `ffmpeg` that cannot encode H.264.
"""

from __future__ import annotations

import shutil
import subprocess  # a fixed command: ffmpeg's list of encoders
from contextlib import closing
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Final

from media_hygiene.actions.journal import journal_file, read_journal
from media_hygiene.actions.kinds import Phase
from media_hygiene.actions.not_worth import not_worth
from media_hygiene.actions.outcome import Tally
from media_hygiene.actions.shrink import Gains, Recipe, ShrinkExecutor
from media_hygiene.constants import FFMPEG_BINARY, FFPROBE_BINARY
from media_hygiene.errors import MountError
from media_hygiene.i18n import _
from media_hygiene.index.read_only import connect_read_only
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.services.acting import ensure_can_act
from media_hygiene.services.journaled_run import new_run
from media_hygiene.services.missing_mount import missing_mount, typed_again
from media_hygiene.services.next_command import CHANGING, NextVerb
from media_hygiene.services.quarantine_space import quarantine_route
from media_hygiene.services.search_pages import shown_roots
from media_hygiene.services.shrink_index import park_originals
from media_hygiene.shrink.candidates import FILES, Selection, candidates
from media_hygiene.shrink.check import Tools
from media_hygiene.shrink.encode import encoding_of

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from media_hygiene.actions.outcome import Outcome
    from media_hygiene.scan.progress import ProgressSink
    from media_hygiene.services.runtime import Runtime
    from media_hygiene.shrink.candidates import Candidate

COMMAND: Final = "shrink"
_ENCODER: Final = "libx264"
_ENCODERS_SECONDS: Final = 30


@dataclass(frozen=True, slots=True)
class ShrinkAsk:
    """What the user asked: the folders (container paths, none for all), the level."""

    folders: tuple[Path, ...] = ()
    lighter: bool = False


@dataclass(frozen=True, slots=True)
class ShrinkJobs:
    """The videos to lighten, the tools that do it, and the level asked."""

    videos: tuple[Candidate, ...]
    tools: Tools
    lighter: bool = False


@dataclass(frozen=True, slots=True)
class ShrinkResult:
    """What a `shrink --apply` run did."""

    run_id: str
    outcome: Outcome
    gains: Gains
    interrupted: bool


class ShrinkService:
    """Lists the videos worth lightening, then lightens them: journaled, undoable."""

    def __init__(self, runtime: Runtime, progress: ProgressSink) -> None:
        """Prepare a run.

        Args:
            runtime: Settings, mount points and output.
            progress: Where to report progress.
        """
        self._runtime = runtime
        self._progress = progress

    def candidates(self, ask: ShrinkAsk) -> tuple[Candidate, ...]:
        """List the videos worth lightening, from the index alone.

        Args:
            ask: The folders and the level.

        Returns:
            The candidates, the largest gain first.

        Raises:
            MountError: No index yet: an audit comes first.
        """
        runtime = self._runtime
        index = runtime.index_file
        if index is None or not index.is_file():
            raise MountError(
                _("No audit yet: 'shrink' reads the videos the audit described."),
                _("Run 'audit' first, then 'shrink' again."),
            )
        folders = runtime.settings.folders
        untouchable = (*folders.protected, *folders.excluded, *folders.backups)
        journal = runtime.locations.journal_dir
        selection = Selection(
            runtime.settings.shrink,
            ask.folders or shown_roots(runtime),
            tuple(runtime.mapper.to_container(path) for path in untouchable),
            not_worth(journal) if journal.is_dir() else frozenset(),
            lighter=ask.lighter,
        )
        with closing(connect_read_only(index)) as connection:
            return candidates(connection.execute(FILES), selection)

    def ensure_ready(self) -> Tools:
        """Check, before changing anything, that lightening is possible and undoable.

        Returns:
            The `ffmpeg` and `ffprobe` to use.

        Raises:
            MountError: No persistent quarantine or journal, read-only folders, or
                no `ffmpeg` able to encode H.264.
        """
        runtime = self._runtime
        if not runtime.persistent(MountKind.QUARANTINE):
            again = NextVerb(typed_again(runtime, COMMAND), CHANGING)
            message = _("'shrink' moves each original to /quarantine: mount it.")
            raise missing_mount(runtime, message, again)
        ensure_can_act(runtime, COMMAND)
        ffmpeg, ffprobe = shutil.which(FFMPEG_BINARY), shutil.which(FFPROBE_BINARY)
        if ffmpeg is None or ffprobe is None or not _encodes(ffmpeg):
            raise MountError(
                _("This ffmpeg cannot encode H.264: nothing was changed."),
                _("Update the image: mh update."),
            )
        return Tools(ffmpeg, ffprobe)

    def execute(self, jobs: ShrinkJobs, stop: Callable[[], bool]) -> ShrinkResult:
        """Lighten the videos under a new run identifier.

        Args:
            jobs: The videos, the tools (`ensure_ready`) and the level.
            stop: Tells when Ctrl+C was pressed: the run stops between two videos.

        Returns:
            The run and what it did.
        """
        runtime = self._runtime
        settings = runtime.settings.shrink
        encoding = encoding_of(settings, lighter=jobs.lighter)
        recipe = Recipe(encoding, jobs.tools, settings.min_gain_percent)
        tally = Tally()
        with new_run(runtime, self._progress, Phase.SHRINK) as opened:
            context = replace(opened, route=quarantine_route(runtime))
            executor = ShrinkExecutor(context, tally, recipe)
            interrupted = executor.run(jobs.videos, stop)
        run_id = context.quarantine_run_dir.name
        journal = journal_file(runtime.locations.journal_dir, run_id)
        park_originals(runtime, run_id, read_journal(journal))
        return ShrinkResult(run_id, tally.freeze(), executor.gains, interrupted)


def _encodes(ffmpeg: str) -> bool:
    """Tell whether an `ffmpeg` can encode H.264 (the image's, since 0303).

    Args:
        ffmpeg: The executable.

    Returns:
        True when it lists `libx264` among its encoders.
    """
    try:
        listed = subprocess.run(  # noqa: S603  # a fixed command, no user input
            (ffmpeg, "-hide_banner", "-encoders"),
            capture_output=True,
            check=False,
            timeout=_ENCODERS_SECONDS,
        )
    except OSError, subprocess.TimeoutExpired:
        return False
    return _ENCODER in listed.stdout.decode(errors="replace")
