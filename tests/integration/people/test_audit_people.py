"""`audit --people`: count, measure, ask; no, no terminal and --yes; never alone."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from media_hygiene.cli import audit_people
from tests.integration.people.test_people_command import face_rows, flat
from tests.support.cli import run
from tests.support.faces import coloured

if TYPE_CHECKING:
    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations


def test_audit_alone_never_looks_for_faces(
    cli: CliRunner, apps: list[object], locations: Locations
) -> None:
    """No option, no setting: not a word about faces."""
    output = flat(run(cli, "audit").output)
    assert "faces" not in output
    assert face_rows(locations) == 0
    assert apps == []


def test_without_a_terminal_the_audit_ends_without_faces(
    cli: CliRunner, apps: list[object], locations: Locations
) -> None:
    """The count and estimate are said; nothing waits for an answer."""
    result = run(cli, "audit", "--people")
    assert result.exit_code == 0, result.output
    output = flat(result.output)
    assert "10 photos have not been looked at for faces yet: about" in output
    assert "the two face models, 39 MB, are downloaded first" in output
    assert "Ctrl+C stops between two photos" in output
    assert "No terminal to answer in: the audit ends without faces." in output
    assert face_rows(locations) == 0
    assert apps == []


def test_yes_finds_the_faces_then_nothing_is_left(
    cli: CliRunner, apps: list[object], locations: Locations
) -> None:
    """--yes: faces found and grouped, no page; the next run has nothing to do."""
    output = flat(run(cli, "audit", "--people", "--yes").output)
    assert "10 photos analysed: 8 faces" in output
    assert "2 groups of faces alike" in output
    assert "Run 'people' to see the groups in your browser" in output
    # Copies to clean come first: 'clean' stays the next step.
    assert "What next: run 'clean'" in output
    assert face_rows(locations) == 8
    assert apps == []
    again = flat(run(cli, "audit", "--people").output)
    assert "every photo of the audit was looked at already" in again
    status = flat(run(cli, "status").output)
    assert "Faces: 8 found in 10 photos" in status


@pytest.mark.usefixtures("apps")
def test_measured_then_refused(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """With the models here, a sample is measured (and kept); a no stops there."""
    monkeypatch.setattr(audit_people, "models_present", lambda _runtime: True)
    monkeypatch.setattr(audit_people, "SAMPLE", 3)
    monkeypatch.setattr(audit_people, "has_terminal", lambda: True)
    monkeypatch.setattr(
        "media_hygiene.console.output.Output.confirm", lambda _self, _question: False
    )
    output = flat(run(cli, "audit", "--people").output)
    assert "7 photos have not been looked at for faces yet" in output
    assert "on this PC (measured on 3 photos)" in output
    assert "No face looked for: 'people', or the next 'audit --people'" in output
    assert 0 < face_rows(locations) <= 3
    monkeypatch.setattr(audit_people, "SAMPLE", 10)
    rest = flat(run(cli, "audit", "--people").output)
    assert "have not been looked at" not in rest
    assert "2 groups of faces alike" in rest
    assert face_rows(locations) == 8


def test_the_setting_and_a_cache_not_mounted(
    cli: CliRunner, apps: list[object], monkeypatch: pytest.MonkeyPatch
) -> None:
    """`[people] with_audit` asks as --people does; without /cache it only warns."""
    monkeypatch.setenv("MEDIA_HYGIENE_PEOPLE__WITH_AUDIT", "true")
    assert "No terminal to answer in" in flat(run(cli, "audit").output)
    monkeypatch.delenv("MEDIA_HYGIENE_CACHE_DIR")
    output = flat(run(cli, "audit").output)
    assert "--people keeps the faces in the cache: mount /cache" in output
    assert apps == []


def test_without_copies_naming_the_faces_comes_next(
    cli: CliRunner, apps: list[object], locations: Locations
) -> None:
    """No copy, no burst: the next step is the people page, its port published."""
    for picture in (locations.data_dir / "c").rglob("*.png"):
        picture.unlink()
    for number, person in enumerate((0, 0, 1, 1)):
        coloured(locations.data_dir / "c" / f"P{number}.png", person, (90 + number, 64))
    output = flat(run(cli, "audit", "--people", "--yes").output)
    assert (
        "What next: name the groups of faces in your browser, with 'people'." in output
    )
    assert "-p 127.0.0.1:8088:8088" in output
    assert apps == []
