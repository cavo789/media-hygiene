"""Drop words from every photo (0546, 0622), or merge one into another tag.

Dropping: stop words, index rows, sidecars. Merging: the synonym in `[tags] synonyms`,
its rows and sidecar words become the tag it means.

In that order: a stop in the middle leaves a word that no run brings back, and dropping
again finishes it. The sidecars are written like those of `xmp`: journaled, read back,
undone by `undo`. Without a journal or on read-only folders they wait: the next
`xmp --apply` takes the word back, since the index no longer gives it. A protected
folder is never written; a photo that also has the word typed by hand keeps it.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from media_hygiene.actions.kinds import Phase
from media_hygiene.actions.outcome import Tally
from media_hygiene.actions.xmp_write import XmpExecutor, XmpJob
from media_hygiene.errors import MountError
from media_hygiene.index.repository import FactsRepository
from media_hygiene.index.tag_drop import delete_word, paths_of
from media_hygiene.index.tag_merge import merge_word as merge_rows
from media_hygiene.paths.host_paths import is_within
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.acting import ensure_can_act
from media_hygiene.services.journaled_run import new_run
from media_hygiene.services.run_listings import forget_run_listings
from media_hygiene.services.xmp_sidecars import sidecar_of
from media_hygiene.tags.hand_files import hand_words
from media_hygiene.tags.stop_edit import add_stop_word
from media_hygiene.tags.synonym_edit import add_synonym
from media_hygiene.tags.xmp_doc import XmpError, parse
from media_hygiene.tags.xmp_merge import take_back_subject

if TYPE_CHECKING:
    from media_hygiene.services.runtime import Runtime


@dataclass(frozen=True, slots=True)
class Merge:
    """A synonym (`word`) and the tag it means (`target`); no target: words dropped."""

    words: tuple[str, ...]
    target: str = ""


@dataclass(frozen=True, slots=True)
class Dropped:
    """What dropping a word did."""

    rows: int
    sidecars: int = 0  # written, read back
    failed: int = 0  # sidecars left as they were
    waiting: bool = False  # not writable now: the next `xmp --apply` does it
    run_id: str = ""  # the run `undo` takes back, when a sidecar was written


def drop_words(runtime: Runtime, words: tuple[str, ...]) -> Dropped:
    """Add the words to the stop words, take them off the index and the sidecars.

    Args:
        runtime: Settings, mount points and output.
        words: The words.

    Returns:
        What was done.

    Raises:
        ValueError: `config.toml` is not TOML.
        OSError: It cannot be written.
        sqlite3.Error: The index cannot be written.
    """
    for word in words:
        add_stop_word(runtime.locations.config_file, word)
    with FactsRepository.open(runtime.locations.index_file) as repository:
        paths = paths_of(repository.connection, words)
        rows = delete_word(repository.connection, words)
    return _sidecars(runtime, Merge(words), (paths, rows))


def merge_word(runtime: Runtime, merge: Merge) -> Dropped:
    """Name a word as another tag: `[tags] synonyms`, the index, the sidecars (0622).

    Args:
        runtime: Settings, mount points and output.
        merge: The synonym (one word) and the tag it means.

    Returns:
        What was done.

    Raises:
        ValueError: `config.toml` is not TOML.
        OSError: It cannot be written.
        sqlite3.Error: The index cannot be written.
    """
    word = merge.words[0]
    add_synonym(runtime.locations.config_file, word, merge.target)
    with FactsRepository.open(runtime.locations.index_file) as repository:
        paths = paths_of(repository.connection, merge.words)
        rows = merge_rows(repository.connection, word, merge.target)
    return _sidecars(runtime, merge, (paths, rows))


def _sidecars(runtime: Runtime, merge: Merge, found: tuple[list[str], int]) -> Dropped:
    """Write the sidecars of the photos that had the words, journaled.

    Args:
        runtime: Settings, mount points and output.
        merge: The words, and the tag written instead (none: dropped).
        found: The paths that had them, the rows changed.

    Returns:
        What was done.
    """
    paths, rows = found
    try:
        ensure_can_act(runtime, Phase.XMP.value)
    except MountError:
        return Dropped(rows, waiting=True)
    jobs, unread = _jobs(runtime, merge, paths)
    if not jobs:
        return Dropped(rows, failed=unread)
    tally = Tally()
    with new_run(runtime, NullProgress(), Phase.XMP) as context:
        XmpExecutor(context, tally).run(jobs, lambda: False)
    run_id = context.quarantine_run_dir.name
    forget_run_listings(runtime, run_id, Phase.XMP)
    return Dropped(rows, tally.done, len(tally.failed) + unread, run_id=run_id)


def _jobs(runtime: Runtime, merge: Merge, paths: list[str]) -> tuple[list[XmpJob], int]:
    """The sidecars that hold the words as ours, without them.

    Args:
        runtime: Settings, mount points and output.
        merge: The words, and the tag written instead.
        paths: The container paths that had it.

    Returns:
        The sidecars to write, and how many could not be read.
    """
    protected = tuple(
        map(runtime.mapper.to_container, runtime.settings.folders.untouched)
    )
    typed = hand_words(runtime.locations.config_file, runtime.mapper)
    folded = {word.casefold() for word in merge.words}
    folders: dict[Path, list[str]] = {}
    jobs: list[XmpJob] = []
    unread = 0
    for photo in map(Path, paths):
        if (
            any(is_within(photo, folder) for folder in protected)
            or any(each.casefold() in folded for each in typed.get(photo, ()))
            or not photo.is_file()
        ):
            continue
        try:
            sidecar = sidecar_of(photo, folders)
            if not sidecar.is_file():
                continue
            previous = sidecar.read_bytes()
            doc = parse(previous)
        except OSError, XmpError:
            unread += 1
            continue
        if take_back_subject(doc, merge.words, merge.target):
            jobs.append(XmpJob(photo, sidecar, doc.to_bytes(), previous))
    return jobs, unread
