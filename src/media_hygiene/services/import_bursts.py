"""After an import: the burst series holding a new file, the only ones reviewed (0480).

The page opens on what the phone just brought, not on the library's older series:
a series counts when one of its shots is a new file.
"""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING, Final

from media_hygiene.services.import_chain import chain_file, read_chain
from media_hygiene.services.import_end import imported

if TYPE_CHECKING:
    from collections.abc import Collection
    from pathlib import Path

    from media_hygiene.plan.models import AuditFindings
    from media_hygiene.services.runtime import Runtime

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


def import_view(
    runtime: Runtime, findings: AuditFindings
) -> tuple[AuditFindings, frozenset[str]] | None:
    """The series of the last chain's import, from the home page (0630).

    Args:
        runtime: Settings and mount points (the chain's file, the journal).
        findings: The audit's findings.

    Returns:
        The findings cut to the import's series, and the host shots of the series
        left out (their decisions stay); None without a chain.
    """
    chain = read_chain(chain_file(runtime))
    if chain is None:
        return None
    new = imported(runtime, chain.folder, chain.since or None)
    shown = import_bursts(findings, new)
    kept = {id(series) for series in shown.similar.bursts}
    hidden = frozenset(
        runtime.mapper.to_host(shot.path)
        for series in findings.similar.bursts
        if id(series) not in kept
        for shot in series.shots
    )
    return shown, hidden
