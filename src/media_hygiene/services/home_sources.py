"""Where the home page's content comes from: the tool folders, and its audit."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

    from media_hygiene.console.page_progress import PageProgress
    from media_hygiene.review.apply_api import ApplyStep
    from media_hygiene.review.home_parts import HomeSample
    from media_hygiene.review.home_views import HomeState
    from media_hygiene.services.home_audit import AuditResult
    from media_hygiene.services.home_tags_models import TagsRunner


@dataclass(frozen=True, slots=True)
class HomeSources:
    """Where the home page's content comes from: the tool folders, and its audit."""

    state: Callable[[], HomeState]
    audit: Callable[[PageProgress], AuditResult]
    apply: Callable[[], ApplyStep | None] | None = None  # browse's *Apply now* (0356)
    runs: Mapping[str, TagsRunner] = field(default_factory=dict)  # by path (0343)
    samples: Callable[[], tuple[HomeSample, ...]] | None = None  # random photos (0485)
