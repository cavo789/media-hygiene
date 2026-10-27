"""`media-hygiene backup` and `restore`: the index and settings kept apart (0352)."""

# pylint: disable=import-outside-toplevel  # lazy: a command loads its code when it runs

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

import typer

from media_hygiene.cli.context import runtime_of, user_errors
from media_hygiene.i18n import _

if TYPE_CHECKING:
    from media_hygiene.services.runtime import Runtime


def backup_command(ctx: typer.Context) -> None:
    """Back up the index and the settings into one archive, read back.

    Args:
        ctx: Typer context holding the runtime.
    """
    from media_hygiene.console.formatting import human_size
    from media_hygiene.services.cache_backup import KEPT, make_backup

    runtime = runtime_of(ctx)
    with user_errors(runtime.output):
        backup = make_backup(runtime)
    output = runtime.output
    output.success(
        _("Backup written and read back: {path} ({size}).").format(
            path=runtime.mapper.to_host(backup.path), size=human_size(backup.size)
        )
    )
    _counts(runtime, backup.manifest.counts)
    for old in backup.removed:
        output.info(
            _("Older backup removed ({kept} kept): {name}").format(
                kept=KEPT, name=old.name
            )
        )
    output.tip(
        _(
            "This copy is on the same disk as Docker: it protects from a wrong move, "
            "not from a disk failure; copy it to a USB stick or the NAS too."
        )
    )
    output.next_step(_("if the cache is ever lost: mh restore."))


def restore_command(
    ctx: typer.Context,
    *,
    archive: Annotated[
        str | None,
        typer.Argument(
            help=_("The backup to restore, by its name; the most recent by default."),
            show_default=False,
        ),
    ] = None,
    config: Annotated[
        bool,
        typer.Option(
            "--config",
            help=_(
                "Restore the settings (config.toml, people) too; the index alone "
                "by default."
            ),
        ),
    ] = False,
) -> None:
    """Put back a backup of the index, after backing up the current one.

    Args:
        ctx: Typer context holding the runtime.
        archive: The archive's name, or None for the most recent.
        config: `--config`, the settings restored too.
    """
    from media_hygiene.services.cache_restore import RestoreRequest, restore_backup

    runtime = runtime_of(ctx)
    with user_errors(runtime.output):
        restored = restore_backup(runtime, RestoreRequest(archive, config=config))
    output = runtime.output
    output.success(
        _("Index restored from {name}, read back:").format(name=restored.archive.name)
    )
    _counts(runtime, restored.counts)
    for name in restored.config:
        output.info(_("Setting restored: {name}").format(name=name))
    if restored.before is None:
        output.next_step(_("mh audit: it reads again only what changed."))
        return
    output.info(
        _(
            "↩️ The index replaced was backed up first: mh restore {name} puts it back."
        ).format(name=restored.before.path.name)
    )
    output.next_step(_("mh audit: it reads again only what changed."))


def _counts(runtime: Runtime, counts: dict[str, int]) -> None:
    """Show the rows of each costly table, as read back.

    Args:
        runtime: Settings, mount points and output.
        counts: Table → rows.
    """
    for table, rows in counts.items():
        runtime.output.info(f"  {table}: {rows}")
