"""Check what the audit sees, and say what it leaves out or handles apart.

Every file of `/data` must be seen once: a file seen twice is no duplicate.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.errors import MountError
from media_hygiene.i18n import _, ngettext
from media_hygiene.paths.overlaps import mount_overlaps
from media_hygiene.services.policy import unmounted_folders
from media_hygiene.services.tool_mounts import refuse_tool_folders_in_data

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from media_hygiene.config.scan_settings import ScanSettings
    from media_hygiene.scan.aliases import Alias
    from media_hygiene.services.runtime import Runtime


def refuse_empty_data(runtime: Runtime) -> None:
    """Stop when no folder is mounted, or a tool folder is mixed with the photos.

    Args:
        runtime: Mount points.

    Raises:
        MountError: Nothing to analyse, or the quarantine, the journal, the cache or
            the reports folder is, holds or lies inside a folder to analyse.
    """
    data_dir = runtime.locations.data_dir
    if not data_dir.is_dir() or not any(data_dir.iterdir()):
        raise MountError(
            _("No folder to analyse under {path}.").format(path=data_dir),
            _('Mount your folders, e.g. -v "C:\\Photos:/data/c/Photos:ro".'),
        )
    refuse_tool_folders_in_data(runtime)


def refuse_overlapping_mounts(runtime: Runtime) -> None:
    r"""Stop when a Windows folder is mounted twice under the data directory.

    Args:
        runtime: Settings, mount points and output.

    Raises:
        MountError: `C:\Photos` and `C:\photos\2019` are mounted on unrelated paths.
    """
    data_dir = runtime.locations.data_dir
    overlaps = mount_overlaps(
        (point, host)
        for point, host in runtime.mounts.host_sources
        if point.is_relative_to(data_dir)
    )
    if not overlaps:
        return
    folders = "; ".join(
        _("{folder} (seen as {first} and as {second})").format(
            folder=item.folder, first=item.first, second=item.second
        )
        for item in overlaps
    )
    raise MountError(
        _(
            "The same folder is mounted twice: {folders}. Each of its files would "
            "look like a duplicate of itself."
        ).format(folders=folders),
        _(
            "Mount each folder only once (a folder already includes its subfolders): "
            "remove one of these -v options."
        ),
    )


def warn_about_aliases(runtime: Runtime, aliases: Sequence[Alias]) -> None:
    """Tell that some files are reachable through two paths and analysed once.

    Args:
        runtime: Settings, mount points and output.
        aliases: The paths set aside.
    """
    if not aliases:
        return
    example = aliases[0]
    runtime.output.warning(
        ngettext(
            "{count} file is reachable through two paths (hard link, or folder "
            "mounted twice): it is analysed once, e.g. {path} is {same_as}.",
            "{count} files are reachable through two paths (hard links, or folder "
            "mounted twice): each is analysed once, e.g. {path} is {same_as}.",
            len(aliases),
        ).format(
            count=len(aliases),
            path=runtime.mapper.to_host(example.path),
            same_as=runtime.mapper.to_host(example.same_as),
        )
    )


def warn_about_scope(runtime: Runtime) -> None:
    """Warn about the scope: unmounted folders, extensions, folder names, other files.

    Args:
        runtime: Settings, mount points and output.
    """
    for folder in unmounted_folders(runtime.settings.folders, runtime.mapper):
        runtime.output.warning(
            _("Configured folder {path} is not mounted: it is ignored.").format(
                path=folder
            ),
        )
    scan = runtime.settings.scan
    if scan.extensions:
        runtime.output.warning(
            _("Only analysed: {scope}.").format(scope=_scope(scan)),
        )
    if scan.excluded_names:
        runtime.output.warning(
            _("Folders skipped by name, wherever they are: {names}.").format(
                names=", ".join(scan.excluded_names)
            ),
        )
    if scan.other_files:
        runtime.output.warning(
            _(
                "Not photos or videos: {extensions}. These files are only compared "
                "byte for byte, and their copies are moved to the quarantine."
            ).format(extensions=", ".join(scan.other_files)),
        )
        runtime.output.tip(
            _(
                "Software folders (.git, node_modules, AppData, Program Files, ...) "
                "are skipped: there, where a file lies makes a program work."
            )
        )


def _scope(scan: ScanSettings) -> str:
    """Name what `--ext` asked for: categories by name, the user's with their list.

    Args:
        scan: The `[scan]` settings.

    Returns:
        E.g. `video, documents (pdf, docx, txt), heic`.
    """
    labels = (
        f"{item} ({', '.join(ext.lstrip('.') for ext in scan.categories[item])})"
        if item in scan.categories
        else item.lstrip(".")
        for item in scan.extensions
    )
    return ", ".join(labels)


def unreadable_index(runtime: Runtime, index: Path, error: Exception) -> MountError:
    """The error of an index that cannot be read.

    Args:
        runtime: Mount points.
        index: The index file.
        error: What SQLite said.

    Returns:
        The error, with the tip to let the next audit build it again.
    """
    return MountError(
        _("The index {file} cannot be read: {reason}.").format(
            file=runtime.mapper.to_host(index), reason=error
        ),
        _("Delete it: the next audit builds it again, reading every file once."),
    )
