"""Named faces as `{path, id, face}` (TODO 0570): one test per event.

The settings keep `<container path>#<n>`; the files hold the host path, the content
id and the face number. The old string form loads and stays until its id is known;
the tool's moves carry the id; an audit finds a photo renamed outside, forgets the
names of an edited one, and gives an id to the old form.
"""

from __future__ import annotations

import hashlib
import tomllib
from typing import TYPE_CHECKING, Final

import pytest

from media_hygiene.config.face_refs import FaceRef, face_keys, face_line, split_key
from media_hygiene.config.people_settings import PeopleSettings
from media_hygiene.config.photo_ref import content_id
from media_hygiene.paths.host_paths import HostPathMapper
from media_hygiene.people.config_file import read_people, save_people
from media_hygiene.people.followed import follow_people
from media_hygiene.services.face_refs_audit import (
    FaceSources,
    FaceTally,
    face_files,
    rewrite_file,
    wanted_ids,
)

if TYPE_CHECKING:
    from pathlib import Path

ID: Final = "fc7749d8b88880b3:2484373"
HOST: Final = "C:\\Photos\\2024\\IMG_0096.JPG"


@pytest.fixture
def data(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """The data folder the faces' mapper uses, below `tmp_path`."""
    folder = tmp_path / "data"
    folder.mkdir()
    monkeypatch.setenv("MEDIA_HYGIENE_DATA_DIR", str(folder))
    monkeypatch.setenv("MEDIA_HYGIENE_CACHE_DIR", str(tmp_path / "cache"))
    return folder


def photo(data: Path, relative: str, content: bytes) -> tuple[Path, str]:
    """A photo on drive C: and its id."""
    path = data / "c" / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return path, content_id(hashlib.sha256(content).hexdigest(), len(content))


def people_file(config: Path, faces: str) -> Path:
    """A person whose faces file is written by hand."""
    config.write_text('[[people.person]]\nname = "Chloé"\nfile = "people/Chloé.toml"\n')
    file = config.parent / "people" / "Chloé.toml"
    file.parent.mkdir(exist_ok=True)
    file.write_text(f"# faces\nfaces = [\n{faces}\n]\n")
    return file


def audit(config: Path, data: Path, found: dict[str, list[str]]) -> FaceTally:
    """What an audit does to the people's files."""
    tally = FaceTally()
    sources = FaceSources(found, HostPathMapper(data))
    for file in face_files(config.parent):
        rewrite_file(file, sources, tally)
    return tally


def test_a_face_line_is_a_table_once_its_id_is_known(tmp_path: Path) -> None:
    """Host path, id, face; else the old string."""
    mapper = HostPathMapper(tmp_path)
    key = f"{tmp_path}/c/Photos/a.jpg#2"
    path = str(tmp_path / "c/Photos/a.jpg")
    line = face_line(key, {path: ID}, mapper)
    entry = tomllib.loads(f"x = {line}")["x"]
    assert entry == {"path": "C:\\Photos\\a.jpg", "id": ID, "face": 2}
    assert face_keys([entry], mapper) == [key]
    assert face_line(key, {}, mapper) == f'"{key}"'
    assert split_key("no number") is None


def test_both_forms_load(tmp_path: Path, data: Path) -> None:
    """The table and the form before 0570 give the same settings' keys."""
    config = tmp_path / "config.toml"
    people_file(
        config, f'  {{path = \'{HOST}\', id = "{ID}", face = 1}},\n  "/x.jpg#0",'
    )
    faces = read_people(config).person[0].faces
    assert faces == (f"{data}/c/Photos/2024/IMG_0096.JPG#1", "/x.jpg#0")


@pytest.mark.usefixtures("data")
def test_a_save_keeps_the_ids(tmp_path: Path) -> None:
    """Read then saved: the table stays a table, the unknown stays a string."""
    config = tmp_path / "config.toml"
    file = people_file(config, f"  {{path = '{HOST}', id = \"{ID}\", face = 1}},")
    before = read_people(config)
    person = before.person[0]
    more = person.model_copy(update={"faces": (*person.faces, "/new.jpg#0")})
    save_people(config, before.model_copy(update={"person": (more,)}))
    text = file.read_text()
    assert f'id = "{ID}", face = 1' in text
    assert '"/new.jpg#0"' in text


def test_sort_and_undo_carry_the_id(tmp_path: Path, data: Path) -> None:
    """A run's moves: the new path keeps the id; undone: home again."""
    config = tmp_path / "config.toml"
    file = people_file(config, f"  {{path = '{HOST}', id = \"{ID}\", face = 1}},")
    old = f"{data}/c/Photos/2024/IMG_0096.JPG"
    new = f"{data}/c/Photos/Events/IMG_0096.JPG"
    assert follow_people(config, {old: new}) == 1
    assert "C:\\Photos\\Events\\IMG_0096.JPG" in file.read_text()
    assert ID in file.read_text()
    follow_people(config, {new: old})
    assert HOST in file.read_text()
    assert ID in file.read_text()


def test_quarantine_and_back(tmp_path: Path, data: Path) -> None:
    """Set aside then restored in one go of moves: the face stays home."""
    config = tmp_path / "config.toml"
    file = people_file(config, f"  {{path = '{HOST}', id = \"{ID}\", face = 1}},")
    old = f"{data}/c/Photos/2024/IMG_0096.JPG"
    follow_people(config, {old: "/quarantine/IMG_0096.JPG"})
    follow_people(config, {"/quarantine/IMG_0096.JPG": old})
    assert HOST in file.read_text()
    assert ID in file.read_text()


def test_an_explorer_rename_is_found_by_the_audit(tmp_path: Path, data: Path) -> None:
    """The id is elsewhere: the new path, said once."""
    config = tmp_path / "config.toml"
    file = people_file(config, f"  {{path = '{HOST}', id = \"{ID}\", face = 1}},")
    assert wanted_ids(face_files(tmp_path)) == {ID}
    renamed = "C:\\Photos\\2024 Geer\\IMG_0096.JPG"
    tally = audit(config, data, {ID: [renamed]})
    assert tally.moved == 1
    assert renamed in file.read_text()


def test_a_copy_on_another_drive_changes_nothing(tmp_path: Path, data: Path) -> None:
    """The path is still among the files of its id."""
    config = tmp_path / "config.toml"
    file = people_file(config, f"  {{path = '{HOST}', id = \"{ID}\", face = 1}},")
    before = file.read_text()
    tally = audit(config, data, {ID: [HOST, "D:\\Backup\\IMG_0096.JPG"]})
    assert (tally.moved, file.read_text()) == (0, before)


def test_identical_copies_the_same_name_wins(tmp_path: Path, data: Path) -> None:
    """Two copies elsewhere: the one of the same file name, every run."""
    config = tmp_path / "config.toml"
    file = people_file(config, f"  {{path = '{HOST}', id = \"{ID}\", face = 1}},")
    copies = ["C:\\A\\copy.JPG", "C:\\B\\IMG_0096.JPG"]
    audit(config, data, {ID: copies})
    assert "C:\\B\\IMG_0096.JPG" in file.read_text()


def test_an_edited_photo_loses_its_names(tmp_path: Path, data: Path) -> None:
    """Its path now holds another content: the face is forgotten."""
    photo(data, "Photos/2024/IMG_0096.JPG", b"edited")
    config = tmp_path / "config.toml"
    file = people_file(config, f"  {{path = '{HOST}', id = \"{ID}\", face = 1}},")
    tally = audit(config, data, {})
    assert tally.dropped == 1
    assert tomllib.loads(file.read_text())["faces"] == []


def test_a_photo_not_mounted_keeps_its_name(tmp_path: Path, data: Path) -> None:
    """Found nowhere, its path unreadable: left as written."""
    config = tmp_path / "config.toml"
    file = people_file(config, f"  {{path = '{HOST}', id = \"{ID}\", face = 1}},")
    before = file.read_text()
    audit(config, data, {})
    assert file.read_text() == before


def test_the_old_form_gets_its_id(tmp_path: Path, data: Path) -> None:
    """`<path>#<n>` of a readable photo: rewritten as a table, read back."""
    path, photo_id = photo(data, "Photos/a.jpg", b"pixels")
    config = tmp_path / "config.toml"
    file = people_file(config, f'  "{path}#3",')
    tally = audit(config, data, {})
    assert tally.identified == 1
    entry = tomllib.loads(file.read_text())["faces"][0]
    assert entry == {"path": "C:\\Photos\\a.jpg", "id": photo_id, "face": 3}
    assert FaceRef.model_validate(entry).face == 3
    assert read_people(config).person[0].faces == (f"{path}#3",)


def test_the_ignored_faces_follow_too(tmp_path: Path, data: Path) -> None:
    """The ignored file is a people's file like the others."""
    path, _photo_id = photo(data, "Photos/b.jpg", b"stranger")
    config = tmp_path / "config.toml"
    save_people(config, PeopleSettings(ignored=(f"{path}#0",)))
    audit(config, data, {})
    assert "C:\\Photos\\b.jpg" in (tmp_path / "people" / "ignored.toml").read_text()
    assert read_people(config).ignored == (f"{path}#0",)
