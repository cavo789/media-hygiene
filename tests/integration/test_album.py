"""`album`: a folder of hard links, never seen as duplicates, undone whole."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.constants import ALBUM_MARKER
from tests.support.albums import ALBUMS, WEDDING_CATEGORY, album_files, classified
from tests.support.cli import run
from tests.support.sorting import EVENT_NAME, PARTY_SHOTS, name_first_event, snapshot

if TYPE_CHECKING:
    import pytest
    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations


def flat(text: str) -> str:
    """The output on one line, as the console wraps it.

    Args:
        text: The output.

    Returns:
        Its words, separated by single spaces.
    """
    return " ".join(text.split())


def test_an_album_of_a_category_is_linked_skipped_and_undone(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Dry run first; links to the same bytes; the audit sees no duplicate; undo."""
    photos = classified(cli, locations, monkeypatch)
    before = snapshot(photos)
    shown = run(cli, "album", "Noces", "--category", WEDDING_CATEGORY.lower())
    assert shown.exit_code == 0, shown.output
    assert "Links to make │ 3" in flat(shown.output)
    assert "add --apply" in shown.output
    assert not (locations.data_dir / ALBUMS).exists()
    made = run(cli, "album", "Noces", "--category", WEDDING_CATEGORY, "--apply")
    assert made.exit_code == 0, made.output
    assert "3 links made" in made.output
    assert "🛟 An album only adds names (hard links)" in made.output
    links = album_files(locations, "Noces")
    assert sorted(links) == ["DSC_0000.jpg", "DSC_0001.jpg", "DSC_0002.jpg"]
    for name, link in links.items():
        assert link.samefile(photos / WEDDING_CATEGORY / name)
    assert (locations.data_dir / ALBUMS / "Noces" / ALBUM_MARKER).is_file()
    again = run(cli, "album", "Noces", "--category", WEDDING_CATEGORY, "--apply")
    assert "Nothing to add" in again.output
    audit = flat(run(cli, "audit").output)
    assert "Media files scanned │ 10" in audit
    assert "Groups of identical files │ 0" in audit
    history = run(cli, "history").output
    assert "album" in history
    assert "Linked" in history
    undone = run(cli, "undo")
    assert undone.exit_code == 0, undone.output
    assert not (locations.data_dir / ALBUMS).exists()
    assert snapshot(photos) == before


def test_an_album_by_stars_reads_them_from_the_index(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Four stars and more: the two photos rated so."""
    classified(cli, locations, monkeypatch)
    made = run(cli, "album", "Best", "--rating", "4", "--apply")
    assert made.exit_code == 0, made.output
    assert sorted(album_files(locations, "Best")) == ["DSC_0001.jpg", "IMG_9000.jpg"]


def test_an_album_follows_a_sort_and_survives_its_undo(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The files are found where the sort moved them; links outlive moves."""
    classified(cli, locations, monkeypatch)
    (workbook,) = locations.reports_dir.glob("*-classify/classify.xlsx")
    name_first_event(workbook)
    assert run(cli, "sort", "--yes").exit_code == 0
    made = run(cli, "album", "Fair", "--event", EVENT_NAME, "--apply")
    assert made.exit_code == 0, made.output
    links = album_files(locations, "Fair")
    assert len(links) == PARTY_SHOTS
    found = locations.data_dir.rglob("IMG_000*.jpg")
    sorted_ = [path for path in found if "Albums" not in path.parts]
    assert len(sorted_) == PARTY_SHOTS
    assert all(EVENT_NAME in path.parts for path in sorted_)
    for link in links.values():
        assert any(link.samefile(path) for path in sorted_)
    by_category = run(cli, "album", "Fair", "--category", EVENT_NAME)
    assert "In the album already │ 6" in flat(by_category.output)
    history = run(cli, "history").output
    sort_run = next(
        line.split()[1] for line in history.splitlines() if " sort " in line
    )
    assert run(cli, "undo", "--yes", sort_run).exit_code == 0
    assert all(link.stat().st_nlink == 2 for link in links.values())


def test_undo_keeps_a_link_that_became_the_last_name(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The original deleted since: the album's name is all that is left."""
    photos = classified(cli, locations, monkeypatch)
    run(cli, "album", "Noces", "--category", WEDDING_CATEGORY, "--apply")
    (photos / WEDDING_CATEGORY / "DSC_0000.jpg").unlink()
    undone = run(cli, "undo")
    assert "may be the last name of the photo" in flat(undone.output)
    assert list(album_files(locations, "Noces")) == ["DSC_0000.jpg"]


def test_album_refusals_say_what_to_do(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No criterion, a bad name, no folder, a protected one, stars without cache."""
    classified(cli, locations, monkeypatch)
    cases = {
        ("album", "Noces"): "Say what the album gathers",
        ("album", "a/b", "--rule", "x"): "cannot be a folder name",
    }
    for args, message in cases.items():
        result = run(cli, *args)
        assert result.exit_code == 1
        assert message in flat(result.output)
    monkeypatch.setenv("MEDIA_HYGIENE_FOLDERS__PROTECTED", '["C:\\\\Photos"]')
    protected = run(cli, "album", "Noces", "--rule", "x")
    assert "inside a protected folder" in flat(protected.output)
    monkeypatch.delenv("MEDIA_HYGIENE_FOLDERS__PROTECTED")
    monkeypatch.delenv("MEDIA_HYGIENE_CACHE_DIR")
    stars = run(cli, "album", "Best", "--rating", "3")
    assert "not mounted" in flat(stars.output)
    monkeypatch.delenv("MEDIA_HYGIENE_ALBUM__ROOT")
    nowhere = run(cli, "album", "Noces", "--rule", "x")
    assert nowhere.exit_code == 1
    assert "No folder for the albums" in flat(nowhere.output)


def test_a_file_gone_since_classify_is_never_linked(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Listed as not found, with what to do."""
    photos = classified(cli, locations, monkeypatch)
    (photos / WEDDING_CATEGORY / "DSC_0000.jpg").unlink()
    shown = flat(run(cli, "album", "Noces", "--category", WEDDING_CATEGORY).output)
    assert "Not found │ 1" in shown
    assert "Run 'classify' again" in shown
