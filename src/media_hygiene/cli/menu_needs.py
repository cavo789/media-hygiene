"""What an action needs before it can run, said as the reason it cannot yet.

Read by the `mh menu` lines (no number, "nothing to do yet") and by the home page
(the button off, the reason in its place): computed once, here, never in the page.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.cli.status_step import to_import
from media_hygiene.i18n import _

if TYPE_CHECKING:
    from collections.abc import Callable

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
        "review-sort": _proposal,
        "sort": _proposal,
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


def _proposal(status: Status) -> str | None:
    """A classify proposal waiting to be applied.

    Args:
        status: What the tool folders say.

    Returns:
        The reason, or None.
    """
    if status.sort.proposed is None:
        return _("No proposal to apply: ask classify for one first.")
    if status.sort.sorted:
        return _("Already sorted as the workbook says.")
    return None
