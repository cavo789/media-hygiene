"""Say that Czkawka's results are out of date, and how to refresh or drop them."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from media_hygiene.i18n import _

if TYPE_CHECKING:
    from datetime import datetime

    from media_hygiene.console.output import Output
    from media_hygiene.services.crosscheck import CzkawkaRefresh

_DATE_FORMAT: Final = "%Y-%m-%d"


def show_outdated(
    output: Output, date: datetime | None, refresh: CzkawkaRefresh
) -> None:
    """Explain that the second opinion is ignored, then the two ways out, concretely.

    Args:
        output: Where to print.
        date: When Czkawka ran, if known.
        refresh: The command to run again and the results file to delete.
    """
    output.warning(
        _(
            "The second opinion of Czkawka (another duplicate finder you ran on "
            "{date}) is out of date: photos were moved or deleted since. It is "
            "ignored; cleaning does not need it."
        ).format(date=date.strftime(_DATE_FORMAT) if date else "?")
    )
    if refresh.runs_here:
        output.tip(
            _(
                "For an up-to-date second opinion (optional): run 'crosscheck' "
                "again, it runs Czkawka itself:"
            )
        )
    else:
        output.tip(
            _(
                "For an up-to-date second opinion (optional): run this command, "
                "then 'media-hygiene crosscheck' with your usual -v options:"
            )
        )
    output.command(refresh.command)
    output.tip(
        _("Or, to no longer see this message, delete this file: {path}").format(
            path=refresh.results_file
        )
    )
