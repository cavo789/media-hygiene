"""The reviews the home server serves itself, each under its own prefix (0357, 0417).

Each kind says where it is served, what it says when there is nothing to review, and
how its page is opened from an audit just run, as `review` typed with its option does
(`cli/review_modes`): its session resumed from the decisions file, its app, and what
*Apply now* checks (None: no button).
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import partial
from typing import TYPE_CHECKING, Final

from media_hygiene.i18n import _
from media_hygiene.review.app import DECIDE_PATH, FILE_PATH, ReviewApp
from media_hygiene.review.apply_api import ApplyOffer
from media_hygiene.review.gone_app import GONE_DECIDE_PATH, GONE_FILE_PATH, GoneApp
from media_hygiene.review.near_app import NEAR_DECIDE_PATH, NEAR_FILE_PATH, NearApp
from media_hygiene.review.pairs_app import PAIRS_DECIDE_PATH, PAIRS_FILE_PATH, PairsApp
from media_hygiene.review.step_watch import (
    BURSTS_PAGE,
    GONE_PAGE,
    JUNK_PAGE,
    NEAR_REVIEW_PAGE,
    PAIRS_PAGE,
)
from media_hygiene.review.unwanted_app import (
    JUNK_DECIDE_PATH,
    JUNK_FILE_PATH,
    UnwantedApp,
)
from media_hygiene.services import (
    gone_reviewing,
    near_reviewing,
    pairs_reviewing,
    reviewing,
    unwanted_reviewing,
)
from media_hygiene.services.albums import album_desk
from media_hygiene.services.review_serving import ReviewPage
from media_hygiene.share.album_pickers import KeyPicker

if TYPE_CHECKING:
    from collections.abc import Callable
    from concurrent.futures import Executor
    from pathlib import Path

    from media_hygiene.plan.models import AuditFindings
    from media_hygiene.review.local_app import LocalApp
    from media_hygiene.services.runtime import Runtime

type Opening = Callable[[Runtime, AuditFindings, Path], ReviewPage | None]


@dataclass(frozen=True, slots=True)
class ReviewKind:
    """A review served by the home server."""

    page: str  # e.g. `/review/near/`
    empty: Callable[[], str]  # what it says when there is nothing to review
    opened: Opening


def _near(runtime: Runtime, findings: AuditFindings, target: Path) -> ReviewPage | None:
    """`review --near`.

    Args:
        runtime: Settings, mount points and output.
        findings: The audit just run.
        target: The decisions file.

    Returns:
        Its page; None without near duplicates.
    """
    if not findings.similar.groups:
        return None
    session = near_reviewing.open_near_review(runtime, findings, target)
    offer = ApplyOffer(None, lambda: session.decided[0] > 0)
    api = (NEAR_DECIDE_PATH, NEAR_FILE_PATH)
    app = partial(NearApp, session)
    return ReviewPage(near_reviewing.PAGE_TEMPLATE, session.place, api, app, offer)


def _pairs(
    runtime: Runtime, findings: AuditFindings, target: Path
) -> ReviewPage | None:
    """`review --pairs`.

    Args:
        runtime: Settings, mount points and output.
        findings: The audit just run.
        target: The decisions file.

    Returns:
        Its page; None without folder pairs.
    """
    if not findings.plan.decisions:
        return None
    session = pairs_reviewing.open_pairs_review(runtime, findings, target)
    offer = ApplyOffer(None, lambda: session.decided[0] > 0)
    api = (PAIRS_DECIDE_PATH, PAIRS_FILE_PATH)
    app = partial(PairsApp, session)
    return ReviewPage(pairs_reviewing.PAGE_TEMPLATE, session.place, api, app, offer)


def _junk(runtime: Runtime, findings: AuditFindings, target: Path) -> ReviewPage | None:
    """`review --junk`.

    Args:
        runtime: Settings, mount points and output.
        findings: The audit just run.
        target: The decisions file.

    Returns:
        Its page; None when no photo looks unwanted.
    """
    if not unwanted_reviewing.audit_unwanted(runtime, findings):
        return None
    session = unwanted_reviewing.open_unwanted_review(runtime, findings, target)
    offer = ApplyOffer(None, lambda: session.decided[1] > 0)  # set aside only
    api = (JUNK_DECIDE_PATH, JUNK_FILE_PATH)
    app = partial(UnwantedApp, session)
    template = unwanted_reviewing.PAGE_TEMPLATE
    return ReviewPage(template, session.place, api, app, offer)


def _gone(runtime: Runtime, findings: AuditFindings, target: Path) -> ReviewPage | None:
    """`review --gone`: answers only, nothing to apply.

    Args:
        runtime: Settings, mount points and output.
        findings: The audit just run.
        target: The decisions file.

    Returns:
        Its page; None when no file is gone.
    """
    if not gone_reviewing.files_gone(runtime):
        return None
    session = gone_reviewing.open_gone_review(runtime, findings, target)
    api = (GONE_DECIDE_PATH, GONE_FILE_PATH)
    app = partial(GoneApp, session)
    return ReviewPage(gone_reviewing.PAGE_TEMPLATE, session.place, api, app)


def _bursts(
    runtime: Runtime, findings: AuditFindings, target: Path
) -> ReviewPage | None:
    """`review`: the burst series, their albums too.

    Args:
        runtime: Settings, mount points and output.
        findings: The audit just run.
        target: The decisions file.

    Returns:
        Its page; None without burst series.
    """
    if not findings.similar.bursts:
        return None
    session = reviewing.open_review(runtime, findings, target)
    albums = album_desk(runtime, KeyPicker(session.preview_source).files)

    def app(page: bytes, executor: Executor, previews: Path | None) -> LocalApp:
        """The burst review's app, with its albums.

        Args:
            page: The page.
            executor: The worker pool.
            previews: The previews' cache folder.

        Returns:
            The app.
        """
        return ReviewApp(session, page, executor, previews, albums)

    offer = ApplyOffer(None, lambda: session.progress[1] > 0)
    api = (DECIDE_PATH, FILE_PATH)
    return ReviewPage(reviewing.PAGE_TEMPLATE, session.place, api, app, offer)


REVIEWS: Final = (
    ReviewKind(
        NEAR_REVIEW_PAGE, lambda: _("No near duplicates: nothing to review."), _near
    ),
    ReviewKind(PAIRS_PAGE, lambda: _("No folder pairs: nothing to review."), _pairs),
    ReviewKind(
        JUNK_PAGE,
        lambda: _("No photo looks unwanted: nothing to review."),
        _junk,
    ),
    ReviewKind(
        GONE_PAGE,
        lambda: _("No photo nor video has disappeared: nothing to review."),
        _gone,
    ),
    ReviewKind(BURSTS_PAGE, lambda: _("No burst series: nothing to review."), _bursts),
)
