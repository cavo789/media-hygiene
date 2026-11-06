"""The photos `review --junk` decided earlier and its thresholds no longer list (0636).

A choice made by hand never disappears by itself: a photo set aside or kept stays
listed, with its decision, when its reason was turned off. A photo that changed since,
is gone, became protected or joined a burst series or near duplicates is another matter:
its decision is dropped.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.errors import DecisionsError
from media_hygiene.plan.unwanted import UnwantedPhoto
from media_hygiene.review.unwanted_file import entry_key
from media_hygiene.services.policy import keep_policy
from media_hygiene.services.review_file import resume_decisions

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.plan.models import AuditFindings
    from media_hygiene.report.decisions import DecisionsFile
    from media_hygiene.services.runtime import Runtime


def never_listed(runtime: Runtime, findings: AuditFindings) -> frozenset[Path]:
    """Name the photos the review leaves out, whatever the thresholds.

    Args:
        runtime: Settings, mount points and output.
        findings: The audit just run.

    Returns:
        Those of protected folders, the burst shots, the near duplicates.
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
    return frozenset(excluded)


def decided_earlier(
    runtime: Runtime, findings: AuditFindings, base: DecisionsFile
) -> tuple[UnwantedPhoto, ...]:
    """Find the photos of a decisions file the review may still list.

    Args:
        runtime: Settings, mount points and output.
        findings: The audit just run.
        base: What the decisions file holds.

    Returns:
        Each one with the reason it was decided under, in the file's order.
    """
    excluded = never_listed(runtime, findings)
    mapper = runtime.mapper
    files = {
        (mapper.to_host(file.path), file.size, file.mtime_ns): file
        for file in findings.similar.images
        if file.path not in excluded
    }
    return tuple(
        UnwantedPhoto(files[key], entry.reason)
        for entry in base.unwanted
        if (key := entry_key(entry)) in files
    )


def any_decided(runtime: Runtime, findings: AuditFindings, target: Path) -> bool:
    """Tell whether a decisions file holds a photo the review would show.

    Args:
        runtime: Settings, mount points and output.
        findings: The audit just run.
        target: The decisions file, in the container.

    Returns:
        True when it does; False without a usable file, nothing to resume there.
    """
    try:
        base = resume_decisions(runtime, findings, target)
    except DecisionsError:
        return False
    return bool(decided_earlier(runtime, findings, base))
