"""The sorting part of `status` (0405): what the tree says, and the folders left."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from rich.markup import escape

from media_hygiene.cli.next_steps import carried
from media_hygiene.console.advice import Advice, TipKind
from media_hygiene.console.formatting import human_number
from media_hygiene.i18n import _, ngettext
from media_hygiene.services.next_command import NextVerb, next_command
from media_hygiene.services.sort_disk import disk_progress

if TYPE_CHECKING:
    from media_hygiene.services.runtime import Runtime
    from media_hygiene.services.sort_disk import DiskProgress

SHOWN_FOLDERS: Final = 10  # the folders left `status` lists; the page lists them all
_PERCENT: Final = 100


def show_sorting(runtime: Runtime) -> None:
    """Say how far the sorting is, the largest folders left, and how to open one.

    Args:
        runtime: Settings, mount points and output.
    """
    progress = disk_progress(runtime)
    if progress is None or not progress.total:
        return
    output = runtime.output
    output.info(sorting_line(progress))
    if not progress.folders:
        return
    output.info(_("Folders left, the largest first:"))
    for folder, files in progress.folders[:SHOWN_FOLDERS]:
        output.info(f"  {human_number(files):>7}  {escape(folder)}")
    largest = progress.folders[0][0].replace('"', "")
    verb = NextVerb(carried(runtime, f'search --folder "{largest}"'))
    output.advise(
        Advice(
            TipKind.DISCOVERY,
            _("Open a folder left in the search page, pick, then Move to an event…:"),
            next_command(runtime, verb).command,
        )
    )


def sorting_line(progress: DiskProgress) -> str:
    """One line: sorted, nothing special, left, in percent of the files.

    Args:
        progress: The counts.

    Returns:
        E.g. `Sorted: 62 % · nothing special: 9 % · left: 16,400 files in 214 folders.`
    """
    total = progress.total
    left = ngettext(
        "{files} file in {folders} folders",
        "{files} files in {folders} folders",
        progress.left,
    ).format(
        files=human_number(progress.left), folders=human_number(len(progress.folders))
    )
    line = _(
        "Sorted: {sorted} % · nothing special: {nothing} % · left: {left}."
    ).format(
        sorted=round(progress.sorted * _PERCENT / total),
        nothing=round(progress.nothing_special * _PERCENT / total),
        left=left,
    )
    if progress.kept:
        line += " " + _("{files} files of protected or left folders apart.").format(
            files=human_number(progress.kept)
        )
    return line
