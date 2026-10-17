"""The files the disk or the cloud could not read during the audit, on the screen.

They are not broken: nothing about them is stored, `clean` leaves them, and the next
audit reads them again. The first few are named; the HTML report lists them all.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from rich.markup import escape

from media_hygiene.console.formatting import human_number
from media_hygiene.i18n import _, ngettext

if TYPE_CHECKING:
    from collections.abc import Sequence

    from media_hygiene.scan.read_errors import UnreadFile
    from media_hygiene.services.runtime import Runtime

# Files named, one per line, before the line saying how many more there are.
SHOWN_FIRST: Final = 5


def show_unread(runtime: Runtime, unread: Sequence[UnreadFile]) -> None:
    """Say how many files could not be read this time, and name the first ones.

    Args:
        runtime: Settings, mount points and output.
        unread: The files, sorted by path.
    """
    if not unread:
        return
    output = runtime.output
    output.warning(
        ngettext(
            "{count} file could not be read this time (disk, network or cloud): "
            "not marked broken, left alone by clean, read again at the next audit.",
            "{count} files could not be read this time (disk, network or cloud): "
            "not marked broken, left alone by clean, read again at the next audit.",
            len(unread),
        ).format(count=human_number(len(unread)))
    )
    for item in unread[:SHOWN_FIRST]:
        output.info(f"  {escape(str(runtime.mapper.to_host(item.file.path)))}")
    hidden = len(unread) - SHOWN_FIRST
    if hidden > 0:
        output.info(
            _("  … and {count} more: the HTML report lists them all.").format(
                count=human_number(hidden)
            )
        )
