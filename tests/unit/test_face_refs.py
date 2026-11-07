"""Named faces as `{path, id, face}` (TODO 0570): one test per event.

The settings keep `<container path>#<n>`; the files hold the host path, the content
id and the face number. The old string form loads and stays until its id is known;
the tool's moves carry the id; an audit finds a photo renamed outside, forgets the
names of an edited one, and gives an id to the old form.
"""

from __future__ import annotations

import hashlib
import os
import sqlite3
import tomllib
from typing import TYPE_CHECKING, Final

import pytest

from media_hygiene.classify import hand_placed
from media_hygiene.config.face_refs import FaceRef, face_keys, face_line, split_key
from media_hygiene.config.people_settings import PeopleSettings
from media_hygiene.config.photo_ref import content_id
from media_hygiene.index.repository import FactsRepository
from media_hygiene.paths.host_paths import HostPathMapper
from media_hygiene.people.config_file import read_people, save_people
from media_hygiene.people.followed import follow_people
from media_hygiene.plan.backups import BackupFolders
from media_hygiene.services.face_ids_read import FaceIdReader
from media_hygiene.services.face_refs_audit import (
    FaceSources,
    FaceTally,
    face_files,
    rewrite_file,
    wanted_ids,
)
from media_hygiene.services.face_refs_said import (
    READ_ONCE_SAID,
    photos_to_read,
    say_reading,
)
from media_hygiene.services.photo_refs_audit import located, relocate_after_audit
from tests.support.runtime import make_locations, make_runtime, output_of

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.services.runtime import Runtime

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


def index_with(rows: list[tuple[Path, str | None]]) -> sqlite3.Connection:
    """An index whose rows match the files as they are now."""
    connection = sqlite3.connect(":memory:")
    connection.execute(
        "CREATE TABLE files (path TEXT, size INT, mtime_ns INT, full_digest TEXT)"
    )
    for path, digest in rows:
        facts = path.stat()
        connection.execute(
            "INSERT INTO files VALUES (?, ?, ?, ?)",
            (str(path), facts.st_size, facts.st_mtime_ns, digest),
        )
    return connection


@pytest.fixture
def reads(monkeypatch: pytest.MonkeyPatch) -> list[Path]:
    """Every photo read whole, in order."""
    seen: list[Path] = []

    def counted(path: Path) -> str:
        seen.append(path)
        return hashlib.sha256(path.read_bytes()).hexdigest()

    monkeypatch.setattr(hand_placed, "full_digest", counted)
    return seen


def run_reader(
    config: Path, data: Path, connection: sqlite3.Connection
) -> tuple[int, FaceTally]:
    """The count the audit says, then what it does."""
    sources = FaceSources({}, HostPathMapper(data), FaceIdReader(connection))
    files = face_files(config.parent)
    count = photos_to_read(files, sources)
    tally = FaceTally()
    for file in files:
        rewrite_file(file, sources, tally)
    connection.close()
    return count, tally


def test_a_photo_with_a_digest_is_not_read(
    tmp_path: Path, data: Path, reads: list[Path]
) -> None:
    """0635: the row of its (path, size, mtime) gives the id; nothing is read."""
    path, photo_id = photo(data, "Photos/a.jpg", b"pixels")
    config = tmp_path / "config.toml"
    file = people_file(config, f'  "{path}#0",\n  "{path}#1",')
    digest = hashlib.sha256(b"pixels").hexdigest()
    count, tally = run_reader(config, data, index_with([(path, digest)]))
    assert (count, reads, tally.identified) == (0, [], 2)
    assert photo_id in file.read_text()


def test_the_count_is_exactly_the_photos_read(
    tmp_path: Path, data: Path, reads: list[Path]
) -> None:
    """Known, unknown with 2 faces, table form, gone: 2 said, 2 read, once each."""
    known, _known_id = photo(data, "Photos/known.jpg", b"known")
    unknown, _unknown_id = photo(data, "Photos/unknown.jpg", b"unknown")
    photo(data, "Photos/edited.jpg", b"edited")
    config = tmp_path / "config.toml"
    people_file(
        config,
        f'  "{known}#0",\n  "{unknown}#0",\n  "{unknown}#1",\n'
        f"  {{path = 'C:\\Photos\\edited.jpg', id = \"{ID}\", face = 0}},\n"
        f'  "{data}/c/gone.jpg#0",\n  "no number",',
    )
    digest = hashlib.sha256(b"known").hexdigest()
    count, tally = run_reader(config, data, index_with([(known, digest)]))
    assert count == len(reads) == 2
    assert unknown in reads
    assert tally.dropped == 1


@pytest.mark.parametrize("event", ["same_size", "other_size", "touch", "replace"])
def test_a_row_older_than_the_file_is_not_trusted(
    data: Path, reads: list[Path], event: str
) -> None:
    """In-place write, atomic save, `touch`: the file is read, its true id written."""
    path, _old_id = photo(data, "Photos/a.jpg", b"before")
    connection = index_with([(path, hashlib.sha256(b"before").hexdigest())])
    content = {"same_size": b"after!", "other_size": b"longer now"}.get(
        event, b"before"
    )
    if event == "replace":
        fresh = path.with_suffix(".tmp")
        fresh.write_bytes(content)
        fresh.replace(path)
    else:
        path.write_bytes(content)
    facts = path.stat()
    os.utime(path, ns=(facts.st_atime_ns, facts.st_mtime_ns + 10**9))
    config = data.parent / "config.toml"
    file = people_file(config, f'  "{path}#0",')
    count, _tally = run_reader(config, data, connection)
    assert (count, reads) == (1, [path])
    expected = content_id(hashlib.sha256(content).hexdigest(), len(content))
    assert expected in file.read_text()


def test_a_copy_keeping_the_mtime_keeps_the_index_answer(
    tmp_path: Path, data: Path, reads: list[Path]
) -> None:
    """Same size and time: the index's contract, as for every reader of a row."""
    path, photo_id = photo(data, "Photos/a.jpg", b"before")
    connection = index_with([(path, hashlib.sha256(b"before").hexdigest())])
    facts = path.stat()
    path.write_bytes(b"after!")
    os.utime(path, ns=(facts.st_atime_ns, facts.st_mtime_ns))
    config = tmp_path / "config.toml"
    file = people_file(config, f'  "{path}#0",')
    assert run_reader(config, data, connection)[0] == 0
    assert (reads, photo_id in file.read_text()) == ([], True)


def test_the_audit_end_reads_nothing_the_index_knows(
    tmp_path: Path, reads: list[Path]
) -> None:
    """`relocate_after_audit` itself: no read, no line, the ids written."""
    locations = make_locations(tmp_path)
    runtime = make_runtime(locations)
    data = locations.data_dir
    paths = [data / "c" / f"{i}.jpg" for i in range(READ_ONCE_SAID + 1)]
    paths[0].parent.mkdir(parents=True, exist_ok=True)
    lines = []
    with FactsRepository.open(runtime.index_file) as repository:
        for path in paths:
            path.write_bytes(path.name.encode())
            facts = path.stat()
            repository.connection.execute(
                "INSERT INTO files (path, size, mtime_ns, full_digest) "
                "VALUES (?, ?, ?, ?)",
                (
                    str(path),
                    facts.st_size,
                    facts.st_mtime_ns,
                    hashlib.sha256(path.read_bytes()).hexdigest(),
                ),
            )
            lines.append(f'  "{path}#0",')
        repository.connection.commit()
    file = people_file(locations.config_file, "\n".join(lines))
    relocate_after_audit(runtime)
    assert reads == []
    assert "read once" not in output_of(runtime)
    assert tomllib.loads(file.read_text())["faces"][0]["id"]


def test_many_photos_to_read_are_said_before(tmp_path: Path) -> None:
    """0570: a line over the threshold, none up to it."""
    runtime = make_runtime(make_locations(tmp_path))
    say_reading(runtime, READ_ONCE_SAID)
    assert "read once" not in output_of(runtime)
    say_reading(runtime, READ_ONCE_SAID + 1)
    assert f"{READ_ONCE_SAID + 1} named photos read once" in output_of(runtime)


def test_the_line_is_said_when_the_index_has_no_digest(
    tmp_path: Path, reads: list[Path]
) -> None:
    """No row at all: every photo is read, and said."""
    locations = make_locations(tmp_path)
    runtime = make_runtime(locations)
    paths = [locations.data_dir / "c" / f"{i}.jpg" for i in range(READ_ONCE_SAID + 1)]
    paths[0].parent.mkdir(parents=True, exist_ok=True)
    for path in paths:
        path.write_bytes(path.name.encode())
    people_file(locations.config_file, "\n".join(f'  "{p}#0",' for p in paths))
    relocate_after_audit(runtime)
    assert len(reads) == len(paths)
    assert f"{len(paths)} named photos read once" in output_of(runtime)


def _backup_index(runtime: Runtime, photos: list[Path]) -> None:
    """Index the photos without a digest, as an audit leaves a backup's files."""
    with FactsRepository.open(runtime.index_file) as repository:
        for path in photos:
            facts = path.stat()
            repository.connection.execute(
                "INSERT INTO files (path, size, mtime_ns, full_digest) "
                "VALUES (?, ?, ?, NULL)",
                (str(path), facts.st_size, facts.st_mtime_ns),
            )
        repository.connection.commit()


def test_a_copy_only_in_a_backup_is_not_read_and_its_names_stay(
    tmp_path: Path, data: Path, reads: list[Path]
) -> None:
    """Renamed into a backup folder: not read, not found, the face as it was (0274)."""
    copy, photo_id = photo(data, "Backup/IMG_0096.JPG", b"in the backup")
    locations = make_locations(tmp_path)
    file = people_file(
        locations.config_file, f"  {{path = '{HOST}', id = \"{photo_id}\", face = 1}},"
    )
    before = file.read_text()
    runtime = make_runtime(locations, {"folders": {"backups": ["C:\\Backup"]}})
    _backup_index(runtime, [copy])
    relocate_after_audit(runtime)
    assert reads == []
    assert file.read_text() == before


def test_a_backup_row_with_a_digest_is_skipped_too(data: Path) -> None:
    """A digest in hand changes nothing: a backup's row never answers."""
    copy, photo_id = photo(data, "Backup/a.jpg", b"known")
    connection = sqlite3.connect(":memory:")
    connection.execute("CREATE TABLE files (path TEXT, size INT, full_digest TEXT)")
    digest = hashlib.sha256(b"known").hexdigest()
    connection.execute("INSERT INTO files VALUES (?, 5, ?)", (str(copy), digest))
    backups = BackupFolders((copy.parent,))
    assert not located(connection, [photo_id], backups)
    assert located(connection, [photo_id], BackupFolders()) == {photo_id: [str(copy)]}
    connection.close()


def test_a_named_photo_in_a_backup_is_not_read_for_its_id(
    tmp_path: Path, data: Path, reads: list[Path]
) -> None:
    """Old form, in a backup, no digest: not counted, not read, the line stays."""
    path, _ = photo(data, "Backup/a.jpg", b"pixels")
    config = tmp_path / "config.toml"
    file = people_file(config, f'  "{path}#0",')
    before = file.read_text()
    reader = FaceIdReader(backups=BackupFolders((path.parent,)))
    tally = FaceTally()
    sources = FaceSources({}, HostPathMapper(data), reader)
    assert photos_to_read([file], sources) == 0
    rewrite_file(file, sources, tally)
    assert reads == []
    assert (tally.identified, tally.dropped, file.read_text()) == (0, 0, before)
