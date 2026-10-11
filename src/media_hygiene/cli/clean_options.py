"""Options only `clean` has, translated once the locale is known."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import typer

from media_hygiene.cli.options import panel_advanced
from media_hygiene.i18n import _

if TYPE_CHECKING:
    from typer.models import OptionInfo


def tier() -> OptionInfo:
    """`--tier`: how far `clean` goes (near duplicates only when asked).

    Returns:
        The option definition.
    """
    return cast(
        "OptionInfo",
        typer.Option(
            "--tier",
            help=_(
                "How far to clean. exact (default): the byte-for-byte copies only. "
                "near: also the shrunk copies (sent by WhatsApp or e-mail, resized, "
                "recompressed) and the re-encoded videos that are sure; the groups "
                "to check are left alone. near-all: every near duplicate; check "
                "them in the report first. Near duplicates go to the quarantine, "
                "never deleted."
            ),
            show_default=False,
            case_sensitive=False,
        ),
    )


def delete() -> OptionInfo:
    """`--delete`: delete the exact copies for good instead of moving them.

    Returns:
        The option definition.
    """
    return cast(
        "OptionInfo",
        typer.Option(
            "--delete",
            help=_(
                "Free the space at once: delete the exact copies for good, after a "
                "byte comparison with the kept copy, instead of moving them to the "
                "quarantine; 'undo' rebuilds them from the kept copy."
            ),
            rich_help_panel=panel_advanced(),
        ),
    )


def decisions() -> OptionInfo:
    """`--decisions`: apply the decisions of a report or of `review`.

    Returns:
        The option definition.
    """
    return decisions_option(
        _(
            "Apply the choices made in the browser: decisions.json downloaded "
            "from an audit report (swap or leave alone some folder pairs) or "
            "written by 'review' (burst shots set aside, near duplicates decided). "
            "A relative path is read from the folder mounted on /reports. The "
            "file is refused if the folders, the pairs or the series changed. "
            "Alone, --decisions reads decisions.json."
        )
    )


def decisions_option(help_text: str, panel: str | None = None) -> OptionInfo:
    """`--decisions`, shared by `clean` (reads it) and `review` (writes it).

    Args:
        help_text: The translated help of the command.
        panel: Help panel of the option; None for the options of daily use.

    Returns:
        The option definition.
    """
    return cast(
        "OptionInfo",
        typer.Option(
            "--decisions", help=help_text, rich_help_panel=panel, show_default=False
        ),
    )
