"""`docker run … audit` without any `-v`: the error is the first thing said, alone."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from typer.testing import CliRunner

from media_hygiene.constants import ExitCode
from tests.support.cli import point_mounts, run

if TYPE_CHECKING:
    from media_hygiene.paths.locations import Locations


@pytest.mark.parametrize("command", ["audit", "classify"])
def test_without_any_folder_the_error_comes_first(
    command: str, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No 🔒 reassurance, no `:ro` tip, no title before the ❌ and its 💡."""
    point_mounts(locations, monkeypatch)
    locations.config_file.write_text("", encoding="utf-8")  # not a first run
    result = run(CliRunner(), command)
    assert result.exit_code == ExitCode.FAILURE
    lines = [line for line in result.output.splitlines() if line.strip()]
    assert lines[0].startswith("❌ No folder to analyse under")
    text = " ".join(result.output.split())
    assert "The tool only sees the folders you give it with -v" in text
    assert f"cavo789/media-hygiene {command}" in text  # the command to paste
    guide = next(line for line in lines if line.startswith("📖"))
    assert guide.endswith("/start/01-first-audit/")  # never cut
    assert "🔒" not in text
    assert ":ro to the -v" not in text
