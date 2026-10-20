"""The lines of `status`: one per part, in the user's words."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Final

from media_hygiene.console.formatting import human_number, human_size
from media_hygiene.constants import RunKind
from media_hygiene.i18n import _, ngettext

if TYPE_CHECKING:
    from media_hygiene.services.status import LastAnalysis, Status
    from media_hygiene.services.status_parts import QuarantineState, ReviewState

_SHOWN_RUNS: Final = 3  # undoable runs listed; the others are counted
_MOMENT: Final = "%Y-%m-%d %H:%M"


def days_since(moment: datetime) -> int:
    """Count the whole days since a moment.

    Args:
        moment: An aware moment.

    Returns:
        Days, 0 for today (or a moment in the future).
    """
    return max((datetime.now(moment.tzinfo) - moment).days, 0)


def when(moment: datetime) -> str:
    """Write a moment in local time, and how long ago it was.

    Args:
        moment: An aware moment.

    Returns:
        E.g. `2026-10-07 14:02 (3 days ago)`.
    """
    return f"{moment.astimezone().strftime(_MOMENT)} ({ago(moment)})"


def ago(moment: datetime) -> str:
    """Say how long ago a moment was, in days.

    Args:
        moment: An aware moment.

    Returns:
        E.g. `today`, `3 days ago`.
    """
    days = days_since(moment)
    if not days:
        return _("today")
    return ngettext("{count} day ago", "{count} days ago", days).format(
        count=human_number(days)
    )


def status_lines(status: Status) -> tuple[str, ...]:
    """Every line of `status`, the parts not mounted said last.

    Args:
        status: What the tool folders say.

    Returns:
        Translated lines.
    """
    lines = [_analysis(status.analysis), _quarantine(status.quarantine)]
    if status.undoable:
        shown = ", ".join(
            f"{run.run_id} ({run.kind.value})" for run in status.undoable[:_SHOWN_RUNS]
        )
        more = len(status.undoable) - _SHOWN_RUNS
        if more > 0:
            shown += " " + _("and {count} more").format(count=human_number(more))
        lines.append(_("Runs you can still undo: {runs}.").format(runs=shown))
    lines += _review(status.review)
    if status.sort.proposed is not None:
        state = _("sorted since.") if status.sort.sorted else _("not sorted yet.")
        lines.append(
            _("Last classify proposal: {when}, {state}").format(
                when=when(status.sort.proposed), state=state
            )
        )
    if status.tagged is not None:
        lines.append(_tags(*status.tagged))
    if status.faces is not None:
        photos, faces = status.faces
        lines.append(
            _("Faces: {faces} found in {photos} photos; 'people' groups them.").format(
                faces=human_number(faces), photos=human_number(photos)
            )
        )
    if status.missing:
        points = ", ".join(f"/{kind.value}" for kind in status.missing)
        lines.append(_("Not looked at (not mounted): {points}.").format(points=points))
    return tuple(lines)


def _analysis(analysis: LastAnalysis) -> str:
    """Say when the last audit or clean ran, and what it found.

    Args:
        analysis: The newest report, or the date the cache knows.

    Returns:
        One line.
    """
    summary = analysis.summary
    if summary is not None:
        label = _("Last clean") if summary.kind is RunKind.CLEAN else _("Last audit")
        figures = _(
            "{files} files, {copies} extra copies ({size}), {broken} broken."
        ).format(
            files=human_number(summary.files_scanned),
            copies=human_number(summary.duplicate_files),
            size=human_size(summary.reclaimable_bytes),
            broken=human_number(summary.broken_files),
        )
        return f"{label}: {when(summary.created_at)} — {figures}"
    if analysis.walked is not None:
        return _("Last audit: {when} (mount /reports to see its figures).").format(
            when=when(analysis.walked)
        )
    return _("No audit yet.")


def _quarantine(quarantine: QuarantineState) -> str:
    """Say what the quarantine holds, and since when.

    Args:
        quarantine: The runs still in the quarantine.

    Returns:
        One line.
    """
    if not quarantine.runs:
        return _("Quarantine: empty.")
    oldest = min(run.started for run in quarantine.runs)
    return ngettext(
        "Quarantine: {files} files, {size}, {count} run, set aside {when}.",
        "Quarantine: {files} files, {size}, {count} runs, the oldest set aside {when}.",
        len(quarantine.runs),
    ).format(
        files=human_number(quarantine.files),
        size=human_size(quarantine.size),
        count=human_number(len(quarantine.runs)),
        when=when(oldest),
    )


def _review(review: ReviewState) -> list[str]:
    """Say what `decisions.json` holds that no clean applied yet.

    Args:
        review: Its counts.

    Returns:
        Zero, one or two lines.
    """
    if review.unreadable:
        return [_("decisions.json cannot be read: 'review' will say why.")]
    lines = []
    if review.bursts_to_see:
        lines.append(
            ngettext(
                "Burst review: {count} series still to see.",
                "Burst review: {count} series still to see.",
                review.bursts_to_see,
            ).format(count=human_number(review.bursts_to_see))
        )
    if review.shots_set_aside or review.near_groups:
        lines.append(
            _(
                "Decided, not applied yet: {shots} shots set aside, {groups} near "
                "duplicate groups."
            ).format(
                shots=human_number(review.shots_set_aside),
                groups=human_number(review.near_groups),
            )
        )
    return lines


def _tags(files: int, seen: int) -> str:
    """Say how many files have words to be found by, and how many the model saw.

    Args:
        files: Files with any tag.
        seen: Files with the words of the vision model.

    Returns:
        One line.
    """
    return _(
        "Tags: {files} files have words, {seen} of them from the vision model; "
        "'search' finds them."
    ).format(files=human_number(files), seen=human_number(seen))
