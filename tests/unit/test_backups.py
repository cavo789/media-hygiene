"""Backup folders: compared by content, one role per folder, two lines (0204)."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from pydantic import ValidationError

from media_hygiene.cli.folder_options import FolderOptions
from media_hygiene.config.folder_roles import overlap
from media_hygiene.config.settings import FolderSettings
from media_hygiene.console.backup_view import backup_lines
from media_hygiene.constants import MediaKind
from media_hygiene.errors import DecisionsError
from media_hygiene.paths.host_paths import HostPathMapper
from media_hygiene.plan.backups import BackupCoverage, BackupFolders, ComparedFiles
from media_hygiene.report.chosen_decisions import ChosenFile
from media_hygiene.scan.models import DuplicateGroup, MediaFile
from media_hygiene.scan.walker import Walk
from media_hygiene.services.chosen_review import chosen_files
from tests.support.runtime import make_runtime

if TYPE_CHECKING:
    from media_hygiene.paths.locations import Locations

_BACKUP = Path("/data/d/backup")


def media(path: str, size: int = 10) -> MediaFile:
    """A file of the given size."""
    return MediaFile(Path(path), size, 0, MediaKind.IMAGE)


def test_a_backup_file_identical_to_two_library_files_covers_both() -> None:
    """One copy in the backup: both library files backed up, their group kept."""
    one, two = media("/data/c/a/x.jpg"), media("/data/c/b/x.jpg")
    backed = media("/data/d/backup/x.jpg")
    alone = media("/data/c/a/y.jpg", size=11)
    old = media("/data/d/backup/old.jpg", size=12)
    folders = BackupFolders((_BACKUP,))
    group = DuplicateGroup("d1", 10, (one, two))
    compared = folders.compare(
        (group,),
        ComparedFiles(
            (one, two, alone), (backed, old), {one: "p", two: "p", backed: "p"}
        ),
    )
    assert compared.groups == (group,)
    (coverage,) = compared.folders
    assert coverage.files == 2
    assert coverage.missing == (alone,)
    assert coverage.only == (old,)
    assert (coverage.missing_size, coverage.only_size) == (11, 12)


def test_a_library_file_and_its_backup_copy_form_no_group() -> None:
    """A copy only in the backup is never the reason a library file goes."""
    mine, theirs = media("/data/c/x.jpg"), media("/data/d/backup/x.jpg")
    compared = BackupFolders((_BACKUP,)).compare(
        (), ComparedFiles((mine,), (theirs,), {mine: "p", theirs: "p"})
    )
    assert not compared.groups
    assert compared.folders == (BackupCoverage(_BACKUP, files=1),)


def test_a_backup_file_matching_start_and_end_counts_as_a_copy() -> None:
    """Same size and partial digest, middle unknown: covered (0274's trade-off)."""
    mine, theirs = media("/data/c/x.jpg"), media("/data/d/backup/x.jpg")
    other = media("/data/d/backup/y.jpg")
    compared = BackupFolders((_BACKUP,)).compare(
        (),
        ComparedFiles((mine,), (theirs, other), {mine: "p", theirs: "p", other: "q"}),
    )
    (coverage,) = compared.folders
    assert not coverage.missing
    assert coverage.only == (other,)


def test_a_backup_file_of_the_same_size_but_unread_has_no_copy() -> None:
    """No partial digest (unreadable): only in the backup, the library's missing."""
    mine, theirs = media("/data/c/x.jpg"), media("/data/d/backup/x.jpg")
    compared = BackupFolders((_BACKUP,)).compare(
        (), ComparedFiles((mine,), (theirs,), {mine: "p"})
    )
    (coverage,) = compared.folders
    assert coverage.missing == (mine,)
    assert coverage.only == (theirs,)


def test_two_identical_backup_files_without_library_copy_are_only_there() -> None:
    """Twins inside the backup alone: both files are only in the backup."""
    first, second = media("/data/d/backup/a.jpg"), media("/data/d/backup/b.jpg")
    compared = BackupFolders((_BACKUP,)).compare(
        (), ComparedFiles((), (first, second), {first: "p", second: "p"})
    )
    assert not compared.groups
    assert compared.folders[0].only == (first, second)


def test_without_backup_folder_the_groups_are_unchanged() -> None:
    """No backup: the comparison hands the groups back as they are."""
    group = DuplicateGroup("d1", 10, (media("/data/c/a.jpg"), media("/data/c/b.jpg")))
    compared = BackupFolders().compare((group,), ComparedFiles((), ()))
    assert compared.groups == (group,)
    assert not compared.folders


def test_the_library_walk_leaves_backup_files_and_sidecars_out() -> None:
    """Files and sidecars below a backup folder are out of the library, case aside."""
    mine, theirs = media("/data/c/x.jpg"), media("/data/d/BACKUP/x.jpg")
    walk = BackupFolders((_BACKUP,)).library(Walk(files=(mine, theirs)))
    assert walk.files == (mine,)
    assert BackupFolders((_BACKUP,)).files_in((mine, theirs)) == (theirs,)


@pytest.mark.parametrize(
    ("role", "other"),
    [
        ("protected", "d:\\Backup"),
        ("preferred", "D:\\backup\\2019"),
        ("excluded", "D:\\"),
    ],
)
def test_a_backup_folder_has_no_other_role(role: str, other: str) -> None:
    """Same folder (case ignored on Windows), inside it or holding it: refused."""
    with pytest.raises(ValidationError) as caught:
        FolderSettings.model_validate({"backups": ["D:\\backup"], role: [other]})
    message = str(caught.value)
    assert "D:\\backup (folders.backups)" in message
    assert f"{other} (folders.{role})" in message


def test_distinct_folders_keep_their_roles() -> None:
    """A backup next to a protected folder is fine; POSIX paths keep their case."""
    folders = FolderSettings(
        backups=("D:\\backup", "/home/me/Backup"),
        protected=("D:\\backups 2", "/home/me/backup"),
    )
    assert folders.untouched == (
        "D:\\backups 2",
        "/home/me/backup",
        "D:\\backup",
        "/home/me/Backup",
    )
    assert not overlap("D:\\backup", "/data/d/backup")


def test_the_backup_option_becomes_a_setting() -> None:
    """`--backup` lands in `[folders] backups`; options not given stay out."""
    layer = FolderOptions(backup=["D:\\backup"]).layer()
    assert layer == {"folders": {"backups": ["D:\\backup"]}}
    assert not FolderOptions().layer()


def test_two_lines_say_when_nothing_is_missing_or_only_there() -> None:
    """A complete backup: one line says so, the other that nothing is only in it."""
    lacks, holds = backup_lines(
        BackupCoverage(_BACKUP, files=3), HostPathMapper(Path("/data"))
    )
    assert "every file of your photos is in this backup" in lacks
    assert "Nothing is only in it" in holds


def test_a_file_chosen_in_a_backup_folder_is_refused(locations: Locations) -> None:
    """`clean --decisions` never moves a file of a backup folder set aside earlier."""
    runtime = make_runtime(locations, {"folders": {"backups": ["D:\\backup"]}})
    chosen = ChosenFile(path="D:\\backup\\x.jpg", size=1, mtime_ns=0)
    with pytest.raises(DecisionsError, match="backup folder"):
        chosen_files(runtime, (chosen,))
