"""Every review page that records choices for `clean --decisions` offers *Apply now*.

The pages come from the registry the home page serves (`REVIEWS`) and from the
`serve_*` functions of the services that build a `ReviewPage`: a new page that
forgets its `ApplyOffer`, or the shared `apply_now` template in its bar, fails here.
"""

from __future__ import annotations

import inspect
import re
from pathlib import Path
from typing import TYPE_CHECKING, Final

import pytest

from media_hygiene.services import (
    gone_reviewing,
    intruders_reviewing,
    near_reviewing,
    pairs_reviewing,
    reviewing,
    unwanted_reviewing,
)
from media_hygiene.services.review_kinds import REVIEWS, ReviewKind

if TYPE_CHECKING:
    from collections.abc import Callable
    from types import ModuleType

_TEMPLATES: Final = Path(reviewing.__file__).parent.parent / "review" / "templates"
_INCLUDE: Final = re.compile(r'{%\s*(?:include|extends)\s+"([^"]+)"')
_APPLY: Final = "apply_now.html.j2"
_HIDDEN: Final = "_PAGE_TEMPLATE"  # the intruders service keeps its template private
# The services serving a page that writes the decisions file, outside the registry.
_SERVICES: Final[tuple[ModuleType, ...]] = (
    gone_reviewing,
    intruders_reviewing,
    near_reviewing,
    pairs_reviewing,
    reviewing,
    unwanted_reviewing,
)


def _reaches_apply(name: str, seen: set[str]) -> bool:
    """Whether a template, or one it includes or extends, holds `apply_now`.

    Args:
        name: The template's file name.
        seen: The templates already read.

    Returns:
        True when `apply_now.html.j2` is reached.
    """
    if name == _APPLY:
        return True
    if name in seen or not (_TEMPLATES / name).is_file():
        return False
    seen.add(name)
    text = (_TEMPLATES / name).read_text(encoding="utf-8")
    return any(_reaches_apply(found, seen) for found in _INCLUDE.findall(text))


def _page_template(module: ModuleType) -> str:
    """The template a review service serves.

    Args:
        module: The service.

    Returns:
        Its `PAGE_TEMPLATE` (or `_PAGE_TEMPLATE`).
    """
    found = getattr(module, "PAGE_TEMPLATE", None) or getattr(module, _HIDDEN)
    assert isinstance(found, str)
    return found


@pytest.mark.parametrize("kind", REVIEWS, ids=lambda kind: str(kind.page))
def test_every_registered_review_builds_an_apply_offer(kind: ReviewKind) -> None:
    """Each review of the registry passes an `ApplyOffer` to its page."""
    build: Callable[..., object] = kind.opened
    assert "ApplyOffer(" in inspect.getsource(build)


@pytest.mark.parametrize("module", _SERVICES, ids=lambda module: module.__name__)
def test_every_review_service_offers_apply(module: ModuleType) -> None:
    """Each service serving a `ReviewPage` gives it an offer and the shared bar."""
    source = inspect.getsource(module)
    if "ReviewPage(" in source:
        assert "ApplyOffer(" in source
    assert _reaches_apply(_page_template(module), set())


def test_the_registry_is_covered() -> None:
    """The registry's pages are all served by a service listed here."""
    templates = {_page_template(module) for module in _SERVICES}
    assert {"gone_review.html.j2", "review.html.j2"} <= templates
    assert len(REVIEWS) >= len(templates) - 1  # the intruders are served alone
