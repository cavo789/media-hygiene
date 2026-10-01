"""Folders skipped by name on every disk: trash folders, `--exclude-name`, Czkawka."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.audit import AuditService
from media_hygiene.services.crosscheck import czkawka_command
from tests.support.cli import run
from tests.support.media import MediaFactory
from tests.support.runtime import make_runtime, output_of

if TYPE_CHECKING:
    import pytest
    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations


def test_a_trash_copy_is_no_duplicate(locations: Locations) -> None:
    """A photo and its copy in a Linux trash: the trash is never analysed."""
    media = MediaFactory(locations.data_dir)
    photo = media.image("d/Disk/Photos/IMG_1.jpg", seed=1)
    media.copy(photo, "d/Disk/.Trash-1000/files/IMG_1.jpg")
    findings = AuditService(make_runtime(locations), NullProgress()).run()
    assert not findings.groups


def test_names_from_the_file_and_the_environment(
    locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`excluded_names` skips the folder wherever it is, and the audit says so."""
    media = MediaFactory(locations.data_dir)
    photo = media.image("c/Photos/2019/IMG_1.jpg", seed=1)
    media.copy(photo, "c/Photos/2019/thumbnails/IMG_1.jpg")
    locations.config_file.write_text("[scan]\nexcluded_names = ['Thumbnails']\n")
    runtime = make_runtime(locations)
    assert not AuditService(runtime, NullProgress()).run().groups
    assert "skipped by name, wherever they are: Thumbnails." in output_of(runtime)
    assert '-E "*/Thumbnails/*"' in czkawka_command(runtime).render()
    monkeypatch.setenv("MEDIA_HYGIENE_SCAN__EXCLUDED_NAMES", '["Other"]')
    assert len(AuditService(make_runtime(locations), NullProgress()).run().groups) == 1


def test_exclude_name_on_the_command_line(cli: CliRunner) -> None:
    """`--exclude-name` is accepted, a path is refused, `config` lists system names."""
    result = run(cli, "audit", "--exclude-name", "Vacances,.Trash-*")
    assert result.exit_code == 0, result.output
    assert "wherever they are: Vacances, .Trash-*." in result.output
    path = run(cli, "audit", "--exclude-name", "C:\\Photos\\Thumbnails")
    assert path.exit_code == 1
    assert "use --exclude" in path.output
    config = run(cli, "config").output
    assert "(always skipped)" in config
    assert "@recycle" in config
