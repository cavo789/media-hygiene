"""The console side of carrying the edits of the previous workbook over."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Final

from rich.markup import escape

from media_hygiene.classify.layout import month_name
from media_hygiene.classify.names import lost_line
from media_hygiene.console.formatting import human_number
from media_hygiene.i18n import _, ngettext

if TYPE_CHECKING:
    from media_hygiene.classify.carry_models import CarryRecord
    from media_hygiene.console.output import Output

_SHOWN_LOST: Final = 10


def show_carried(output: Output, record: CarryRecord | None) -> None:
    """Say how many edits were carried over, which events were split, what was not.

    Args:
        output: Where to print.
        record: What was carried; None when nothing was read.
    """
    if record is None or not (record.edits or record.notes or record.lost):
        return
    saved = datetime.fromisoformat(record.saved_at)
    output.success(
        ngettext(
            "{count} edit carried over from the workbook saved on {day} {month} "
            "{year} at {time}: {path}",
            "{count} edits carried over from the workbook saved on {day} {month} "
            "{year} at {time}: {path}",
            record.edits,
        ).format(
            count=human_number(record.edits),
            day=saved.day,
            month=month_name(saved.month),
            year=saved.year,
            time=saved.strftime("%H:%M"),
            path=escape(record.workbook),
        )
    )
    if record.notes:
        output.info(
            _("Notes carried over too: {count}.").format(
                count=human_number(record.notes)
            )
        )
    if record.split:
        output.info(
            _("Events split in several, each part keeps the edit: {names}.").format(
                names=escape(", ".join(record.split))
            )
        )
    if not record.lost:
        return
    output.warning(
        ngettext(
            "{count} edit found no place in the new proposal:",
            "{count} edits found no place in the new proposal:",
            len(record.lost),
        ).format(count=human_number(len(record.lost)))
    )
    for lost in record.lost[:_SHOWN_LOST]:
        output.warning(escape(lost_line(lost)))
    output.tip(_("The report lists them all: type them again where they belong."))
