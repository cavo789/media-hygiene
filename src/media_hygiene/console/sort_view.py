"""The console side of `sort`: what was read, what will move, what moved, the proof."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from rich.markup import escape
from rich.table import Table

from media_hygiene.classify.layout import month_name
from media_hygiene.classify.models import Band
from media_hygiene.console.formatting import human_number, human_size
from media_hygiene.i18n import _, ngettext

if TYPE_CHECKING:
    from media_hygiene.actions.manifest import Manifest
    from media_hygiene.actions.sort_folders import FolderReport
    from media_hygiene.console.output import Output
    from media_hygiene.services.runtime import Runtime
    from media_hygiene.services.sort import Prepared
    from media_hygiene.services.sort_inputs import SortInputs

_TO_CHECK: Final = frozenset({Band.UNSURE})


def show_inputs(runtime: Runtime, inputs: SortInputs) -> None:
    """Say which workbook was read, how many edits, and when it was saved.

    Args:
        runtime: Settings, mount points and output.
        inputs: The workbook and its edits.
    """
    output = runtime.output
    saved = inputs.saved_at
    output.info(
        _("Workbook: {path}").format(path=runtime.mapper.to_host(inputs.workbook))
    )
    output.info(
        ngettext(
            "{count} edit read; workbook saved on {day} {month} {year} at {time}.",
            "{count} edits read; workbook saved on {day} {month} {year} at {time}.",
            inputs.edit_count,
        ).format(
            count=human_number(inputs.edit_count),
            day=saved.day,
            month=month_name(saved.month),
            year=saved.year,
            time=saved.strftime("%H:%M"),
        )
    )
    if inputs.open_elsewhere:
        output.warning(
            _(
                "The workbook is open in Excel or LibreOffice: what is not saved is "
                "not read."
            )
        )
        output.tip(_("Save it, close it, then run 'sort' again."))


def sort_table(prepared: Prepared) -> Table:
    """What the sort will do, before anything moves.

    Args:
        prepared: The sort.

    Returns:
        A two-column table.
    """
    plan = prepared.plan
    table = Table(title=_("Sort"), show_header=False, title_justify="left")
    table.add_column(style="bold")
    table.add_column(justify="right")
    rows = [
        (_("Files to move"), human_number(len(plan.moves))),
        (_("Into folders"), human_number(len(plan.folders))),
        (_("Size"), human_size(plan.size)),
        (_("Already in place"), human_number(plan.in_place)),
        (_("Staying where they are"), human_number(plan.stay)),
        (_("Going to a 'to check' folder"), human_number(plan.count(_TO_CHECK))),
        (_("Going to a 'to sort' folder"), human_number(plan.to_sort)),
        (_("Source folders removed"), human_number(prepared.folders.removed)),
    ]
    if plan.done:
        rows.insert(4, (_("Moved by an earlier run"), human_number(plan.done)))
    for label, value in rows:
        table.add_row(label, value)
    return table


def show_kept_folders(runtime: Runtime, folders: FolderReport, *, done: bool) -> None:
    """Say how many source folders stay, and why.

    Args:
        runtime: Settings, mount points and output.
        folders: The prediction, or what was done.
        done: The sort is over (else: it is about to start).
    """
    if not folders.kept:
        return
    example = runtime.mapper.to_host(folders.kept[0].folder)
    message = (
        ngettext(
            "{count} source folder stays: it still holds other files, e.g. {path}.",
            "{count} source folders stay: they still hold other files, e.g. {path}.",
            len(folders.kept),
        )
        if done
        else ngettext(
            "{count} source folder will stay: it holds other files, e.g. {path}.",
            "{count} source folders will stay: they hold other files, e.g. {path}.",
            len(folders.kept),
        )
    )
    runtime.output.info(
        message.format(count=human_number(len(folders.kept)), path=escape(example))
    )


def show_manifest(output: Output, manifest: Manifest) -> None:
    """Show the proof: the counts before and after, every move checked.

    Args:
        output: Where to print.
        manifest: The proof of the run.
    """
    before, after = manifest.before, manifest.after
    counts = {
        "before": human_number(before.files),
        "before_size": human_size(before.bytes),
        "after": human_number(after.files),
        "after_size": human_size(after.bytes),
        "verified": human_number(manifest.verified),
        "moved": human_number(manifest.moved),
    }
    if manifest.intact:
        output.success(
            _(
                "Nothing lost: {before} files ({before_size}) before and after; "
                "{verified} of {moved} moves verified."
            ).format(**counts)
        )
        return
    output.error(
        _(
            "Check this run: {before} files ({before_size}) before, {after} files "
            "({after_size}) after; {verified} of {moved} moves verified."
        ).format(**counts)
    )
    for problem in manifest.problems:
        output.error(escape(problem))
    output.tip(
        _("A file changed by another program meanwhile also changes the counts.")
    )
