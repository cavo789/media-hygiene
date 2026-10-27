"""The audit's line about intruder files: what in the photo folders is not media."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from media_hygiene.console.formatting import human_number, human_size
from media_hygiene.i18n import ngettext
from media_hygiene.scan.intruders import tally

if TYPE_CHECKING:
    from media_hygiene.console.output import Output
    from media_hygiene.plan.models import AuditFindings

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
        "in your photo folders: see 'Intruder files' in the report.",
        "🧹 {count} files that are not photos or videos ({extensions}) take {size} "
        "in your photo folders: see 'Intruder files' in the report.",
        len(intruders),
    )
    size = sum(item.size for item in intruders)
    output.info(
        said.format(
            count=human_number(len(intruders)), extensions=names, size=human_size(size)
        )
    )
