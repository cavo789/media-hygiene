"""After `sort` or `undo`: every file naming photos by path names their new path (0382).

The index follows each move, but the user's own files name photos too: the people's
face lists (`/config/people/`), `albums.json` and `decisions.json` (`/reports`), the
videos chosen in `shrink --try`. Each is rewritten by the run that moved the photos,
then read back from the disk, so that no link depends on the cache any more. A file
that cannot be rewritten is named; the run itself is over and stays done.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from media_hygiene.errors import MediaHygieneError
from media_hygiene.i18n import _, ngettext
from media_hygiene.people.followed import follow_people
from media_hygiene.report.decisions_moves import DecisionMoves, follow_decisions
from media_hygiene.review.place import DEFAULT_DECISIONS
from media_hygiene.services.classify_inputs import root_of
from media_hygiene.services.sort_links_folders import emptied_settings
from media_hygiene.share.album_moves import follow_albums
from media_hygiene.share.albums import ALBUMS_FILE
from media_hygiene.shrink.drafts import drafts_root
from media_hygiene.shrink.try_choices import CHOICES_FILE, follow_choices

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence

    from media_hygiene.services.runtime import Runtime

_FAILED = (OSError, ValueError, MediaHygieneError)


@dataclass(frozen=True, slots=True)
class LinksFollowed:
    """What the user is told: the files rewritten, those that could not be."""

    lines: tuple[str, ...] = ()  # one line: what was rewritten and read back
    problems: tuple[str, ...] = ()  # one line per file not rewritten, or folder emptied


def follow_links(runtime: Runtime, moved: Sequence[tuple[str, str]]) -> LinksFollowed:
    """Rewrite each file naming the moved photos, and read it back.

    Args:
        runtime: Settings, mount points and output.
        moved: Old and new container path of each file the run moved.

    Returns:
        The lines to show.
    """
    if not moved:
        return LinksFollowed()
    moves = dict(moved)
    mapper, locations = runtime.mapper, runtime.locations
    hosts = {mapper.to_host(Path(old)): mapper.to_host(Path(new)) for old, new in moved}
    reports = locations.reports_dir
    stores: tuple[tuple[str, Callable[[], str]], ...] = (
        (str(locations.config_file), lambda: _people(locations.config_file, moves)),
        (ALBUMS_FILE, lambda: _albums(reports / ALBUMS_FILE, hosts)),
        (
            DEFAULT_DECISIONS,
            lambda: _decisions(runtime, reports / DEFAULT_DECISIONS, hosts),
        ),
        (CHOICES_FILE, lambda: _choices(drafts_root(locations.cache_dir), moves)),
    )
    done: list[str] = []
    problems: list[str] = []
    for name, rewrite in stores:
        try:
            said = rewrite()
        except _FAILED as exc:
            problems.append(
                _(
                    "{file} was not updated ({reason}): its links follow the moves "
                    "through the cache only."
                ).format(file=name, reason=exc)
            )
            continue
        if said:
            done.append(said)
    problems.extend(emptied_settings(runtime, moves))
    line = (
        _("Links updated, read back from the disk: {parts}.").format(
            parts="; ".join(done)
        )
        if done
        else ""
    )
    return LinksFollowed((line,) if line else (), tuple(problems))


def _people(config_file: Path, moves: Mapping[str, str]) -> str:
    """The people's face lists.

    Args:
        config_file: `config.toml`.
        moves: New container path by old one.

    Returns:
        What changed, or nothing.
    """
    count = follow_people(config_file, moves)
    return (
        ngettext("{count} named face", "{count} named faces", count).format(count=count)
        if count
        else ""
    )


def _albums(path: Path, hosts: Mapping[str, str]) -> str:
    """The albums.

    Args:
        path: `albums.json`.
        hosts: New host path by old one.

    Returns:
        What changed, or nothing.
    """
    count = follow_albums(path, hosts)
    return (
        ngettext("{count} album photo", "{count} album photos", count).format(
            count=count
        )
        if count
        else ""
    )


def _decisions(runtime: Runtime, path: Path, hosts: Mapping[str, str]) -> str:
    """The review decisions.

    Args:
        runtime: Mount points.
        path: `decisions.json`.
        hosts: New host path by old one.

    Returns:
        What changed, or nothing.
    """
    mapper = runtime.mapper
    roots = runtime.mounts.data_roots(runtime.locations.data_dir)
    root_by_new = {
        new: mapper.to_host(root_of(mapper.to_container(new), roots, runtime))
        for new in hosts.values()
    }
    followed = follow_decisions(
        path,
        DecisionMoves(
            hosts, root_by_new, lambda folder: mapper.to_container(folder).is_dir()
        ),
    )
    parts = []
    if followed.paths:
        parts.append(
            ngettext(
                "{count} decided file", "{count} decided files", followed.paths
            ).format(count=followed.paths)
        )
    if followed.pairs_dropped:
        parts.append(
            ngettext(
                "{count} folder pair whose folder is gone dropped",
                "{count} folder pairs whose folder is gone dropped",
                followed.pairs_dropped,
            ).format(count=followed.pairs_dropped)
        )
    return ", ".join(parts)


def _choices(drafts: Path, moves: Mapping[str, str]) -> str:
    """The videos chosen in `shrink --try`.

    Args:
        drafts: The drafts folder.
        moves: New container path by old one.

    Returns:
        What changed, or nothing.
    """
    count = follow_choices(drafts / CHOICES_FILE, moves)
    return (
        ngettext(
            "{count} video chosen to lighten", "{count} videos chosen to lighten", count
        ).format(count=count)
        if count
        else ""
    )
