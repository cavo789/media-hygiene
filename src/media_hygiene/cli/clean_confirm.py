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
    return runtime.output.confirm(_question(plan))


def _question(plan: CleanPlan) -> str:
    """The question of the confirmation: only what the clean does, no zero counts.

    Args:
        plan: What would be cleaned.

    Returns:
        The translated question, e.g. "Move 1,396 near duplicates to the quarantine?".
    """
    actions = _actions(plan)
    if not actions:
        return _("Go on with the clean?")
    joined = actions[0]
    if len(actions) > 1:
        joined = _("{actions} and {last}").format(
            actions=", ".join(actions[:-1]), last=actions[-1]
        )
    return _("{actions}?").format(actions=joined[0].upper() + joined[1:])


def _actions(plan: CleanPlan) -> list[str]:
    """What the clean does, one phrase per kind of file it touches.

    Args:
        plan: What would be cleaned.

    Returns:
        The phrases, lower case; none for a count of zero.
    """
    count, near = plan.removable_count, plan.near_count
    size, broken = human_size(plan.reclaimable), len(plan.broken)
    actions: list[str] = []
    if count and plan.delete_copies:
        phrase = ngettext(
            "delete {count} duplicate copy ({size})",
            "delete {count} duplicate copies ({size})",
            count,
        )
        actions.append(phrase.format(count=human_number(count), size=size))
    if count and near and not plan.delete_copies:
        both = ngettext(
            "move {count} duplicate copy ({size}) and {near} near duplicates to "
            "the quarantine",
            "move {count} duplicate copies ({size}) and {near} near duplicates to "
            "the quarantine",
            count,
        )
        actions.append(
            both.format(count=human_number(count), size=size, near=human_number(near))
        )
    elif count and not plan.delete_copies:
        phrase = ngettext(
            "move {count} duplicate copy ({size}) to the quarantine",
            "move {count} duplicate copies ({size}) to the quarantine",
            count,
        )
        actions.append(phrase.format(count=human_number(count), size=size))
    elif near:
        phrase = ngettext(
            "move {count} near duplicate to the quarantine",
            "move {count} near duplicates to the quarantine",
            near,
        )
        actions.append(phrase.format(count=human_number(near)))
    if broken:
        phrase = ngettext(
            "handle {count} broken file", "handle {count} broken files", broken
        )
        actions.append(phrase.format(count=human_number(broken)))
    return actions


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
        output.info(_safe_line(runtime, plan))
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


def _safe_line(runtime: Runtime, plan: CleanPlan) -> str:
    """Say that nothing will be erased, where the files go and how they come back.

    Args:
        runtime: Settings, mount points and output.
        plan: What would be cleaned (without `--delete`).

    Returns:
        The line; the byte comparison is named for exact copies only.
    """
    quarantine = runtime.mapper.to_host(runtime.locations.quarantine_dir)
    if plan.removable_count:
        line = _(
            "🛟 Nothing will be erased: each copy is first compared byte for byte "
            "with the kept one, then moved to the quarantine ({path}). 'undo' puts "
            "it back; 'purge' erases it once you have checked."
        )
    else:
        line = _(
            "🛟 Nothing will be erased: the files are moved to the quarantine "
            "({path}). 'undo' puts them back; 'purge' erases them once you have "
            "checked."
        )
    return line.format(path=quarantine)
