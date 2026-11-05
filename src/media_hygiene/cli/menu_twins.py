"""The fast paths of the catalog and their visual twin (0593, inventory of 0524).

A fast path acts on files it does not show; it stays, for large collections. Each says
so in one line, added to its text, and names the page that shows the files first: the
home page offers that page before running the step.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Final

from media_hygiene.i18n import _

if TYPE_CHECKING:
    from collections.abc import Mapping

    from media_hygiene.cli.menu_entry import Step


REPORTS_PAGE: Final = "/console/reports/"  # `step_watch.SERVED_HERE`: a test holds it


@dataclass(frozen=True, slots=True)
class Twin:
    """What a fast path skips, and what shows it first: a step, or a page."""

    says: str  # translated
    step: str = ""  # the step that shows the files
    page: str = ""  # or the page, when no step of the home page opens it


def twins() -> Mapping[str, Twin]:
    """The twin of each fast path, in the language in use.

    Returns:
        By step name.
    """
    report = REPORTS_PAGE
    return {
        "clean": Twin(
            _("Moves the copies without showing them: the report shows them first."),
            page=report,
        ),
        "clean-delete": Twin(
            _("Erases the copies without showing them: the report shows them first."),
            page=report,
        ),
        "sort": Twin(
            _(
                "Moves every file of the plan without showing it: the classify "
                "report shows them first."
            ),
            page=report,
        ),
        "undo": Twin(
            _(
                "Puts a whole run back without showing it: the quarantine's page "
                "shows the photos first."
            ),
            step="undo-pick",
        ),
        "purge": Twin(
            _(
                "Erases without showing the files: the quarantine's page shows the "
                "photos first."
            ),
            step="undo-pick",
        ),
        "import": Twin(
            _("Copies without showing the files: the page shows them first."),
            step="import-pick",
        ),
        "import-folder": Twin(
            _("Copies without showing the files: the page shows them first."),
            step="import-folder-pick",
        ),
        "upkeep": Twin(
            _(
                "Chains the steps without showing the files; each names its page "
                "before it runs, the report shows them first."
            ),
            page=report,
        ),
    }


def with_twin_lines(steps: tuple[Step, ...]) -> tuple[Step, ...]:
    """Add to each fast path's text the line saying what it skips.

    Args:
        steps: The actions.

    Returns:
        The same actions, in order.
    """
    known = twins()
    return tuple(
        replace(step, text=f"{step.text} {known[step.name].says}")
        if step.name in known
        else step
        for step in steps
    )
