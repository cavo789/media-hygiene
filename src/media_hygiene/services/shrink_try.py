"""`shrink --try`: drafts to compare in the browser, always removed (0307).

The first `try_count` candidates are encoded one at a time in the background, into
`/cache/shrink-try/<run>/` alone. The folder and the decisions file are removed when
the try ends, whatever ends it: the page closed, Ctrl+C or `docker stop` (SIGTERM is
turned into Ctrl+C by `__main__`), an error. Refused without a persistent `/cache`
(never a fallback inside the container) and while another `shrink --try` runs.
"""

from __future__ import annotations

import contextlib
import shutil
import time
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Final

from media_hygiene.actions.shrink import Recipe
from media_hygiene.errors import MountError
from media_hygiene.i18n import _
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.services.missing_mount import missing_mount, typed_again
from media_hygiene.services.next_command import NextVerb
from media_hygiene.shrink.draft_bench import DraftBench, draft_file
from media_hygiene.shrink.drafts import TryLock, drafts_root, sweep
from media_hygiene.shrink.encode import encoding_of
from media_hygiene.shrink.try_choices import CHOICES_FILE, read_choices

if TYPE_CHECKING:
    from collections.abc import Iterator

    from media_hygiene.services.runtime import Runtime
    from media_hygiene.services.shrink import ShrinkJobs
    from media_hygiene.shrink.candidates import Candidate, FileKey

COMMAND: Final = "shrink"
_RUN_NAME: Final = "%Y%m%d-%H%M%S"


@dataclass(frozen=True, slots=True)
class Trial:
    """One try: its drafts, its folder and its decisions file."""

    run: str
    bench: DraftBench
    choices: Path  # `shrink-decisions.json`, beside the runs' folders
    lighter: bool = False


@dataclass(frozen=True, slots=True)
class Chosen:
    """The videos chosen on the page that still match, their drafts, the others."""

    videos: tuple[Candidate, ...]
    drafts: dict[FileKey, Path]
    skipped: tuple[str, ...]  # container paths moved, renamed or changed since


def sweep_drafts(runtime: Runtime) -> None:
    """Remove the drafts a crashed run left, and say so in one line.

    Args:
        runtime: Settings, mount points and output.
    """
    if not runtime.persistent(MountKind.CACHE):
        return
    removed = sweep(drafts_root(runtime.locations.cache_dir))
    if removed:
        said = _("Previous drafts removed: {size} MB.")
        runtime.output.info(said.format(size=round(removed / 1_000_000)))


def ensure_cache(runtime: Runtime) -> None:
    """Refuse a try whose drafts would not land in the cache volume.

    Args:
        runtime: Settings, mount points and output.

    Raises:
        MountError: No persistent `/cache`: the line to add is said.
    """
    if runtime.persistent(MountKind.CACHE):
        return
    message = _("'shrink --try' writes its drafts in /cache only: mount it.")
    raise missing_mount(runtime, message, NextVerb(typed_again(runtime, COMMAND)))


@contextlib.contextmanager
def opened_try(runtime: Runtime, jobs: ShrinkJobs) -> Iterator[Trial]:
    """Start the drafts; whatever ends the try, remove them.

    Args:
        runtime: Settings, mount points and output.
        jobs: The videos to try (`try_count` of them at most), the tools, the level.

    Yields:
        The try, its drafts encoding in the background.

    Raises:
        MountError: Another `shrink --try` is running on this cache.
    """
    root = drafts_root(runtime.locations.cache_dir)
    settings = runtime.settings.shrink
    with contextlib.ExitStack() as stack:
        try:
            stack.enter_context(TryLock(root))
        except FileExistsError:
            raise MountError(
                _("Another 'shrink --try' is running: one at a time."),
                _("Close its page first, then try again."),
            ) from None
        run = time.strftime(_RUN_NAME)
        folder = root / run
        stack.callback((root / CHOICES_FILE).unlink, missing_ok=True)
        stack.callback(shutil.rmtree, folder, ignore_errors=True)
        folder.mkdir(parents=True, exist_ok=True)
        encoding = encoding_of(settings, lighter=jobs.lighter)
        recipe = Recipe(encoding, jobs.tools, settings.min_gain_percent)
        bench = DraftBench(folder, jobs.videos, recipe)
        stack.callback(bench.stop)  # first: no ffmpeg writes in a folder removed
        bench.start()
        yield Trial(run, bench, root / CHOICES_FILE, lighter=jobs.lighter)


def chosen(trial: Trial) -> Chosen:
    """Read the choices back from the disk, and match them with the files now.

    Args:
        trial: The try.

    Returns:
        The videos still as their drafts saw them, with their drafts; the others.
    """
    choices = read_choices(trial.choices)
    drafts = {draft.number: draft for draft in trial.bench.drafts()}
    videos: list[Candidate] = []
    reused: dict[FileKey, Path] = {}
    skipped: list[str] = []
    for choice in choices.chosen if choices is not None else ():
        draft = drafts.get(choice.draft)
        try:
            stat = Path(choice.path).stat()
        except OSError:
            stat = None
        now = None if stat is None else (choice.path, stat.st_size, stat.st_mtime_ns)
        if draft is None or now != choice.key or draft.video.key != choice.key:
            skipped.append(choice.path)
            continue
        videos.append(draft.video)
        made = draft_file(trial.bench.folder, draft.number)
        if made.is_file():
            reused[choice.key] = made
    return Chosen(tuple(videos), reused, tuple(skipped))
