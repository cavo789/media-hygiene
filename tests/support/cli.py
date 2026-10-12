"""Invoke the command line in-process."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.cli.app import build_app
from media_hygiene.paths.mount_kind import MountKind

if TYPE_CHECKING:
    import pytest
    from typer.testing import CliRunner, Result

    from media_hygiene.paths.locations import Locations


def run(runner: CliRunner, *args: str) -> Result:
    """Invoke the CLI with `args`, letting unexpected exceptions through.

    Args:
        runner: The Typer runner.
        *args: The command line.

    Returns:
        The result.
    """
    return runner.invoke(build_app(), list(args), catch_exceptions=False)


def point_mounts(locations: Locations, monkeypatch: pytest.MonkeyPatch) -> None:
    """Point every mount point of the command line to the test's temporary folders.

    Args:
        locations: The test mount points.
        monkeypatch: Pytest monkeypatch fixture.
    """
    for kind in MountKind:
        monkeypatch.setenv(
            f"MEDIA_HYGIENE_{kind.value.upper()}_DIR", str(locations.path_of(kind))
        )
