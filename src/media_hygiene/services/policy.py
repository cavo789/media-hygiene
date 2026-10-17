"""Turn the `[folders]`, `[scan]` and `[review]` settings into policies and filters."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.plan.backups import BackupFolders
from media_hygiene.plan.burst_proposals import ProposalLimits
from media_hygiene.plan.keeper import KeepPolicy
from media_hygiene.plan.name_rules import NameRules
from media_hygiene.scan.filters import ScanFilters

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.config.review_settings import ReviewSettings
    from media_hygiene.config.settings import FolderSettings, Settings
    from media_hygiene.paths.host_paths import HostPathMapper


def keep_policy(
    settings: Settings,
    mapper: HostPathMapper,
    with_sidecar: frozenset[Path] = frozenset(),
) -> KeepPolicy:
    """Build the keep policy from the `[folders]` host paths and the `[keep]` names.

    Args:
        settings: The effective settings.
        mapper: Host/container path translator.
        with_sidecar: Files with a sidecar next to them, from the walk.

    Returns:
        The policy, in container paths.
    """
    folders, keep = settings.folders, settings.keep
    return KeepPolicy(
        preferred=tuple(mapper.to_container(path) for path in folders.preferred),
        protected=tuple(mapper.to_container(path) for path in folders.protected),
        names=NameRules.from_patterns(keep.generated_names, keep.generic_folders),
        with_sidecar=with_sidecar,
    )


def backup_folders(settings: Settings, mapper: HostPathMapper) -> BackupFolders:
    """Build the backup folders, compared and never changed (0204).

    Args:
        settings: The effective settings.
        mapper: Host/container path translator.

    Returns:
        The `[folders] backups`, in container paths.
    """
    backups = settings.folders.backups
    return BackupFolders(tuple(mapper.to_container(path) for path in backups))


def proposal_limits(review: ReviewSettings) -> ProposalLimits:
    """Build what the burst review proposes aside from the `[review]` thresholds.

    Args:
        review: The `[review]` settings.

    Returns:
        The thresholds of the proposals.
    """
    return ProposalLimits(
        sharpness_below=review.propose_aside_below,
        identical_below=review.identical_below,
        brightness_gap=review.brightness_gap,
        clipped_gap=review.clipped_gap,
    )


def scan_filters(settings: Settings, mapper: HostPathMapper) -> ScanFilters:
    """Build the scan filters from the excluded host paths and names, the extensions.

    Categories (`photo`, `documents`) are replaced by their extensions.

    Args:
        settings: The effective settings.
        mapper: Host/container path translator.

    Returns:
        The filters, in container paths.
    """
    return ScanFilters(
        excluded=tuple(mapper.to_container(p) for p in settings.folders.excluded),
        extensions=frozenset(settings.scan.resolved),
        excluded_names=settings.scan.excluded_names,
    )


def unmounted_folders(folders: FolderSettings, mapper: HostPathMapper) -> list[str]:
    """List configured folders that are not visible in the container.

    A protected folder that is not mounted protects nothing: the user must know.

    Args:
        folders: The `[folders]` settings.
        mapper: Host/container path translator.

    Returns:
        The host paths that do not exist in the container.
    """
    configured = (
        *folders.preferred,
        *folders.protected,
        *folders.excluded,
        *folders.backups,
    )
    return [path for path in configured if not mapper.to_container(path).exists()]
