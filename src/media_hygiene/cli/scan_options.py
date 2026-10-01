"""The `[scan]` options of `audit`, `clean` and `crosscheck`, and their settings layer.

Translated once the locale is known; built before the settings are read.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import typer

from media_hygiene.config.categories import BUILTIN_CATEGORIES
from media_hygiene.i18n import _

if TYPE_CHECKING:
    from typer.models import OptionInfo

    from media_hygiene.config.layers import Layer


def _panel_scan() -> str:
    """Title of the help panel of these options.

    Returns:
        The translated title.
    """
    return _("Scan (override scan.* of config.toml)")


def extensions() -> OptionInfo:
    """`--ext`: only analyse some categories or extensions (repeatable).

    Built before the settings are read: the user's categories cannot be listed.

    Returns:
        The option definition.
    """
    return cast(
        "OptionInfo",
        typer.Option(
            "--ext",
            help=_(
                "Only analyse these categories or extensions, e.g. --ext photo,video "
                "or --ext png,webp (repeatable). Categories: {categories} and those "
                "of scan.categories in config.toml. Other types too, such as --ext "
                "pdf,docx: their copies are moved to the quarantine. Default: media "
                "(every photo, RAW and video)."
            ).format(categories=", ".join(BUILTIN_CATEGORIES)),
            rich_help_panel=_panel_scan(),
            show_default=False,
        ),
    )


def exclude_name() -> OptionInfo:
    """`--exclude-name`: folder names skipped wherever they are (repeatable).

    Returns:
        The option definition.
    """
    return cast(
        "OptionInfo",
        typer.Option(
            "--exclude-name",
            help=_(
                "Folder name never analysed, wherever it is, case ignored; * and ? "
                "allowed, e.g. --exclude-name Thumbnails,.Trash-* (repeatable). Adds "
                "to the system folders already skipped. For one precise folder, use "
                "--exclude."
            ),
            rich_help_panel=_panel_scan(),
            show_default=False,
        ),
    )


def scan_layer(ext: list[str] | None, names: list[str] | None = None) -> Layer:
    """Turn the `--ext` and `--exclude-name` options into a settings layer.

    Args:
        ext: `--ext` values (validated and split by the settings).
        names: `--exclude-name` values (validated and split by the settings).

    Returns:
        The `[scan]` overrides actually given.
    """
    given = {"extensions": ext, "excluded_names": names}
    scan: dict[str, object] = {key: value for key, value in given.items() if value}
    return {"scan": scan} if scan else {}
