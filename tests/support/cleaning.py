"""A clean as `clean --yes` runs it: audit, then copies to the quarantine."""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.audit import AuditService
from media_hygiene.services.clean import CleanMode, CleanService

if TYPE_CHECKING:
    from media_hygiene.services.runtime import Runtime


def clean(runtime: Runtime) -> str:
    """Audit then clean to the quarantine.

    Args:
        runtime: Settings, mount points and output.

    Returns:
        The run identifier.
    """
    findings = AuditService(runtime, NullProgress()).run()
    service = CleanService(runtime, NullProgress())
    service.ensure_ready(CleanMode())
    run_id, _outcome = service.execute(service.feasible(replace(findings.plan)))
    return run_id
