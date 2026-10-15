"""The console side of `xmp`: the sidecars to write, those left out, how to undo."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from rich.markup import escape
from rich.table import Table

from media_hygiene.console.formatting import human_number
from media_hygiene.console.incidents_view import show_failed
from media_hygiene.i18n import _, ngettext
from media_hygiene.tags.models import TagSource

if TYPE_CHECKING:
    from media_hygiene.services.runtime import Runtime
    from media_hygiene.services.xmp import XmpResult
    from media_hygiene.services.xmp_plan import XmpPlan

_SHOWN: Final = 10


def show_plan(runtime: Runtime, plan: XmpPlan) -> None:
    """Say which sidecars would be written, and which files are left out and why.

    Args:
        runtime: Settings, mount points and output.
        plan: The plan.
    """
    output, host = runtime.output, runtime.mapper.to_host
    merged = sum(1 for job in plan.jobs if job.previous is not None)
    output.info(
        _(
            "{count} sidecars to write: {new} new, {merged} with the words added to "
            "those of another application."
        ).format(
            count=human_number(len(plan.jobs)),
            new=human_number(len(plan.jobs) - merged),
            merged=human_number(merged),
        )
    )
    if plan.jobs and TagSource.PERSON in runtime.settings.tags.xmp_sources:
        output.warning(
            _(
                "The names of the people go into the sidecars, next to the photos: "
                "anyone who gets a copy of them can read who is on them."
            )
        )
    if plan.jobs:
        table = Table(_("Photo"), _("Sidecar"))
        for job in plan.jobs[:_SHOWN]:
            table.add_row(escape(host(job.photo)), escape(job.sidecar.name))
        output.show(table)
        more = len(plan.jobs) - _SHOWN
        if more > 0:
            output.info(_("... and {count} more.").format(count=human_number(more)))
    _left_out(runtime, plan)
    for sidecar, reason in plan.refused[:_SHOWN]:
        output.warning(
            escape(
                _(
                    "{path}: not an XMP file this tool can read ({reason}); left as is."
                ).format(path=host(sidecar), reason=reason)
            )
        )


def _left_out(runtime: Runtime, plan: XmpPlan) -> None:
    """Say how many files are left out, and why.

    Args:
        runtime: Settings, mount points and output.
        plan: The plan.
    """
    output = runtime.output
    if plan.unchanged:
        output.info(
            _("{count} sidecars hold these words already.").format(
                count=human_number(plan.unchanged)
            )
        )
    if plan.protected:
        output.info(
            _("{count} files of protected folders: never written.").format(
                count=human_number(plan.protected)
            )
        )
    if plan.copies:
        output.info(
            _("{count} files have an identical copy: left out.").format(
                count=human_number(plan.copies)
            )
        )
        output.tip(_("Run 'clean' first: only the copy kept then gets a sidecar."))
    if plan.without_words:
        output.info(
            _("{count} files have no word to write.").format(
                count=human_number(plan.without_words)
            )
        )


def show_result(runtime: Runtime, result: XmpResult) -> None:
    """Say what the run wrote, what failed, and how to undo it.

    Args:
        runtime: Settings, mount points and output.
        result: The run.
    """
    output = runtime.output
    outcome = result.outcome
    output.success(
        ngettext(
            "{count} sidecar written and read back; no photo was changed.",
            "{count} sidecars written and read back; no photo was changed.",
            outcome.done,
        ).format(count=human_number(outcome.done))
    )
    show_failed(runtime, outcome.failed)
    if result.interrupted:
        output.warning(_("Stopped before the end, as asked."))
        output.tip(_("Run the same command again: the sidecars written are skipped."))
