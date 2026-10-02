"""What `classify` does around the service: check the rules, write and announce."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Final

from rich.markup import escape

from media_hygiene.cli.context import warn
from media_hygiene.config.classify_rules import overlapping_ranges
from media_hygiene.console.carry_view import show_carried
from media_hygiene.constants import CLASSIFY_WORKBOOK_FILE_NAME, REPORT_FILE_NAME
from media_hygiene.errors import ConfigError, MountError
from media_hygiene.i18n import _
from media_hygiene.services.classify_output import write_classify_output

if TYPE_CHECKING:
    from media_hygiene.classify.carry_types import CarrySource
    from media_hygiene.services.classify import ClassifyResult
    from media_hygiene.services.runtime import Runtime

_YEARS: Final = re.compile(r"(?P<first>\d{4})(?:-(?P<last>\d{4}))?")


def warn_overlaps(runtime: Runtime) -> None:
    """Warn about date ranges sharing a day: only the first one listed applies there.

    Args:
        runtime: Settings and output.
    """
    for first, second in overlapping_ranges(runtime.settings.classify.rules):
        runtime.output.warning(
            _(
                "The date ranges of the rules '{first}' and '{second}' overlap: "
                "on the days they share, the first one listed wins."
            ).format(first=escape(first), second=escape(second))
        )


def write_output(
    runtime: Runtime, result: ClassifyResult, source: CarrySource | None
) -> None:
    """Write the plan, the workbook and the report, and say where they are.

    Files that cannot be written are only a warning: the proposals are on screen.

    Args:
        runtime: Settings, mount points and output.
        result: The proposals.
        source: The previous workbook, whose edits are carried over.
    """
    output = runtime.output
    if not result.classification.proposals:
        return
    try:
        written = write_classify_output(runtime, result, source)
    except MountError as exc:
        warn(output, exc)
        return
    if written is None:
        output.tip(
            _('Add -v "<a folder of yours>:/reports" to get the workbook to edit.')
        )
        return
    show_carried(output, written.carried)
    host, folder = runtime.mapper.to_host, written.folder
    output.success(
        _("Workbook to edit: {path}").format(
            path=host(folder / CLASSIFY_WORKBOOK_FILE_NAME)
        )
    )
    output.success(
        _("Report with the photos: {path}").format(path=host(folder / REPORT_FILE_NAME))
    )
    output.tip(_("Edit the yellow cells and save: nothing moves until 'sort'."))


def parse_years(text: str | None) -> tuple[int, int] | None:
    """Read `--year`.

    Args:
        text: `2016` or `2015-2017`, or None.

    Returns:
        First and last year, or None for every year.

    Raises:
        ConfigError: The value is not a year nor a range.
    """
    if text is None:
        return None
    found = _YEARS.fullmatch(text.strip())
    if found is None:
        raise ConfigError(
            _("--year {value}: write a year (2016) or a range (2015-2017).").format(
                value=text
            )
        )
    first = int(found["first"])
    last = int(found["last"] or first)
    return (min(first, last), max(first, last))
