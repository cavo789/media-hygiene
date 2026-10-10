"""What a clean run says while it works: where the copies go, and the file at hand."""

from __future__ import annotations

from pathlib import Path

from media_hygiene.actions.clean_step import clean_labels, clean_step, said
from media_hygiene.constants import BrokenReason, MediaKind
from media_hygiene.paths.host_paths import HostPathMapper
from media_hygiene.scan.models import BrokenFile, MediaFile

MAPPER = HostPathMapper(Path("/data"))
VIDEO = MediaFile(Path("/data/c/Photos/clip.mp4"), 400, 0, MediaKind.VIDEO)
DOCUMENT = MediaFile(Path("/data/c/Docs/a.pdf"), 10, 0, MediaKind.OTHER)


def test_by_default_the_copies_go_to_the_quarantine() -> None:
    """Nothing is deleted by a default clean: the hint never says so."""
    hint = clean_step([], delete_copies=False).hint
    assert "before going to the quarantine" in hint
    assert "deletion" not in hint


def test_with_delete_the_copies_are_deleted() -> None:
    """`clean --delete` says plainly that the copies are deleted."""
    assert "before deletion" in clean_step([], delete_copies=True).hint


def test_the_estimate_follows_the_bytes_of_the_files() -> None:
    """The step weighs every file it handles."""
    actions = [(VIDEO, "", lambda: None), (DOCUMENT, "", lambda: None)]
    assert clean_step(actions, delete_copies=False).total_weight == 410


def test_the_line_under_the_bar_names_the_action_and_the_windows_path() -> None:
    """A copy set aside, shown with the path the user knows."""
    label = clean_labels(delete_copies=False).of_copy(VIDEO)
    line = said((VIDEO, label, lambda: None), MAPPER)
    assert line == "Moving a duplicate copy to the quarantine: C:\\Photos\\clip.mp4"


def test_with_delete_only_media_copies_are_said_deleted() -> None:
    """Copies of other files than media still go to the quarantine, and say so."""
    labels = clean_labels(delete_copies=True)
    assert labels.of_copy(VIDEO).startswith("Deleting a duplicate copy")
    assert labels.of_copy(DOCUMENT).startswith("Moving a duplicate copy")


def test_an_empty_file_is_said_deleted_an_unreadable_one_set_aside() -> None:
    """Broken files: 0 bytes deleted, unreadable ones to the quarantine."""
    labels = clean_labels(delete_copies=False)
    empty = BrokenFile(VIDEO, BrokenReason.EMPTY)
    assert labels.of_broken(empty).startswith("Deleting an empty file")
    unreadable = BrokenFile(VIDEO, BrokenReason.UNREADABLE_VIDEO)
    assert labels.of_broken(unreadable).startswith("Moving an unreadable file")
