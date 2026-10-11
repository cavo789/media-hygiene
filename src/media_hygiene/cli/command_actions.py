"""The commands that change files: the panel "Act" of `--help`."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.cli.cmd_album import album_command
from media_hygiene.cli.cmd_clean import clean_command
from media_hygiene.cli.cmd_purge import purge_command
from media_hygiene.cli.cmd_sort import sort_command
from media_hygiene.cli.cmd_undo import undo_command
from media_hygiene.cli.cmd_xmp import xmp_command
from media_hygiene.i18n import _

if TYPE_CHECKING:
    from collections.abc import Callable


def action_commands(act: str) -> tuple[tuple[str, Callable[..., None], str, str], ...]:
    """List the commands that change files.

    Args:
        act: The translated name of the panel of actions.

    Returns:
        Name, function, panel and help text of each command.
    """
    return (
        (
            "clean",
            clean_command,
            act,
            _(
                "Audit, confirm, then move the duplicate copies to the quarantine, "
                "after a byte comparison (journaled, undoable); --delete deletes "
                "them for good."
            ),
        ),
        (
            "sort",
            sort_command,
            act,
            _(
                "Move the photos and videos as the edited classify workbook says "
                "(journaled, undoable)."
            ),
        ),
        (
            "album",
            album_command,
            act,
            _(
                "Gather a selection of the classify plan into a folder of hard "
                "links: nothing is copied nor moved (journaled, undoable)."
            ),
        ),
        (
            "xmp",
            xmp_command,
            act,
            _(
                "Write the words of 'tags' into .xmp sidecars next to the photos, "
                "for digiKam, darktable, Lightroom or Immich; never into a photo "
                "(journaled, undoable)."
            ),
        ),
        (
            "undo",
            undo_command,
            act,
            _(
                "Restore every file of a run, from the kept copy, the quarantine "
                "or where it was moved; remove the links of an album."
            ),
        ),
        (
            "purge",
            purge_command,
            act,
            _(
                "Erase the quarantine of a run for good: with 'clean --delete', the "
                "only way the tool removes content."
            ),
        ),
    )
