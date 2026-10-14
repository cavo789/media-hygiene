"""Options only `crosscheck` has, translated once the locale is known."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import typer

from media_hygiene.cli.options import panel_advanced
from media_hygiene.i18n import _

if TYPE_CHECKING:
    from typer.models import OptionInfo


def fresh() -> OptionInfo:
    """`--fresh`: Czkawka ignores its cache and reads every file again.

    Returns:
        The option definition.
    """
    return cast(
        "OptionInfo",
        typer.Option(
            "--fresh",
            help=_(
                "Czkawka reads and hashes every file again, ignoring what its cache "
                "in /cache remembers from its previous run. Slower; for a second "
                "opinion that owes nothing to an earlier one."
            ),
            rich_help_panel=panel_advanced(),
        ),
    )


def print_command() -> OptionInfo:
    """`--print-command`: run Czkawka yourself, then compare its results.

    Returns:
        The option definition.
    """
    return cast(
        "OptionInfo",
        typer.Option(
            "--print-command",
            help=_(
                "Do not run Czkawka here: print the command that runs it in its own "
                "image, then compare the results it wrote in /reports (czkawka.json)."
            ),
            rich_help_panel=panel_advanced(),
        ),
    )
