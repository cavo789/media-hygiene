"""The console side of `config --upgrade`, and the tip that offers it."""

from __future__ import annotations

from importlib.metadata import version as package_version
from typing import TYPE_CHECKING

from rich.markup import escape

from media_hygiene.cli.context import user_errors
from media_hygiene.config.upgrade import written_by
from media_hygiene.console.formatting import human_number
from media_hygiene.constants import APP_NAME
from media_hygiene.i18n import _, ngettext
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.services.config_upgrade import config_upgrade, pending_upgrade
from media_hygiene.text_files import read_user_text

if TYPE_CHECKING:
    from media_hygiene.services.runtime import Runtime


def show_upgrade(runtime: Runtime, *, dry_run: bool) -> None:
    """Complete `config.toml` (or list what it would gain), and say what it now holds.

    Args:
        runtime: Settings, mount points and output.
        dry_run: Write nothing.
    """
    output = runtime.output
    host = runtime.mapper.to_host(runtime.locations.config_file)
    with user_errors(output):
        upgrade = config_upgrade(runtime, dry_run=dry_run)
    count = len(upgrade.added)
    if not count:
        output.success(
            _("{path} is up to date ({version}).").format(
                path=escape(host), version=package_version(APP_NAME)
            )
        )
        return
    if dry_run:
        output.info(
            ngettext(
                "{count} setting would be added to {path}, with its explanation:",
                "{count} settings would be added to {path}, with their explanation:",
                count,
            ).format(count=human_number(count), path=escape(host))
        )
    else:
        output.success(
            ngettext(
                "{count} setting added to {path}, read back from the disk:",
                "{count} settings added to {path}, read back from the disk:",
                count,
            ).format(count=human_number(count), path=escape(host))
        )
    for name in upgrade.added:
        output.info(f"  + {escape(name)}")
    if dry_run:
        output.tip(_("Nothing was written: run 'config --upgrade' to add them."))
        return
    output.tip(
        _(
            "Your values and comments are kept; the new settings hold their default "
            "value."
        )
    )


def upgrade_tip(runtime: Runtime) -> None:
    """Offer `config --upgrade` when `config.toml` lacks settings of this version.

    Args:
        runtime: Settings, mount points and output.
    """
    config_file = runtime.locations.config_file
    if not runtime.persistent(MountKind.CONFIG) or not config_file.is_file():
        return
    text = read_user_text(config_file)
    missing = len(pending_upgrade(text).added)
    if not missing:
        return
    version = written_by(text)
    message = (
        ngettext(
            "config.toml was written by {version}: {count} new setting since.",
            "config.toml was written by {version}: {count} new settings since.",
            missing,
        )
        if version
        else ngettext(
            "config.toml was written by an earlier version: {count} new setting since.",
            "config.toml was written by an earlier version: {count} new settings "
            "since.",
            missing,
        )
    )
    output = runtime.output
    output.tip(message.format(version=version, count=human_number(missing)))
    output.tip(
        _(
            "'config --upgrade' adds them with their explanation; your values are kept "
            "(--dry-run lists them first)."
        )
    )
