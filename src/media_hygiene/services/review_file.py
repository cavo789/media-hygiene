"""The decisions file a review opens, and the page that writes it.

Shared by the burst review and `review --near`: both write the same file, resumed when
made on the same folders and saved once as the review opens.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from media_hygiene.errors import DecisionsError
from media_hygiene.i18n import _
from media_hygiene.i18n.templates import translated_environment
from media_hygiene.report.decisions import DecisionsFile, read_decisions
from media_hygiene.review.apply_api import APPLY_PATH
from media_hygiene.review.local_app import STATE_PATH
from media_hygiene.review.page_header import page_header
from media_hygiene.review.place import decisions_flag
from media_hygiene.share.album_api import ALBUMS_PATH

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from media_hygiene.plan.models import AuditFindings
    from media_hygiene.review.place import DecisionsPlace
    from media_hygiene.services.runtime import Runtime

_TEMPLATES_PACKAGE: Final = "media_hygiene.review"


def review_page(template: str, place: DecisionsPlace, api: tuple[str, str]) -> bytes:
    """Render the page of a review.

    Args:
        template: Its template, in `media_hygiene.review`.
        place: The decisions file it writes.
        api: The paths that decide and that read the file back.

    Returns:
        The page.
    """
    environment = translated_environment(_TEMPLATES_PACKAGE, escaped=("html", "j2"))
    decide_path, file_path = api
    header = page_header(template)
    return (
        environment.get_template(template)
        .render(
            header=header,
            # Opened from the home page: *Apply now*, where the page includes it (0288).
            apply_offered=header.home,
            apply_path=APPLY_PATH,
            state_path=STATE_PATH,
            decide_path=decide_path,
            file_path=file_path,
            albums_path=ALBUMS_PATH,  # the pages that add to an album include it
            file=place.argument,
            clean_option=decisions_flag(place.argument),
            place=place.host,
        )
        .encode()
    )


def resume_decisions(
    runtime: Runtime, findings: AuditFindings, target: Path
) -> DecisionsFile:
    """Read the decisions file a review resumes, or start an empty one.

    Args:
        runtime: Settings, mount points and output.
        findings: The audit just run.
        target: The decisions file, in the container.

    Returns:
        What the file holds, made on the folders of this audit.

    Raises:
        DecisionsError: The file is not a decisions file, or was made on other
            folders.
    """
    roots = runtime.mapper.roots_on_host(findings.roots)
    base = (
        read_decisions(target)
        if target.exists()
        else DecisionsFile(version=1, roots=roots)
    )
    if base.only_chosen:  # files chosen in `search` need no audit
        return base.model_copy(update={"roots": roots})
    if sorted(base.roots) != sorted(roots):
        message = _(
            "{path} was made on other folders ({theirs}); this review analyses {ours}."
        )
        raise DecisionsError(
            message.format(
                path=target.name, theirs=", ".join(base.roots), ours=", ".join(roots)
            ),
            _("Name another file with --decisions, or mount the same folders."),
        )
    return base


def first_save(save: Callable[[], None]) -> None:
    """Write the decisions file as a review opens: an unwritable file fails now.

    Args:
        save: Writes the file.

    Raises:
        DecisionsError: The file cannot be written.
    """
    try:
        save()
    except OSError as exc:
        message = _("Cannot save the decisions file: {error}.")
        raise DecisionsError(message.format(error=exc.strerror or exc)) from exc
