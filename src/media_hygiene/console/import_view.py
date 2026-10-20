"""What `import` says: what it will copy, what it leaves apart, then what it did."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from rich.markup import escape

from media_hygiene.console.backup_view import show_backups
from media_hygiene.console.formatting import human_number, human_size
from media_hygiene.i18n import _, ngettext

if TYPE_CHECKING:
    from media_hygiene.services.import_plan import ImportPlan
    from media_hygiene.services.import_run import ImportResult
    from media_hygiene.services.runtime import Runtime

_SHOWN: Final = 10  # the first copies listed; the count says the rest


def show_plan(runtime: Runtime, plan: ImportPlan) -> None:
    """Say what each backup holds, then the copies to make and what stays apart.

    Args:
        runtime: Settings, mount points and output.
        plan: The copies.
    """
    output = runtime.output
    show_backups(runtime, plan.backups)
    if plan.near:
        output.info(
            ngettext(
                "{count} photo is probably in your photos already (a near copy: "
                "another size or format): not copied.",
                "{count} photos are probably in your photos already (a near copy: "
                "another size or format): not copied.",
                len(plan.near),
            ).format(count=human_number(len(plan.near)))
        )
    if plan.twins:
        output.info(
            ngettext(
                "{count} file is an identical copy of another one of the backup: "
                "copied once.",
                "{count} files are identical copies of others of the backup: "
                "copied once.",
                plan.twins,
            ).format(count=human_number(plan.twins))
        )
    if not plan.jobs:
        return
    output.info(
        ngettext(
            "{count} file to copy into your photos ({size}):",
            "{count} files to copy into your photos ({size}):",
            len(plan.jobs),
        ).format(count=human_number(len(plan.jobs)), size=human_size(plan.size))
    )
    for job in plan.jobs[:_SHOWN]:
        output.info(f"   {escape(runtime.mapper.to_host(job.target))}")
    if len(plan.jobs) > _SHOWN:
        rest = len(plan.jobs) - _SHOWN
        output.info(
            ngettext("   … and {count} more.", "   … and {count} more.", rest).format(
                count=human_number(rest)
            )
        )


def show_result(runtime: Runtime, result: ImportResult) -> None:
    """Say what was copied, read back from the photos, and what failed.

    Args:
        runtime: Settings, mount points and output.
        result: The run.
    """
    output = runtime.output
    outcome = result.outcome
    output.success(
        ngettext(
            "{count} file copied into your photos ({size}), each one compared with "
            "its source, read back where it was written.",
            "{count} files copied into your photos ({size}), each one compared with "
            "its source, read back where they were written.",
            len(result.copied),
        ).format(
            count=human_number(len(result.copied)),
            size=human_size(outcome.bytes_done),
        )
    )
    for incident in outcome.failed:
        output.warning(
            _("{path}: not copied: {reason}").format(
                path=escape(runtime.mapper.to_host(incident.path)),
                reason=escape(incident.reason),
            )
        )
    if result.interrupted:
        output.warning(_("Stopped by Ctrl+C: type the command again for the rest."))
