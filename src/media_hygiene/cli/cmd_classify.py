"""`media-hygiene classify`: propose a tree for the photos and videos; read-only."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Annotated, Final

import typer

from media_hygiene.cli.context import runtime_of, user_errors, warn
from media_hygiene.console.classify_view import show_classification
from media_hygiene.console.progress import RichProgress
from media_hygiene.constants import CLASSIFY_WORKBOOK_FILE_NAME, REPORT_FILE_NAME
from media_hygiene.errors import ConfigError, MountError
from media_hygiene.i18n import _
from media_hygiene.services.classify import ClassifyService
from media_hygiene.services.classify_output import write_classify_output

if TYPE_CHECKING:
    from media_hygiene.services.classify import ClassifyResult
    from media_hygiene.services.runtime import Runtime

_YEARS: Final = re.compile(r"(?P<first>\d{4})(?:-(?P<last>\d{4}))?")


def classify_command(  # pylint: disable=too-many-arguments
    ctx: typer.Context,
    *,
    year: Annotated[
        str | None,
        typer.Option(
            "--year",
            help=_(
                "Only the files of this year, or of these years: 2016 or 2015-2017."
            ),
        ),
    ] = None,
    layout: Annotated[
        str | None,
        typer.Option(
            "--layout",
            help=_("Where sure files go, e.g. '{year}/{month} - {month_name}'."),
        ),
    ] = None,
    target: Annotated[
        str | None,
        typer.Option(
            "--target",
            help=_("Host folder receiving the tree; in place by default."),
        ),
    ] = None,
    leave: Annotated[
        list[str] | None,
        typer.Option(
            "--leave",
            help=_("Host folder never sorted (analysed and cleaned as usual)."),
        ),
    ] = None,
) -> None:
    """Propose where every photo and video should go; never moves anything.

    Args:
        ctx: Typer context holding the runtime.
        year: `--year` scope.
        layout: `--layout` for the sure files.
        target: `--target` host folder.
        leave: `--leave` host folders.
    """
    runtime = runtime_of(ctx)
    given: dict[str, object] = {"layout": layout, "target": target, "leave": leave}
    overrides = {key: value for key, value in given.items() if value}
    with user_errors(runtime.output):
        if overrides:
            runtime = runtime.with_overrides({"classify": overrides})
        years = parse_years(year)
        runtime.output.title(_("Classify"))
        with RichProgress(runtime.output.console) as progress:
            result = ClassifyService(runtime, progress).run(years)
    show_classification(runtime.output, result)
    _write_output(runtime, result)


def _write_output(runtime: Runtime, result: ClassifyResult) -> None:
    """Write the plan, the workbook and the report, and say where they are.

    Files that cannot be written are only a warning: the proposals are on screen.

    Args:
        runtime: Settings, mount points and output.
        result: The proposals.
    """
    output = runtime.output
    if not result.classification.proposals:
        return
    try:
        folder = write_classify_output(runtime, result)
    except MountError as exc:
        warn(output, exc)
        return
    if folder is None:
        output.tip(
            _('Add -v "<a folder of yours>:/reports" to get the workbook to edit.')
        )
        return
    host = runtime.mapper.to_host
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
