"""`places`: the folders named after a town, placed on the map, saved in `config.toml`.

TODO 0231. A folder `Saint-Jean de Luz` holds two photos without GPS: listed at the
town's centre; its position saved, read back, forgotten; its name said to be no town;
a saved folder renamed since is listed as not found; `xmp` writes the saved position.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Final

from media_hygiene.places.config_folders import read_folders, read_ignored
from media_hygiene.services import places as places_service
from media_hygiene.tags.xmp_doc import parse
from media_hygiene.tags.xmp_gps import LATITUDE, coordinate
from media_hygiene.tags.xmp_places import simple_value
from tests.support.cli import run
from tests.support.places_map import audited_garden, call, fake_server, gps_on, open_map
from tests.support.scenes import Shot, write_shot

if TYPE_CHECKING:
    import pytest
    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations
    from media_hygiene.places.app import PlacesApp
    from media_hygiene.review.http import Response

HOST: Final = "C:\\Photos\\2019\\Saint-Jean de Luz"
BEACH: Final = {"latitude": 43.3889, "longitude": -1.6698}  # the bay, not the centre
JPEG_START: Final = b"\xff\xd8"


def _tree(locations: Locations, monkeypatch: pytest.MonkeyPatch) -> CliRunner:
    """The garden (located), and two unlocated photos in `Saint-Jean de Luz`."""
    folder = locations.data_dir / "c" / "Photos" / "2019" / "Saint-Jean de Luz"
    for seed in (31, 32):
        write_shot(folder / f"IMG_{seed}.jpg", Shot(seed))
    return audited_garden(locations, monkeypatch)


def _folders(answer: Response) -> list[dict[str, object]]:
    """The folders of an answer."""
    found: list[dict[str, object]] = json.loads(answer.body)["folders"]
    return found


def test_a_folder_named_after_a_town_is_listed_with_its_photos(
    locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """At the town's centre, two photos without GPS, their previews served."""
    runner = _tree(locations, monkeypatch)
    seen: list[Response] = []

    async def act(app: PlacesApp) -> None:
        seen.append(await call(app, "GET /api/folders"))
        seen.append(await call(app, "GET /api/folder/0"))
        first = json.loads(seen[-1].body)["photos"][0]["preview"]
        seen.append(await call(app, f"GET {first}"))
        seen.append(await call(app, "GET /api/folder/9"))

    monkeypatch.setattr(places_service, "run_server", fake_server(act))
    assert run(runner, "places").exit_code == 0
    listed, photos, preview, unknown = seen[0], seen[1], seen[2], seen[3]
    [folder] = _folders(listed)
    assert (folder["folder"], folder["town"], folder["count"]) == (
        HOST,
        "Saint-Jean-de-Luz",
        2,
    )
    assert (folder["saved"], folder["found"], folder["videos"]) == (False, True, 0)
    shown = json.loads(photos.body)["photos"]
    assert sorted(photo["name"] for photo in shown) == ["IMG_31.jpg", "IMG_32.jpg"]
    assert {photo["folder"] for photo in shown} == {HOST}  # 0233: the host path
    assert preview.body.startswith(JPEG_START)
    assert unknown.status == 404


def test_save_forget_and_ignore_are_read_back(
    locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Each answer is the file read again; an unknown folder is refused."""
    runner = _tree(locations, monkeypatch)
    save = {"action": "save", "folder": HOST, **BEACH}
    answers = open_map(
        monkeypatch,
        runner,
        [
            ("GET /api/folders", None),
            ("POST /api/folder", save),
            ("POST /api/folder", {"action": "forget", "folder": HOST}),
            ("POST /api/folder", {"action": "save", "folder": "C:\\Elsewhere"}),
            ("POST /api/folder", {"action": "ignore", "folder": HOST}),
        ],
    )
    saved = _folders(answers[1])[0]
    assert (saved["saved"], saved["latitude"], saved["longitude"]) == (
        True,
        BEACH["latitude"],
        BEACH["longitude"],
    )
    assert not _folders(answers[2])[0]["saved"]
    assert answers[3].status == 422
    assert "is not one of the folders listed" in json.loads(answers[3].body)["error"]
    assert _folders(answers[4]) == []
    config = locations.config_file
    assert not read_folders(config)
    assert read_ignored(config) == ("Saint-Jean de Luz",)


def test_a_name_ignored_from_its_line_is_restored_from_the_set_aside_fold(
    locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """0235: the line's ✕ ignores the name, Restore lists it again; comments kept."""
    runner = _tree(locations, monkeypatch)
    config = locations.config_file
    comments = [
        line for line in config.read_text("utf-8").splitlines() if line.startswith("#")
    ]
    assert comments  # the default file, written by the audit
    name = "Saint-Jean de Luz"
    answers = open_map(
        monkeypatch,
        runner,
        [
            ("GET /api/folders", None),
            ("POST /api/folder", {"action": "ignore", "folder": HOST}),
            ("POST /api/folder", {"action": "restore", "folder": name.upper()}),
        ],
    )
    assert json.loads(answers[0].body)["ignored"] == []
    ignored = json.loads(answers[1].body)
    assert (ignored["folders"], ignored["ignored"]) == ([], [name])
    restored = json.loads(answers[2].body)
    assert restored["ignored"] == []
    assert [row["folder"] for row in restored["folders"]] == [HOST]
    assert not read_ignored(config)
    kept = [
        line for line in config.read_text("utf-8").splitlines() if line.startswith("#")
    ]
    assert kept == comments


def test_a_saved_folder_renamed_since_is_not_found_and_xmp_says_so(
    locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Renamed in Explorer after saving: listed as not found; xmp warns, never fails."""
    runner = _tree(locations, monkeypatch)
    save = {"action": "save", "folder": HOST, **BEACH}
    open_map(
        monkeypatch, runner, [("GET /api/folders", None), ("POST /api/folder", save)]
    )
    folder = locations.data_dir / "c" / "Photos" / "2019" / "Saint-Jean de Luz"
    folder.rename(folder.with_name("Luz"))
    listed = open_map(monkeypatch, runner, [("GET /api/folders", None)])[0]
    gone = next(row for row in _folders(listed) if row["folder"] == HOST)
    assert (gone["saved"], gone["found"]) == (True, False)
    config = locations.config_file
    gps_on(config)
    shown = run(runner, "xmp")
    assert shown.exit_code == 0, shown.output
    assert "cannot be found" in " ".join(shown.output.split())


def test_xmp_writes_the_saved_position_not_the_towns_centre(
    locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The bay where the photos were taken, with the town and country of the folder."""
    runner = _tree(locations, monkeypatch)
    save = {"action": "save", "folder": HOST, **BEACH}
    open_map(
        monkeypatch, runner, [("GET /api/folders", None), ("POST /api/folder", save)]
    )
    config = locations.config_file
    gps_on(config)
    written = run(runner, "xmp", "--apply")
    assert written.exit_code == 0, written.output
    folder = locations.data_dir / "c" / "Photos" / "2019" / "Saint-Jean de Luz"
    doc = parse((folder / "IMG_31.jpg.xmp").read_bytes())
    assert simple_value(doc, LATITUDE) == coordinate(BEACH["latitude"], "NS")


def test_the_folders_of_one_town_are_one_group_saved_together(
    locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """TODO 0383: 2019 and 2023 of one town: one group, its photos, one save."""
    later = locations.data_dir / "c" / "Photos" / "2023" / "Saint-Jean de Luz"
    write_shot(later / "IMG_41.jpg", Shot(41))
    runner = _tree(locations, monkeypatch)
    other = "C:\\Photos\\2023\\Saint-Jean de Luz"
    save = {"action": "save", "folder": HOST, "together": [HOST, other], **BEACH}
    answers = open_map(
        monkeypatch,
        runner,
        [
            ("GET /api/folders", None),
            ("GET /api/group/0", None),
            ("POST /api/folder", save),
            ("POST /api/folder", {**save, "action": "forget"}),
        ],
    )
    [group] = json.loads(answers[0].body)["groups"]
    assert len(group["folders"]) == 2
    assert group["positions"] == 0
    shown = json.loads(answers[1].body)["photos"]
    assert sorted(photo["name"] for photo in shown) == [
        "IMG_31.jpg",
        "IMG_32.jpg",
        "IMG_41.jpg",
    ]
    placed = _folders(answers[2])
    assert all(folder["saved"] for folder in placed)
    assert json.loads(answers[2].body)["groups"][0]["positions"] == 1
    assert not any(folder["saved"] for folder in _folders(answers[3]))
    assert not read_folders(locations.config_file)
