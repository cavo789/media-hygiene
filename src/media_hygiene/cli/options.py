"""Shared, translated option definitions, evaluated once the locale is known."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import typer

from media_hygiene.i18n import _

if TYPE_CHECKING:
    from collections.abc import Callable

    from typer.models import OptionInfo


def panel_advanced() -> str:
    """Title of the help panel of the options seldom needed.

    The options of daily use carry no panel: Typer lists them first, under
    "Options". Only commands with more than four options split them.

    Returns:
        The translated title.
    """
    return _("Advanced options")


def panel_local_ai() -> str:
    """Title of the help panel of the options that only serve a local vision model.

    Everything else works without one: the panel tells, at a glance, what to skip.

    Returns:
        The translated title.
    """
    return _("🤖 Local AI (Ollama), optional: a model set in config.toml")


def _panel_output() -> str:
    return _("Output (override general.* of config.toml)")


def locale() -> OptionInfo:
    """`--locale`: interface language.

    Returns:
        The option definition.
    """
    return cast(
        "OptionInfo",
        typer.Option(
            "--locale",
            help=_("Interface language."),
            rich_help_panel=_panel_output(),
            show_default=False,
        ),
    )


def verbosity() -> OptionInfo:
    """`--verbosity`: log level.

    Returns:
        The option definition.
    """
    return cast(
        "OptionInfo",
        typer.Option(
            "--verbosity",
            help=_("How much to log."),
            rich_help_panel=_panel_output(),
            show_default=False,
        ),
    )


def color() -> OptionInfo:
    """`--color`: ANSI colours.

    Returns:
        The option definition.
    """
    return cast(
        "OptionInfo",
        typer.Option(
            "--color",
            help=_("When to use colours (NO_COLOR is honoured too)."),
            rich_help_panel=_panel_output(),
            show_default=False,
        ),
    )


def version(callback: Callable[[bool], None]) -> OptionInfo:
    """`--version`: print the version and exit.

    Args:
        callback: Eager callback printing the version.

    Returns:
        The option definition.
    """
    return cast(
        "OptionInfo",
        typer.Option(
            "--version",
            help=_("Show the version and exit."),
            callback=callback,
            is_eager=True,
        ),
    )


def yes() -> OptionInfo:
    """`--yes`: do not ask for confirmation.

    Returns:
        The option definition.
    """
    return cast(
        "OptionInfo",
        typer.Option(
            "--yes",
            "-y",
            help=_("Do not ask for confirmation (overrides clean.confirm)."),
        ),
    )
