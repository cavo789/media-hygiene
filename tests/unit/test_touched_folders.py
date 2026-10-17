"""The folders a run changed: where each file was, went, and was set aside."""

from __future__ import annotations

from media_hygiene.actions.journal import JournalEntry
from media_hygiene.actions.kinds import ActionKind, Phase, Status
from media_hygiene.index.touched_folders import touched_folders


def _entry(action: ActionKind, path: str, **extra: str) -> JournalEntry:
    """A `done` entry of a clean."""
    entry = JournalEntry(
        seq=1,
        phase=Phase.CLEAN,
        status=Status.DONE,
        action=action,
        path=path,
        host_path=path,
        size=0,
        mtime_ns=0,
    )
    return entry.model_copy(update=extra)


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
