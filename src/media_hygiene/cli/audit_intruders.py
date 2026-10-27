"""The audit's line about intruder files: what in the photo folders is not media."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from media_hygiene.cli.audit_gone import gone_step
from media_hygiene.cli.next_steps import carried, suggest
from media_hygiene.console.formatting import human_number, human_size
from media_hygiene.i18n import _, ngettext
from media_hygiene.scan.intruders import tally
from media_hygiene.services.next_command import NextVerb

if TYPE_CHECKING:
    import typer

    from media_hygiene.console.output import Output
    from media_hygiene.plan.models import AuditFindings
    from media_hygiene.services.runtime import Runtime

# How many extensions the line names, the heaviest first.
_NAMED_EXTENSIONS: Final = 3


def tell_intruders(output: Output, findings: AuditFindings) -> None:
    """Say how many files are neither photos nor videos, their weight; nothing if none.

    Args:
        output: Where to print.
        findings: What the audit found.
    """
    intruders = findings.intruders
    if not intruders:
        return
    by_extension = tally(intruders)
    heaviest = by_extension.heaviest(_NAMED_EXTENSIONS + 1)
    names = ", ".join(
        key.lstrip(".") for key, _count, _size in heaviest[:_NAMED_EXTENSIONS]
    )
    if len(heaviest) > _NAMED_EXTENSIONS:
        names += ", …"
    said = ngettext(
        "🧹 {count} file that is not a photo or a video ({extensions}) takes {size} "
        "in your photo folders: see 'Intruder files' in the report; "
        "'review --intruders' picks those to set aside.",
        "🧹 {count} files that are not photos or videos ({extensions}) take {size} "
        "in your photo folders: see 'Intruder files' in the report; "
        "'review --intruders' picks those to set aside.",
        len(intruders),
    )
    size = sum(item.size for item in intruders)
    output.info(
        said.format(
            count=human_number(len(intruders)), extensions=names, size=human_size(size)
        )
    )


def intruders_step(ctx: typer.Context, runtime: Runtime) -> None:
    """Nothing else to do: lead to the page that picks the intruder files.

    Args:
        ctx: Typer context of the audit, whose options the next command keeps.
        runtime: Settings, mount points and output.
    """
    suggest(
        runtime,
        _(
            "tick in 'review --intruders' the intruder files to set aside, per "
            "extension or per folder."
        ),
        NextVerb(
            carried(runtime, "review --intruders", ctx),
            port=runtime.settings.review.port,
        ),
    )


def quiet_end_step(
    ctx: typer.Context, runtime: Runtime, findings: AuditFindings
) -> None:
    """No copies, no bursts: lead to the files gone, else to the intruder files.

    Args:
        ctx: Typer context of the audit, whose options the next command keeps.
        runtime: Settings, mount points and output.
        findings: What the audit found.
    """
    if findings.gone:
        gone_step(ctx, runtime)
    elif findings.intruders:
        intruders_step(ctx, runtime)
