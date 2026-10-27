"""`media-hygiene review --junk`: list the photos most likely unwanted, serve the page.

Same server, same decisions file as the other reviews. Nothing is set aside until the
user says so; `clean --decisions` then moves what was set aside to the quarantine.
"""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING, Final

from media_hygiene.classify.models import MediaInput
from media_hygiene.classify.rules.matchers import is_screenshot
from media_hygiene.plan.unwanted import (
    Flat,
    UnwantedLimits,
    UnwantedSource,
    unwanted_photos,
)
from media_hygiene.review.apply_api import ApplyOffer
from media_hygiene.review.place import decisions_place
from media_hygiene.review.unwanted_app import (
    JUNK_DECIDE_PATH,
    JUNK_FILE_PATH,
    UnwantedApp,
)
from media_hygiene.review.unwanted_session import UnwantedPages, UnwantedSession
from media_hygiene.review.unwanted_views import UnwantedStateBuilder
from media_hygiene.services.policy import keep_policy
from media_hygiene.services.review_file import first_save, resume_decisions
from media_hygiene.services.review_serving import ReviewPage, serve_review_page

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.config.review_settings import UnwantedSettings
    from media_hygiene.plan.models import AuditFindings
    from media_hygiene.plan.unwanted import UnwantedPhoto
    from media_hygiene.review.apply_api import ReviewStart
    from media_hygiene.scan.models import MediaFile
    from media_hygiene.services.runtime import Runtime

_PAGE_TEMPLATE: Final = "unwanted_review.html.j2"


def unwanted_limits(settings: UnwantedSettings) -> UnwantedLimits:
    """Read the thresholds of `[review.unwanted]`.

    Args:
        settings: The section.

    Returns:
        The limits.
    """
    return UnwantedLimits(
        tiny_megapixels=settings.tiny_megapixels,
        screenshots=settings.screenshots,
        dark=Flat(settings.dark_mean, settings.dark_share),
        white=Flat(settings.white_mean, settings.white_share),
        blur_percentile=settings.blur_percentile,
    )


def audit_unwanted(
    runtime: Runtime, findings: AuditFindings
) -> tuple[UnwantedPhoto, ...]:
    """The photos of an audit most likely unwanted, by the settings of the run.

    Never a photo of a protected folder, a burst shot, nor a near duplicate.

    Args:
        runtime: Settings, mount points and output.
        findings: The audit just run.

    Returns:
        The photos, the reason with the most photos first.
    """
    similar = findings.similar
    policy = keep_policy(runtime.settings, runtime.mapper)
    groups = (*similar.near, *similar.videos)
    excluded = {file.path for series in similar.bursts for file in series.shots}
    excluded |= {
        file.path
        for group in groups
        for file in (group.keeper, *group.removable, *group.protected)
    }
    excluded |= {file.path for file in similar.images if policy.is_protected(file)}
    source = UnwantedSource(
        similar.images, similar.visuals, similar.metadata, frozenset(excluded)
    )

    def screenshot(file: MediaFile) -> bool:
        """`classify`'s test, on what the audit knows of the file.

        Args:
            file: The photo.

        Returns:
            True for a screenshot or a document.
        """
        known = MediaInput(
            file.path,
            file.path.parent,
            file.size,
            file.mtime_ns,
            visual=similar.visuals.get(file.path),
            metadata=similar.metadata.get(file.path),
        )
        return is_screenshot(known)

    limits = unwanted_limits(runtime.settings.review.unwanted)
    return unwanted_photos(source, limits, screenshot)


def open_unwanted_review(
    runtime: Runtime, findings: AuditFindings, target: Path
) -> UnwantedSession:
    """Start the review of the photos most likely unwanted, resuming the file.

    Args:
        runtime: Settings, mount points and output.
        findings: The audit just run.
        target: The decisions file, in the container.

    Returns:
        The session, saved once: decisions about photos no longer listed are dropped.

    Raises:
        DecisionsError: The file is not a decisions file, was made on other
            folders, or cannot be written.
    """
    mapper = runtime.mapper
    builder = UnwantedStateBuilder(mapper, findings.similar.visuals)
    place = decisions_place(mapper, runtime.locations.reports_dir, target)
    base = resume_decisions(runtime, findings, target)
    pages = UnwantedPages(audit_unwanted(runtime, findings), builder, target, place)
    session = UnwantedSession(pages, base)
    first_save(session.save)
    return session


def serve_unwanted_review(
    runtime: Runtime, session: UnwantedSession, start: ReviewStart
) -> int:
    """Serve the page until Ctrl+C; every decision is saved as it is made.

    Args:
        runtime: Settings, mount points and output.
        session: The review.
        start: The port to listen on, inside the container (0: any free one), and
            the step *Apply now* ends on.

    Returns:
        `STEP_EXIT_BASE + n` when *Apply now* chose step `n`; 0 otherwise.
    """
    api = (JUNK_DECIDE_PATH, JUNK_FILE_PATH)
    # Only the photos set aside move: a photo kept leaves nothing to apply.
    offer = ApplyOffer(start.apply, lambda: session.decided[1] > 0)
    page = ReviewPage(
        _PAGE_TEMPLATE, session.place, api, partial(UnwantedApp, session), offer
    )
    return serve_review_page(runtime, page, start.port)
