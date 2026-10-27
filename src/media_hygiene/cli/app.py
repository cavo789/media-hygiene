"""Assemble the Typer app — after the locale is installed, so help is translated."""

from __future__ import annotations

import typer

from media_hygiene.cli.cmd_phone_free import phone_done_command, phone_prove_command
from media_hygiene.cli.cmd_phone_plan import phone_plan_command
from media_hygiene.cli.cmd_phone_review import phone_review_command
from media_hygiene.cli.cmd_push_step import push_step_command
from media_hygiene.cli.commands import PAGE_ONLY, commands
from media_hygiene.cli.localized import LocalizedCommand, LocalizedGroup
from media_hygiene.cli.root import root_callback
from media_hygiene.cli.safety import help_of
from media_hygiene.cli.usage_errors import localize_error_frame
from media_hygiene.constants import APP_NAME, DOC_PAGES
from media_hygiene.i18n import _
from media_hygiene.services.phone_plan import (
    PHONE_DONE,
    PHONE_PLAN,
    PHONE_PROVE,
    PHONE_REVIEW,
)
from media_hygiene.services.push_lines import PUSH_STEP

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
            _("Step-by-step guide and every command: {url}").format(
                url=f"{DOC_PAGES}{_('/')}"
            ),
        ),
    )


def build_app() -> typer.Typer:
    """Create the CLI with every command and its translated help.

    Returns:
        The Typer application.
    """
    localize_error_frame()
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
        pretty_exceptions_enable=False,  # an unexpected error: see `cli/unexpected.py`
        context_settings={"help_option_names": ["-h", "--help"]},
    )
    app.callback()(root_callback)
    for name, function, panel, help_text in commands():
        app.command(
            name=name,
            cls=LocalizedCommand,
            help=help_of(name, help_text),
            short_help=help_text,
            rich_help_panel=panel,
            hidden=name in PAGE_ONLY,
        )(function)
    # Plumbing for `mh phone` and `mh push` only (0219, 0248, 0264): hidden from
    # `--help`, no page.
    plumbing = (
        (
            PHONE_PLAN,
            _("For mh phone: which files of a phone are new, from its listing."),
            phone_plan_command,
        ),
        (
            PHONE_REVIEW,
            _("For mh phone: the page where you tick what leaves the phone."),
            phone_review_command,
        ),
        (
            PHONE_PROVE,
            _("For mh phone: prove by their content the files ticked to delete."),
            phone_prove_command,
        ),
        (
            PHONE_DONE,
            _("For mh phone: journal the files gone from the phone."),
            phone_done_command,
        ),
        (
            PUSH_STEP,
            _("For mh push: one step of a backup, its lines on stdin and stdout."),
            push_step_command,
        ),
    )
    for name, help_text, function in plumbing:
        app.command(
            name=name,
            cls=LocalizedCommand,
            help=help_of(name, help_text),
            hidden=True,
        )(function)
    return app
