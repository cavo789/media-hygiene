"""After an import: the burst series holding a new file, the only ones reviewed (0480).

The page opens on what the phone just brought, not on the library's older series:
a series counts when one of its shots is a new file.
"""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from collections.abc import Collection
    from pathlib import Path

    from media_hygiene.plan.models import AuditFindings

# An import's series are decided in their own file: the library's choices stay as
# they are; `mh` applies it with `clean --decisions` once the page is done.
IMPORT_DECISIONS: Final = "import-bursts.json"


def import_bursts(findings: AuditFindings, new: Collection[Path]) -> AuditFindings:
    """The audit's findings, their burst series cut to those of the import.

    Args:
        findings: The audit's findings.
        new: The files the import copied (container paths).

    Returns:
        The same findings, keeping only the series with a new shot.
    """
    chosen = frozenset(new)
    bursts = tuple(
        series
        for series in findings.similar.bursts
        if any(shot.path in chosen for shot in series.shots)
    )
    return replace(findings, similar=replace(findings.similar, bursts=bursts))
