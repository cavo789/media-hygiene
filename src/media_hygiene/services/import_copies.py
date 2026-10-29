"""After an import: the exact copies among the new files set aside (0478).

The same photo twice (sent by WhatsApp, then copied again) or a photo the library
already holds: the new file goes to the quarantine through `clean`'s own path (the
write-ahead journal, the byte compare, `mh undo` puts it back). Only new files are
ever set aside: a group whose kept copy would be a new file while an older one lies
in the library keeps the older one, the new one goes.
"""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

from media_hygiene.config.import_settings import ImportStep
from media_hygiene.errors import MountError
from media_hygiene.i18n import _
from media_hygiene.plan.models import CleanPlan
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.audit import AuditService
from media_hygiene.services.clean import CleanService

if TYPE_CHECKING:
    from collections.abc import Collection
    from pathlib import Path

    from media_hygiene.plan.keep_decision import KeepDecision
    from media_hygiene.services.runtime import Runtime


def import_copies(plan: CleanPlan, new: Collection[Path]) -> CleanPlan:
    """The plan of an audit, cut to the new files that are exact copies.

    Args:
        plan: The audit's plan.
        new: The files the import copied (container paths).

    Returns:
        A plan that only sets new files aside, each group keeping one copy.
    """
    decisions = tuple(
        kept for decision in plan.decisions if (kept := _new_only(decision, new))
    )
    return CleanPlan(decisions=decisions, broken=())


def _new_only(decision: KeepDecision, new: Collection[Path]) -> KeepDecision | None:
    """One duplicate group, cut to its new files.

    Args:
        decision: The group as the keep policy decided it.
        new: The files the import copied.

    Returns:
        The group setting aside its new copies only; None when none goes.
    """
    keeper = decision.keeper
    removable = [file for file in decision.removable if file not in decision.linked]
    if keeper.path in new and not decision.protected:
        older = next((file for file in removable if file.path not in new), None)
        if older is not None:
            removable = [keeper, *(file for file in removable if file is not older)]
            keeper = older
    going = tuple(file for file in removable if file.path in new)
    if not going:
        return None
    return replace(decision, keeper=keeper, removable=going, linked=(), spared=())


def set_aside_copies(runtime: Runtime, new: Collection[Path]) -> int:
    """Audit, then move the new files that are exact copies to the quarantine.

    Args:
        runtime: Settings, mount points and output.
        new: The files the import copied.

    Returns:
        How many were set aside; 0 when cleaning is not possible here (said).
    """
    if not new:
        return 0
    service = CleanService(runtime, NullProgress())
    try:
        service.ensure_ready()
    except MountError as error:
        runtime.output.warning(str(error))
        return 0
    findings = AuditService(runtime, NullProgress()).run()
    plan = import_copies(findings.plan, frozenset(new))
    if plan.is_empty:
        return 0
    _run_id, outcome = service.execute(plan)
    return outcome.quarantined


def tell_done(runtime: Runtime, new: Collection[Path]) -> None:
    """Set the copies aside when `copies` is on, then say what the import did.

    Args:
        runtime: Settings, mount points and output.
        new: The files the import copied.
    """
    aside = 0
    if ImportStep.COPIES in runtime.settings.imports.then:
        aside = set_aside_copies(runtime, new)
    runtime.output.success(
        _("✨ All done: {count} imported, {aside} copies set aside.").format(
            count=len(new), aside=aside
        )
    )
    if aside:
        runtime.output.info(_("↩️ Put them back: mh undo"))
