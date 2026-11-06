"""The try handed from the home server to `mh`: `shrink --chosen` (0599).

The home server encodes the drafts; its container reads the photos only, so *Lighten*
is a step of its own, in another container, sharing `/cache`. Before the step starts,
the drafts and the decisions move to `handed/`: closing the try removes nothing of
them. The step takes the lock, finds each video again in the index (moved, renamed or
changed since the page: skipped) and removes `handed/` whatever ends it; one left by a
crash goes with the next `shrink`'s sweep.
"""

from __future__ import annotations

import contextlib
import shutil
from pathlib import Path
from typing import TYPE_CHECKING, Final

from media_hygiene.errors import MediaHygieneError
from media_hygiene.i18n import _
from media_hygiene.review.step_watch import WATCH
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.shrink import ShrinkAsk, ShrinkJobs, ShrinkService
from media_hygiene.services.shrink_tools import encoding_tools
from media_hygiene.services.shrink_try import (
    Chosen,
    ensure_cache,
    opened_try,
    sweep_drafts,
    try_lock,
)
from media_hygiene.shrink.draft_bench import draft_file
from media_hygiene.shrink.drafts import drafts_root
from media_hygiene.shrink.try_choices import CHOICES_FILE, read_choices

if TYPE_CHECKING:
    from collections.abc import Iterator

    from media_hygiene.services.runtime import Runtime
    from media_hygiene.services.shrink_try import Trial
    from media_hygiene.shrink.candidates import Candidate, FileKey

CHOSEN_WORDS: Final = ("shrink", "--chosen", "--yes")
_HANDED: Final = "handed"
_DRAFTS: Final = "drafts"


def opened_here(runtime: Runtime) -> tuple[contextlib.ExitStack, Trial]:
    """Start the drafts of the first videos, unless a step still needs the folder.

    Args:
        runtime: Settings, mount points and output.

    Returns:
        What closes the try, and the try.

    Raises:
        MediaHygieneError: A step runs, no audit yet, or nothing is worth lightening.
    """
    folder = runtime.locations.reports_dir
    if (folder / WATCH.now).exists() or (folder / WATCH.running).exists():
        raise MediaHygieneError(
            _("A step is running in the window of mh: wait for its end.")
        )
    ensure_cache(runtime)
    sweep_drafts(runtime)
    videos = ShrinkService(runtime, NullProgress()).candidates(ShrinkAsk(()))
    if not videos:
        raise MediaHygieneError(_("No video worth lightening."))
    jobs = ShrinkJobs(videos[: runtime.settings.shrink.try_count], encoding_tools())
    stack = contextlib.ExitStack()
    return stack, stack.enter_context(opened_try(runtime, jobs))


def hand_over(trial: Trial) -> None:
    """Stop the encodings, and set the drafts and the choices apart for the step.

    Args:
        trial: The try; closing it afterwards removes nothing of them.
    """
    trial.bench.stop()
    target = trial.choices.parent / _HANDED
    shutil.rmtree(target, ignore_errors=True)
    target.mkdir()
    trial.choices.rename(target / CHOICES_FILE)
    trial.bench.folder.rename(target / _DRAFTS)


def _matched(runtime: Runtime, target: Path) -> Chosen:
    """Match the choices with what the index says now.

    Args:
        runtime: Settings, mount points and output.
        target: The folder handed over.

    Returns:
        The videos still as their drafts saw them, with their drafts; the others.
    """
    choices = read_choices(target / CHOICES_FILE)
    if choices is None or not choices.chosen:
        return Chosen((), {}, ())
    known = {
        video.key: video
        for video in ShrinkService(runtime, NullProgress()).candidates(ShrinkAsk(()))
    }
    videos: list[Candidate] = []
    reused: dict[FileKey, Path] = {}
    skipped: list[str] = []
    for choice in choices.chosen:
        video = known.get(choice.key)
        if video is None or not _unchanged(choice.key):
            skipped.append(choice.path)
            continue
        videos.append(video)
        made = draft_file(target / _DRAFTS, choice.draft)
        if made.is_file():
            reused[choice.key] = made
    return Chosen(tuple(videos), reused, tuple(skipped))


def _unchanged(key: FileKey) -> bool:
    """Tell whether a video is still the one its draft was made from.

    Args:
        key: Its path, size and modification time at the page.

    Returns:
        True when the file on the disk still matches.
    """
    try:
        stat = Path(key[0]).stat()
    except OSError:
        return False
    return (stat.st_size, stat.st_mtime_ns) == key[1:]


@contextlib.contextmanager
def handed_try(runtime: Runtime) -> Iterator[Chosen]:
    """Hold the lock on the try handed over; whatever ends it, remove its drafts.

    Args:
        runtime: Settings, mount points and output.

    Yields:
        What the page chose that still matches.

    Raises:
        MountError: A `shrink --try` is running on this cache.
    """
    root = drafts_root(runtime.locations.cache_dir)
    target = root / _HANDED
    with try_lock(root):
        try:
            yield _matched(runtime, target)
        finally:
            shutil.rmtree(target, ignore_errors=True)
