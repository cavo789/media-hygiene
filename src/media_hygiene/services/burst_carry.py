"""The burst series seen before a clean stay seen: carried over from the archive.

`clean --decisions` archives the decisions file it applied (`decisions_archive`): the
next `review` would list again every series still in the audit, those kept whole
included. A series seen in the archive whose kept shots are now exactly a series of
the audit (kept whole, or what is left once the shots set aside went to quarantine)
is carried over as seen, every shot kept. A series that changed since (a shot added,
or back from the quarantine after an `undo`) is listed again.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.errors import DecisionsError
from media_hygiene.i18n import ngettext
from media_hygiene.report.burst_decisions import BurstDecision, BurstStatus
from media_hygiene.report.decisions import read_decisions
from media_hygiene.services.decisions_archive import newest_archive
from media_hygiene.services.review_file import resume_decisions

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.plan.models import AuditFindings
    from media_hygiene.report.decisions import DecisionsFile
    from media_hygiene.services.runtime import Runtime


def resume_bursts(
    runtime: Runtime, findings: AuditFindings, target: Path
) -> DecisionsFile:
    """Read the decisions file a burst review resumes, with the series seen before.

    Args:
        runtime: Settings, mount points and output.
        findings: The audit just run.
        target: The decisions file, in the container.

    Returns:
        What the file holds, plus the series of the newest archive still the same.

    Raises:
        DecisionsError: The file is not a decisions file, or was made on other
            folders.
    """
    base = resume_decisions(runtime, findings, target)
    seen = {
        shot
        for decision in base.bursts
        if decision.status is BurstStatus.DONE
        for shot in (*decision.kept, *decision.discarded)
    }
    carried = tuple(
        decision
        for decision in _still_series(runtime, findings, _archived(target, base))
        if seen.isdisjoint(decision.kept)
    )
    if not carried:
        return base
    shots = {shot for decision in carried for shot in decision.kept}
    listed = tuple(
        decision
        for decision in base.bursts
        if decision.status is BurstStatus.DONE or shots.isdisjoint(decision.kept)
    )
    message = ngettext(
        "{count} burst series seen before the last clean stays seen.",
        "{count} burst series seen before the last clean stay seen.",
        len(carried),
    )
    runtime.output.info(message.format(count=len(carried)))
    return base.model_copy(update={"bursts": (*listed, *carried)})


def _archived(target: Path, base: DecisionsFile) -> tuple[BurstDecision, ...]:
    """Read the series seen in the newest archive of the decisions file.

    Args:
        target: The decisions file, in the container.
        base: What the decisions file holds: the archive must share its folders.

    Returns:
        The series seen; none without a readable archive made on the same folders.
    """
    archive = newest_archive(target)
    if archive is None:
        return ()
    try:
        applied = read_decisions(archive)
    except DecisionsError:
        return ()
    if sorted(applied.roots) != sorted(base.roots):
        return ()
    return tuple(d for d in applied.bursts if d.status is BurstStatus.DONE)


def _still_series(
    runtime: Runtime, findings: AuditFindings, archived: tuple[BurstDecision, ...]
) -> tuple[BurstDecision, ...]:
    """Keep the series seen whose kept shots are exactly a series of the audit.

    Args:
        runtime: Settings, mount points and output.
        findings: The audit just run.
        archived: The series seen, from the archive.

    Returns:
        Those series, seen and kept whole.
    """
    mapper = runtime.mapper
    series = {
        frozenset(mapper.to_host(shot.path) for shot in burst.shots)
        for burst in findings.similar.bursts
    }
    return tuple(
        BurstDecision(kept=decision.kept)
        for decision in archived
        if frozenset(decision.kept) in series
    )
