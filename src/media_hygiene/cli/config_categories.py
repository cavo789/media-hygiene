"""The parts of `config` around its settings: categories, origins, tips, actions."""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from rich.table import Table

from media_hygiene.cli.config_mounts import on_host
from media_hygiene.config.categories import BUILTIN_CATEGORIES
from media_hygiene.config.loader import Origin
from media_hygiene.i18n import _
from media_hygiene.paths.mount_kind import MountKind

if TYPE_CHECKING:
    from media_hygiene.services.runtime import Runtime


class ConfigAction(StrEnum):
    """What `config` does besides explaining the settings."""

    TIDY = "tidy"


def categories_table(runtime: Runtime) -> Table:
    """Every category `--ext` accepts, built in or from `[scan.categories]`.

    Args:
        runtime: Settings, mount points and output.

    Returns:
        The table: name, extensions, origin.
    """
    table = Table(title=_("Extension categories (--ext)"), title_justify="left")
    for header in (_("Category"), _("Extensions"), _("Origin")):
        table.add_column(header, overflow="fold")
    user = origin_label(runtime.loaded.origin_of("scan", "categories"))
    rows = [
        (name, listed, _("built-in")) for name, listed in BUILTIN_CATEGORIES.items()
    ]
    rows += [
        (name, listed, user)
        for name, listed in runtime.settings.scan.categories.items()
    ]
    for name, listed, origin in rows:
        table.add_row(name, ", ".join(ext.lstrip(".") for ext in listed), origin)
    return table


def origin_label(origin: Origin) -> str:
    """Name where a setting comes from.

    Args:
        origin: Its origin.

    Returns:
        The label.
    """
    labels = {
        Origin.DEFAULT: _("default"),
        Origin.FILE: _("config.toml"),
        Origin.ENV: _("environment"),
        Origin.CLI: _("command line"),
    }
    return labels[origin]


def edit_tip(runtime: Runtime) -> None:
    """Say where to edit the settings, or how to keep them.

    Args:
        runtime: Settings, mount points and output.
    """
    config_file = runtime.locations.config_file
    if runtime.persistent(MountKind.CONFIG):
        runtime.output.tip(
            _("Edit {path} to change these settings; command-line options win.").format(
                path=on_host(runtime, config_file) or config_file,
            ),
        )
    else:
        runtime.output.tip(
            _(
                "To keep settings, mount a folder of yours on /config, e.g. "
                '-v "$HOME\\media-hygiene\\config:/config": config.toml is created '
                "there, commented, on the first run; edit it with any text editor."
            ),
        )
