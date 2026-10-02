"""`media-hygiene classify`: propose a tree for the photos and videos; read-only."""

from __future__ import annotations

from typing import Annotated

import typer

from media_hygiene.cli.classify_ai_flow import (
    SubjectRequest,
    ask_subjects,
    sample_subjects,
)
from media_hygiene.cli.classify_flow import parse_years, warn_overlaps, write_output
from media_hygiene.cli.context import runtime_of, user_errors
from media_hygiene.console.classify_view import show_classification
from media_hygiene.console.progress import RichProgress
from media_hygiene.i18n import _
from media_hygiene.services.carry import CarryRequest, carry_source
from media_hygiene.services.classify import ClassifyService


def classify_command(  # pylint: disable=too-many-arguments,too-many-locals
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
    carry_over: Annotated[
        str | None,
        typer.Option(
            "--carry-over",
            help=_(
                "Workbook whose edits are carried over; the latest classify run's "
                "by default."
            ),
        ),
    ] = None,
    no_carry_over: Annotated[
        bool,
        typer.Option(
            "--no-carry-over",
            help=_("Start fresh: carry no edit of a previous workbook over."),
        ),
    ] = False,
    sample: Annotated[
        int,
        typer.Option(
            "--sample",
            min=0,
            help=_(
                "Describe this many random photos with the local model, print the "
                "time per photo and the estimate of a full run, and stop."
            ),
            show_default=False,
        ),
    ] = 0,
    no_describe: Annotated[
        bool,
        typer.Option(
            "--no-describe",
            help=_(
                "Ask the local model nothing new: the subject rules read the "
                "descriptions already in the cache."
            ),
        ),
    ] = False,
    yes: Annotated[
        bool,
        typer.Option(
            "--yes",
            "-y",
            help=_("Describe the photos without asking, however many."),
        ),
    ] = False,
) -> None:
    """Propose where every photo and video should go; never moves anything.

    Args:
        ctx: Typer context holding the runtime.
        year: `--year` scope.
        layout: `--layout` for the sure files.
        target: `--target` host folder.
        leave: `--leave` host folders.
        carry_over: `--carry-over` workbook.
        no_carry_over: `--no-carry-over`.
        sample: `--sample N`.
        no_describe: `--no-describe`.
        yes: `--yes`.
    """
    runtime = runtime_of(ctx)
    given: dict[str, object] = {"layout": layout, "target": target, "leave": leave}
    overrides = {key: value for key, value in given.items() if value}
    with user_errors(runtime.output):
        if overrides:
            runtime = runtime.with_overrides({"classify": overrides})
        years = parse_years(year)
        runtime.output.title(_("Classify"))
        warn_overlaps(runtime)
        source = (
            None
            if sample
            else carry_source(runtime, CarryRequest(carry_over, not no_carry_over))
        )
        with RichProgress(runtime.output.console) as progress:
            inputs = ClassifyService(runtime, progress).collect(years)
        if sample:
            sample_subjects(runtime, inputs, sample)
            return
        subjects = ask_subjects(
            runtime, inputs, SubjectRequest(describe=not no_describe, yes=yes)
        )
        with RichProgress(runtime.output.console) as progress:
            result = ClassifyService(runtime, progress).decide(inputs, subjects)
    show_classification(runtime.output, result)
    write_output(runtime, result, source)
