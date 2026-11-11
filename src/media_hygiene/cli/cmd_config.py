"""`media-hygiene config`: show every effective setting, its origin, and the mounts."""

# pylint: disable=import-outside-toplevel,too-many-locals  # lazy: a command imports
# the code it runs when it runs; those imports count as local variables.

from __future__ import annotations

from typing import Annotated, Final

import typer

from media_hygiene.cli.config_categories import ConfigAction
from media_hygiene.cli.context import runtime_of
from media_hygiene.i18n import _

_SYSTEM_NAMES_AFTER: Final = ("scan", "excluded_names")
_PEOPLE, _IGNORED = "people", "ignored"


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


def config_command(  # pylint: disable=too-many-arguments  # one per option
    ctx: typer.Context,
    action: Annotated[
        ConfigAction | None,
        typer.Argument(
            help=_(
                "tidy: list the entries of config.toml that point at nothing any "
                "more (folders gone, rules matching no photo)."
            ),
        ),
    ] = None,
    *,
    apply: Annotated[
        bool,
        typer.Option(
            "--apply",
            help=_(
                "With tidy: remove the ticked entries, after a copy of config.toml."
            ),
        ),
    ] = False,
    dates: Annotated[
        bool,
        typer.Option(
            "--dates",
            help=_("With tidy: tick the date_range rules with no photo too."),
        ),
    ] = False,
    superseded: Annotated[
        bool,
        typer.Option(
            "--superseded",
            help=_(
                "With tidy: tick the path rules whose files already sit in folders "
                "you named too."
            ),
        ),
    ] = False,
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
    convention: Annotated[
        bool,
        typer.Option(
            "--convention",
            help=_(
                "Move the [classify] layouts of your config.toml to the sort "
                "convention year/year-month/event: shows each change, asks, writes."
            ),
        ),
    ] = False,
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            help=_(
                "With --upgrade or --convention: list what would change, write nothing."
            ),
        ),
    ] = False,
) -> None:
    """Explain the effective configuration and the state of each mount point.

    Args:
        ctx: Typer context holding the runtime.
        action: `tidy`, or nothing.
        apply: `--apply`.
        dates: `--dates`.
        superseded: `--superseded`.
        upgrade: `--upgrade`.
        convention: `--convention`.
        dry_run: `--dry-run`.
    """
    from rich.table import Table

    from media_hygiene.cli.config_categories import (
        categories_table,
        edit_tip,
        origin_label,
    )
    from media_hygiene.cli.config_mounts import mounts_table
    from media_hygiene.cli.config_upgrade_flow import show_upgrade, upgrade_tip
    from media_hygiene.scan.skipped_dirs import SYSTEM_DIR_NAMES

    runtime = runtime_of(ctx)
    if action is ConfigAction.TIDY:
        from media_hygiene.cli.config_tidy_flow import show_tidy
        from media_hygiene.config.tidy_rules import OptIn

        asked = {OptIn.DATES: dates, OptIn.SUPERSEDED: superseded}
        show_tidy(
            runtime, apply=apply, opt_in=frozenset(k for k, v in asked.items() if v)
        )
        return
    if convention:
        from media_hygiene.cli.config_convention_flow import show_convention

        show_convention(runtime, dry_run=dry_run)
        return
    if upgrade or dry_run:
        show_upgrade(runtime, dry_run=dry_run)
        return
    settings = runtime.settings.model_dump(mode="json")
    table = Table(title=_("Effective settings"), title_justify="left")
    for header in (_("Setting"), _("Value"), _("Origin")):
        table.add_column(header, overflow="fold")
    for section, values in settings.items():
        for key, value in values.items():
            origin = origin_label(runtime.loaded.origin_of(section, key))
            table.add_row(f"{section}.{key}", _shown(section, key, value), origin)
            if (section, key) == _SYSTEM_NAMES_AFTER:
                # Always skipped too: the user's names add to these.
                system = str(list(SYSTEM_DIR_NAMES))
                table.add_row(_("(always skipped)"), system, _("built-in"))
    runtime.output.show(table)
    runtime.output.blank()
    runtime.output.show(categories_table(runtime))
    runtime.output.blank()
    runtime.output.show(mounts_table(runtime))
    runtime.output.blank()
    edit_tip(runtime)
    upgrade_tip(runtime)
