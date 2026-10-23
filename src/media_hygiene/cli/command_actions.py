"""The commands that change files: the panel "Act" of `--help`."""

from __future__ import annotations

from media_hygiene.i18n import _


def action_commands(act: str) -> tuple[tuple[str, str, str], ...]:
    """List the commands that change files.

    Args:
        act: The translated name of the panel of actions.

    Returns:
        Name, panel and help text of each command.
    """
    return (
        (
            "clean",
            act,
            _(
                "Audit, confirm, then move the duplicate copies to the quarantine, "
                "after a byte comparison (journaled, undoable); --delete deletes "
                "them for good."
            ),
        ),
        (
            "sort",
            act,
            _(
                "Move the photos and videos as the edited classify workbook says "
                "(journaled, undoable)."
            ),
        ),
        (
            "album",
            act,
            _(
                "Make an album's folder on the disk, as hard links: nothing is "
                "copied nor moved (journaled, undoable)."
            ),
        ),
        (
            "xmp",
            act,
            _(
                "Write the words of 'tags' into .xmp sidecars next to the photos, "
                "for digiKam, darktable, Lightroom or Immich; never into a photo "
                "(journaled, undoable)."
            ),
        ),
        (
            "import",
            act,
            _(
                "Copy into your photos what only a backup (a NAS) holds, never what "
                "you set aside or deleted before; each copy proven (journaled, "
                "undoable)."
            ),
        ),
        (
            "backup",
            act,
            _(
                "Windows only, as mh backup: copy your photo folders into a folder "
                "of their own on the NAS, only what it lacks; a photo moved is "
                "renamed there, a deletion by mistake never carried over. Run here, "
                "it shows the plan."
            ),
        ),
        (
            "shrink",
            act,
            _(
                "List the heavy videos worth lightening (old cameras, MJPEG); with "
                "--apply, re-encode them in H.264, each one checked, the original "
                "in the quarantine (journaled, undoable)."
            ),
        ),
        (
            "undo",
            act,
            _(
                "Restore every file of a run, from the kept copy, the quarantine "
                "or where it was moved; remove the links of an album."
            ),
        ),
        (
            "purge",
            act,
            _(
                "Erase the quarantine of a run for good: with 'clean --delete', the "
                "only way the tool removes content."
            ),
        ),
    )
