"""One quarantine per drive (0183): `clean`, `undo`, `purge`, `status` across C: and D:.

The demo tree has photos on `c/` and `d/`; Docker Desktop's mount table is faked: C:
for `/quarantine`, D:'s own quarantine on `/quarantine/d`. A copy of D: then stays on
D:, one of C: on C:, and a drive whose quarantine is not mounted any more stops
`undo` and `purge` with its name.
"""

from __future__ import annotations

import hashlib
import shutil
from typing import TYPE_CHECKING

from media_hygiene.index.repository import FactsRepository
from media_hygiene.paths.mounts import MountTable
from tests.support.cli import run

if TYPE_CHECKING:
    from pathlib import Path

    import pytest
    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations


def mount(
    locations: Locations, monkeypatch: pytest.MonkeyPatch, *, d_quarantine: bool
) -> Path:
    """Fake the mount table: data of C: and D:, D:'s quarantine when asked.

    Returns:
        D:'s quarantine folder, created as Docker does (empty) in both cases.
    """
    data, quarantine = locations.data_dir, locations.quarantine_dir
    own = quarantine / "d"
    own.mkdir(exist_ok=True)
    points = {data / "c", data / "d", quarantine}
    sources = [
        (data / "c", "C:\\"),
        (data / "d", "D:\\"),
        (quarantine, "C:\\Users\\me\\media-hygiene\\quarantine"),
    ]
    if d_quarantine:
        points.add(own)
        sources.append((own, "D:\\media-hygiene\\quarantine"))
    table = MountTable(frozenset(points), tuple(sources))
    monkeypatch.setattr(MountTable, "current", classmethod(lambda _cls: table))
    return own


def digests(root: Path) -> dict[str, str]:
    """The SHA-256 of every file below a folder."""
    return {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def files(folder: Path) -> list[str]:
    """The files below a folder, relative to it."""
    return sorted(
        str(path.relative_to(folder)) for path in folder.rglob("*") if path.is_file()
    )


def clean(cli: CliRunner, locations: Locations) -> str:
    """Clean; return the run."""
    result = run(cli, "clean", "--yes")
    assert result.exit_code == 0, result.output
    assert "will be copied from" not in " ".join(result.output.split())
    return max(path.stem for path in locations.journal_dir.glob("*.jsonl"))


def test_each_file_stays_on_its_drive_and_undo_brings_both_back(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """C:'s copies in /quarantine, D:'s in /quarantine/d; undo restores every byte."""
    own = mount(locations, monkeypatch, d_quarantine=True)
    before = digests(locations.data_dir)
    run_id = clean(cli, locations)
    on_c = files(locations.quarantine_dir / run_id)
    on_d = files(own / run_id)
    assert on_c
    assert all(name.startswith("c/") for name in on_c)
    assert on_d
    assert all(name.startswith("d/") for name in on_d)
    status = " ".join(run(cli, "status").output.split())
    assert f"{len(on_c) + len(on_d)} files" in status
    result = run(cli, "undo", run_id, "--yes")
    assert result.exit_code == 0, result.output
    assert digests(locations.data_dir) == before
    assert not (own / run_id).exists()
    assert not (locations.quarantine_dir / run_id).exists()
    assert own.is_dir()  # the drive's quarantine itself stays


def test_purge_empties_both_quarantines(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """One run on two drives: `purge` erases it on both, the drive folder stays."""
    own = mount(locations, monkeypatch, d_quarantine=True)
    run_id = clean(cli, locations)
    result = run(cli, "purge", "--yes")
    assert result.exit_code == 0, result.output
    assert not (locations.quarantine_dir / run_id).exists()
    assert not (own / run_id).exists()
    assert own.is_dir()
    assert "The quarantine is empty" in run(cli, "purge", "--yes").output


def test_a_drive_unplugged_stops_undo_and_purge(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """D:'s quarantine gone, an empty `d` left by Docker: refused, nothing changed."""
    own = mount(locations, monkeypatch, d_quarantine=True)
    run_id = clean(cli, locations)
    away = own.with_name("unplugged")
    own.rename(away)
    mount(locations, monkeypatch, d_quarantine=False)  # `d` again, empty, no mount
    before = digests(locations.data_dir), digests(locations.quarantine_dir)
    for command in (("undo", run_id, "--yes"), ("purge", run_id)):
        result = run(cli, *command)
        assert result.exit_code == 1, (command, result.output)
        text = " ".join(result.output.split())
        assert "quarantine of D:, which is not mounted (/quarantine/d)" in text
        assert "nothing was changed" in text
        assert (
            digests(locations.data_dir),
            digests(locations.quarantine_dir),
        ) == before
    assert files(away / run_id)
    result = run(cli, "purge", "--yes")  # every run: that one kept, named
    assert result.exit_code == 0, result.output
    text = " ".join(result.output.split())
    assert f"Kept, their drive's quarantine not mounted: {run_id} (D:)" in text
    assert (digests(locations.data_dir), digests(locations.quarantine_dir)) == before


def test_purge_of_every_run_erases_those_whose_drive_is_mounted(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A run of C: only is erased while the one on the unplugged D: is kept."""
    own = mount(locations, monkeypatch, d_quarantine=True)
    on_both = clean(cli, locations)
    own.rename(own.with_name("unplugged"))
    mount(locations, monkeypatch, d_quarantine=False)
    on_c = locations.quarantine_dir / "20200101-000000"
    (on_c / "c").mkdir(parents=True)
    (on_c / "c" / "a.jpg").write_bytes(b"set aside")
    result = run(cli, "purge", "--yes")
    assert result.exit_code == 0, result.output
    assert not on_c.exists()
    assert (locations.quarantine_dir / on_both).is_dir()


def test_an_interrupted_move_never_done_holds_nothing_back(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Only `done` moves count: a `pending` line alone is not a file on D:."""
    own = mount(locations, monkeypatch, d_quarantine=True)
    run_id = clean(cli, locations)
    journal = locations.journal_dir / f"{run_id}.jsonl"
    kept = [
        line
        for line in journal.read_text(encoding="utf-8").splitlines()
        if '"status":"done"' not in line.replace(" ", "")
        or "/quarantine/d/" not in line
    ]
    assert len(kept) < len(journal.read_text(encoding="utf-8").splitlines())
    journal.write_text("\n".join(kept) + "\n", encoding="utf-8")
    own.rename(own.with_name("unplugged"))
    mount(locations, monkeypatch, d_quarantine=False)
    result = run(cli, "undo", run_id, "--yes")
    assert "which is not mounted" not in " ".join(result.output.split())


def test_the_drive_folder_is_never_a_run(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The empty `d` Docker leaves in /quarantine: no run, not purged by name."""
    mount(locations, monkeypatch, d_quarantine=False)
    result = run(cli, "purge", "d")
    assert result.exit_code == 1
    assert "Run d has no quarantine" in result.output
    assert (locations.quarantine_dir / "d").is_dir()
    assert "The quarantine is empty" in run(cli, "purge", "--yes").output


def remount(
    locations: Locations, monkeypatch: pytest.MonkeyPatch, letters: tuple[str, ...]
) -> None:
    """D: plugged back under other letters: its data and quarantine moved, mounted."""
    data, quarantine = locations.data_dir, locations.quarantine_dir
    for letter in letters:
        if not (data / letter).exists():
            (data / "d").rename(data / letter)
            (quarantine / "d").rename(quarantine / letter)
        (quarantine / letter).mkdir(exist_ok=True)
    (quarantine / "d").mkdir(exist_ok=True)  # the empty folder Docker leaves
    points = {data / "c", quarantine} | {
        root / letter for letter in letters for root in (data, quarantine)
    }
    sources = [(data / "c", "C:\\"), (quarantine, "C:\\Users\\me\\q")] + [
        (data / letter, f"{letter.upper()}:\\") for letter in letters
    ]
    table = MountTable(frozenset(points), tuple(sources))
    monkeypatch.setattr(MountTable, "current", classmethod(lambda _cls: table))


def test_undo_finds_a_run_whose_drive_came_back_under_another_letter(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """0186: D: back as E:: the run found in E:'s quarantine, said, every byte back."""
    mount(locations, monkeypatch, d_quarantine=True)
    before = digests(locations.data_dir / "d")
    run_id = clean(cli, locations)
    remount(locations, monkeypatch, ("e",))
    result = run(cli, "undo", run_id, "--yes")
    assert result.exit_code == 0, result.output
    text = " ".join(result.output.split())
    assert f"Run {run_id} found in the quarantine of E:, not of D:." in text
    assert digests(locations.data_dir / "e") == before
    assert not (locations.quarantine_dir / "e" / run_id).exists()
    with FactsRepository.open(locations.index_file) as repository:  # facts kept
        assert not repository.connection.execute("SELECT * FROM parked").fetchall()


def test_a_run_folder_on_two_drives_is_refused(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """0186: the run's folder in E:'s and F:'s quarantines: a copy, nothing guessed."""
    mount(locations, monkeypatch, d_quarantine=True)
    run_id = clean(cli, locations)
    remount(locations, monkeypatch, ("e",))
    copy = locations.quarantine_dir / "f" / run_id / "d"  # D:'s files, copied by hand
    copy.mkdir(parents=True)
    (locations.data_dir / "f").mkdir()
    remount(locations, monkeypatch, ("e", "f"))
    before = digests(locations.data_dir), digests(locations.quarantine_dir)
    for command in (("undo", run_id, "--yes"), ("purge", run_id)):
        result = run(cli, *command)
        assert result.exit_code == 1, (command, result.output)
        text = " ".join(result.output.split())
        assert "is in the quarantines of E:, F:: nothing was changed" in text
        assert (
            digests(locations.data_dir),
            digests(locations.quarantine_dir),
        ) == before


def test_a_file_whose_folder_is_gone_under_the_new_letter_stays_aside(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """0186: never restored onto a guessed path: that file refused, the others back."""
    mount(locations, monkeypatch, d_quarantine=True)
    run_id = clean(cli, locations)
    remount(locations, monkeypatch, ("e",))
    aside = files(locations.quarantine_dir / "e" / run_id)
    gone = locations.data_dir / aside[0]
    gone_folder = (
        locations.data_dir / "e" / gone.relative_to(locations.data_dir / "d").parent
    )
    while not gone_folder.exists():  # removed by the clean once empty (0202)
        gone_folder = gone_folder.parent
    shutil.rmtree(gone_folder)
    result = run(cli, "undo", run_id, "--yes")
    text = " ".join(result.output.split())
    assert "its folder is not on the drive under its new letter" in text
    assert not gone_folder.exists()
    assert (locations.quarantine_dir / "e" / run_id / aside[0]).is_file()


def test_purge_finds_a_run_whose_drive_came_back_under_another_letter(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """0186: `purge <run>` erases it in E:'s quarantine instead of refusing."""
    mount(locations, monkeypatch, d_quarantine=True)
    run_id = clean(cli, locations)
    remount(locations, monkeypatch, ("e",))
    result = run(cli, "purge", run_id, "--yes")
    assert result.exit_code == 0, result.output
    assert not (locations.quarantine_dir / "e" / run_id).exists()
