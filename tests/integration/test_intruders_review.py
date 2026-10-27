"""`review --intruders` (0428): the page that ticks intruder files to set aside."""

from __future__ import annotations

import asyncio
from http import HTTPStatus
from typing import TYPE_CHECKING

from media_hygiene.index.descriptions import PhotoVersion
from media_hygiene.report.decisions import read_decisions
from media_hygiene.review.http import Request
from media_hygiene.review.intruders_app import IntrudersApp
from media_hygiene.review.place import DecisionsPlace
from media_hygiene.search.chosen import Selection
from media_hygiene.services.chosen_place import chosen_store
from media_hygiene.services.intruders_reviewing import IntrudersDeskOnDisk
from media_hygiene.services.review_file import review_page
from tests.support.cli import run
from tests.support.json_calls import answer, call
from tests.support.runtime import make_runtime

if TYPE_CHECKING:
    from pathlib import Path

    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations
    from tests.support.media import MediaFactory

_ZIP = b"PK" + b"z" * 98
_PDF = b"%PDF" + b"p" * 46
_PROTECTED: dict[str, dict[str, object]] = {"folders": {"protected": ["C:\\Kept"]}}


def _tree(media: MediaFactory, locations: Locations) -> Path:
    """Photos with a zip, a pdf below, a companion, and a zip in a protected folder."""
    media.image("c/Photos/a.jpg")
    photos = locations.data_dir / "c" / "Photos"
    (photos / "Thumbs.db").write_bytes(b"t")
    (photos / "b.zip").write_bytes(_ZIP)
    (photos / "Trip").mkdir()
    (photos / "Trip" / "c.pdf").write_bytes(_PDF)
    (photos / "Trip" / "d.zip").write_bytes(_ZIP)
    media.image("c/Kept/k.jpg", seed=3)
    (locations.data_dir / "c" / "Kept" / "x.zip").write_bytes(_ZIP)
    return photos


def _app(locations: Locations) -> IntrudersApp:
    r"""The page's app on the test folders, `C:\Kept` protected."""
    runtime = make_runtime(locations, _PROTECTED)
    return IntrudersApp(IntrudersDeskOnDisk(runtime), b"<html></html>")


def _on_disk(locations: Locations) -> list[tuple[str, str]]:
    """The `chosen` key, read from the disk: path and found_by."""
    saved = read_decisions(locations.reports_dir / "decisions.json")
    return [(file.path, file.found_by) for file in saved.chosen]


def test_the_state_tallies_per_extension_and_folder(
    media: MediaFactory, locations: Locations
) -> None:
    """Host paths, the heaviest first; the protected folder is left out."""
    _tree(media, locations)
    state = answer(_app(locations), "GET /api/state")
    assert state["total"] == 3
    extensions = state["extensions"]
    assert isinstance(extensions, list)
    assert [(row["key"], row["count"]) for row in extensions] == [
        (".zip", 2),
        (".pdf", 1),
    ]
    folders = state["folders"]
    assert isinstance(folders, list)
    assert sorted(row["key"] for row in folders) == [
        "C:\\Photos",
        "C:\\Photos\\Trip",
    ]
    assert state["set_aside"] == []


def test_an_extension_ticked_is_saved_and_read_back(
    media: MediaFactory, locations: Locations
) -> None:
    """`.zip` alone: both zips of Photos, not the protected one; read back."""
    _tree(media, locations)
    reply = answer(_app(locations), "POST /api/intruders", {"extensions": [".ZIP"]})
    expected = [
        ("C:\\Photos\\Trip\\d.zip", "intruder"),
        ("C:\\Photos\\b.zip", "intruder"),
    ]
    assert sorted(_on_disk(locations)) == sorted(expected)
    files = reply["set_aside"]
    assert isinstance(files, list)
    assert sorted((f["path"], f["found_by"]) for f in files) == sorted(expected)


def test_extension_and_folder_both_must_match(
    media: MediaFactory, locations: Locations
) -> None:
    """`.zip` in the Trip folder: d.zip alone."""
    _tree(media, locations)
    pick = {"extensions": [".zip"], "folders": ["C:\\Photos\\Trip"]}
    answer(_app(locations), "POST /api/intruders", pick)
    assert _on_disk(locations) == [("C:\\Photos\\Trip\\d.zip", "intruder")]


def test_a_folder_ticked_takes_its_subfolders(
    media: MediaFactory, locations: Locations
) -> None:
    """The Photos folder alone: the three intruders below it."""
    _tree(media, locations)
    answer(_app(locations), "POST /api/intruders", {"folders": ["C:\\Photos"]})
    assert len(_on_disk(locations)) == 3


def test_put_back_keeps_the_files_of_the_other_pages(
    media: MediaFactory, locations: Locations
) -> None:
    """Back: the intruders leave the file; a photo chosen in `search` stays."""
    photos = _tree(media, locations)
    runtime = make_runtime(locations, _PROTECTED)
    stat = (photos / "a.jpg").stat()
    chosen_store(runtime).add(
        Selection(
            (PhotoVersion(photos / "a.jpg", stat.st_size, stat.st_mtime_ns),), "x"
        )
    )
    app = _app(locations)
    answer(app, "POST /api/intruders", {"extensions": [".pdf"]})
    assert len(_on_disk(locations)) == 2
    reply = answer(app, "POST /api/intruders", {"back": True})
    assert reply["set_aside"] == []
    assert _on_disk(locations) == [("C:\\Photos\\a.jpg", "x")]


def test_a_pick_needs_a_json_body_that_is_a_pick(
    media: MediaFactory, locations: Locations
) -> None:
    """Not a pick: 400; not JSON: refused; another verb: 405. Nothing is written."""
    _tree(media, locations)
    app = _app(locations)
    assert (
        call(app, "POST /api/intruders", {"oops": 1}).status == HTTPStatus.BAD_REQUEST
    )
    plain = {"host": "127.0.0.1:8766", "content-type": "text/plain"}
    refused = asyncio.run(app.handle(Request("POST", "/api/intruders", plain, b"{}")))
    assert refused.status == HTTPStatus.UNSUPPORTED_MEDIA_TYPE
    assert call(app, "PUT /api/intruders").status == HTTPStatus.METHOD_NOT_ALLOWED
    assert not (locations.reports_dir / "decisions.json").exists()


def test_the_page_renders_with_its_route() -> None:
    """The page names its route; the texts carry no "(s)"."""
    place = DecisionsPlace(argument="decisions.json", host="decisions.json")
    text = review_page(
        "intruders_review.html.j2", place, ("/api/intruders", "/api/file")
    ).decode()
    assert '"api/intruders"' in text
    assert "(s)" not in text


def test_the_audit_leads_to_the_page_then_clean_says_intruders(
    cli: CliRunner, media: MediaFactory, locations: Locations
) -> None:
    """Nothing else to do: the 👉 line names `review --intruders`; clean names them."""
    _tree(media, locations)
    result = run(cli, "audit")
    assert result.exit_code == 0, result.output
    said = " ".join(result.output.split())
    assert "review --intruders" in said
    answer(_app(locations), "POST /api/intruders", {"extensions": [".pdf"]})
    result = run(cli, "clean", "--yes", "--decisions", "decisions.json")
    assert result.exit_code == 0, result.output
    assert "1 intruder file is set aside" in " ".join(result.output.split())


def test_review_intruders_without_any(cli: CliRunner, media: MediaFactory) -> None:
    """No intruder file: said, and no page is served."""
    media.image("c/Photos/a.jpg")
    result = run(cli, "review", "--intruders")
    assert result.exit_code == 0, result.output
    assert "No intruder file: nothing to pick." in result.output
