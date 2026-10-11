"""`status` on the demo tree: audit, clean, purge, each time the step that follows."""

from __future__ import annotations

from typing import TYPE_CHECKING

from tests.support.cli import run

if TYPE_CHECKING:
    from typer.testing import CliRunner


def test_status_follows_the_clean_path(cli: CliRunner) -> None:
    """After the audit: clean. After the clean: the quarantine, undo, purge.

    After the purge, no undo is offered any more: nothing is left to bring back.
    """
    run(cli, "audit")
    audited = run(cli, "status")
    assert audited.exit_code == 0, audited.output
    assert "Last audit:" in audited.output
    assert "'clean' sets them aside" in audited.output
    assert run(cli, "clean", "--yes").exit_code == 0
    cleaned = run(cli, "status").output
    assert "Last clean:" in cleaned
    assert "Quarantine: 12 files" in cleaned
    assert "Runs you can still undo:" in cleaned
    assert "media-hygiene undo " in cleaned
    assert "'purge' frees its space" in cleaned
    assert "media-hygiene purge " in cleaned
    assert run(cli, "purge", "--yes").exit_code == 0
    purged = run(cli, "status").output
    assert "Quarantine: empty." in purged
    assert "Nothing left to do" in purged
    # The quarantined copies are gone: `undo` would put nothing back.
    assert "Runs you can still undo:" not in purged
    assert "media-hygiene undo " not in purged
