"""The options naming the files of an import: its folder and its period (0480).

`mh` passes them after `import --phone` to `review` (the import's burst series
only) and `slideshow` (the new event only).
"""

from __future__ import annotations

from typing import cast

import typer
from typer.models import OptionInfo

from media_hygiene.i18n import _


def imported(panel: str | None = None) -> OptionInfo:
    """`--imported`: the folder an import copied into (hidden: `mh` passes it).

    Args:
        panel: Help panel of the option; None where the command has few options.

    Returns:
        The option definition.
    """
    return cast(
        "OptionInfo",
        typer.Option(
            "--imported",
            help=_("Only the burst series of the files an import copied there."),
            hidden=True,
            rich_help_panel=panel,
            show_default=False,
        ),
    )


def since(panel: str | None = None) -> OptionInfo:
    """`--since`: the period of the files, as `import` takes it.

    Args:
        panel: Help panel of the option; None where the command has few options.

    Returns:
        The option definition.
    """
    return cast(
        "OptionInfo",
        typer.Option(
            "--since",
            help=_(
                "Only the files of a period, by the day in their name, else their "
                "modified time: today, week, month, all or a day such as "
                "2026-10-29."
            ),
            rich_help_panel=panel,
            show_default=False,
        ),
    )
