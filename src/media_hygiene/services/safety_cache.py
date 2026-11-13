"""The slow facts of *Are my photos safe?* kept in `/cache` (0692).

What exists nowhere else in the quarantine (`only_copies`) and the drives to plug in
(`held_back`) read every journal of the runs still set aside and stat every file they
name: 0.2 s for 5,000 files in the devcontainer, far more through Docker Desktop's file
sharing. They are kept in `/cache/home-safety.json` with the key they were read under,
and read again only when the key changes. The key lists what they depend on:

- the quarantines mounted (a drive's quarantine plugged in or out) and the runs in them
  (a `clean` adds one, a `purge` removes one);
- each run's journal: size, mtime and ctime, or missing (an `undo` appends to it; a
  journal put back by hand or restored from `mh backup` changes its ctime even when the
  copy keeps the mtime);
- every folder below each run's quarantine folder, with its mtime and ctime (a file
  removed or put back by hand, by `undo` or by `purge` changes its folder's);
- the NAS listing the last proven push kept (`nas_cover`, 0781: a new push);
- the index file (an audit after a kept twin was removed by hand: the only thing not
  under the tool folders, seen at the next audit; until then the card may count it as
  covered, but `purge` counts the only copies again, uncached, before it erases).

A cache never written (no persistent `/cache`) or unreadable: read as before.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Final

from media_hygiene.actions.journal import journal_file
from media_hygiene.actions.purge import run_folders
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.services.nas_cover import cover_file
from media_hygiene.services.only_copies import only_copies
from media_hygiene.services.only_count import only_count
from media_hygiene.services.quarantines import held_back

if TYPE_CHECKING:
    from media_hygiene.services.runtime import Runtime

SAFETY_CACHE_NAME: Final = "home-safety.json"
_Stamp = tuple[int, int, int] | None


@dataclass(frozen=True, slots=True)
class SlowFacts:
    """The two facts of the card that read the quarantine file by file."""

    only: int  # files of the quarantine that exist nowhere else
    unplugged: tuple[str, ...]  # drives whose quarantine is not mounted
    nas: int = 0  # files of the quarantine whose only other copy is on the NAS


@dataclass(frozen=True, slots=True)
class SlowAsk:
    """What the slow facts are read from."""

    runtime: Runtime
    runs: tuple[str, ...]
    folders: tuple[Path, ...]  # the quarantines mounted


def slow_facts(ask: SlowAsk) -> SlowFacts:
    """The slow facts, from the cache when nothing they depend on changed.

    Args:
        ask: The runtime, the runs, the quarantines.

    Returns:
        The facts.
    """
    runtime = ask.runtime
    key = safety_key(ask)
    cache = (
        runtime.locations.cache_dir / SAFETY_CACHE_NAME
        if runtime.persistent(MountKind.CACHE)
        else None
    )
    kept = _read(cache, key) if cache is not None else None
    if kept is not None:
        return kept
    journal_dir = runtime.locations.journal_dir
    # From the index: 55 s of stats through Docker Desktop became a query (2026-11-11).
    counted = only_count(_index(runtime), journal_dir, ask.runs)
    if counted is None:  # no index: the disk is asked, file by file
        found = only_copies(ask.folders, journal_dir, ask.runs)
        only, nas = len(found.files), found.nas
    else:
        only, nas = counted.only, counted.nas
    unplugged = tuple(sorted(set(held_back(runtime, ask.runs).values())))
    facts = SlowFacts(only, unplugged, nas)
    if cache is not None:
        _write(cache, key, facts)
    return facts


def _index(runtime: Runtime) -> Path | None:
    """The index, when `/cache` is kept.

    Args:
        runtime: Mount points.

    Returns:
        It, or None.
    """
    return runtime.locations.index_file if runtime.persistent(MountKind.CACHE) else None


def safety_key(ask: SlowAsk) -> str:
    """The digest of everything the slow facts depend on.

    Args:
        ask: The runtime, the runs, the quarantines.

    Returns:
        A hexadecimal SHA-256.
    """
    locations = ask.runtime.locations
    parts: list[object] = [[str(folder) for folder in ask.folders]]
    for run in ask.runs:
        folders = run_folders(ask.folders, run)
        parts.append([run, _stamp(journal_file(locations.journal_dir, run))])
        parts.append([_tree(folder) for folder in folders])
    parts.append(_stamp(locations.index_file))
    parts.append(_stamp(cover_file(locations.journal_dir)))
    return hashlib.sha256(json.dumps(parts).encode()).hexdigest()


def _tree(folder: Path) -> list[list[object]]:
    """Every folder below a run's quarantine folder, with its stamp.

    Args:
        folder: The run's folder in one quarantine.

    Returns:
        [path, stamp] per folder, sorted.
    """
    return sorted(
        [str(here), _stamp(Path(here))] for here, _dirs, _files in os.walk(folder)
    )


def _stamp(path: Path) -> _Stamp:
    """Size, mtime and ctime of a file or folder, None when it is missing.

    Args:
        path: The file or folder.

    Returns:
        The stamp.
    """
    try:
        found = path.stat()
    except OSError:
        return None
    return (found.st_size, found.st_mtime_ns, found.st_ctime_ns)


def _read(cache: Path, key: str) -> SlowFacts | None:
    """The facts kept under this key.

    Args:
        cache: `/cache/home-safety.json`.
        key: The key now.

    Returns:
        They, or None: no cache, another key, a file that does not load.
    """
    try:
        kept = json.loads(cache.read_text("utf-8"))
        if kept["key"] != key:
            return None
        unplugged = tuple(str(d) for d in kept["unplugged"])
        return SlowFacts(int(kept["only"]), unplugged, int(kept["nas"]))
    except OSError, ValueError, KeyError, TypeError:
        return None


def _write(cache: Path, key: str, facts: SlowFacts) -> None:
    """Keep the facts under their key, atomically; a write refused is skipped.

    Args:
        cache: `/cache/home-safety.json`.
        key: Their key.
        facts: The facts.
    """
    said = {
        "key": key,
        "only": facts.only,
        "unplugged": list(facts.unplugged),
        "nas": facts.nas,
    }
    temporary = cache.with_name(f".{cache.name}.tmp")
    with contextlib.suppress(OSError):
        temporary.write_text(json.dumps(said), "utf-8")
        temporary.replace(cache)
