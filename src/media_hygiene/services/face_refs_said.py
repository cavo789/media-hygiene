"""The audit's lines about the named faces it followed (0570)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.i18n import ngettext

if TYPE_CHECKING:
    from media_hygiene.services.face_refs_audit import FaceTally
    from media_hygiene.services.runtime import Runtime


def say_faces(runtime: Runtime, tally: FaceTally) -> None:
    """One line per kind of change, none when nothing changed.

    Args:
        runtime: Settings, mount points and output.
        tally: What the audit changed, read back.
    """
    output = runtime.output
    if tally.moved:
        output.info(
            ngettext(
                "{count} named face is on a photo renamed outside: its path is "
                "updated, read back from the disk.",
                "{count} named faces are on photos renamed outside: their path is "
                "updated, read back from the disk.",
                tally.moved,
            ).format(count=tally.moved)
        )
    if tally.dropped:
        output.info(
            ngettext(
                "{count} named face was on a photo edited since: another photo, "
                "its name is forgotten.",
                "{count} named faces were on photos edited since: other photos, "
                "their names are forgotten.",
                tally.dropped,
            ).format(count=tally.dropped)
        )
