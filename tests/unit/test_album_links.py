"""Album links: free names, files set aside, refusals explained, disks without links."""

from __future__ import annotations

import errno
import os
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from pydantic import ValidationError

from media_hygiene.actions.album import AlbumExecutor, AlbumRun
from media_hygiene.actions.album_links import link_blocker, why_not
from media_hygiene.actions.album_plan import Pick, plan_links
from media_hygiene.actions.journal import JournalEntry, JournalWriter, read_journal
from media_hygiene.actions.journaled import CleanContext
from media_hygiene.actions.kinds import ActionKind, Phase, Status
from media_hygiene.actions.outcome import Tally
from media_hygiene.actions.reversal import blocker, reversal_of
from media_hygiene.config.album_settings import AlbumSettings
from media_hygiene.constants import ALBUM_MARKER
from media_hygiene.paths.host_paths import HostPathMapper
from media_hygiene.paths.mounts import MountTable
from media_hygiene.scan.progress import NullProgress

if TYPE_CHECKING:
    from media_hygiene.actions.album_plan import AlbumPlan


def picks(folder: Path, *names: str) -> list[Pick]:
    """Write one small file per name in a folder of its own; pick them."""
    found = []
    for number, name in enumerate(names):
        path = folder / str(number) / name
        path.parent.mkdir(parents=True)
        path.write_bytes(name.encode())
        found.append(Pick(path, path.stat().st_size, path.stat().st_mtime_ns))
    return found


def test_names_are_free_and_files_are_never_linked_twice(tmp_path: Path) -> None:
    """A clash gets ` (2)`, case ignored; a file in the album already is skipped."""
    album = tmp_path / "album"
    album.mkdir()
    chosen = picks(tmp_path / "src", "IMG_1.jpg", "img_1.JPG", "IMG_2.jpg", "far.jpg")
    os.link(chosen[2].source, album / "renamed.jpg")
    far = chosen[3].source
    plan = plan_links(album, chosen, lambda path: path != far)
    assert [link.link.name for link in plan.links] == ["IMG_1.jpg", "img_1 (2).JPG"]
    assert plan.present == (chosen[2].source,)
    assert plan.elsewhere == (far,)
    (album / "IMG_1.jpg").write_bytes(b"other")
    (album / "IMG_1 (2).jpg").write_bytes(b"other")
    again = plan_links(album, chosen[:1], lambda _path: True)
    assert [link.link.name for link in again.links] == ["IMG_1 (3).jpg"]


def test_every_refusal_is_explained() -> None:
    """Two mounts, a disk without links, a name taken, too many names, the rest."""
    reasons = {
        code: why_not(OSError(code, os.strerror(code)))
        for code in (errno.EXDEV, errno.EPERM, errno.EEXIST, errno.EMLINK, errno.EIO)
    }
    assert "two disks or two mounts" in reasons[errno.EXDEV]
    assert "does not support hard links" in reasons[errno.EPERM]
    assert "in the album already" in reasons[errno.EEXIST]
    assert "too many names" in reasons[errno.EMLINK]
    assert reasons[errno.EIO] == os.strerror(errno.EIO)
    assert why_not(OSError("odd")) == "odd"


def make(
    tmp_path: Path, plan: AlbumPlan, *, stop: bool = False
) -> tuple[AlbumRun, Tally]:
    """Run the executor, journaled under `tmp_path`."""
    tally = Tally()
    with JournalWriter.open(tmp_path / "run.jsonl") as journal:
        context = CleanContext(
            journal,
            HostPathMapper(tmp_path),
            tmp_path / "quarantine",
            NullProgress(),
            Phase.ALBUM,
        )
        ended = AlbumExecutor(context, tally).run(plan, lambda: stop)
    return ended, tally


def test_a_disk_without_links_stops_the_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The first refusal of the disk ends the run; another error does not."""
    chosen = picks(tmp_path / "src", "a.jpg", "b.jpg", "c.jpg")
    plan = plan_links(tmp_path / "Albums" / "x", chosen, lambda _path: True)
    calls: list[int] = []

    def refuse(_source: Path, _link: Path) -> None:
        calls.append(1)
        code = errno.ENOENT if len(calls) == 1 else errno.EXDEV
        raise OSError(code, os.strerror(code))

    monkeypatch.setattr("media_hygiene.actions.album.os.link", refuse)
    ended, tally = make(tmp_path, plan)
    assert "two disks" in ended.unsupported
    assert (len(calls), tally.done, len(tally.failed)) == (2, 0, 2)
    kinds = [entry.action for entry in read_journal(tmp_path / "run.jsonl")]
    order = [ActionKind.CREATE_FOLDER, ActionKind.MARK_ALBUM, ActionKind.LINK]
    assert list(dict.fromkeys(kinds)) == order
    assert (tmp_path / "Albums" / "x" / ALBUM_MARKER).is_file()


def test_ctrl_c_stops_between_two_links(tmp_path: Path) -> None:
    """Asked to stop: nothing linked, the marker left for a second run."""
    chosen = picks(tmp_path / "src", "a.jpg")
    plan = plan_links(tmp_path / "x", chosen, lambda _path: True)
    ended, tally = make(tmp_path, plan, stop=True)
    assert ended.interrupted
    assert tally.done == 0
    again, _tally = make(tmp_path, plan)
    assert again == AlbumRun()
    assert len(read_journal(tmp_path / "run.jsonl")) == 6


def test_the_mount_of_a_path_is_the_deepest_one() -> None:
    """Two bind mounts of one drive are two mounts: no link between them."""
    table = MountTable(frozenset({Path("/"), Path("/data/c/Photos"), Path("/data/c")}))
    assert table.owner(Path("/data/c/Photos/2016/a.jpg")) == Path("/data/c/Photos")
    assert table.owner(Path("/data/c/Albums")) == Path("/data/c")
    assert MountTable(frozenset()).owner(Path("/x")) is None


def test_the_albums_root_rejects_control_characters() -> None:
    r"""`"D:\backup"` in TOML holds a backspace."""
    assert AlbumSettings(root="D:\\Albums").root == "D:\\Albums"
    with pytest.raises(ValidationError):
        AlbumSettings(root="D:\backup")


def test_undo_explains_what_it_leaves(tmp_path: Path) -> None:
    """A link gone, a marker gone: nothing to remove, and said so."""
    entry = JournalEntry(
        seq=1,
        phase=Phase.ALBUM,
        status=Status.DONE,
        action=ActionKind.LINK,
        path=str(tmp_path / "gone.jpg"),
        host_path="C:\\gone.jpg",
        size=1,
        mtime_ns=0,
    )
    assert "removed already" in (link_blocker(entry) or "")
    marker = entry.model_copy(
        update={"action": ActionKind.MARK_ALBUM, "path": str(tmp_path / ALBUM_MARKER)}
    )
    assert blocker(marker, reversal_of(marker)) == "it is gone already"
