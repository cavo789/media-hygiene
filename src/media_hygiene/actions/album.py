"""Make an album: its folder, its marker, then one hard link per file, all journaled.

Nothing is copied nor moved: each link is a second name for the bytes of a photo kept
where it is. The marker file tells every scan to skip the folder, so that a link never
looks like a duplicate of its original. `undo` removes the links (never the last name
of a file), the marker, then the folders the run created.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import TYPE_CHECKING

from media_hygiene.actions.album_links import UNSUPPORTED, why_not
from media_hygiene.actions.journaled import JournaledChanges
from media_hygiene.actions.kinds import ActionKind
from media_hygiene.actions.outcome import Incident
from media_hygiene.actions.sort_moves import file_of, make_folders
from media_hygiene.constants import ALBUM_MARKER
from media_hygiene.i18n import _
from media_hygiene.scan.progress import Step

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from media_hygiene.actions.album_plan import AlbumLink, AlbumPlan
    from media_hygiene.actions.journaled import CleanContext
    from media_hygiene.actions.outcome import Tally

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class AlbumRun:
    """How an album run ended: whole, stopped by Ctrl+C, or by a disk without links."""

    interrupted: bool = False
    unsupported: str = ""  # why no link can be made on this disk; empty: none


class AlbumExecutor:
    """Journals and makes the folders, the marker and the links of one album."""

    def __init__(self, context: CleanContext, tally: Tally) -> None:
        """Prepare the changes of a run.

        Args:
            context: Journal (phase `album`), path mapper and progress sink.
            tally: Counters of the run: one per link made, no bytes (none are used).
        """
        self._context = context
        self._tally = tally
        self._changes = JournaledChanges(context, tally)

    def run(self, plan: AlbumPlan, stop: Callable[[], bool]) -> AlbumRun:
        """Make the album.

        Args:
            plan: The links to make.
            stop: Tells when Ctrl+C was pressed: the run stops between two links.

        Returns:
            How the run ended.
        """
        make_folders(self._changes, plan.folder)
        self._mark(plan.folder)
        progress = self._context.progress
        progress.start(
            Step(_("Linking"), _("Gives each file a second name in the album.")),
            len(plan.links),
        )
        ended = AlbumRun()
        for link in plan.links:
            if stop():
                ended = AlbumRun(interrupted=True)
                break
            reason = self._link(link)
            progress.advance()
            if reason:
                ended = AlbumRun(unsupported=reason)
                break
        progress.stop()
        return ended

    def _link(self, link: AlbumLink) -> str:
        """Make one link, journaled; a failure is counted, never raised.

        Args:
            link: The link.

        Returns:
            Why no other link can be made on this disk; empty otherwise.
        """
        file = file_of(link.link, (link.size, link.mtime_ns))
        entry = self._changes.entry(file, ActionKind.LINK).model_copy(
            update={"keeper": str(link.source)}
        )
        try:
            self._changes.record(entry, lambda: os.link(link.source, link.link))
        except OSError as exc:
            _LOGGER.debug("Link failed for %s", link.source, exc_info=True)
            self._tally.failed.append(Incident(link.link, why_not(exc)))
            return why_not(exc) if exc.errno in UNSUPPORTED else ""
        self._tally.done += 1
        return ""

    def _mark(self, folder: Path) -> None:
        """Write the marker that every scan skips the album for, journaled.

        Args:
            folder: The album folder.
        """
        marker = folder / ALBUM_MARKER
        if marker.exists():
            return
        text = _(
            "This folder is an album of media-hygiene: hard links, second names of "
            "photos kept elsewhere, which take no space. The audits skip it. "
            "'media-hygiene undo' removes it; deleting it by hand is safe too."
        )
        entry = self._changes.entry(file_of(marker, (0, 0)), ActionKind.MARK_ALBUM)
        self._changes.record(entry, lambda: marker.write_text(text + "\n", "utf-8"))
