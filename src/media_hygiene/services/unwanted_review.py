"""`clean --decisions`: the photos set aside in `review --junk`, checked first.

Only the photos set aside (`aside`) move; those kept stay in the file for the review to
resume. None may lie in a protected folder: that refuses the whole file. A photo
changed or gone since is not refused here: the clean leaves it and says so.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.i18n import ngettext
from media_hygiene.services.chosen_review import named_files

if TYPE_CHECKING:
    from media_hygiene.report.unwanted_decisions import UnwantedEntry
    from media_hygiene.scan.models import MediaFile
    from media_hygiene.services.runtime import Runtime


def unwanted_files(
    runtime: Runtime, entries: tuple[UnwantedEntry, ...]
) -> tuple[MediaFile, ...]:
    """Translate the photos set aside in `review --junk` into files of the container.

    Args:
        runtime: Settings, mount points and output.
        entries: The `unwanted` key of the decisions file.

    Returns:
        The photos set aside, as the audit saw them (size, modification time).

    Raises:
        DecisionsError: One of them lies in a protected folder.
    """
    files = named_files(runtime, [entry for entry in entries if entry.aside])
    if files:
        said = ngettext(
            "Your decisions — {count} unwanted photo set aside in 'review --junk'.",
            "Your decisions — {count} unwanted photos set aside in 'review --junk'.",
            len(files),
        )
        runtime.output.info(said.format(count=len(files)))
    return files
