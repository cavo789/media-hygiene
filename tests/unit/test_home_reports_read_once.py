"""The home state reads the reports folder once (0821: 616 folders, read twice)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.cli.home_state import home_state
from media_hygiene.constants import REPORT_FILE_NAME
from media_hygiene.report.index_page import report_folders
from media_hygiene.services import status
from tests.support.report_folders import write_summary
from tests.support.runtime import make_locations, make_runtime

if TYPE_CHECKING:
    from pathlib import Path

    import pytest


def test_reports_are_read_once_and_linked(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """One read of the summaries feeds the last audit and the report links."""
    runtime = make_runtime(make_locations(tmp_path))
    folder = runtime.locations.reports_dir / "20261114-210000-audit"
    write_summary(folder)
    (folder / REPORT_FILE_NAME).write_text("<html></html>")
    calls: list[Path] = []

    def counted(reports_dir: Path) -> object:
        calls.append(reports_dir)
        return report_folders(reports_dir)

    monkeypatch.setattr(f"{status.__name__}.report_folders", counted)
    state = home_state(runtime)
    assert len(calls) == 1
    assert [link.url.rsplit("/", 2)[-2] for link in state.reports] == [folder.name]
