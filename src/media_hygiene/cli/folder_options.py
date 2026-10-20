"""The folder options of `audit`, `review`, `clean` and `crosscheck` (`[folders]`).

Translated once the locale is known; built before the settings are read.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

import typer

from media_hygiene.i18n import _

if TYPE_CHECKING:
    from typer.models import OptionInfo

    from media_hygiene.config.layers import Layer


def _panel() -> str:
    """Title of the help panel of these options.

    Returns:
        The translated title.
    """
    return _("Advanced: folders (override folders.* of config.toml)")


def prefer() -> OptionInfo:
    """`--prefer`: folder whose copies are kept first (repeatable, ordered).

    Returns:
        The option definition.
    """
    return cast(
        "OptionInfo",
        typer.Option(
            "--prefer",
            help=_("Folder whose copies are kept first. Repeat it; the order matters."),
            rich_help_panel=_panel(),
            show_default=False,
        ),
    )


def protect() -> OptionInfo:
    """`--protect`: folder never modified (repeatable).

    Returns:
        The option definition.
    """
    return cast(
        "OptionInfo",
        typer.Option(
            "--protect",
            help=_("Folder never modified; its files are the copies kept. Repeatable."),
            rich_help_panel=_panel(),
            show_default=False,
        ),
    )


def exclude() -> OptionInfo:
    """`--exclude`: folder never analysed (repeatable).

    Returns:
        The option definition.
    """
    return cast(
        "OptionInfo",
        typer.Option(
            "--exclude",
            help=_("Folder never analysed, not even read. Repeatable."),
            rich_help_panel=_panel(),
            show_default=False,
        ),
    )


def backup() -> OptionInfo:
    """`--backup`: folder compared, never changed (repeatable, 0204).

    Returns:
        The option definition.
    """
    return cast(
        "OptionInfo",
        typer.Option(
            "--backup",
            help=_(
                "A backup or an old disk: compared, never changed. Says what it "
                "lacks and what only it holds. Repeatable."
            ),
            rich_help_panel=_panel(),
            show_default=False,
        ),
    )


def kept_backup() -> OptionInfo:
    """`--backup` of a command that changes files: a backup it must leave alone (0262).

    `mh` mounts each backup read-only for every command and passes it to those taking
    this option: named, it is never refused for being read-only.

    Returns:
        The option definition.
    """
    return cast(
        "OptionInfo",
        typer.Option(
            "--backup",
            help=_(
                "A backup or an old disk, mounted read-only: never changed, and not "
                "refused for being read-only (mh passes your backups). Repeatable."
            ),
            rich_help_panel=_panel(),
            show_default=False,
        ),
    )


def backup_layer(folders: list[str] | None) -> Layer:
    """Turn `--backup` folders into a settings layer.

    Args:
        folders: The folders given, or None.

    Returns:
        The `[folders] backups` override, empty when none was given.
    """
    return {"folders": {"backups": folders}} if folders else {}


@dataclass(frozen=True, slots=True)
class FolderOptions:
    """The folder options typed on a command line, as their values came."""

    prefer: list[str] | None = None
    protect: list[str] | None = None
    exclude: list[str] | None = None
    backup: list[str] | None = None

    def layer(self) -> Layer:
        """Turn the options into a settings layer.

        Returns:
            The `[folders]` overrides actually given.
        """
        given = {
            "preferred": self.prefer,
            "protected": self.protect,
            "excluded": self.exclude,
            "backups": self.backup,
        }
        folders: dict[str, object] = {k: v for k, v in given.items() if v}
        return {"folders": folders} if folders else {}
