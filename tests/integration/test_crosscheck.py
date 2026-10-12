"""The second opinion, from the command line: audit tip, crosscheck, clean verdict."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

from media_hygiene.constants import CZKAWKA_FILE_NAME
from media_hygiene.report.index_page import load_summaries
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.audit import AuditService
from tests.support.cli import run
from tests.support.runtime import make_runtime

if TYPE_CHECKING:
    from collections.abc import Iterable

    import pytest
    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations


def write_czkawka(locations: Locations, groups: Iterable[Iterable[Path]]) -> None:
    """Write results the way czkawka_cli dup -C does."""
    by_size = {
        str(index): [[{"path": str(path), "size": index} for path in group]]
        for index, group in enumerate(groups, start=1)
    }
    (locations.reports_dir / CZKAWKA_FILE_NAME).write_text(json.dumps(by_size))


def media_hygiene_groups(locations: Locations) -> list[list[Path]]:
    """The groups media-hygiene finds on the demo tree."""
    findings = AuditService(make_runtime(locations), NullProgress()).run()
    return [[file.path for file in group.files] for group in findings.groups]


def test_the_audit_prints_the_czkawka_command(cli: CliRunner) -> None:
    """With duplicates, the audit suggests the command for a second opinion."""
    output = run(cli, "--verbosity", "verbose", "audit").output
    assert "Second opinion" in output
    assert "czkawka_cli dup -d " in output
    assert "-C /out/czkawka.json" in output


def test_crosscheck_agrees_and_reports_it(cli: CliRunner, locations: Locations) -> None:
    """Same groups plus files media-hygiene leaves out: agreement, in the report too."""
    groups = media_hygiene_groups(locations)
    data = locations.data_dir
    sidecars = [data / "c/Family Photos/2019/Vacances/IMG_0001.xmp", data / "x.xmp"]
    write_czkawka(locations, [*groups, sidecars])
    result = run(cli, "crosscheck")
    assert result.exit_code == 0, result.output
    assert "Czkawka agrees" in result.output
    assert "other file types: 2" in " ".join(result.output.split())
    verdict = load_summaries(locations.reports_dir)[0].crosscheck
    assert verdict is not None
    assert verdict.agrees
    assert verdict.set_aside == 2


def test_crosscheck_lists_disagreements(cli: CliRunner, locations: Locations) -> None:
    """A group only Czkawka found is shown, with its paths."""
    data = locations.data_dir
    # Two existing, different photos: Czkawka alone groups them.
    extra = [
        data / "c/Family Photos/Rafale/IMG_200.jpg",
        data / "c/Family Photos/Rafale/IMG_201.jpg",
    ]
    write_czkawka(locations, [*media_hygiene_groups(locations), extra])
    output = run(cli, "crosscheck").output
    assert "Czkawka disagrees on 1 group" in output
    assert "only Czkawka" in output


def test_crosscheck_needs_results_and_a_reports_mount(
    cli: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Without results: the command to run; without /reports: a mount error."""
    missing = run(cli, "crosscheck")
    assert missing.exit_code == 1
    assert "czkawka_cli dup" in missing.output
    monkeypatch.delenv("MEDIA_HYGIENE_REPORTS_DIR")
    unmounted = run(cli, "crosscheck")
    assert unmounted.exit_code == 1
    assert "/reports" in unmounted.output


def test_clean_shows_the_verdict_but_never_needs_it(
    cli: CliRunner, locations: Locations
) -> None:
    """No results is said; results of other folders are a warning: the clean runs."""
    assert "For a second opinion, run 'crosscheck'" in run(cli, "clean", "--yes").output
    assert run(cli, "undo").exit_code == 0
    write_czkawka(locations, [[Path("/elsewhere/a.jpg"), Path("/elsewhere/b.jpg")]])
    result = run(cli, "clean", "--yes")
    assert result.exit_code == 0, result.output
    assert "cover other folders" in result.output


def test_crosscheck_names_the_folders_it_never_analyses(
    cli: CliRunner, locations: Locations
) -> None:
    """Czkawka's files in a recycle bin: counted, and the folder named."""
    data = locations.data_dir
    trash = [data / "c/$RECYCLE.BIN/a.jpg", data / "c/$RECYCLE.BIN/b.jpg"]
    trash[0].parent.mkdir()
    write_czkawka(locations, [*media_hygiene_groups(locations), trash])
    result = run(cli, "crosscheck")
    assert result.exit_code == 0, result.output
    assert "• C:\\$RECYCLE.BIN: 2" in result.output


def test_outdated_results_are_ignored_with_the_way_out(
    cli: CliRunner, locations: Locations
) -> None:
    """Czkawka ran before files were removed: no verdict, its command, its file."""
    removed = [locations.data_dir / "c/gone.jpg", locations.data_dir / "c/gone2.jpg"]
    write_czkawka(locations, [*media_hygiene_groups(locations), removed])
    output = run(cli, "crosscheck").output
    assert "out of date" in output
    assert "Czkawka agrees" not in output
    assert "czkawka_cli dup" in output
    assert "czkawka.json" in output
    assert load_summaries(locations.reports_dir)[0].crosscheck is None
