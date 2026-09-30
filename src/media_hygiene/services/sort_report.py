"""Around the moves of a sort: folders it may remove, roots it counts, its proof.

The manifest goes to `<reports>/<run>-sort/manifest.json`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from media_hygiene.actions.sort_folders import FolderRules
from media_hygiene.errors import MountError
from media_hygiene.i18n import _
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.services.classify_inputs import root_of
from media_hygiene.services.writable import writable_tip

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.actions.manifest import Manifest
    from media_hygiene.actions.sort_plan import SortPlan
    from media_hygiene.classify.plan_file import ClassifyPlan
    from media_hygiene.services.runtime import Runtime

MANIFEST_FILE_NAME: Final = "manifest.json"
SORT_FOLDER_SUFFIX: Final = "sort"


def folder_rules(runtime: Runtime, plan: ClassifyPlan) -> FolderRules:
    """The folders a sort never removes, and the junk that does not keep one alive.

    Args:
        runtime: Settings, mount points and output.
        plan: The classify plan: the roots of its proposals are never removed.

    Returns:
        The rules.
    """
    mapper, data_dir = runtime.mapper, runtime.locations.data_dir
    roots = runtime.mounts.data_roots(data_dir)
    stops = {data_dir, *roots, *runtime.mounts.mount_points}
    for row in plan.rows:
        stops.add(mapper.to_container(row.root))
        stops.add(root_of(mapper.to_container(row.path), roots, runtime))
    settings = runtime.settings
    kept = (
        *settings.folders.protected,
        *settings.folders.excluded,
        *settings.classify.leave,
    )
    return FolderRules(
        junk=settings.sort.junk_names,
        stops=frozenset(stops),
        kept=tuple(mapper.to_container(path) for path in kept),
        quarantine=runtime.persistent(MountKind.QUARANTINE),
    )


def source_roots(runtime: Runtime, plan: SortPlan) -> tuple[Path, ...]:
    """The mounted folders the files of a sort come from.

    Args:
        runtime: Settings, mount points and output.
        plan: The moves.

    Returns:
        Each root once.
    """
    roots = runtime.mounts.data_roots(runtime.locations.data_dir)
    return tuple({root_of(move.source, roots, runtime) for move in plan.moves})


def write_manifest(runtime: Runtime, manifest: Manifest) -> Path | None:
    """Write `manifest.json` to `<reports>/<run>-sort/`.

    Args:
        runtime: Settings, mount points and output.
        manifest: The proof of the run.

    Returns:
        The file, or None when `/reports` would not survive the container.

    Raises:
        MountError: It could not be written; the run itself is over.
    """
    if not runtime.persistent(MountKind.REPORTS):
        return None
    reports_dir = runtime.locations.reports_dir
    folder = reports_dir / f"{manifest.run_id}-{SORT_FOLDER_SUFFIX}"
    try:
        folder.mkdir(parents=True, exist_ok=True)
        target = folder / MANIFEST_FILE_NAME
        target.write_text(manifest.model_dump_json(indent=1), encoding="utf-8")
    except OSError as exc:
        raise MountError(
            _("The manifest could not be written to {folder}: {reason}.").format(
                folder=runtime.mapper.to_host(reports_dir), reason=exc.strerror or exc
            ),
            writable_tip((reports_dir,)) if isinstance(exc, PermissionError) else None,
        ) from exc
    return target
