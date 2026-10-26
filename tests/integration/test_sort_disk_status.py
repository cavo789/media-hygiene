"""`status` says the sorting, from the tree (0405); the pages say the links (0406)."""

from __future__ import annotations

import shutil
from typing import TYPE_CHECKING

from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.audit import AuditService
from media_hygiene.services.group_sort import sort_group
from media_hygiene.services.sort_disk import disk_progress
from media_hygiene.share.albums import ALBUMS_FILE
from tests.support.cli import run
from tests.support.sorting import (
    MIXED,
    PARTY,
    audited_library,
    build_library,
    classify,
)

if TYPE_CHECKING:
    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations


def test_a_folder_moved_in_explorer_counts_as_sorted_after_the_next_audit(
    locations: Locations,
) -> None:
    """Left at first; moved by hand into `2016/2016-07/Kermesse`: sorted."""
    data = locations.data_dir
    runtime = audited_library(locations)
    before = disk_progress(runtime)
    assert before is not None
    assert before.sorted == 0
    assert before.left == before.total
    shutil.move(data / PARTY, data / "c/Photos/2016/2016-07/Kermesse")
    AuditService(runtime, NullProgress()).run()
    after = disk_progress(runtime)
    assert after is not None
    assert after.sorted == before.sorted + 6
    assert after.left == before.left - 6
    assert all("Juillet 2016" not in folder for folder, _files in after.folders)


def test_status_prints_the_line_the_folders_and_the_command(
    cli: CliRunner, locations: Locations
) -> None:
    """One line of percents, the folders left, `search --folder` to open one."""
    build_library(locations.data_dir)
    assert run(cli, "audit").exit_code == 0
    shown = " ".join(run(cli, "status").output.split())
    assert "Sorted: 0 % · nothing special: 0 % · left:" in shown
    assert "Folders left, the largest first:" in shown
    assert "search --folder" in shown


def test_a_group_sorted_from_a_page_says_a_file_not_rewritten(
    locations: Locations,
) -> None:
    """0406: the page's answer holds the line of a file that could not be rewritten."""
    runtime = audited_library(locations)
    classify(runtime)
    locations.reports_dir.mkdir(parents=True, exist_ok=True)
    (locations.reports_dir / ALBUMS_FILE).write_text("not json", encoding="utf-8")
    photo = next((locations.data_dir / MIXED).glob("*.jpg"))
    done = sort_group(runtime, {photo: "2019/2019-03/Divers"}, "Divers")
    assert done.moved == 1
    assert any(ALBUMS_FILE in line for line in done.links), done
