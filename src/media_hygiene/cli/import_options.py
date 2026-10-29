"""The options naming the files of an import: its folder and its period (0480).

`mh` passes them after `import --phone` to `review` (the import's burst series
only) and `slideshow` (the new event only).
"""

from __future__ import annotations

from typing import Final, cast

import typer
from typer.models import OptionInfo

from media_hygiene.i18n import _

_IMPORTED: Final = "--imported"  # hidden: only `mh` passes it


def imported(panel: str | None = None) -> OptionInfo:
    """`--imported`: the folder an import copied into.

    Args:
        panel: Help panel of the option; None where the command has few options.

    Returns:
        The option definition.
    """
    text = _("Only the burst series of the files an import copied there.")
    return _option(_IMPORTED, text, panel)


def since(panel: str | None = None) -> OptionInfo:
    """`--since`: the period of the files, as `import` takes it.

    Args:
        panel: Help panel of the option; None where the command has few options.

    Returns:
        The option definition.
    """
    text = _(
        "Only the files of a period, by the day in their name, else their "
        "modified time: today, week, month, all or a day such as 2026-10-29."
    )
    return _option("--since", text, panel)


def _option(flag: str, text: str, panel: str | None) -> OptionInfo:
    """One option with no default shown.

    Args:
        flag: Its name.
        text: Its help, translated.
        panel: Its help panel.

    Returns:
        The option definition.
    """
    hidden = flag == _IMPORTED
    built = typer.Option(
        flag, help=text, hidden=hidden, rich_help_panel=panel, show_default=False
    )
    return cast("OptionInfo", built)
