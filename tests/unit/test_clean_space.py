"""Before `clean` asks: files copied to a quarantine on another drive, and room."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING

import pytest

from media_hygiene.cli.clean_confirm import confirm_clean
from media_hygiene.config.clean_settings import CleanSettings
from media_hygiene.constants import BrokenReason, MediaKind
from media_hygiene.errors import MountError
from media_hygiene.paths.drives import Drives, QuarantineRoute
from media_hygiene.paths.mounts import MountTable
from media_hygiene.plan.models import CleanPlan, KeepDecision
from media_hygiene.plan.similar_models import NearDecision
from media_hygiene.scan.models import BrokenFile, MediaFile
from media_hygiene.services.quarantine_space import (
    CrossDrive,
    Room,
    cross_drive,
    set_aside,
)
from tests.support.runtime import make_locations, make_runtime, output_of

if TYPE_CHECKING:
    from media_hygiene.services.runtime import Runtime

GB = 1024**3
PHOTO_SIZE = 3 * GB


def copies(folder: str, kind: MediaKind = MediaKind.IMAGE) -> KeepDecision:
    """A kept file and its copy, both below `folder` (a data path)."""
    kept = MediaFile(Path(f"{folder}/A/a.jpg"), PHOTO_SIZE, 0, kind)
    copy = MediaFile(Path(f"{folder}/B/a.jpg"), PHOTO_SIZE, 0, kind)
    return KeepDecision("d", PHOTO_SIZE, kept, (copy,))


def runtime_on(tmp_path: Path, sources: dict[str, str]) -> Runtime:
    """A runtime whose mount table names the Windows source of some folders.

    `sources` maps a folder below the test's data mount ("e"), or "quarantine", to
    its Windows source.
    """
    locations = make_locations(tmp_path)
    table = tuple(
        (
            locations.quarantine_dir
            if name == "quarantine"
            else locations.data_dir / name,
            source,
        )
        for name, source in sources.items()
    )
    return replace(make_runtime(locations), mounts=MountTable(frozenset(), table))


def free(monkeypatch: pytest.MonkeyPatch, size: int) -> None:
    """Pretend the quarantine's drive has `size` bytes free."""
    monkeypatch.setattr("shutil.disk_usage", lambda _folder: SimpleNamespace(free=size))


def said(runtime: Runtime, plan: CleanPlan) -> str:
    """What `clean --yes` prints before acting."""
    assert confirm_clean(runtime, plan, yes=True)
    return " ".join(output_of(runtime).split())


ON_TWO_DRIVES = {"e": "E:\\", "quarantine": "C:\\Users\\me\\media-hygiene\\quarantine"}


def test_drive_of_the_deepest_mount() -> None:
    """The deepest mount with a Windows source tells the drive; none outside."""
    drives = Drives(
        ((Path("/data"), "C:\\"), (Path("/data/e"), "e:\\Photos"), (Path("/x"), "/x"))
    )
    assert drives.drive_of(Path("/data/e/Photos/a.jpg")) == "E:"
    assert drives.drive_of(Path("/data/c/a.jpg")) == "C:"
    assert drives.drive_of(Path("/x/a.jpg")) is None
    assert drives.drive_of(Path("/elsewhere")) is None


def test_the_route_prefers_the_quarantine_of_the_drive() -> None:
    """A drive with its own quarantine keeps its files; any other uses the default."""
    drives = Drives(((Path("/data/e"), "E:\\"), (Path("/q/e"), "E:\\q")))
    route = QuarantineRoute(drives, Path("/q"), (("E:", Path("/q/e")),))
    assert route.receiving(Path("/data/e/a.jpg")) == Path("/q/e")
    assert route.receiving(Path("/data/d/a.jpg")) == Path("/q")
    assert route.crosses_drive(Path("/data/e/a.jpg")) is None


def test_photos_on_e_quarantine_on_c_says_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """One line: how many files, how big, from which drive, the room left."""
    free(monkeypatch, 40 * GB)
    runtime = runtime_on(tmp_path, ON_TWO_DRIVES)
    data = runtime.locations.data_dir
    text = said(runtime, CleanPlan((copies(f"{data}/e"),), ()))
    assert (
        "1 file (3.0 GB) will be copied from E: to the quarantine on C: "
        "(40.0 GB free there)."
    ) in text


def test_same_drive_says_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Photos and quarantine both on C:, even short of room: no line, no refusal."""
    free(monkeypatch, 0)
    runtime = runtime_on(tmp_path, {**ON_TWO_DRIVES, "e": "C:\\Photos"})
    data = runtime.locations.data_dir
    assert "will be copied" not in said(runtime, CleanPlan((copies(f"{data}/e"),), ()))


def test_no_host_source_says_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Linux or a named volume: the drives are unknown, nothing is said."""
    free(monkeypatch, 0)
    runtime = runtime_on(tmp_path, {})
    data = runtime.locations.data_dir
    assert "will be copied" not in said(runtime, CleanPlan((copies(f"{data}/e"),), ()))


def test_short_of_room_refuses_and_says_what_is_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """3 GB to copy, 2 GB free: 2 GB missing (1 GB kept free), --yes or not."""
    free(monkeypatch, 2 * GB)
    runtime = runtime_on(tmp_path, ON_TWO_DRIVES)
    data = runtime.locations.data_dir
    plan = CleanPlan((copies(f"{data}/e"),), ())
    for yes in (True, False):
        with pytest.raises(MountError) as refused:
            confirm_clean(runtime, plan, yes=yes)
        message = " ".join(refused.value.message.split())
        assert "Not enough room on C: for the quarantine" in message
        assert "1 file (3.0 GB) would be copied there from E:, 2.0 GB free" in message
        assert "2.0 GB missing (1.0 GB stay free)" in message
        assert "'purge'" in (refused.value.tip or "")
        tip = " ".join((refused.value.tip or "").split())
        assert "E:\\media-hygiene\\quarantine:/quarantine/e" in tip


def test_a_drive_with_its_own_quarantine_says_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """E:'s quarantine mounted on /quarantine/e (0183): its files stay on E:."""
    free(monkeypatch, 0)
    runtime = runtime_on(tmp_path, ON_TWO_DRIVES)
    own = runtime.locations.quarantine_dir / "e"
    sources = (*runtime.mounts.host_sources, (own, "E:\\media-hygiene\\quarantine"))
    runtime = replace(runtime, mounts=MountTable(frozenset({own}), sources))
    data = runtime.locations.data_dir
    assert "will be copied" not in said(runtime, CleanPlan((copies(f"{data}/e"),), ()))


def test_delete_counts_only_what_still_moves(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """--delete: copies are deleted; near duplicates and unreadable files still move."""
    free(monkeypatch, 0)
    runtime = runtime_on(tmp_path, ON_TWO_DRIVES)
    data = f"{runtime.locations.data_dir}/e"
    media = copies(data)
    plan = CleanPlan((media,), (), delete_copies=True)
    assert not list(set_aside(plan))
    assert said(runtime, plan)  # nothing copied: no refusal even with 0 free
    near = NearDecision(media.keeper, media.removable)
    broken = (
        BrokenFile(
            MediaFile(Path(f"{data}/bad.jpg"), 5, 0, MediaKind.IMAGE),
            BrokenReason.UNREADABLE_IMAGE,
        ),
        BrokenFile(
            MediaFile(Path(f"{data}/empty.jpg"), 0, 0, MediaKind.IMAGE),
            BrokenReason.EMPTY,
        ),
    )
    plan = CleanPlan((media,), broken, near=(near,), delete_copies=True)
    route = QuarantineRoute(
        Drives(runtime.mounts.host_sources), runtime.locations.quarantine_dir
    )
    free(monkeypatch, 100 * GB)
    (room,) = cross_drive(route, set_aside(plan), GB)
    assert (room.cross.count, room.cross.size) == (2, PHOTO_SIZE + 5)
    assert room.cross.sources == ("E:",)
    assert room.missing == 0
    assert room.cross.size + GB < room.free


@pytest.mark.parametrize(("headroom", "missing"), [(0, 0), (GB, GB)])
def test_the_headroom_is_what_stays_free(headroom: int, missing: int) -> None:
    """0191: copies that fit exactly pass with no margin, miss it with 1 GB kept."""
    cross = CrossDrive(Path("/quarantine"), "C:", ("E:",), 1, 10 * GB)
    assert Room(cross, 10 * GB, headroom).missing == missing


def test_the_headroom_setting_defaults_to_one_gigabyte() -> None:
    """0191: `[clean] quarantine_headroom_gb`, 1 by default, in bytes for `clean`."""
    assert CleanSettings().quarantine_headroom == GB
    assert CleanSettings(quarantine_headroom_gb=0).quarantine_headroom == 0
    assert CleanSettings(quarantine_headroom_gb=2.5).quarantine_headroom == 5 * GB // 2


def test_unreadable_free_space_says_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The free space cannot be read: no line, no refusal on a guess."""

    def fails(_folder: Path) -> None:
        raise OSError

    monkeypatch.setattr("shutil.disk_usage", fails)
    runtime = runtime_on(tmp_path, ON_TWO_DRIVES)
    data = runtime.locations.data_dir
    assert "will be copied" not in said(runtime, CleanPlan((copies(f"{data}/e"),), ()))
