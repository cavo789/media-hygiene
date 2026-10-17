"""The folders a run changed: where each file was, went, and was set aside."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.actions.kinds import ActionKind
from media_hygiene.index.touched_folders import touched_folders
from tests.support.journaled import done_line

if TYPE_CHECKING:
    from media_hygiene.actions.journal import JournalEntry


def _entry(action: ActionKind, path: str, **extra: str) -> JournalEntry:
    """A `done` entry of a clean."""
    return done_line(action, path, **extra)


def test_every_folder_a_file_left_or_reached_is_touched() -> None:
    """The source's folder, the target's, the quarantine's, and a folder removed."""
    entries = (
        _entry(ActionKind.MOVE, "/data/c/a/x.jpg", target="/data/c/b/x.jpg"),
        _entry(
            ActionKind.QUARANTINE_BURST,
            "/data/c/r/y.jpg",
            quarantine="/quarantine/run/c/r/y.jpg",
        ),
        _entry(ActionKind.REMOVE_FOLDER, "/data/c/old"),
    )
    touched = touched_folders(entries)
    assert {
        "/data/c/a",
        "/data/c/b",
        "/data/c/r",
        "/quarantine/run/c/r",
        "/data/c/old",
        "/data/c",
    } <= touched
