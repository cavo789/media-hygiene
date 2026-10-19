"""`places`: any folder of the index placed from the "Any folder" list (TODO 0242).

A folder `Mariage Julie`, named after no town, holds two photos without GPS: listed in
the tree with them, its photos served, its position saved and read back from
`config.toml`, written by `xmp --apply`; a folder unknown to the index is refused; one
renamed in Explorer since the audit is refused, and once saved, listed as not found.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Final

from media_hygiene.places.config_folders import read_folders
from media_hygiene.tags.xmp_doc import parse
from media_hygiene.tags.xmp_gps import LATITUDE, coordinate
from media_hygiene.tags.xmp_places import simple_value
from tests.support.cli import run
from tests.support.places_map import audited_garden, gps_on, open_map
from tests.support.scenes import Shot, write_shot

if TYPE_CHECKING:
    from pathlib import Path

    import pytest
    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations
    from media_hygiene.review.http import Response

NAME: Final = "Mariage Julie"
HOST: Final = f"C:\\Photos\\2021\\{NAME}"
CHURCH: Final = {"latitude": 50.6326, "longitude": 5.5797}
UNPROCESSABLE: Final = 422


def _folder(locations: Locations) -> Path:
    """The wedding's folder, in the container."""
    return locations.data_dir / "c" / "Photos" / "2021" / NAME


def _tree(locations: Locations, monkeypatch: pytest.MonkeyPatch) -> CliRunner:
    """The garden (located), and two unlocated photos in `Mariage Julie`."""
    for seed in (41, 42):
        write_shot(_folder(locations) / f"IMG_{seed}.jpg", Shot(seed))
    return audited_garden(locations, monkeypatch)


def _answer(response: Response) -> dict[str, list[dict[str, object]]]:
    """The JSON of an answer."""
    found: dict[str, list[dict[str, object]]] = json.loads(response.body)
    return found


def _node(response: Response, folder: str) -> dict[str, object]:
    """One folder of the tree of an answer."""
    return next(node for node in _answer(response)["tree"] if node["folder"] == folder)


def test_a_folder_named_after_no_town_is_in_the_tree_with_its_photos(
    locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Not in the town list; in the tree under its parents, its two photos shown."""
    runner = _tree(locations, monkeypatch)
    listed = open_map(monkeypatch, runner, [("GET /api/folders", None)])[0]
    assert _answer(listed)["folders"] == []
    node = _node(listed, HOST)
    assert (node["name"], node["parent"], node["count"]) == (
        NAME,
        "C:\\Photos\\2021",
        2,
    )
    photos = _node(listed, "C:\\Photos")  # the garden's three have GPS: not counted
    assert (photos["count"], photos["parent"]) == (2, "C:\\")
    top = _node(listed, "C:\\")
    assert top["parent"] is None
    shown = open_map(
        monkeypatch,
        runner,
        [("GET /api/folders", None), (f"GET /api/tree/{node['rank']}", None)],
    )[1]
    names = sorted(str(photo["name"]) for photo in _answer(shown)["photos"])
    assert names == ["IMG_41.jpg", "IMG_42.jpg"]


def test_any_folder_is_saved_read_back_and_written_by_xmp(
    locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Saved from the tree: read back from config.toml, placed; `xmp` writes it."""
    runner = _tree(locations, monkeypatch)
    save = {"action": "save", "folder": HOST, **CHURCH}
    answers = open_map(
        monkeypatch, runner, [("GET /api/folders", None), ("POST /api/folder", save)]
    )
    [placed] = _answer(answers[1])["folders"]
    assert (placed["folder"], placed["saved"], placed["found"]) == (HOST, True, True)
    assert (placed["latitude"], placed["count"]) == (CHURCH["latitude"], 2)
    [written] = read_folders(locations.config_file)
    assert (written.folder, written.longitude) == (HOST, CHURCH["longitude"])
    config = locations.config_file
    gps_on(config)
    applied = run(runner, "xmp", "--apply")
    assert applied.exit_code == 0, applied.output
    doc = parse((_folder(locations) / "IMG_41.jpg.xmp").read_bytes())
    assert simple_value(doc, LATITUDE) == coordinate(CHURCH["latitude"], "NS")


def test_a_folder_unknown_to_the_index_is_refused(
    locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Neither a town folder nor in the index's tree: nothing is written."""
    runner = _tree(locations, monkeypatch)
    save = {"action": "save", "folder": "C:\\Photos\\Elsewhere", **CHURCH}
    answers = open_map(
        monkeypatch, runner, [("GET /api/folders", None), ("POST /api/folder", save)]
    )
    assert answers[1].status == UNPROCESSABLE
    assert "is not one of the folders listed" in json.loads(answers[1].body)["error"]
    assert not read_folders(locations.config_file)


def test_a_folder_renamed_since_is_refused_then_said_not_found_once_saved(
    locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Renamed in Explorer: the index's old name is refused; a saved one, not found."""
    runner = _tree(locations, monkeypatch)
    folder = _folder(locations)
    folder.rename(folder.with_name("Julie"))
    save = {"action": "save", "folder": HOST, **CHURCH}
    refused = open_map(
        monkeypatch, runner, [("GET /api/folders", None), ("POST /api/folder", save)]
    )[1]
    assert refused.status == UNPROCESSABLE
    assert "renamed or moved since the audit" in json.loads(refused.body)["error"]
    assert not read_folders(locations.config_file)
    folder.with_name("Julie").rename(folder)
    open_map(
        monkeypatch, runner, [("GET /api/folders", None), ("POST /api/folder", save)]
    )
    folder.rename(folder.with_name("Julie"))
    listed = open_map(monkeypatch, runner, [("GET /api/folders", None)])[0]
    [gone] = _answer(listed)["folders"]
    assert (gone["folder"], gone["saved"], gone["found"]) == (HOST, True, False)
