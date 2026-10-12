"""Compare two duplicate finders: agreement, disagreements, what is set aside."""

from __future__ import annotations

from pathlib import Path

from media_hygiene.crosscheck.compare import AnalysedScope, OutsideReason, compare
from media_hygiene.scan.filters import ScanFilters

SCOPE = AnalysedScope(
    roots=(Path("/data/c/Photos"),),
    filters=ScanFilters(
        excluded=(Path("/data/c/Photos/Backup"),), excluded_names=("Thumb*",)
    ),
    broken=frozenset({Path("/data/c/Photos/cut.jpg")}),
)


def group(*names: str) -> frozenset[Path]:
    """A group of files below /data/c/Photos."""
    return frozenset(Path("/data/c/Photos") / name for name in names)


def test_same_groups_agree() -> None:
    """Identical groups, whatever their order: agreement, copies counted."""
    ours = [group("a.jpg", "b.jpg", "c.jpg"), group("d.mp4", "e.mp4")]
    result = compare(ours, list(reversed(ours)), SCOPE)
    assert result.agrees
    assert result.copies == 3
    assert not result.outside


def test_differences_are_listed_both_ways() -> None:
    """A group only one tool found, or split differently, is a disagreement."""
    result = compare(
        [group("a.jpg", "b.jpg")],
        [group("a.jpg", "b.jpg", "c.jpg")],
        SCOPE,
    )
    assert not result.agrees
    assert result.only_ours == (group("a.jpg", "b.jpg"),)
    assert result.only_theirs == (group("a.jpg", "b.jpg", "c.jpg"),)


def test_files_media_hygiene_does_not_analyse_are_set_aside() -> None:
    """Other types, folders excluded by path or name, broken files, other mounts."""
    theirs = [
        group("a.jpg", "b.jpg", "notes.txt"),
        group("x.jpg", "Backup/x.jpg"),
        group("y.jpg", "$RECYCLE.BIN/y.jpg"),
        group("t.jpg", "2019/thumbnails/t.jpg"),
        group("cut.jpg", "cut2.jpg"),
        frozenset({Path("/data/d/z.jpg"), Path("/data/d/z2.jpg")}),
    ]
    result = compare([group("a.jpg", "b.jpg")], theirs, SCOPE)
    assert result.agrees
    assert result.outside == {
        OutsideReason.EXTENSION: 1,
        OutsideReason.EXCLUDED: 3,
        OutsideReason.BROKEN: 1,
        OutsideReason.NOT_MOUNTED: 2,
    }


def test_the_folders_never_analysed_are_named_most_files_first() -> None:
    """The outermost skipped folder of each file, counted: where Czkawka looked."""
    theirs = [
        group("x.jpg", "Backup/2019/x.jpg", "Backup/2020/x.jpg"),
        group("y.jpg", "$RECYCLE.BIN/y.jpg"),
    ]
    result = compare([], theirs, SCOPE)
    assert list(result.skipped_folders.items()) == [
        (Path("/data/c/Photos/Backup"), 2),
        (Path("/data/c/Photos/$RECYCLE.BIN"), 1),
    ]


def test_files_removed_since_czkawka_ran_are_set_aside() -> None:
    """Files the walk no longer lists, or in a deleted skipped folder, are gone."""
    scope = AnalysedScope(
        roots=SCOPE.roots,
        filters=SCOPE.filters,
        broken=frozenset(),
        listed=group("a.jpg"),
        folder_exists=lambda folder: folder.name != "$RECYCLE.BIN",
    )
    theirs = [
        group("a.jpg", "b.jpg"),
        group("a.jpg", "$RECYCLE.BIN/a.jpg"),
        group("a.jpg", "Backup/a.jpg"),
    ]
    result = compare([], theirs, scope)
    assert result.agrees
    assert result.outside == {OutsideReason.GONE: 2, OutsideReason.EXCLUDED: 1}
    assert dict(result.skipped_folders) == {Path("/data/c/Photos/Backup"): 1}
