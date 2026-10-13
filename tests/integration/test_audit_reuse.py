"""A second audit takes unchanged folders from the index; `--full` reads them all."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from tests.support.cli import run

if TYPE_CHECKING:
    from typer.testing import CliRunner

_REUSED = re.compile(r"(\d+) unchanged folders? taken from the index, (\d+) read")


def _said(cli: CliRunner, *args: str) -> str:
    """Run a command that must succeed; its output on one line."""
    result = run(cli, *args)
    assert result.exit_code == 0, result.output
    return " ".join(result.output.split())


def test_the_second_audit_reuses_the_listings(cli: CliRunner) -> None:
    """First audit: everything read; second: everything reused, the same findings."""
    first = _said(cli, "audit")
    assert not _REUSED.search(first)
    second = _said(cli, "audit")
    found = _REUSED.search(second)
    assert found is not None
    assert int(found[1]) > 0
    assert found[2] == "0"
    assert "'audit --full' reads every folder" in second
    scanned = re.compile(r"Media files scanned │ (\d+)")
    assert scanned.findall(first) == scanned.findall(second)


def test_full_reads_every_folder(cli: CliRunner) -> None:
    """`audit --full`: nothing taken from the index."""
    _said(cli, "audit")
    assert not _REUSED.search(_said(cli, "audit", "--full"))
