"""`media-hygiene config`: show every effective setting, its origin, and the mounts."""

# pylint: disable=import-outside-toplevel,too-many-locals  # lazy: a command imports
# the code it runs when it runs; those imports count as local variables.

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Final

import typer

from media_hygiene.cli.context import runtime_of
from media_hygiene.i18n import _

if TYPE_CHECKING:
    from rich.table import Table

    from media_hygiene.config.loader import Origin
    from media_hygiene.services.runtime import Runtime


_SYSTEM_NAMES_AFTER: Final = ("scan", "excluded_names")
_PEOPLE, _IGNORED = "people", "ignored"


def _origin_label(origin: Origin) -> str:
    from media_hygiene.config.loader import Origin

    labels = {
        Origin.DEFAULT: _("default"),
        Origin.FILE: _("config.toml"),
        Origin.ENV: _("environment"),
        Origin.CLI: _("command line"),
    }
    return labels[origin]


def _shown(section: str, key: str, value: object) -> str:
    """Write a value; the names of `people` by name, their thousands of faces counted.

    Args:
        section: The section.
        key: The setting.
        value: Its value, as JSON.

    Returns:
        The text of the cell.
    """
    if section != _PEOPLE or not isinstance(value, list):
        return str(value)
    if key == _IGNORED:
        return _("{count} faces").format(count=len(value))
    return ", ".join(
        _("{name} ({count} faces)").format(name=item["name"], count=len(item["faces"]))
        for item in value
        if isinstance(item, dict)
    )


def config_command(
    ctx: typer.Context,
    *,
    upgrade: Annotated[
        bool,
        typer.Option(
            "--upgrade",
            help=_(
                "Add the settings of this version to your config.toml, with their "
                "explanation; your values and comments are kept."
            ),
        ),
    ] = False,
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            help=_("With --upgrade: list the settings it would add, write nothing."),
        ),
    ] = False,
) -> None:
    """Explain the effective configuration and the state of each mount point.

    Args:
        ctx: Typer context holding the runtime.
        upgrade: `--upgrade`.
        dry_run: `--dry-run`.
    """
    from rich.table import Table

    from media_hygiene.cli.config_mounts import mounts_table, on_host
    from media_hygiene.cli.config_upgrade_flow import show_upgrade, upgrade_tip
    from media_hygiene.paths.mount_kind import MountKind
    from media_hygiene.scan.skipped_dirs import SYSTEM_DIR_NAMES

    runtime = runtime_of(ctx)
    if upgrade or dry_run:
        show_upgrade(runtime, dry_run=dry_run)
        return
    settings = runtime.settings.model_dump(mode="json")
    table = Table(title=_("Effective settings"), title_justify="left")
    for header in (_("Setting"), _("Value"), _("Origin")):
        table.add_column(header, overflow="fold")
    for section, values in settings.items():
        for key, value in values.items():
            origin = _origin_label(runtime.loaded.origin_of(section, key))
            table.add_row(f"{section}.{key}", _shown(section, key, value), origin)
            if (section, key) == _SYSTEM_NAMES_AFTER:
                # Always skipped too: the user's names add to these.
                system = str(list(SYSTEM_DIR_NAMES))
                table.add_row(_("(always skipped)"), system, _("built-in"))
    runtime.output.show(table)
    runtime.output.blank()
    runtime.output.show(_categories_table(runtime))
    runtime.output.blank()
    runtime.output.show(mounts_table(runtime))
    runtime.output.blank()
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
    upgrade_tip(runtime)


def _categories_table(runtime: Runtime) -> Table:
    """Every category `--ext` accepts, built in or from `[scan.categories]`.

    Args:
        runtime: Settings, mount points and output.

    Returns:
        The table: name, extensions, origin.
    """
    from rich.table import Table

    from media_hygiene.config.categories import BUILTIN_CATEGORIES

    table = Table(title=_("Extension categories (--ext)"), title_justify="left")
    for header in (_("Category"), _("Extensions"), _("Origin")):
        table.add_column(header, overflow="fold")
    user = _origin_label(runtime.loaded.origin_of("scan", "categories"))
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
