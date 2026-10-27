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
        for line in push_lines(backup, runtime.mapper):
            runtime.output.info(line)
    if backups:
        runtime.output.blank()


def push_lines(backup: BackupCoverage, mapper: HostPathMapper) -> tuple[str, str]:
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
    return f"🗄️ {lacks}", _holds(backup)


def _holds(backup: BackupCoverage) -> str:
    """What only the backup holds: to import, or dealt with before (0245).

    Args:
        backup: The folder compared with the library.

    Returns:
        The line.
    """
    fresh = backup.to_import
    if fresh:
        line = ngettext(
            "   {count} file is only in it, never in your photos ({size}): 'import' "
            "copies it into them.",
            "   {count} files are only in it, never in your photos ({size}): 'import' "
            "copies them into them.",
            len(fresh),
        ).format(
            count=human_number(len(fresh)),
            size=human_size(sum(file.size for file in fresh)),
        )
    else:
        line = _("   Nothing to bring back from it:")
    aside = len(backup.only) - len(fresh)
    if not aside:
        return line
    dealt = ngettext(
        " {count} other file is one you set aside or deleted before: not proposed.",
        " {count} other files are ones you set aside or deleted before: not proposed.",
        aside,
    )
    return line + dealt.format(count=human_number(aside))
