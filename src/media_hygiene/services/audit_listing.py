"""The audit's walk: every root once, without listing a file twice."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.i18n import _
from media_hygiene.scan.aliases import unique_files
from media_hygiene.scan.progress import Step
from media_hygiene.scan.walker import Walk
from media_hygiene.services.data_checks import warn_about_aliases
from media_hygiene.services.listing import list_media

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.scan.progress import ProgressSink
    from media_hygiene.services.runtime import Runtime


def list_walk(
    runtime: Runtime, roots: tuple[Path, ...], progress: ProgressSink
) -> tuple[Walk, frozenset[Path]]:
    """Walk every root, without listing a file twice (nested mounts, hard links).

    Args:
        runtime: Settings, mount points and output.
        roots: Mounted folders.
        progress: Where to report progress.

    Returns:
        The media files, by path, every sidecar found, what could not be read;
        then every media path listed, the aliases set aside included.
    """
    step = Step(
        _("Listing media files"),
        _(
            "Walks through every folder; photos and videos are recognised by their "
            "extension."
        ),
    )
    progress.start(step, None)
    found = list_media(runtime, roots, progress)
    progress.stop()
    unique = unique_files(found.files)
    warn_about_aliases(runtime, unique.aliases)
    every_path = frozenset(file.path for file in found.files)
    return Walk(unique.files, found.sidecars, found.unreadable), every_path
