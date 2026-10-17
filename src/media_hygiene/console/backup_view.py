"""What the audit says of each backup folder: what it lacks, what only it holds."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.markup import escape

from media_hygiene.console.formatting import human_number, human_size
from media_hygiene.i18n import _, ngettext

if TYPE_CHECKING:
    from collections.abc import Sequence

    from media_hygiene.paths.host_paths import HostPathMapper
    from media_hygiene.plan.backups import BackupCoverage
    from media_hygiene.services.runtime import Runtime


def show_backups(runtime: Runtime, backups: Sequence[BackupCoverage]) -> None:
    """Say, in two lines per backup folder, what it lacks and what only it holds.

    Args:
        runtime: Settings, mount points and output.
        backups: Each backup folder compared with the library.
    """
    for backup in backups:
        for line in backup_lines(backup, runtime.mapper):
            runtime.output.info(line)
    if backups:
        runtime.output.blank()


def backup_lines(backup: BackupCoverage, mapper: HostPathMapper) -> tuple[str, str]:
    """The two lines of one backup folder.

    Args:
        backup: The folder compared with the library.
        mapper: Host/container path translator.

    Returns:
        What the library has that the backup lacks, then what only the backup holds.
    """
    folder = escape(mapper.to_host(backup.folder))
    missing = len(backup.missing)
    if missing:
        lacks = ngettext(
            "{folder}: {count} file of your photos is not in this backup ({size}).",
            "{folder}: {count} files of your photos are not in this backup ({size}).",
            missing,
        ).format(
            folder=folder,
            count=human_number(missing),
            size=human_size(backup.missing_size),
        )
    else:
        lacks = _("{folder}: every file of your photos is in this backup.").format(
            folder=folder
        )
    only = len(backup.only)
    if not only:
        return f"🗄️ {lacks}", _(
            "   Nothing is only in it: each of its files has a copy in your photos."
        )
    holds = ngettext(
        "   {count} file is only in it, nowhere else ({size}): copy it before "
        "wiping this disk.",
        "   {count} files are only in it, nowhere else ({size}): copy them before "
        "wiping this disk.",
        only,
    )
    return f"🗄️ {lacks}", holds.format(
        count=human_number(only), size=human_size(backup.only_size)
    )
