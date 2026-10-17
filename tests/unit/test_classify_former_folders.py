"""`classify` reads the folders of the copies `clean` removed, after its own (0208)."""

# classify works on naive local dates, as EXIF writes them.
# ruff: noqa: DTZ001

from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Final

import pytest

from media_hygiene.classify.engine import Scope, classify
from media_hygiene.classify.former import FormerCopy, FormerHint
from media_hygiene.classify.models import Band, MediaInput, SortReason
from media_hygiene.classify.names import former_note
from media_hygiene.classify.plan_build import build_plan
from media_hygiene.classify.rules.kinds import RuleMatch
from media_hygiene.config.classify_rules import ClassifyRule
from media_hygiene.config.classify_settings import ClassifySettings
from media_hygiene.geo.gazetteer import Gazetteer
from media_hygiene.paths.host_paths import HostPathMapper
from tests.support.located import HOME
from tests.support.towns import write_towns
from tests.unit.test_classify_engine import ROOT, SETTINGS, by_name, shot
from tests.unit.test_classify_folder_towns import FOLDER_TOWN, shots

if TYPE_CHECKING:
    from media_hygiene.classify.models import Proposal

_BACKUP: Final = Path("/data/d/Backup")
_WHEN: Final = datetime(2015, 6, 20, 14)


def removed(*folders: str) -> tuple[FormerCopy, ...]:
    """Copies removed from these folders below the backup root."""
    return tuple(
        FormerCopy(_BACKUP / folder / "IMG_0001.jpg", _BACKUP) for folder in folders
    )


def kept(relative: str, *former: str) -> MediaInput:
    """A photo below the root whose copies lay in `former` folders."""
    return replace(shot(relative, _WHEN), former=removed(*former))


def one(file: MediaInput, settings: ClassifySettings = SETTINGS) -> Proposal:
    """The proposal of one file."""
    return by_name(classify([file], settings, Scope()).proposals)[file.path.name]


def test_a_file_in_dcim_takes_the_event_of_its_removed_copy() -> None:
    """`DCIM` says nothing; `Mariage Julie 2015` does: the file goes there, marked."""
    found = one(kept("DCIM/IMG_0001.jpg", "Mariage Julie 2015"))
    assert found.category == "Mariage Julie 2015"
    assert found.reason is SortReason.EXISTING_FOLDER
    assert found.band is Band.SURE
    assert found.verdict.hint == FormerHint((_BACKUP / "Mariage Julie 2015",))


def test_its_own_folder_wins() -> None:
    """A file in `Anniversaire` keeps it, whatever its copies' folders said."""
    found = one(kept("Anniversaire/IMG_0001.jpg", "Mariage Julie 2015"))
    assert found.category == "Anniversaire"
    assert found.verdict.hint is None


def test_disagreeing_folders_give_none_and_leave_it_to_the_user() -> None:
    """`Mariage Julie` and `Noël`: neither is used; the file is left to sort."""
    found = one(kept("DCIM/IMG_0001.jpg", "Mariage Julie", "Noël"))
    assert not found.category
    assert found.reason is SortReason.NO_SIGNAL
    assert found.band is Band.MANUAL
    assert found.verdict.hint is not None
    assert not found.verdict.hint.agreed


def test_agreeing_folders_and_generic_ones_count_once() -> None:
    """Two copies in folders of one meaning, one in `DCIM`: that meaning."""
    found = one(kept("DCIM/IMG_0001.jpg", "Mariage", "2015/Mariage", "DCIM"))
    assert found.category == "Mariage"
    assert found.verdict.hint is not None
    assert found.verdict.hint.agreed


def test_a_file_without_removed_copies_is_unchanged() -> None:
    """No former folder: the same proposal as before 0208."""
    plain = shot("DCIM/IMG_0001.jpg", _WHEN)
    assert one(plain) == one(replace(plain, former=()))
    assert one(plain).verdict.hint is None


def test_the_workbook_says_where_the_hint_came_from() -> None:
    """The row's why names the removed copy's folder, as the host writes it."""
    file = kept("DCIM/IMG_0001.jpg", "Mariage Julie 2015")
    mapper = HostPathMapper(Path("/data"))
    classification = classify([file], SETTINGS, Scope())
    (row,) = build_plan(classification, SETTINGS, mapper).rows
    folder = mapper.to_host(_BACKUP / "Mariage Julie 2015")
    assert row.former == (folder,)
    assert row.why.endswith(f"(the folder of a removed copy: {folder})")
    assert row.decided_by in row.why
    assert former_note((), agreed=True) == ""
    assert "disagree" in former_note(("a", "b"), agreed=False)


@pytest.fixture(name="towns")
def towns_fixture(tmp_path: Path) -> Gazetteer:
    """The tiny snapshot."""
    return Gazetteer.load(write_towns(tmp_path))


def test_a_town_folder_of_a_removed_copy_names_the_place(towns: Gazetteer) -> None:
    """Photos in `DCIM` whose copies lay in `2017/Durbuy`: Durbuy, marked."""
    settings = ClassifySettings.model_validate(
        {"rules": (FOLDER_TOWN,), "places": (HOME,)}
    )
    files = [
        replace(
            file,
            former=(FormerCopy(_BACKUP / "2017/Durbuy" / file.path.name, _BACKUP),),
        )
        for file in shots("DCIM")
    ]
    found = classify(files, settings, Scope(towns=towns)).proposals
    assert {p.category for p in found} == {"Belgium/Durbuy"}
    assert {p.verdict.hint for p in found} == {FormerHint((_BACKUP / "2017/Durbuy",))}
    own = [replace(file, path=ROOT / "Bruges" / file.path.name) for file in files]
    found = classify(own, settings, Scope(towns=towns)).proposals
    assert {p.category for p in found} == {"Belgium/Bruges"}
    assert {p.verdict.hint for p in found} == {None}


def test_disagreeing_town_folders_name_no_place(towns: Gazetteer) -> None:
    """One copy in `Durbuy`, another in `Nice`: no town."""
    settings = ClassifySettings.model_validate(
        {"rules": (ClassifyRule(name="Towns", match=RuleMatch.FOLDER_TOWN),)}
    )
    files = [
        replace(
            file,
            former=(
                FormerCopy(_BACKUP / "Durbuy" / file.path.name, _BACKUP),
                FormerCopy(_BACKUP / "Nice" / file.path.name, _BACKUP),
            ),
        )
        for file in shots("DCIM")
    ]
    found = classify(files, settings, Scope(towns=towns)).proposals
    assert {p.reason for p in found} == {SortReason.NO_SIGNAL}
