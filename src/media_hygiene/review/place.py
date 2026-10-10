r"""Where the decisions file of a review lies, as the user can find it on the host.

On Docker Desktop the mount table names the Windows folder behind `/reports`
(`C:\Users\<name>\media-hygiene\reports\decisions.json`); with a named volume or on a
Linux host it does not, and the user is told which mount holds the file rather than a
container path they never typed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.i18n import _

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.paths.host_paths import HostPathMapper


DECISIONS_OPTION: Final = "--decisions"
DEFAULT_DECISIONS: Final = "decisions.json"  # what `--decisions` alone names


@dataclass(frozen=True, slots=True)
class DecisionsPlace:
    """The decisions file, named for `clean --decisions` and for the user's eyes."""

    argument: str
    host: str


def decisions_flag(argument: str) -> str:
    """Write the option that names a decisions file, as short as possible.

    Args:
        argument: The file, as `--decisions` takes it.

    Returns:
        `--decisions` alone for the default file, else with the file.
    """
    if argument == DEFAULT_DECISIONS:
        return DECISIONS_OPTION
    return f"{DECISIONS_OPTION} {argument}"


def decisions_place(
    mapper: HostPathMapper, reports_dir: Path, target: Path
) -> DecisionsPlace:
    """Name the decisions file for `--decisions`, and say where it lies on the host.

    Args:
        mapper: Container to host path translator.
        reports_dir: The reports mount point, where a relative `--decisions` lies.
        target: The decisions file, in the container.

    Returns:
        The value to give `--decisions` (relative to the reports folder when the
        file is in it), and the host path or, unknown, the mount holding it.
    """
    in_reports = target.is_relative_to(reports_dir)
    argument = str(target.relative_to(reports_dir) if in_reports else target)
    host = mapper.to_host(target)
    if host != str(target) or not in_reports:
        return DecisionsPlace(argument, host)
    unknown = _("{file}, in the folder mounted on {mount}")
    return DecisionsPlace(argument, unknown.format(file=argument, mount=reports_dir))
