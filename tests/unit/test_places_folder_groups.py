"""TODO 0383: the folders of one town are one line of the map page, one pin."""

from __future__ import annotations

from pathlib import Path

from media_hygiene.config.places_settings import FolderPosition
from media_hygiene.places.config_folders import read_folders, save_folders
from media_hygiene.places.folder_act import FolderAct, FolderAction
from media_hygiene.places.folder_groups import folder_groups, group_photos, groups_json
from media_hygiene.places.folder_rows import FolderRow


def _row(folder: str, town: str = "Turin", **changes: object) -> FolderRow:
    """A folder of the list: unsaved at Turin's centre, found, one photo."""
    values: dict[str, object] = {
        "country": "IT",
        "latitude": 45.07,
        "longitude": 7.68,
        "saved": False,
        "found": True,
        "photos": (Path(f"/data/c/{folder}/a.jpg"),),
    } | changes
    return FolderRow(folder, town, **values)  # type: ignore[arg-type]


def test_three_turin_folders_are_one_group_with_two_positions() -> None:
    """Two saved at different points, one not: one group, pinned at the first."""
    rows = (
        _row("2019/Turin", saved=True, latitude=45.1, longitude=7.7),
        _row("2023/turin", town="turin", saved=True, latitude=45.2, longitude=7.6),
        _row("2024/Turin"),
        _row("Mariage", town="", saved=True),  # placed by hand: alone
        _row("2020/Turin", found=False, saved=True),  # ⚠ not found: alone
    )

    groups = folder_groups(rows)
    assert len(groups) == 1
    group = groups[0]

    assert group.ranks == (0, 1, 2)
    assert (group.positions, group.latitude, group.longitude) == (2, 45.1, 7.7)
    assert len(group_photos(rows, group)) == 3
    assert groups_json([group])[0]["folders"] == [0, 1, 2]


def test_one_name_in_two_countries_is_two_groups_and_one_folder_none() -> None:
    """Paris FR and Paris US do not meet; a single folder is its own line."""
    rows = (
        _row("a/Paris", town="Paris", country="FR"),
        _row("b/Paris", town="Paris", country="US"),
        _row("c/Paris", town="Paris", country="FR"),
        _row("d/Paris", town="Paris", country="US"),
        _row("e/Lyon", town="Lyon", country="FR"),
    )

    groups = folder_groups(rows)

    assert [group.ranks for group in groups] == [(0, 2), (1, 3)]
    assert all(group.positions == 0 for group in groups)


def test_a_group_is_saved_in_one_write_then_forgotten_comments_kept(
    tmp_path: Path,
) -> None:
    """Every folder written once; forget takes them out, not the others."""
    config = tmp_path / "config.toml"
    config.write_text(
        '# my notes\n[[places.folders]]\nfolder = "C:\\\\Other"\n'
        "latitude = 1.0\nlongitude = 2.0\n",
        "utf-8",
    )
    act = FolderAct(
        action=FolderAction.SAVE,
        folder="C:\\2019\\Turin",
        together=("C:\\2019\\Turin", "C:\\2023\\Turin"),
        latitude=45.0,
        longitude=7.0,
    )

    save_folders(config, act.changes())
    saved = read_folders(config)
    forget = act.model_copy(update={"action": FolderAction.FORGET})
    save_folders(config, forget.changes())

    assert [position.folder for position in saved] == [
        "C:\\Other",
        "C:\\2019\\Turin",
        "C:\\2023\\Turin",
    ]
    assert {position.latitude for position in saved[1:]} == {45.0}
    assert read_folders(config) == (
        FolderPosition(folder="C:\\Other", latitude=1.0, longitude=2.0),
    )
    assert config.read_text("utf-8").startswith("# my notes")
