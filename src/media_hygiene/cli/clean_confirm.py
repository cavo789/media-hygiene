"""The confirmation of `clean`: what goes where, said plainly before anything moves."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from media_hygiene.cli.flows import require_terminal
from media_hygiene.console.formatting import human_number, human_size
from media_hygiene.i18n import _, ngettext

if TYPE_CHECKING:
    from media_hygiene.plan.models import CleanPlan
    from media_hygiene.services.runtime import Runtime


def confirm_clean(runtime: Runtime, plan: CleanPlan, yes: bool) -> bool:  # noqa: FBT001
    """Say what the clean does, then ask, unless `--yes` or `[clean] confirm = false`.

    Args:
        runtime: Settings, mount points and output.
        plan: What would be cleaned.
        yes: `--yes` was given.

    Returns:
        True when the clean may proceed.
    """
    _announce(runtime, plan)
    if yes or not runtime.settings.clean.confirm:
        return True
    require_terminal(sys.stdin)
    return runtime.output.confirm(
        _question(plan).format(
            count=human_number(plan.removable_count),
            size=human_size(plan.reclaimable),
            near=human_number(plan.near_count),
            broken=human_number(len(plan.broken)),
        ),
    )


def _question(plan: CleanPlan) -> str:
    """The question of the confirmation.

    Args:
        plan: What would be cleaned.

    Returns:
        The translated question, its placeholders not filled yet.
    """
    if plan.delete_copies:
        if plan.near_count:
            return _(
                "Delete {count} duplicate copies ({size}), move {near} near duplicates "
                "to the quarantine and handle {broken} broken files?"
            )
        return _(
            "Delete {count} duplicate copies ({size}) and handle {broken} broken files?"
        )
    if plan.near_count:
        return _(
            "Move {count} duplicate copies ({size}) and {near} near duplicates to the "
            "quarantine, and handle {broken} broken files?"
        )
    return _(
        "Move {count} duplicate copies ({size}) to the quarantine and handle "
        "{broken} broken files?"
    )


def _announce(runtime: Runtime, plan: CleanPlan) -> None:
    """Say, in a line or two, what happens to the files: nothing erased, or what.

    Args:
        runtime: Settings, mount points and output.
        plan: What would be cleaned.
    """
    output = runtime.output
    if plan.delete_copies:
        output.warning(
            _(
                "--delete: the copies are deleted for good, after a byte comparison "
                "with the kept copy; 'undo' rebuilds them from it."
            )
        )
        if plan.moved_copies:
            moved = ngettext(
                "{count} copy of another file than a media will be moved to the "
                "quarantine, not deleted.",
                "{count} copies of other files than media will be moved to the "
                "quarantine, not deleted.",
                plan.moved_copies,
            )
            output.info(moved.format(count=human_number(plan.moved_copies)))
    else:
        output.info(
            _(
                "🛟 Nothing is erased: each copy is compared byte for byte with the "
                "kept one, then moved to the quarantine. 'purge' erases it once you "
                "have checked."
            )
        )
    if plan.burst_count:
        bursts = ngettext(
            "{count} burst shot you set aside will be moved to the quarantine.",
            "{count} burst shots you set aside will be moved to the quarantine.",
            plan.burst_count,
        )
        output.info(bursts.format(count=human_number(plan.burst_count)))
    if plan.orphans:
        orphans = ngettext(
            "{count} orphan sidecar (.xmp, .aae, .thm) will be moved to the "
            "quarantine.",
            "{count} orphan sidecars (.xmp, .aae, .thm) will be moved to the "
            "quarantine.",
            len(plan.orphans),
        )
        output.info(orphans.format(count=human_number(len(plan.orphans))))
