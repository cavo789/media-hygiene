"""Refuse to start when a tool folder is mixed with the folders to analyse.

Refused for every command that reads or changes the photos (`audit`, `classify`,
`clean`, `sort`, `album`), and for the two that delete inside a tool folder (`purge`,
`reports --prune`). `undo` is never refused: it is how files come back.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from media_hygiene.errors import MountError
from media_hygiene.i18n import _
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.paths.tool_overlaps import DataScope, tool_overlaps

if TYPE_CHECKING:
    from media_hygiene.services.runtime import Runtime

# The folders the tool writes to, apart from `/config` (config.toml only).
TOOL_FOLDERS: Final = (
    MountKind.QUARANTINE,
    MountKind.JOURNAL,
    MountKind.CACHE,
    MountKind.REPORTS,
)


def refuse_tool_folders_in_data(
    runtime: Runtime, kinds: tuple[MountKind, ...] = TOOL_FOLDERS
) -> None:
    """Stop when a tool folder is, holds or lies inside a folder to analyse.

    Args:
        runtime: Settings, mount points and output.
        kinds: The tool folders to check.

    Raises:
        MountError: The first overlap found, with how to mount the folder instead.
    """
    locations, mapper = runtime.locations, runtime.mapper
    scope = DataScope(
        runtime.mounts,
        runtime.mounts.data_roots(locations.data_dir),
        tuple(mapper.to_container(path) for path in runtime.settings.folders.excluded),
    )
    overlaps = tool_overlaps(scope, ((kind, locations.path_of(kind)) for kind in kinds))
    if not overlaps:
        return
    first = overlaps[0]
    raise MountError(
        _(
            "The {kind} folder ({tool}) and the photo folder {data} are one inside "
            "the other: the tool's own files would mix with your photos."
        ).format(
            kind=first.kind.value,
            tool=mapper.to_host(first.tool),
            data=mapper.to_host(first.data),
        ),
        _(
            'Mount it outside your photo folders, e.g. -v "$HOME\\media-hygiene\\'
            '{kind}:/{kind}" (or list it in [folders] excluded).'
        ).format(kind=first.kind.value),
    )
