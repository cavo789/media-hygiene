"""`classify --path`: only the files below a folder get a proposal; `--year` too."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from typer.testing import CliRunner

from tests.support.cli import point_mounts, run
from tests.support.media import MediaFactory

if TYPE_CHECKING:
    import pytest

    from media_hygiene.paths.locations import Locations


def _cli(locations: Locations, monkeypatch: pytest.MonkeyPatch) -> CliRunner:
    """Two folders: 2015 (two photos) and 2016 (one), their dates in their names."""
    point_mounts(locations, monkeypatch)
    media = MediaFactory(locations.data_dir)
    media.image("c/Photos/A/IMG_20150702_101010.jpg", seed=1)
    media.image("c/Photos/A/IMG_20160702_101010.jpg", seed=2)
    media.image("c/Photos/B/IMG_20160703_101010.jpg", seed=3)
    return CliRunner()


def _proposed(output: str) -> int:
    """How many files the summary proposes a place for."""
    found = re.search(r"Already in place: \d+ of (\d+)", " ".join(output.split()))
    return int(found[1]) if found else 0


def test_path_proposes_only_the_files_below_it(
    locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    r"""`--path C:\Photos\A`: its two files; with `--year 2016`, one."""
    cli = _cli(locations, monkeypatch)
    assert _proposed(run(cli, "classify").output) == 3
    folder = run(cli, "classify", "--path", "C:\\Photos\\A", "--no-carry-over")
    assert folder.exit_code == 0, folder.output
    assert _proposed(folder.output) == 2
    both = run(cli, "classify", "--path", "C:\\Photos\\A", "--year", "2016")
    assert _proposed(both.output) == 1


def test_a_folder_outside_the_mounts_is_refused(
    locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A folder no -v gives: one message, the failure code, nothing proposed."""
    cli = _cli(locations, monkeypatch)
    result = run(cli, "classify", "--path", "D:\\Elsewhere")
    assert result.exit_code == 1
    assert "The folder D:\\Elsewhere is not mounted." in " ".join(result.output.split())
