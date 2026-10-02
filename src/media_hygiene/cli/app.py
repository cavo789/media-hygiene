"""Assemble the Typer app — after the locale is installed, so help is translated."""

from __future__ import annotations

import typer

from media_hygiene.cli.commands import commands
from media_hygiene.cli.localized import LocalizedCommand, LocalizedGroup
from media_hygiene.cli.root import root_callback
from media_hygiene.constants import APP_NAME
from media_hygiene.i18n import _

# One short command per line, so a copy/paste stays a single command.
# "\b" tells Click not to re-wrap the block.
_WINDOWS_FOLDER = (
    'docker run --rm -it -v "C:\\Photos:/data/c/Photos:ro" media-hygiene audit'
)
_CURRENT_FOLDER = 'docker run --rm -it -v "${PWD}:/data/current:ro" media-hygiene audit'


def _epilog() -> str:
    """Translated examples block shown at the end of `--help`, each one labelled.

    Returns:
        The epilog text.
    """
    return "\n\n".join(
        (
            "\n".join(
                (
                    "\b",
                    _("A Windows folder (PowerShell):"),
                    f"  {_WINDOWS_FOLDER}",
                    _("The current folder (PowerShell, or bash on WSL, Linux, macOS):"),
                    f"  {_CURRENT_FOLDER}",
                ),
            ),
            _("Full commands (reports, journal, WSL): see README.md."),
        ),
    )


def build_app() -> typer.Typer:
    """Create the CLI with every command and its translated help.

    Returns:
        The Typer application.
    """
    app = typer.Typer(
        name=APP_NAME,
        cls=LocalizedGroup,
        help=_(
            "Find and safely clean duplicate photos and videos across folders and "
            "disks. Start with 'audit' (read-only), then 'clean'."
        ),
        epilog=_epilog(),
        subcommand_metavar=_("COMMAND [ARGS]..."),
        rich_markup_mode="rich",
        no_args_is_help=True,
        add_completion=False,
        context_settings={"help_option_names": ["-h", "--help"]},
    )
    app.callback()(root_callback)
    for name, function, panel, help_text in commands():
        app.command(
            name=name,
            cls=LocalizedCommand,
            help=help_text,
            rich_help_panel=panel,
        )(function)
    return app
