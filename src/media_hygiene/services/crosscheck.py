"""The cross-check use case: run Czkawka (or print its command), compare its results."""

from __future__ import annotations

import shutil
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from functools import cache
from pathlib import Path
from typing import TYPE_CHECKING

from media_hygiene.constants import CZKAWKA_FILE_NAME, MEDIA_EXTENSIONS
from media_hygiene.crosscheck.compare import AnalysedScope, OutsideReason, compare
from media_hygiene.crosscheck.czkawka import (
    CZKAWKA_BINARY,
    CzkawkaCommand,
    CzkawkaScope,
    read_czkawka_groups,
)
from media_hygiene.crosscheck.czkawka_run import CzkawkaRun
from media_hygiene.errors import CrossCheckError
from media_hygiene.i18n import _
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.services.next_command import NextVerb, next_command
from media_hygiene.services.policy import scan_filters

if TYPE_CHECKING:
    from media_hygiene.crosscheck.compare import CrossCheckResult
    from media_hygiene.plan.models import AuditFindings
    from media_hygiene.services.runtime import Runtime


@dataclass(frozen=True, slots=True)
class CzkawkaRefresh:
    """How to get rid of outdated Czkawka results: run it again, or delete them."""

    command: str
    results_file: str
    runs_here: bool = False  # the command is `crosscheck`, which runs Czkawka itself


def czkawka_refresh(runtime: Runtime) -> CzkawkaRefresh:
    """The command that runs Czkawka again, and its results file as the user sees it.

    Args:
        runtime: Settings, mount points and output.

    Returns:
        Both, ready to print: `crosscheck` where the image ships Czkawka, else the
        command that runs it in its own image.
    """
    results_file = runtime.mapper.to_host(czkawka_results(runtime))
    if czkawka_executable() is None:
        return CzkawkaRefresh(czkawka_command(runtime).render(), results_file)
    return CzkawkaRefresh(crosscheck_command(runtime), results_file, runs_here=True)


def crosscheck_command(runtime: Runtime, arguments: str = "crosscheck") -> str:
    """The full `crosscheck` command, with this run's folders.

    Args:
        runtime: Settings, mount points and output.
        arguments: The command line after the image, e.g. with global options.

    Returns:
        The command, ready to paste.
    """
    verb = NextVerb(arguments, (MountKind.REPORTS,))
    return next_command(runtime, verb).command


def czkawka_executable() -> str | None:
    """Find Czkawka's command-line tool: shipped in the image, absent elsewhere.

    Returns:
        Its path, or None.
    """
    return shutil.which(CZKAWKA_BINARY)


def czkawka_run(runtime: Runtime, *, fresh: bool) -> CzkawkaRun | None:
    """How to run Czkawka here: its results in /reports, its cache in /cache.

    Args:
        runtime: Settings, mount points and output.
        fresh: Ignore Czkawka's cache.

    Returns:
        The run, or None where Czkawka is not installed (outside the image).
    """
    executable = czkawka_executable()
    if executable is None:
        return None
    kept = runtime.persistent(MountKind.CACHE)
    cache_dir = runtime.locations.cache_dir if kept else None
    return CzkawkaRun(executable, czkawka_results(runtime), cache_dir, fresh)


def czkawka_results(runtime: Runtime) -> Path:
    """Where Czkawka's command writes its results: the reports mount point.

    Args:
        runtime: Settings, mount points and output.

    Returns:
        The JSON file path, inside this container.
    """
    return runtime.locations.reports_dir / CZKAWKA_FILE_NAME


def czkawka_command(runtime: Runtime) -> CzkawkaCommand:
    """Build the Czkawka command that sees exactly what this run sees.

    Same host folders on the same mount points (Czkawka reports container paths),
    same extensions (categories replaced by theirs: `-x` takes extensions only),
    same excluded folders and folder names, every file size.

    Args:
        runtime: Settings, mount points and output.

    Returns:
        The command.
    """
    settings, locations, mapper = runtime.settings, runtime.locations, runtime.mapper
    sources = dict(runtime.mounts.host_sources)
    roots = runtime.mounts.data_roots(locations.data_dir)
    extensions = settings.scan.resolved or tuple(sorted(MEDIA_EXTENSIONS))
    return CzkawkaCommand(
        mounts=tuple(
            (sources.get(root) or mapper.to_host(root), root) for root in roots
        ),
        output_dir=sources.get(locations.reports_dir)
        or _("<the folder you mount on /reports>"),
        scope=CzkawkaScope(
            data_dir=locations.data_dir,
            extensions=tuple(extension.lstrip(".") for extension in extensions),
            excluded=tuple(  # a backup is compared, never in Czkawka's groups (0204)
                mapper.to_container(folder)
                for folder in (*settings.folders.excluded, *settings.folders.backups)
            ),
            excluded_names=settings.scan.excluded_names,
        ),
    )


def cross_check(runtime: Runtime, findings: AuditFindings) -> CrossCheckResult | None:
    """Compare an audit with Czkawka's results, when they exist.

    Args:
        runtime: Settings, mount points and output.
        findings: The audit just run.

    Returns:
        The comparison, or None when there are no Czkawka results.

    Raises:
        CrossCheckError: The results cover none of the mounted folders.
    """
    results = czkawka_results(runtime)
    if not results.is_file():
        return None
    theirs = read_czkawka_groups(results)
    plan = findings.plan
    broken = (*plan.broken, *plan.protected_broken)
    scope = AnalysedScope(
        roots=findings.roots,
        filters=scan_filters(runtime.settings, runtime.mapper),
        broken=frozenset(item.file.path for item in broken),
        listed=findings.listed,
        folder_exists=cache(Path.is_dir),
    )
    ours = (frozenset(file.path for file in group.files) for group in findings.groups)
    result = compare(ours, theirs, scope)
    files = sum(len(group) for group in theirs)
    if files and result.outside.get(OutsideReason.NOT_MOUNTED) == files:
        raise CrossCheckError(
            _("Czkawka's results cover other folders than this run."),
            _("Run Czkawka with the same -v options: 'audit' prints the command."),
        )
    modified = datetime.fromtimestamp(results.stat().st_mtime, UTC)
    return replace(result, results_date=modified)
