"""The one step that comes next, chosen once for `status` and the `mh` menu alike."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

from media_hygiene.cli.review_options import PAGE_PORT
from media_hygiene.cli.status_view import days_since
from media_hygiene.constants import RunKind
from media_hygiene.i18n import _
from media_hygiene.review.place import DEFAULT_DECISIONS, decisions_flag
from media_hygiene.services.next_command import CHANGING

if TYPE_CHECKING:
    from media_hygiene.paths.mount_kind import MountKind
    from media_hygiene.services.status import Status


class Slot(StrEnum):
    """Which step of the guide a proposal stands for: a line of the menu."""

    AUDIT = "audit"
    CLEAN = "clean"
    REVIEW = "review"
    APPLY = "apply"  # clean --decisions: the review applied
    UNDO = "undo"
    PURGE = "purge"
    CLASSIFY = "classify"
    SORT = "sort"
    PEOPLE = "people"
    TAGS = "tags"


@dataclass(frozen=True, slots=True)
class NextStep:
    """The step left to do first: why, and the command, without the global options."""

    slot: Slot
    text: str  # translated, in lower case after the label
    command: str  # e.g. `purge 20261015-101010`
    needs: tuple[MountKind, ...] = ()
    port: int | None = None


def next_step(status: Status, purge_hint_days: int) -> NextStep | None:
    """Choose the step: the first thing left, in the order of the guide.

    Args:
        status: What the tool folders say.
        purge_hint_days: The age from which a quarantine is worth purging first.

    Returns:
        The step, or None when nothing is left.
    """
    summary, review = status.analysis.summary, status.review
    if status.blank:
        return NextStep(
            Slot.AUDIT, _("start with an audit: it changes nothing."), "audit"
        )
    if summary and summary.kind is RunKind.AUDIT and summary.duplicate_files:
        text = _("the last audit found extra copies: 'clean' sets them aside.")
        return NextStep(Slot.CLEAN, text, "clean", CHANGING)
    if review.bursts_to_see:
        text = _("finish the burst review where you stopped.")
        return NextStep(Slot.REVIEW, text, "review", port=PAGE_PORT)
    if review.shots_set_aside or review.near_groups:
        tier = "--tier near " if review.near_groups else ""
        text = _("apply your review: the files you set aside go to the quarantine.")
        command = f"clean {tier}{decisions_flag(DEFAULT_DECISIONS)}"
        return NextStep(Slot.APPLY, text, command, CHANGING)
    return _quarantine_or_sort(status, purge_hint_days)


def _quarantine_or_sort(status: Status, purge_hint_days: int) -> NextStep | None:
    """An old quarantine first, then a proposal not sorted, then a recent quarantine.

    Args:
        status: What the tool folders say.
        purge_hint_days: The age from which a quarantine is worth purging first.

    Returns:
        The step, or None when nothing is left.
    """
    runs = status.quarantine.runs
    old = [run for run in runs if days_since(run.started) >= purge_hint_days]
    if old:
        run_id = old[-1].run_id
        text = _(
            "the quarantine of {run_id} is more than {days} days old: once checked, "
            "'purge' frees its space."
        ).format(run_id=run_id, days=purge_hint_days)
        return NextStep(Slot.PURGE, text, f"purge {run_id}", CHANGING)
    if status.sort.proposed is not None and not status.sort.sorted:
        text = _("the classify proposal waits: 'sort' applies the edited workbook.")
        return NextStep(Slot.SORT, text, "sort", CHANGING)
    if runs:
        text = _("once you have checked the quarantine, 'purge' frees its space.")
        return NextStep(Slot.PURGE, text, f"purge {runs[0].run_id}", CHANGING)
    return None
