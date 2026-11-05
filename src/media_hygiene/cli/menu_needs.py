"""What an action needs before it can run, said as the reason it cannot yet.

Read by the `mh menu` lines (no number, "nothing to do yet") and by the home page
(the button off, the reason in its place): computed once, here, never in the page.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.cli.status_step import to_import
from media_hygiene.constants import RunKind
from media_hygiene.i18n import _, ngettext

if TYPE_CHECKING:
    from collections.abc import Callable
    from datetime import datetime

    from media_hygiene.cli.menu_entry import Step
    from media_hygiene.services.status import Status

type Need = Callable[[Status], str | None]


def missing(step: Step, status: Status) -> str | None:
    """Tell why an action cannot run yet.

    Args:
        step: The action.
        status: What the tool folders say.

    Returns:
        The reason, translated; None when it can run.
    """
    need = _needs().get(step.name)
    return need(status) if need else None


def _needs() -> dict[str, Need]:
    """The rule of each action that needs something first.

    Returns:
        By action name.
    """
    audit = _audit_seen
    return {
        "import": _import,
        "import-pick": _import,
        "open": lambda status: (
            None
            if status.analysis.summary is not None
            else _("No report yet: the audit writes one.")
        ),
        "undo": lambda status: None if status.undoable else _("Nothing to undo yet."),
        "purge": lambda status: (
            None if status.quarantine.runs else _("The quarantine is empty.")
        ),
        "review": audit,
        "review-near": audit,
        "review-pairs": audit,
        "review-junk": audit,
        "review-gone": audit,
        "review-intruders": audit,
        "sort": _proposal,
        "clean": clean_finished,
    }


def _audit_seen(status: Status) -> str | None:
    """A review needs an audit first.

    Args:
        status: What the tool folders say.

    Returns:
        The reason, or None.
    """
    return None if status.analysis.seen else _("The audit must run first.")


def _import(status: Status) -> str | None:
    """Something to get back: files only a backup holds, not imported since.

    Args:
        status: What the tool folders say.

    Returns:
        The reason, or None.
    """
    if to_import(status):
        return None
    summary = status.analysis.summary
    if summary is None or not (summary.backup_only or status.imported):
        return _("Plug in your NAS or an old disk first, then audit.")
    return _("Nothing to get back: the PC already has what the NAS keeps.")


def _day(moment: datetime) -> str:
    """Write a moment's day, in local time.

    Args:
        moment: An aware moment.

    Returns:
        E.g. `2026-10-30`.
    """
    return moment.astimezone().strftime("%Y-%m-%d")


def clean_finished(status: Status) -> str | None:
    """Nothing left to set aside since the last audit or clean, no review pending.

    The one rule of the ✅ (`menu_steps`), of the button off and of its reason.

    Args:
        status: What the tool folders say.

    Returns:
        The reason, dated; None when `clean` has something to do (or no audit yet).
    """
    summary, review = status.analysis.summary, status.review
    if summary is None or not summary.nothing_to_clean:
        return None
    if review.shots_set_aside or review.near_groups:
        return None
    day = _day(summary.created_at)
    if summary.kind is RunKind.CLEAN:
        return _(
            "Nothing to set aside since the clean of {date}: "
            "audit again after adding photos."
        ).format(date=day)
    return _(
        "Nothing to set aside since the audit of {date}: "
        "audit again after adding photos."
    ).format(date=day)


def _proposal(status: Status) -> str | None:
    """A classify proposal waiting to be applied.

    Args:
        status: What the tool folders say.

    Returns:
        The reason, or None.
    """
    if status.sort.proposed is None:
        return _("No proposal to apply: ask classify for one first.")
    sort = status.sort
    if sort.sorted and sort.applied is not None and sort.proposed is not None:
        return ngettext(
            "Already done: the proposal of {proposed} was applied on {applied} "
            "({count} file moved).",
            "Already done: the proposal of {proposed} was applied on {applied} "
            "({count} files moved).",
            sort.moved,
        ).format(
            proposed=_day(sort.proposed),
            applied=_day(sort.applied),
            count=sort.moved,
        )
    return None
