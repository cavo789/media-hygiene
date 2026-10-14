"""The progress steps of the integrity pass, as the user reads them."""

from __future__ import annotations

from media_hygiene.i18n import _
from media_hygiene.scan.progress import Step


def check_step() -> Step:
    """The progress step of the full checks.

    Returns:
        Its translated title and explanation.
    """
    return Step(
        _("Checking that files can be read"),
        _(
            "Finds broken files: empty (0 bytes), images and RAW files that cannot "
            "be decoded, videos that cannot be opened."
        ),
    )


def metadata_step() -> Step:
    """The progress step of the one-time metadata reading, after an update.

    Returns:
        Its translated title and explanation.
    """
    return Step(
        _("Reading the metadata of files already in the cache"),
        _(
            "Once, after an update: dates, places and devices recorded in the files. "
            "Images are not decoded again, only their header is read."
        ),
    )
