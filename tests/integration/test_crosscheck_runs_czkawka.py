"""`crosscheck` runs Czkawka itself where the image ships it (a fake `czkawka_cli`)."""

from __future__ import annotations

import json
import os
from typing import TYPE_CHECKING, Final

import pytest
from typer.testing import CliRunner

from media_hygiene.constants import CZKAWKA_FILE_NAME
from media_hygiene.crosscheck.czkawka import CZKAWKA_BINARY
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.audit import AuditService
from tests.support.cli import run
from tests.support.runtime import make_runtime

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from media_hygiene.paths.locations import Locations

# The demo tree and the mount points first: the fake's results come from an audit of it.
pytestmark = pytest.mark.usefixtures("cli")

_FAKE: Final = """#!/bin/sh
printf '%s\\n' "$@" > "{record}"
printf 'cache=%s\\n' "$XDG_CACHE_HOME" >> "{record}"
while [ $# -gt 0 ]; do
  if [ "$1" = "-C" ]; then cp "{results}" "$2"; fi
  shift
done
exit {code}
"""


def install_fake(locations: Locations, folder: Path, code: int = 0) -> Path:
    """Put a fake `czkawka_cli` on PATH, writing media-hygiene's own groups.

    Returns:
        The file where it records its arguments and cache folder.
    """
    findings = AuditService(make_runtime(locations), NullProgress()).run()
    by_size = {
        str(group.size): [[{"path": str(file.path)} for file in group.files]]
        for group in findings.groups
    }
    results = folder / "results.json"
    results.write_text(json.dumps(by_size), encoding="utf-8")
    record = folder / "record.txt"
    fake = folder / "bin" / CZKAWKA_BINARY
    fake.parent.mkdir()
    fake.write_text(
        _FAKE.format(record=record, results=results, code=code), encoding="utf-8"
    )
    fake.chmod(0o755)
    return record


type Install = Callable[[int], Path]


@pytest.fixture
def install(
    locations: Locations, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Install:
    """Put a fake Czkawka on PATH, ending with the exit code it is given."""

    def put(code: int) -> Path:
        recorded = install_fake(locations, tmp_path, code)
        path = f"{tmp_path / 'bin'}{os.pathsep}{os.environ['PATH']}"
        monkeypatch.setenv("PATH", path)
        return recorded

    return put


@pytest.fixture
def record(install: Install) -> Path:
    """A fake Czkawka on PATH that agrees with media-hygiene."""
    return install(0)


def test_crosscheck_runs_czkawka_then_compares(
    cli: CliRunner, locations: Locations, record: Path
) -> None:
    """One command: Czkawka runs on the audit's folders, its results compared."""
    result = run(cli, "crosscheck")
    assert result.exit_code == 0, result.output
    assert "Czkawka finished in" in result.output
    assert "Czkawka agrees" in result.output
    arguments = record.read_text(encoding="utf-8").splitlines()
    assert arguments[:3] == ["dup", "-d", str(locations.data_dir)]
    assert "-H" not in arguments
    results = locations.reports_dir / CZKAWKA_FILE_NAME
    assert arguments[arguments.index("-C") + 1] == f"{results}.part"
    assert results.is_file()
    assert not results.with_name(f"{CZKAWKA_FILE_NAME}.part").exists()
    assert f"cache={locations.cache_dir}" in arguments


def test_fresh_ignores_czkawka_cache(cli: CliRunner, record: Path) -> None:
    """`--fresh`: Czkawka hashes every file again."""
    assert run(cli, "crosscheck", "--fresh").exit_code == 0
    assert "-H" in record.read_text(encoding="utf-8").splitlines()


def test_print_command_leaves_czkawka_to_the_user(cli: CliRunner, record: Path) -> None:
    """`--print-command`: nothing runs, the command to paste is printed."""
    result = run(cli, "crosscheck", "--print-command")
    assert result.exit_code == 1
    assert "czkawka_cli dup" in result.output
    assert not record.exists()


def test_a_failed_czkawka_leaves_no_results(
    locations: Locations, install: Install
) -> None:
    """Exit code 3: said plainly, and no results file to compare later."""
    install(3)
    result = run(CliRunner(), "crosscheck")
    assert result.exit_code == 1
    assert "Czkawka stopped with exit code 3" in result.output
    assert not (locations.reports_dir / CZKAWKA_FILE_NAME).exists()
    assert not list(locations.reports_dir.glob("*.part"))


def test_the_audit_suggests_crosscheck(cli: CliRunner, record: Path) -> None:
    """Where Czkawka is shipped, the tip is the crosscheck command, not Czkawka's."""
    output = run(cli, "--verbosity", "verbose", "audit").output
    assert "'crosscheck' runs Czkawka" in output
    assert "czkawka_cli dup" not in output
    assert not record.exists()
