"""The vocabulary of the journal: which command wrote an entry, what it did, how far."""

from __future__ import annotations

from enum import StrEnum
from typing import Final


class ActionKind(StrEnum):
    """What a run did to a file or a folder — recorded so `undo` can reverse it.

    Each kind needs its reversal in `actions/reversal.py`: `undo` refuses a kind it does
    not know rather than guess.
    """

    DELETE_DUPLICATE = "delete-duplicate"
    DELETE_EMPTY = "delete-empty"
    QUARANTINE = "quarantine"
    QUARANTINE_NEAR = "quarantine-near"
    QUARANTINE_DUPLICATE = "quarantine-duplicate"
    QUARANTINE_SIDECAR = "quarantine-sidecar"
    QUARANTINE_BURST = "quarantine-burst"
    # A file set aside in `search` (`clean --decisions`).
    QUARANTINE_CHOSEN = "quarantine-chosen"
    # A photo set aside in `review --junk` (`clean --decisions`).
    QUARANTINE_UNWANTED = "quarantine-unwanted"
    # A file set aside before by a choice, found again (a phone backup, 0216).
    QUARANTINE_RETURNED = "quarantine-returned"
    # Written by `sort`: a junk file (`Thumbs.db`) that alone kept a folder alive.
    QUARANTINE_JUNK = "quarantine-junk"
    # Written by `sort`: a file moved to `target`, a folder created, a folder left empty
    # and removed.
    MOVE = "move"
    CREATE_FOLDER = "create-folder"
    REMOVE_FOLDER = "remove-folder"
    # Written by `album`: a hard link made in the album folder (`path`) to a file
    # (`keeper`), and the marker telling the scans to skip that folder.
    LINK = "link"
    MARK_ALBUM = "mark-album"
    # Written by `clean --decisions`: a copy replaced by a hard link to its kept file
    # (`keeper`), a pair that keeps both names (0213).
    LINK_DUPLICATE = "link-duplicate"
    # Written by `xmp`: a sidecar created next to a photo, or one of another
    # application rewritten with our words (its previous bytes kept in `quarantine`).
    CREATE_XMP = "create-xmp"
    MERGE_XMP = "merge-xmp"
    # Written by `clean --decisions`: a file deleted outside the tool (the Explorer),
    # confirmed deleted on purpose in `review --gone` (0224). Nothing moves.
    MARK_GONE = "mark-gone"
    # Written by `mh phone` (0248): a file deleted from the phone, its content proven
    # on the PC — in the library (`keeper`), in the import's copy (`keeper`), or set
    # aside before on purpose. `undo` cannot put a file back on a phone.
    PHONE_LIBRARY = "phone-library"
    PHONE_IMPORTED = "phone-imported"
    PHONE_SET_ASIDE = "phone-set-aside"
    # Written by `import` (0245): a file only a backup held, copied into the library
    # (`path`) from the backup (`keeper`), proven by its SHA-256. `undo` removes the
    # copy while it still holds those bytes; the backup is never touched.
    COPY_IN = "copy-in"

    @property
    def remembered(self) -> bool:
        """Tell whether the content of a file set aside so stays set aside (0216).

        A file set aside by a choice (a burst shot, a near duplicate, a file chosen,
        an unwanted photo) is proposed again when it comes back; an exact copy (its
        content is kept) or a broken file is not.

        Returns:
            True for the kinds of `REMEMBERED`.
        """
        return self in REMEMBERED


class Phase(StrEnum):
    """Which command wrote a journal entry."""

    CLEAN = "clean"
    SORT = "sort"
    ALBUM = "album"
    XMP = "xmp"
    PHONE = "phone"
    IMPORT = "import"
    UNDO = "undo"


class Status(StrEnum):
    """Write-ahead state of a journal entry: `pending` before acting, `done` after."""

    PENDING = "pending"
    DONE = "done"


# The phases that change files; `undo` reverses one of them, but `phone`'s (0248).
ACTING_PHASES: Final = (
    Phase.CLEAN,
    Phase.SORT,
    Phase.ALBUM,
    Phase.XMP,
    Phase.PHONE,
    Phase.IMPORT,
)
# Actions on folders (an album's marker included): nothing is deleted nor freed by them.
FOLDER_ACTIONS: Final = frozenset(
    {ActionKind.CREATE_FOLDER, ActionKind.REMOVE_FOLDER, ActionKind.MARK_ALBUM}
)
# The copies of a kept file a clean removes: the kept file remembers where they lay
# (`index.former_names`); burst shots and files set aside by choice are not copies.
REMOVED_COPIES: Final = frozenset(
    {
        ActionKind.DELETE_DUPLICATE,
        ActionKind.QUARANTINE_DUPLICATE,
        ActionKind.QUARANTINE_NEAR,
    }
)
# The files set aside by a choice: their content is proposed again when it comes back.
REMEMBERED: Final = frozenset(
    {
        ActionKind.QUARANTINE_BURST,
        ActionKind.QUARANTINE_NEAR,
        ActionKind.QUARANTINE_CHOSEN,
        ActionKind.QUARANTINE_UNWANTED,
        ActionKind.QUARANTINE_RETURNED,
        ActionKind.MARK_GONE,
    }
)
# Hard links a run made: an album's (nothing freed), a copy's (its bytes freed).
LINKS: Final = frozenset({ActionKind.LINK, ActionKind.LINK_DUPLICATE})
# Journal marks: no file is deleted, moved nor freed by them (0224).
MARKS: Final = frozenset({ActionKind.MARK_GONE})
# Files deleted from a phone (0248): nothing on the PC is deleted, moved nor freed.
PHONE_DELETIONS: Final = frozenset(
    {ActionKind.PHONE_LIBRARY, ActionKind.PHONE_IMPORTED, ActionKind.PHONE_SET_ASIDE}
)
# Sidecars written by `xmp`: no photo is deleted, moved nor freed by them.
XMP_ACTIONS: Final = frozenset({ActionKind.CREATE_XMP, ActionKind.MERGE_XMP})
# Files `import` copied into the library (0245): nothing is deleted nor freed.
COPIES_IN: Final = frozenset({ActionKind.COPY_IN})
